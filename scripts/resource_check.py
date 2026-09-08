#!/usr/bin/env python3
"""Measure the synthetic approval core and verify every signed result separately."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import uuid

from check import ROOT, baseline, budget_status, run_command, verification_lock


CASE_NAMES = [f"outputs-{n}" for n in range(1, 9)] + [f"inputs-{n}" for n in range(2, 9)]
PHASE_NAMES = ("constructor", "begin", "approve", "sign", "serialize", "teardown")
FAILURE_NAMES = ("max_cancel_drop", "max_replacement_drop", "oversize_65537_admission", "nine_action_admission")


def input_hashes():
    files = [ROOT / "Cargo.toml", ROOT / "scripts/resource_check.py", ROOT / "scripts/check.py",
             ROOT / "scripts/check_approval_dependencies.py", ROOT / "tests/test_resources.py", ROOT / "upstreams.lock.json",
             ROOT / "crates/approval/Cargo.toml", ROOT / "crates/approval/tests/common/mod.rs"]
    files += sorted((ROOT / "crates/approval/src").rglob("*.rs"))
    for name in ("resource-fixtures", "resource-probe"):
        directory = ROOT / "experiments" / name
        files += [directory / "Cargo.toml", directory / "Cargo.lock"]
        files += sorted((directory / "src").rglob("*.rs"))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def validate_phase(phase):
    fields = ("allocations", "reallocations", "deallocations", "failed_requests", "requested_bytes",
              "largest_request_bytes", "baseline_live_bytes", "peak_live_bytes", "live_bytes",
              "accounting_errors", "elapsed_ns")
    if not isinstance(phase, dict) or any(type(phase.get(k)) is not int or phase[k] < 0 for k in fields):
        raise ValueError("Missing or invalid allocation/timing metrics")
    if phase["accounting_errors"] != 0 or phase["failed_requests"] != 0:
        raise ValueError("Allocator reported an error or failed request")
    if phase["peak_live_bytes"] < max(phase["baseline_live_bytes"], phase["live_bytes"]):
        raise ValueError("Reported live bytes exceed the phase peak")
    if phase["largest_request_bytes"] > phase["requested_bytes"]:
        raise ValueError("Largest allocation exceeds cumulative requested bytes")


def validate_run(run, wire_bytes, warmup=False):
    fields = ("process_baseline_bytes", "input_capacity_bytes", "review_output_capacity_bytes",
              "teardown_retained_bytes")
    if not isinstance(run, dict) or any(type(run.get(k)) is not int or run[k] < 0 for k in fields):
        raise ValueError("Invalid run ownership metrics")
    if run["teardown_retained_bytes"] != 0 or run["input_capacity_bytes"] < wire_bytes:
        raise ValueError("Incomplete input ownership or teardown")
    phases = run.get("phases")
    if not isinstance(phases, dict) or set(phases) != set(PHASE_NAMES):
        raise ValueError("Missing measured lifecycle phase")
    live = run["process_baseline_bytes"] + run["input_capacity_bytes"]
    for name in PHASE_NAMES:
        phase = phases[name]
        validate_phase(phase)
        if phase["baseline_live_bytes"] != live:
            raise ValueError("Live allocations changed between measured phases")
        if name in ("begin", "sign") and (phase["allocations"] == 0 or (not warmup and phase["elapsed_ns"] == 0)):
            raise ValueError("Validation/signing instrumentation recorded no work")
        if warmup and phase["elapsed_ns"] != 0:
            raise ValueError("Warm-up must be untimed")
        live = phase["live_bytes"]
    if live != run["process_baseline_bytes"]:
        raise ValueError("Teardown did not restore the harness baseline")
    # The only allocation outside these phases is the owned input Vec.
    if sum(p["deallocations"] - p["allocations"] for p in phases.values()) != 1:
        raise ValueError("Allocation events do not balance the owned input copy")


def validate_measurements(data, manifest, signed_sizes):
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("Unknown measurement schema")
    for name, expected in (("warmup_runs", 1), ("recorded_runs", 5),
                           ("height", manifest["height"]), ("maximum_fee", manifest["fee_cap"])):
        if type(data.get(name)) is not int or data[name] != expected:
            raise ValueError("Measurement policy or run counts differ from the corpus")
    if data.get("oracle_verified") is not False:
        raise ValueError("Only the independent oracle may mark a report verified")
    cases = data.get("cases", [])
    if not isinstance(cases, list) or any(not isinstance(c, dict) or not isinstance(c.get("name"), str) for c in cases):
        raise ValueError("Invalid measurement cases")
    if sorted(c["name"] for c in cases) != sorted(CASE_NAMES):
        raise ValueError("Measurement must contain each of the 15 fixtures exactly once")
    fixtures = {f["name"].removesuffix(".pczt"): f for f in manifest["fixtures"]}
    if len(manifest["fixtures"]) != 15 or set(fixtures) != set(CASE_NAMES):
        raise ValueError("Manifest must describe the same 15 fixtures")
    for case in cases:
        fixture = fixtures[case["name"]]
        expected_facts = {
            "wire_bytes": fixture["byte_length"], "signed_wire_bytes": signed_sizes[fixture["name"]],
            "action_count": fixture["action_count"], "signature_count": fixture["required_signature_count"],
            "output_count": fixture["positive_output_count"], "padding_outputs": fixture["padding_output_count"],
            "dummy_spends": fixture["padding_input_count"], "anchor_present": fixture["anchor_present"],
            "ock_count": sum(fixture["ock_present"]), "sighash_hex": fixture["shielded_sighash"],
        }
        if any(type(case.get(k)) is not type(v) or case[k] != v for k, v in expected_facts.items()):
            raise ValueError("Reported fixture facts or digest differ from verified artifacts")
        if not 0 < case["wire_bytes"] <= 65536:
            raise ValueError("Invalid measured input size")
        expected_signatures = int(case["name"].split("-")[1]) if case["name"].startswith("inputs-") else 1
        if case["signature_count"] != expected_signatures:
            raise ValueError("Measured signature count differs from fixture series")
        if not isinstance(case.get("runs"), list) or len(case["runs"]) != 5:
            raise ValueError("Each fixture requires five measured runs")
        validate_run(case.get("warmup"), case["wire_bytes"], warmup=True)
        for run in case["runs"]:
            validate_run(run, case["wire_bytes"])
        summary = case.get("timing_summary_ns")
        if not isinstance(summary, dict) or set(summary) != set(PHASE_NAMES):
            raise ValueError("Missing timing summary")
        for name in PHASE_NAMES:
            times = [run["phases"][name]["elapsed_ns"] for run in case["runs"]]
            expected = {"first": times[0], "median": sorted(times)[2], "max": max(times)}
            if not isinstance(summary[name], dict) or any(type(v) is not int for v in summary[name].values()) or summary[name] != expected:
                raise ValueError("Timing summary differs from recorded runs")
    failures = data.get("failure_checks")
    if not isinstance(failures, list) or any(not isinstance(c, dict) or not isinstance(c.get("name"), str) for c in failures):
        raise ValueError("Missing failure characterization")
    if sorted(c["name"] for c in failures) != sorted(FAILURE_NAMES):
        raise ValueError("Failure checks must cover cancellation, replacement and both admission limits")
    for check in failures:
        if type(check.get("teardown_retained_bytes")) is not int or check["teardown_retained_bytes"] != 0:
            raise ValueError("Failure path retained allocations")
        phase = check.get("metrics")
        validate_phase(phase)
        if phase["live_bytes"] != phase["baseline_live_bytes"]:
            raise ValueError("Failure path did not restore its baseline")
        if check["name"].endswith("admission") and any(phase[k] != 0 for k in ("allocations", "reallocations", "deallocations")):
            raise ValueError("Oversized admission reached an allocating path")


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = ROOT / "work/runs" / f"{stamp}-resources-{uuid.uuid4().hex[:8]}"
    with verification_lock(ROOT / "work/approval-verification.lock"):
        directory.mkdir(parents=True)
        report = {"lane": "resources", "started_utc": stamp, "passed": False, "commands": []}
        try:
            report["budget"] = budget_status(json.loads((ROOT / "ops/budget.json").read_text()))
            pins = json.loads((ROOT / "upstreams.lock.json").read_text())["repositories"]
            revision = pins["librustzcash"]["revision"]
            report["revisions"] = {"librustzcash": baseline(ROOT, "librustzcash", revision)}
            report["local_inputs_sha256"] = input_hashes()
            env = dict(os.environ, CARGO_HOME=str(ROOT / "work/cargo-home"),
                       CARGO_TARGET_DIR=str(ROOT / "work/resource-target"),
                       CARGO_BUILD_JOBS="4", LC_ALL="C")
            overrides = [k for k in env if k in ("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC",
                "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_TARGET", "CARGO_BUILD_RUSTFLAGS")
                or k.startswith("CARGO_PROFILE_") or (k.startswith("CARGO_TARGET_") and k.endswith("_RUSTFLAGS"))]
            if overrides:
                raise ValueError("Remove compiler/profile environment overrides: " + ", ".join(sorted(overrides)))
            report["environment"] = {k: env[k] for k in ("CARGO_BUILD_JOBS", "LC_ALL")}

            def run(command, timeout=1200, minimum_tests=0):
                logfile = directory / f"{len(report['commands']):02d}.log"
                print("Running resources: " + " ".join(map(str, command)), flush=True)
                result = run_command(list(map(str, command)), ROOT, env, logfile, timeout, minimum_tests)
                report["commands"].append(result)
                print(json.dumps(result), flush=True)
                if not result["passed"]:
                    raise ValueError("Resource command failed; retained log: " + str(logfile))
                return logfile

            run(["rustc", "--version", "--verbose"], 30)
            run(["sysctl", "-n", "machdep.cpu.brand_string", "hw.memsize"], 30)
            binaries = {}
            for name in ("resource-fixtures", "resource-probe"):
                manifest = ROOT / "experiments" / name / "Cargo.toml"
                package = tomllib.loads(manifest.read_text())["package"]["name"]
                run([sys.executable, "scripts/check_approval_dependencies.py", manifest.with_name("Cargo.lock")], 30)
                run(["cargo", "fmt", "--manifest-path", manifest, "--check"], 120)
                run(["cargo", "clippy", "--locked", "--offline", "--manifest-path", manifest,
                     "--all-targets", "--", "-D", "warnings"])
                run(["cargo", "test", "--release", "--locked", "--offline", "--manifest-path", manifest,
                     "--", "--test-threads=1"], minimum_tests=3)
                run(["cargo", "build", "--release", "--locked", "--offline", "--manifest-path", manifest])
                binaries[name] = Path(env["CARGO_TARGET_DIR"]) / "release" / package
            report["binaries_sha256"] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                         for name, path in binaries.items()}
            metadata_log = run(["cargo", "metadata", "--format-version=1", "--locked", "--offline",
                                "--manifest-path", ROOT / "experiments/resource-probe/Cargo.toml"])
            metadata = json.loads(metadata_log.read_text())
            packages = {p["id"]: p for p in metadata["packages"]}
            monitored = ("ironwood-approval", "pczt", "orchard", "zcash_protocol", "zcash_primitives",
                         "zcash_transparent", "sapling-crypto", "zcash_note_encryption", "blake2b_simd",
                         "rand_core", "rand_chacha", "serde", "serde_core", "serde_json")
            measured_features = [{"name": packages[n["id"]]["name"],
                                  "version": packages[n["id"]]["version"], "features": n["features"]}
                                 for n in metadata["resolve"]["nodes"] if packages[n["id"]]["name"] in monitored]
            for name, expected in (("ironwood-approval", []), ("pczt", ["orchard"])):
                found = [p["features"] for p in measured_features if p["name"] == name]
                if found != [expected]:
                    raise ValueError("Builder or OS features leaked into the measured core")
            for package in measured_features:
                if any(
                        feature in package["features"] for feature in ("getrandom", "std")):
                    raise ValueError("Measured dependencies enabled OS features")
            report["measured_features"] = measured_features
            fixtures, signed = directory / "fixtures", directory / "signed"
            run([binaries["resource-fixtures"], "generate", fixtures])
            fixture_hashes = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in fixtures.iterdir() if p.is_file()}
            measurements = run([binaries["resource-probe"], fixtures, signed])
            data = json.loads(measurements.read_text())
            manifest = json.loads((fixtures / "manifest.json").read_text())
            signed_sizes = {p.name: p.stat().st_size for p in signed.iterdir() if p.is_file()}
            validate_measurements(data, manifest, signed_sizes)
            run([binaries["resource-fixtures"], "verify", fixtures, signed])
            for name, digest in fixture_hashes.items():
                if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                    raise ValueError("Fixture bytes changed during measurement or verification")
            report["artifacts_sha256"] = fixture_hashes | {
                str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in signed.iterdir() if p.is_file()}
            data["oracle_verified"] = True
            (directory / "measurements.json").write_text(json.dumps(data, indent=2) + "\n")
            baseline(ROOT, "librustzcash", revision)
            if {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in binaries.items()} != report["binaries_sha256"]:
                raise ValueError("Executables changed during measurement or verification")
            if input_hashes() != report["local_inputs_sha256"]:
                raise ValueError("Sources changed during resource verification")
            report["passed"] = True
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            report["error"] = str(error)
        finally:
            report["finished_utc"] = datetime.now(timezone.utc).isoformat()
            (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            print("Report: " + str(directory / "report.json"), flush=True)
        return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
