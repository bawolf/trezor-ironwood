"""Exercise failure modes that could create misleading verification evidence."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("checks", ROOT / "scripts/check.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.budget = json.loads((ROOT / "ops/budget.json").read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def run_program(self, source, timeout=10, minimum=0):
        return checks.run_command([sys.executable, "-c", source], self.path, os.environ,
                                  self.path / "command.log", timeout, minimum)

    def test_zero_tests_is_failure(self):
        result = self.run_program("print('test result: ok. 0 passed; 0 failed')", minimum=1)
        self.assertFalse(result["passed"])

    def test_failure_wins_over_success_text(self):
        result = self.run_program("print('test result: ok. 99 passed'); raise SystemExit(1)", minimum=1)
        self.assertFalse(result["passed"])

    def test_nonzero_test_run_produces_digest(self):
        result = self.run_program("print('test result: ok. 4 passed; 0 failed')", minimum=4)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["log_sha256"]), 64)

    def test_timeout_stops_descendants(self):
        marker = self.path / "escaped-child"
        child = "import time,pathlib;time.sleep(1);pathlib.Path(" + repr(str(marker)) + ").touch()"
        source = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(60)"
        result = self.run_program(source, timeout=0.2)
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["passed"])
        # Wait past the child's planned side effect to detect surviving descendants.
        subprocess.run([sys.executable, "-c", "import time;time.sleep(1.1)"], check=True)
        self.assertFalse(marker.exists())

    def test_lock_excludes_second_holder_and_releases(self):
        lock = self.path / "verification.lock"
        with checks.verification_lock(lock):
            with self.assertRaises(RuntimeError):
                with checks.verification_lock(lock):
                    self.fail("concurrent lock acquired")
        with checks.verification_lock(lock):
            pass

    def test_missing_executable_is_failure(self):
        result = checks.run_command([str(self.path / "absent")], self.path, os.environ,
                                    self.path / "missing.log", 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["returncode"], 127)

    def test_baseline_rejects_changed_revision_and_dirty_work(self):
        repo = self.path / "upstream" / "fixture"
        repo.mkdir(parents=True)
        def git(*args):
            return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL, text=True).strip()
        git("init", "-q")
        git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "fixture")
        sha = git("rev-parse", "HEAD")
        self.assertEqual(checks.baseline(self.path, "fixture", sha), sha)
        with self.assertRaises(ValueError):
            checks.baseline(self.path, "fixture", "0" * 40)
        (repo / "untracked.txt").write_text("unexpected change")
        with self.assertRaises(ValueError):
            checks.baseline(self.path, "fixture", sha)

    def test_budget_counts_pending_reservations(self):
        self.budget["entries"] = [{"id": "a", "cents": 25000, "status": "spent"},
                                  {"id": "b", "cents": 5001, "status": "reserved"}]
        with self.assertRaises(ValueError):
            checks.budget_status(self.budget)

    def test_budget_rejects_invalid_amounts_and_duplicate_ids(self):
        for amount in (-1, True, 1.5):
            with self.subTest(amount=amount):
                budget = deepcopy(self.budget)
                budget["entries"] = [{"id": "a", "cents": amount, "status": "spent"}]
                with self.assertRaises(ValueError):
                    checks.budget_status(budget)
        self.budget["entries"] = [{"id": "a", "cents": 1, "status": "spent"}] * 2
        with self.assertRaises(ValueError):
            checks.budget_status(self.budget)

    def test_unknown_model_cost_is_not_reported_as_zero(self):
        result = checks.budget_status(self.budget)
        self.assertEqual(result["codex_dollar_metering"], "unavailable")
        self.budget["paid_execution_enabled"] = True
        with self.assertRaises(ValueError):
            checks.budget_status(self.budget)


if __name__ == "__main__":
    unittest.main()
