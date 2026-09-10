"""Run the caller contract tests against a firmware root; retain hashes and logs."""

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("firmware_root", type=Path,
                    help="root containing core/src/apps/zcash")
args = parser.parse_args()
firmware = args.firmware_root.resolve()
root = Path(__file__).resolve().parent
sources = [firmware / "core/src/apps/zcash" / name
           for name in ("sign_pczt.py", "ironwood_review.py")]
for source in sources:
    if not source.is_file():
        parser.error(f"missing firmware source: {source}")
files = sources + [root / "test_caller_cleanup.py", Path(__file__).resolve()]
run = root / "runs" / datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S%fZ")
logs = run / "logs"
logs.mkdir(parents=True)


def hashes():
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}


argv = [sys.executable, "-B", "-W", "error", str(root / "test_caller_cleanup.py"),
        str(firmware)]
record = {"argv": argv, "cwd": str(root), "python": sys.version,
          "firmware_root": str(firmware),
          "started_utc": datetime.datetime.now(datetime.UTC).isoformat(),
          "before": hashes(), "scope": "CPython caller contract with boundary stubs only"}
start = time.monotonic()
with (logs / "stdout").open("wb") as stdout, (logs / "stderr").open("wb") as stderr:
    result = subprocess.run(argv, cwd=root, stdout=stdout, stderr=stderr, timeout=60)
record.update(returncode=result.returncode, seconds=time.monotonic() - start,
              after=hashes(), finished_utc=datetime.datetime.now(datetime.UTC).isoformat())
record["inputs_unchanged"] = record["before"] == record["after"]
record["logs"] = {name: hashlib.sha256((logs / name).read_bytes()).hexdigest()
                  for name in ("stdout", "stderr")}
(run / "run.json").write_text(json.dumps(record, indent=2) + "\n")
print("Evidence: " + str(run))
print(json.dumps(record, indent=2))
raise SystemExit(result.returncode or (0 if record["inputs_unchanged"] else 1))
