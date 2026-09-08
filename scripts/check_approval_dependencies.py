#!/usr/bin/env python3
"""Reject accidental dependency drift from the pinned upstream PCZT baseline."""
from pathlib import Path
import tomllib
import sys

root = Path(__file__).resolve().parents[1]
base = tomllib.loads((root / "upstream/librustzcash/Cargo.lock").read_text())["package"]
base = {(p["name"], p["version"], p.get("source")): p.get("checksum") for p in base}
lock = root / (sys.argv[1] if len(sys.argv) == 2 else "Cargo.lock")
packages = tomllib.loads(lock.read_text())["package"]
registry = [p for p in packages if p.get("source", "").startswith("registry+")]
if not registry:
    raise ValueError("Empty dependency inventory")
for p in registry:
    key = (p["name"], p["version"], p["source"])
    if key not in base or base[key] != p.get("checksum"):
        raise ValueError(f"Unreviewed dependency drift: {p['name']} {p['version']}")
print(f"Approval dependencies: {len(registry)} registry packages match upstream versions and checksums")
