"""Two private sampler mutations; reuse objects from a successful canonical run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("result_json", type=Path)
result_path = parser.parse_args().result_json.resolve()
baseline = json.loads(result_path.read_text())
assert baseline["verdict"] == "PASS"
commands = {item["name"]: item["argv"] for item in baseline["commands"]}
original = Path(next(path for path in baseline["inputs_before"] if path.endswith("/memory_trace.c")))
text = original.read_text()
root = result_path.parent / "negative-controls"
root.mkdir()
env = dict(os.environ, **baseline["environment_overrides"])
records = []

def run(name, argv, expected):
    start = time.monotonic()
    result = subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=60)
    item = {"name": name, "argv": argv, "cwd": str(root), "timeout_seconds": 60,
            "returncode": result.returncode, "seconds": time.monotonic() - start}
    for label, data in (("stdout", result.stdout), ("stderr", result.stderr)):
        path = root / (name + "." + label)
        path.write_bytes(data)
        item[label] = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}
    records.append(item)
    (root / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
    assert result.returncode == expected, item
    return result.stderr.decode()

controls = (
    ("missing-byte-conversion", "info.max_free * MICROPY_BYTES_PER_GC_BLOCK", "info.max_free",
     "got->largest_free_bytes == want.largest_free_bytes"),
    ("missing-valid-bit", "trace.valid_phases |= UINT32_C(1) << (unsigned int)phase;", "",
     "trace->valid_phases & (UINT32_C(1) << phase)"),
)
for name, old, new, error in controls:
    assert text.count(old) == 1
    source = root / (name + ".c")
    source.write_text(text.replace(old, new))
    obj = root / (name + ".o")
    compile_argv = list(commands["sampler"])
    compile_argv[compile_argv.index(str(original))] = str(source)
    compile_argv[compile_argv.index("-o") + 1] = str(obj)
    compile_argv[compile_argv.index("-MF") + 1] = str(root / (name + ".d"))
    run(name + "-compile", compile_argv, 0)
    executable = root / name
    link_argv = list(commands["link"])
    link_argv[link_argv.index(str(result_path.parent / "sampler.o"))] = str(obj)
    link_argv[link_argv.index("-o") + 1] = str(executable)
    run(name + "-link", link_argv, 0)
    assert error in run(name + "-test", [str(executable)], 1)
    print("EXPECTED_REJECTION", name, error)

for filename, digest in baseline["inputs_after"].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == digest, filename
summary = {"verdict": "PASS: both mutations rejected for their intended assertions",
           "baseline": str(result_path), "canonical_inputs_unchanged": True,
           "commands": records,
           "mutant_source_hashes": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in root.glob("*.c")}}
(root / "RESULT.json").write_text(json.dumps(summary, indent=2) + "\n")
