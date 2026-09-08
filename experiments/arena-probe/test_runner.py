"""Negative evidence tests. They must also pass under python -O."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import shutil
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import check_dependencies as deps
import verify


class RunnerEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=verify.WORK/'verification-01/outputs-1.pczt.stdout'
        cls.good=json.loads(path.read_bytes())

    def test_real_report_control(self):
        verify.validate_reports(json.dumps(self.good).encode(),'sign',[1])

    def test_empty_report_is_failure_even_with_zero_exit(self):
        with tempfile.TemporaryDirectory(dir=verify.WORK/'tmp') as folder:
            record,out,_=verify.capture(Path(folder),'empty',[sys.executable,'-c','pass'],0)
            self.assertTrue(record['exit_matched'])
            with self.assertRaisesRegex(ValueError,'report count'):
                verify.validate_reports(out,'sign',[1])

    def test_oracle_requires_exact_final_census(self):
        census = b'verified 15 fixtures, 43 real-spend signatures; all fields and digests preserved'
        verify.validate_oracle(b'verified inputs-8.pczt: 8 real-spend signatures\n'+census+b'\n', b'')
        for out, err in [
            (b'', b''),
            (b'hash: ab43cd\nverified 15 fixtures\n', b''),
            (census.replace(b'43', b'143')+b'\n', b''),
            (census.replace(b'15 fixtures', b'14 fixtures')+b'\n', b''),
            (census.split(b';')[0]+b'\n', b''),
            (b'prefix '+census+b'\n', b''),
            (census+b' trailing\n', b''),
            (census+b'\nlater output\n', b''),
            (census+b'\n', b'diagnostic'),
        ]:
            with self.subTest(out=out, err=err):
                with self.assertRaisesRegex(ValueError, 'oracle success census missing'):
                    verify.validate_oracle(out, err)

    def test_repeat_requires_three_reports(self):
        with self.assertRaisesRegex(ValueError,'report count'):
            verify.validate_reports(json.dumps(self.good).encode(),'repeat',[1,8,1])

    def test_zero_begin_instrumentation_rejected(self):
        changed=deepcopy(self.good)
        changed['phases']['begin']=changed['phases']['constructor'].copy()
        with self.assertRaisesRegex(ValueError,'zero begin instrumentation'):
            verify.validate_report(changed,'sign',1)

    def test_wrong_status_and_phase_mask(self):
        for key,value in [('status',verify.REJECTED),('phase_mask',32)]:
            with self.subTest(key=key):
                changed=deepcopy(self.good);changed[key]=value
                with self.assertRaisesRegex(ValueError,'status/phase'):
                    verify.validate_report(changed,'sign',1)

    def test_wrong_recovery_and_rebaseline(self):
        for key,value in [('recovered_large_block',1),('baseline',self.good['startup']['cold'])]:
            with self.subTest(key=key):
                changed=deepcopy(self.good);changed[key]=value
                with self.assertRaises(ValueError):
                    verify.validate_report(changed,'sign',1)

    def test_partial_diagnostic_remains_generic_and_saved(self):
        with tempfile.TemporaryDirectory(dir=verify.WORK/'tmp') as folder:
            record,out,err=verify.capture(Path(folder),'partial',[
                sys.executable,'-c',"import os; os.write(2,b'partial'); os._exit(84)"],84)
            self.assertTrue(record['exit_matched'])
            self.assertEqual(record['diagnostic']['kind'],'generic_invariant')
            self.assertEqual((Path(folder)/'partial.stderr').read_bytes(),b'partial')
            self.assertEqual(out,b'')
            self.assertEqual(err,b'partial')

    def test_complete_v1_diagnostic_and_corruption(self):
        raw=(verify.ROOT/'work/arena-probe/verification-02/outputs-1.pczt.stderr').read_bytes()
        self.assertEqual(verify.invariant_diagnostic(raw,1)['kind'],'retained_ownership')
        self.assertEqual(verify.invariant_diagnostic(bytes(len(raw)),1)['kind'],'generic_invariant')
        self.assertEqual(verify.invariant_diagnostic(raw[:-1],1)['kind'],'generic_invariant')

    def test_parser_checks_run_under_optimization(self):
        original=(verify.FIXTURES/'inputs-8.pczt').read_bytes()
        nine=verify.nine_actions(original)
        self.assertGreater(len(nine),len(original))
        with self.assertRaises(ValueError):
            verify.nine_actions(b'BAD!'+original[4:])

    def test_feature_change_cannot_reuse_saved_metadata(self):
        # Both calls see the same old lock and cached metadata. Only the second
        # manifest enables std, which a fresh locked resolution must detect.
        with tempfile.TemporaryDirectory(dir=verify.WORK/'tmp') as folder:
            root = Path(folder)
            for name in ('work', 'crates', 'scripts', 'upstream'):
                (root/name).symlink_to(verify.ROOT/name, target_is_directory=True)
            (root/'Cargo.toml').symlink_to(verify.ROOT/'Cargo.toml')
            experiment = root/'experiments/arena-probe'
            (experiment/'src').mkdir(parents=True)
            (experiment/'src/lib.rs').write_text('pub fn placeholder() {}\n')
            original = verify.ROOT/'experiments/arena-probe'
            manifest = (original/'Cargo.toml').read_text()
            (experiment/'Cargo.toml').write_text(manifest)
            shutil.copyfile(original/'Cargo.lock', experiment/'Cargo.lock')
            evidence = root/'evidence'
            evidence.mkdir()
            shutil.copyfile(verify.WORK/'metadata.stdout', evidence/'metadata.stdout')
            with patch.object(deps, 'ROOT', root), patch.object(deps, 'WORK', evidence), redirect_stdout(io.StringIO()):
                code = deps.main()
                reports = list(evidence.glob('dependency-audit-*/report.json'))
                details = reports[-1].read_text() if reports else 'no audit report'
                self.assertEqual(code, 0, details)
                before = 'path = "../../crates/approval", default-features = false'
                self.assertIn(before, manifest)
                changed = manifest.replace(before, before.replace('false', 'true'))
                (experiment/'Cargo.toml').write_text(changed)
                self.assertEqual(deps.main(), 1, 'changed features must reject cached evidence')

    def test_projection_exact_package_equality(self):
        full=tomllib.loads((verify.ROOT/'experiments/arena-probe/Cargo.lock').read_text())
        projected=dict(full,package=[p for p in full['package'] if p!=deps.EXCEPTION])
        deps.validate_projection(full,projected)
        changed=deepcopy(projected);changed['package'].pop()
        with self.assertRaises(ValueError):
            deps.validate_projection(full,changed)
        changed=deepcopy(projected);changed['package'][0]['version']='999'
        with self.assertRaises(ValueError):
            deps.validate_projection(full,changed)


if __name__=='__main__':
    unittest.main()
