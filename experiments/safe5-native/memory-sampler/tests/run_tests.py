"""Bounded host compile/run using the retained Unix GC configuration."""
import datetime
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("micropython_root", type=Path, help="pinned root containing py/gc.c and ports/unix")
P = parser.parse_args().micropython_root.resolve()
PROPOSAL = ROOT.parent / "proposal"
RUN = ROOT / "runs" / datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S%fZ")
RUN.mkdir(parents=True)
ENV = dict(os.environ, TMPDIR=str(RUN), CLANG_MODULE_CACHE_PATH=str(RUN / "clang-cache"),
           XDG_CACHE_HOME=str(RUN / "cache"), CCACHE_DISABLE="1", PYTHONDONTWRITEBYTECODE="1")
records = []

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command(name, argv, timeout=60):
    start = time.monotonic()
    try:
        result = subprocess.run([str(a) for a in argv], cwd=RUN, env=ENV,
                                capture_output=True, timeout=timeout)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    record = {"name": name, "argv": [str(a) for a in argv], "cwd": str(RUN),
              "timeout_seconds": timeout, "seconds": time.monotonic() - start, "returncode": code}
    for label, data in (("stdout", stdout), ("stderr", stderr)):
        path = RUN / (name + "." + label)
        path.write_bytes(data)
        record[label] = {"path": str(path), "sha256": digest(path)}
    records.append(record)
    (RUN / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
    print(name, code, round(record["seconds"], 3), flush=True)
    if code:
        print(stderr.decode(errors="replace")[-5000:])
        raise SystemExit(code)
    return stdout

# Retained successful Unix-minimal command, with only include/output locations
# made portable. Generated headers are copied here, never regenerated in donor.
config = ROOT / "host-config"
recipe = json.loads((config / "compile.json").read_text())
original = recipe["original_gc_argv"]
compiler = recipe["compiler"]
flags = [arg.format(micropython=P, config=config) for arg in recipe["flags"]] + ["-I" + str(PROPOSAL)]
sources = [P / "py/gc.c", PROPOSAL / "memory_trace.c", PROPOSAL / "memory_trace.h",
           ROOT / "test_memory_trace.c", Path(__file__).resolve(), *sorted(config.rglob("*.h")),
           config / "compile.json"]
before = {str(path): digest(path) for path in sources}
assert digest(P / "py/gc.c") == "ddb8fe0e6d497488d223dc28994b1bbbd0875ad1cb3c3083fa1650535aa509dc"
(RUN / "inputs-before.json").write_text(json.dumps(before, indent=2) + "\n")
aliases = ["-D" + name + "=" + name + "_real" for name in
           ("gc_info", "gc_alloc", "gc_free", "gc_realloc")]
objects = []
for name, source, extra in (("gc", P / "py/gc.c", aliases),
                            ("sampler", PROPOSAL / "memory_trace.c", []),
                            ("test", ROOT / "test_memory_trace.c", [])):
    obj = RUN / (name + ".o")
    command(name, [compiler, *flags, *extra, "-MD", "-MF", RUN / (name + ".d"),
                   "-c", source, "-o", obj])
    objects.append(obj)
sdk = flags[flags.index("-isysroot") + 1]
command("link", [compiler, *objects, "-Wl,-dead_strip", "-isysroot", sdk,
                 "-o", RUN / "test_memory_trace"])
nm = str(Path(compiler).parent / "nm")
symbols = command("sampler-imports", [nm, "-u", RUN / "sampler.o"])
output = command("test-run", [RUN / "test_memory_trace"], timeout=20)
assert b"RESULT checks=8 " in output and output.count(b"PASS ") == 8
after = {str(path): digest(path) for path in sources}
assert before == after
dependencies = {}
for name in ("gc", "sampler", "test"):
    dep = (RUN / (name + ".d")).read_text().replace("\\\n", " ").split(":", 1)[1]
    for word in shlex.split(dep):
        path = Path(word)
        if path.is_file():
            dependencies[str(path.resolve())] = digest(path)
summary = {"verdict": "PASS", "checks": 8, "run": str(RUN), "inputs_before": before,
           "inputs_after": after, "dependencies_sha256": dependencies,
           "compiler": {"path": compiler, "sha256": digest(Path(compiler))},
           "original_gc_argv": original, "host_flags": flags,
           "gc_observation_symbol_aliases": aliases, "sampler_undefined_symbols": symbols.decode(),
           "commands": records, "output": output.decode(),
           "environment_overrides": {k: ENV[k] for k in ("TMPDIR", "CLANG_MODULE_CACHE_PATH", "XDG_CACHE_HOME", "CCACHE_DISABLE", "PYTHONDONTWRITEBYTECODE")}}
(RUN / "RESULT.json").write_text(json.dumps(summary, indent=2) + "\n")
print(output.decode())
print("Result:", RUN / "RESULT.json")
