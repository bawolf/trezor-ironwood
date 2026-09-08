"""Reject resource reports that could hide missing cases or retained allocations."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("resources", ROOT / "scripts/resource_check.py")
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)


class ResourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.phase = {key: 0 for key in ("allocations", "reallocations", "deallocations",
            "failed_requests", "requested_bytes", "largest_request_bytes", "baseline_live_bytes",
            "peak_live_bytes", "live_bytes", "accounting_errors", "elapsed_ns")}
        self.phase.update(baseline_live_bytes=1100, peak_live_bytes=1100, live_bytes=1100)
        run = {"teardown_retained_bytes": 0, "process_baseline_bytes": 100,
               "input_capacity_bytes": 1000, "review_output_capacity_bytes": 0,
               "phases": {name: deepcopy(self.phase) for name in resources.PHASE_NAMES}}
        run["phases"]["teardown"].update(live_bytes=100, deallocations=1)
        for phase in ("begin", "sign"):
            run["phases"][phase].update(allocations=1, deallocations=1, requested_bytes=1, largest_request_bytes=1)
        self.manifest = {"height": 10_000_000, "fee_cap": 100_000, "fixtures": []}
        self.signed_sizes = {}
        self.report = {"schema_version": 1, "oracle_verified": False, "height": 10_000_000,
            "maximum_fee": 100_000, "warmup_runs": 1, "recorded_runs": 5, "cases": [],
            "failure_checks": [{"name": name, "metrics": deepcopy(self.phase),
                "teardown_retained_bytes": 0} for name in resources.FAILURE_NAMES]}
        for name in resources.CASE_NAMES:
            n = int(name.split("-")[1])
            inputs, outputs = (n, 1) if name.startswith("inputs-") else (1, n)
            self.manifest["fixtures"].append({"name": name + ".pczt", "byte_length": 1000,
                "action_count": n, "required_signature_count": inputs, "positive_output_count": outputs,
                "padding_input_count": n - inputs, "padding_output_count": n - outputs,
                "anchor_present": False, "ock_present": [False] * n, "shielded_sighash": "ab" * 32})
            self.signed_sizes[name + ".pczt"] = 1000 + 64 * inputs
            timed = deepcopy(run)
            for phase in ("begin", "sign"):
                timed["phases"][phase]["elapsed_ns"] = 1
            self.report["cases"].append({"name": name, "wire_bytes": 1000,
                "signed_wire_bytes": self.signed_sizes[name + ".pczt"], "action_count": n,
                "signature_count": inputs, "output_count": outputs, "padding_outputs": n - outputs,
                "dummy_spends": n - inputs, "anchor_present": False, "ock_count": 0,
                "sighash_hex": "ab" * 32, "warmup": deepcopy(run), "runs": [deepcopy(timed) for _ in range(5)],
                "timing_summary_ns": {phase: {key: timed["phases"][phase]["elapsed_ns"] for key in ("first", "median", "max")} for phase in resources.PHASE_NAMES}})

    def test_complete_zero_retention_report_is_accepted(self):
        resources.validate_measurements(self.report, self.manifest, self.signed_sizes)

    def test_missing_or_duplicated_fixture_is_rejected(self):
        missing = deepcopy(self.report)
        missing["cases"].pop()
        duplicate = deepcopy(self.report)
        duplicate["cases"][-1] = duplicate["cases"][0]
        for report in (missing, duplicate):
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_wrong_signature_count_or_incomplete_runs_are_rejected(self):
        for field, value in (("signature_count", 0), ("signature_count", True), ("runs", []), ("runs", None)):
            report = deepcopy(self.report)
            report["cases"][0][field] = value
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_retention_and_invalid_accounting_values_are_rejected(self):
        for value in (1, -1, None, False, "0"):
            report = deepcopy(self.report)
            report["cases"][0]["runs"][0]["teardown_retained_bytes"] = value
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_missing_failure_checks_or_impossible_peaks_are_rejected(self):
        missing = deepcopy(self.report)
        missing["failure_checks"].pop()
        impossible = deepcopy(self.report)
        impossible["cases"][0]["runs"][0]["phases"]["begin"]["live_bytes"] = 1101
        allocated = deepcopy(self.report)
        allocated["failure_checks"][-1]["metrics"]["allocations"] = 1
        for report in (missing, impossible, allocated):
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_reported_digest_and_fixture_facts_must_match_artifacts(self):
        for field, value in (("sighash_hex", "cd" * 32), ("wire_bytes", 1001),
                             ("signed_wire_bytes", 1000), ("action_count", 2),
                             ("anchor_present", 0), ("ock_count", 1)):
            report = deepcopy(self.report)
            report["cases"][0][field] = value
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_warmup_and_adjacent_phase_accounting_are_checked(self):
        for run_name in ("warmup", "runs"):
            report = deepcopy(self.report)
            case = report["cases"][0]
            run = case[run_name][0] if run_name == "runs" else case[run_name]
            run["phases"]["begin"]["baseline_live_bytes"] -= 1
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)
        report = deepcopy(self.report)
        report["cases"][0]["warmup"] = None
        with self.assertRaises(ValueError):
            resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_failure_retention_cannot_contradict_live_bytes(self):
        report = deepcopy(self.report)
        report["failure_checks"][0]["metrics"].update(live_bytes=1101, peak_live_bytes=1101)
        with self.assertRaises(ValueError):
            resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_claimed_timing_and_allocation_totals_are_recomputed(self):
        timings = deepcopy(self.report)
        timings["cases"][0]["timing_summary_ns"]["begin"]["median"] = 2
        events = deepcopy(self.report)
        events["cases"][0]["runs"][0]["phases"]["teardown"]["deallocations"] = 0
        baseline = deepcopy(self.report)
        baseline["cases"][0]["runs"][0]["process_baseline_bytes"] = False
        for report in (timings, events, baseline):
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_only_the_runner_can_set_verification_and_fixed_policy(self):
        for name, value in (("oracle_verified", True), ("warmup_runs", True),
                            ("recorded_runs", 0), ("height", 1), ("maximum_fee", 0)):
            report = deepcopy(self.report)
            report[name] = value
            with self.assertRaises(ValueError):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)

    def test_empty_instrumentation_is_rejected(self):
        for field in ("allocations", "elapsed_ns"):
            report = deepcopy(self.report)
            report["cases"][0]["runs"][0]["phases"]["begin"][field] = 0
            with self.assertRaisesRegex(ValueError, "instrumentation recorded no work"):
                resources.validate_measurements(report, self.manifest, self.signed_sizes)


if __name__ == "__main__":
    unittest.main()
