#!/usr/bin/env python3
"""Download exact baseline checkouts; never reset or update existing work."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def bootstrap():
    manifest = json.loads((ROOT / "upstreams.lock.json").read_text())
    for name, source in manifest["repositories"].items():
        if not source["checkout"]:
            continue
        destination = ROOT / "upstream" / name
        if destination.exists():
            print(f"preserved existing checkout: {name}")
            continue
        destination.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(destination)], check=True)
        for args in (
            ["remote", "add", "origin", source["url"]],
            ["fetch", "--depth=1", "origin", source["revision"]],
            ["checkout", "--detach", source["revision"]],
        ):
            subprocess.run(["git", "-C", str(destination), *args], check=True, timeout=300)
    print("Baselines downloaded. Run scripts/check.py project to validate the harness.")


if __name__ == "__main__":
    bootstrap()
