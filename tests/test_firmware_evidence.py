"""False-positive guards for emulator identity and test evidence."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_firmware import check_junit, check_model


class FirmwareEvidenceTests(unittest.TestCase):
    def test_wrong_or_missing_model_rejected(self):
        for props in ({}, {'internal_model': 'T2T1'}):
            with self.subTest(props=props), self.assertRaises(ValueError):
                check_model(props)
        check_model({'internal_model': 'T3W1'})

    def test_only_actual_passing_testcases_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.xml'
            path.write_text('<testsuites><testsuite tests="2"><testcase name="a"/>'
                            '<testcase name="b"/></testsuite></testsuites>')
            self.assertEqual(check_junit(path, 2)['tests_passed'], 2)
            with self.assertRaises(ValueError):
                check_junit(path, 9)
            # Claimed counts on a summary element must not substitute for test evidence.
            path.write_text('<testsuites tests="9"/>')
            with self.assertRaises(ValueError):
                check_junit(path)

    def test_failure_error_and_skip_are_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.xml'
            for tag in ('failure', 'error', 'skipped'):
                with self.subTest(tag=tag):
                    path.write_text(f'<testsuite><testcase name="a"><{tag}/></testcase></testsuite>')
                    with self.assertRaises(ValueError):
                        check_junit(path, 1)
