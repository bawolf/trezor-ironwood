#!/usr/bin/env python3
"""Run named verification lanes with revision checks and durable evidence."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CHECKS = (
    "check_build_coverage", "check_endpoint_census", "check_csimp_census",
    "check_costed_group_work_census", "check_no_umbrella_imports",
    "check_fixture_manifest",
)


def budget_status(budget):
    """Validate integer-cent commitments. Never treat absent telemetry as zero cost."""
    cap = budget["authorized_cents"]
    if type(cap) is not int or cap < 0 or budget["currency"] != "USD":
        raise ValueError("Invalid authorized budget")
    committed = 0
    ids = set()
    for entry in budget["entries"]:
        if entry["id"] in ids:
            raise ValueError("Duplicate expense ID")
        ids.add(entry["id"])
        amount = entry["cents"]
        if type(amount) is not int or amount < 0:
            raise ValueError("Expenses require nonnegative integer cents")
        if entry["status"] not in ("reserved", "spent", "cancelled"):
            raise ValueError("Unknown expense status")
        if entry["status"] != "cancelled":
            committed += amount
    if committed > cap:
        raise ValueError("Authorized budget exceeded")
    if budget["paid_execution_enabled"] is not False:
        raise ValueError("No metered paid runner exists; paid execution must remain disabled")
    return {"committed_cents": committed, "remaining_cents": cap - committed,
            "codex_dollar_metering": budget["codex_dollar_metering"],
            "paid_execution_enabled": False}


@contextmanager
def verification_lock(path):
    """An OS lock is released on exit/crash; do not unlink the lock inode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another verification run holds the lock") from error
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def baseline(root, name, revision):
    path = root / "upstream" / name
    sha = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"], text=True
    ).strip()
    if sha != revision or dirty:
        raise ValueError(f"{name}: baseline must be clean at {revision}; got {sha}, dirty={bool(dirty)}")
    return sha


def run_command(command, cwd, env, logfile, timeout, minimum_tests=0):
    start = time.monotonic()
    timed_out = False
    with logfile.open("w") as log:
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as error:
            log.write(str(error))
            return {"command": command, "returncode": 127, "passed": False,
                    "error": str(error), "log": str(logfile)}
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            # Kill the whole command group, including compiler/prover descendants.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            returncode = 124
    output = logfile.read_text(errors="replace")
    tests = sum(int(n) for n in re.findall(r"test result: ok\. (\d+) passed", output))
    tests += sum(int(n) for n in re.findall(r"^Ran (\d+) tests? in ", output, re.MULTILINE))
    return {"command": command, "returncode": returncode, "timed_out": timed_out,
            "seconds": round(time.monotonic() - start, 2), "tests_passed": tests,
            "minimum_tests": minimum_tests,
            "passed": returncode == 0 and tests >= minimum_tests,
            "log": str(logfile), "log_sha256": hashlib.sha256(logfile.read_bytes()).hexdigest()}


def lane_commands(root, lane):
    upstream = root / "upstream"
    if lane == "project":
        return [(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], 120, 13)]
    if lane == "ironwood-source":
        return [(upstream / "ironwood", ["bash", "scripts/" + name + ".sh"], 180, 0)
                for name in SOURCE_CHECKS]
    if lane == "pczt":
        base = ["cargo", "test", "--locked", "-p", "pczt", "--all-features"]
        return [(upstream / "librustzcash", base + ["--lib"], 1200, 66),
                (upstream / "librustzcash", base + ["--test", "end_to_end", "ironwood"], 1200, 4),
                (upstream / "librustzcash", base + ["--test", "firmware_compat"], 300, 4)]
    if lane == "lean":
        return [(upstream / "ironwood", ["lake", "build", "--wfail"], 3600, 0)]
    raise ValueError("Unknown lane")


def run_lane(root, lane):
    manifest = json.loads((root / "upstreams.lock.json").read_text())
    budget = budget_status(json.loads((root / "ops/budget.json").read_text()))
    required = {"project": [], "ironwood-source": ["ironwood"],
                "pczt": ["librustzcash"], "lean": ["ironwood"]}[lane]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with verification_lock(root / "work/verification.lock"):
        directory = root / "work/runs" / (timestamp + "-" + lane + "-" + uuid.uuid4().hex[:8])
        directory.mkdir(parents=True)
        report = {"lane": lane, "started_utc": timestamp, "revisions": {},
                  "budget": budget, "commands": [], "passed": False}
        try:
            for name in required:
                report["revisions"][name] = baseline(root, name, manifest["repositories"][name]["revision"])
            env = dict(os.environ)
            env.update(CARGO_HOME=str(root / "work/cargo-home"),
                       CARGO_TARGET_DIR=str(root / "work/cargo-target"), CARGO_BUILD_JOBS="4",
                       ELAN_HOME=str(root / "work/elan"), LC_ALL="C")
            env["PATH"] = str(root / "work/elan/bin") + os.pathsep + env.get("PATH", "")
            report["environment"] = {key: env[key] for key in ("LC_ALL", "CARGO_BUILD_JOBS")}
            for index, (cwd, command, timeout, minimum_tests) in enumerate(lane_commands(root, lane)):
                print(f"Running {lane}: {' '.join(command)}", flush=True)
                result = run_command(command, cwd, env, directory / f"{index:02d}.log", timeout, minimum_tests)
                result["cwd"] = str(cwd)
                report["commands"].append(result)
                print(json.dumps(result), flush=True)
                if not result["passed"]:
                    break
            else:
                # Detect changes made during verification, not only before it.
                for name in required:
                    baseline(root, name, manifest["repositories"][name]["revision"])
                report["passed"] = True
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            report["error"] = str(error)
        finally:
            report["finished_utc"] = datetime.now(timezone.utc).isoformat()
            path = directory / "report.json"
            path.write_text(json.dumps(report, indent=2) + "\n")
            print(f"Report: {path}", flush=True)
        return 0 if report["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane", choices=("project", "ironwood-source", "pczt", "lean"))
    args = parser.parse_args()
    try:
        sys.exit(run_lane(ROOT, args.lane))
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
