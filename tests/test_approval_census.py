"""Reject missing theorem coverage, widened axioms and ineffective guards."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("approval_census", ROOT / "scripts/check_approval_proof_census.py")
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)


class CensusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "proofs").mkdir()
        for name in ("Approval.lean", "AxiomCheck.lean", "axioms.json", "lean-toolchain"):
            shutil.copyfile(ROOT / "proofs" / name, self.root / "proofs" / name)
        (self.root / "upstream/ironwood").mkdir(parents=True)
        shutil.copyfile(self.root / "proofs/lean-toolchain", self.root / "upstream/ironwood/lean-toolchain")
        self.assertEqual(census.validate(self.root), 11)

    def tearDown(self):
        self.tmp.cleanup()

    def test_added_theorem_requires_guard(self):
        path = self.root / "proofs/Approval.lean"
        path.write_text(path.read_text() + "\ntheorem uncovered : True := True.intro\n")
        with self.assertRaises(ValueError):
            census.validate(self.root)

    def test_extra_axiom_is_not_allowed(self):
        path = self.root / "proofs/axioms.json"
        data = json.loads(path.read_text())
        data["accounting_conserves"].append("sorryAx")
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            census.validate(self.root)

    def test_print_without_guard_is_not_evidence(self):
        path = self.root / "proofs/AxiomCheck.lean"
        path.write_text(path.read_text().replace("#guard_msgs in\n", "", 1))
        with self.assertRaises(ValueError):
            census.validate(self.root)
