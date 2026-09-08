#!/usr/bin/env python3
"""Ensure every structural-model theorem has its exact Lean axiom guard."""
import json
from pathlib import Path
import re


def validate(root):
    source = (root / "proofs/Approval.lean").read_text()
    expected = json.loads((root / "proofs/axioms.json").read_text())
    guards = (root / "proofs/AxiomCheck.lean").read_text()
    theorems = re.findall(r"^theorem (\w+)", source, re.MULTILINE)
    if not len(theorems) == len(set(theorems)) == len(expected) >= 11 or set(theorems) != set(expected):
        raise ValueError("Theorem census differs from axiom manifest")
    if len(re.findall(r"^#guard_msgs in$", guards, re.MULTILINE)) != len(expected):
        raise ValueError("Missing axiom guard")
    if re.findall(r"^#print axioms IronwoodApproval\.(\w+)$", guards, re.MULTILINE) != list(expected):
        raise ValueError("Printed theorem census differs from manifest")
    for name, axioms in expected.items():
        if not set(axioms) <= {"propext", "Classical.choice", "Quot.sound"}:
            raise ValueError("Unexpected axiom")
        full = "IronwoodApproval." + name
        message = (f"'{full}' depends on axioms: [" + ", ".join(axioms) + "]"
                   if axioms else f"'{full}' does not depend on any axioms")
        if f"/-- info: {message} -/\n#guard_msgs in\n#print axioms {full}\n" not in guards:
            raise ValueError("Axiom guard text differs from manifest")
    if (root / "proofs/lean-toolchain").read_text() != (root / "upstream/ironwood/lean-toolchain").read_text():
        raise ValueError("Proof toolchain differs from Ironwood pin")
    return len(theorems)


if __name__ == "__main__":
    count = validate(Path(__file__).resolve().parents[1])
    print(f"Approval theorem census: {count} exact axiom guards; toolchain matches Ironwood pin")
