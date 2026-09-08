#!/usr/bin/env python3
"""Build or test the pinned Safe 7 emulator; never discover physical devices."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

from check import ROOT, budget_status, run_command, verification_lock


def check_checkout(path, revision):
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=path, text=True).strip()
    submodules = subprocess.check_output(['git', 'submodule', 'status', '--recursive'], cwd=path, text=True)
    if actual != revision or dirty or any(line[:1] != ' ' for line in submodules.splitlines()):
        raise ValueError('Firmware checkout and submodules must be clean at the pinned revisions')


def firmware_env(root):
    fw = root / 'work/firmware-t3w1'
    env = dict(os.environ)
    env.update(CARGO_HOME=str(root / 'work/firmware-cargo'),
               RUSTUP_HOME=str(root / 'work/rustup'), CARGO_BUILD_JOBS='2',
               LIBCLANG_PATH='/opt/homebrew/opt/llvm/lib', CC='/opt/homebrew/bin/gcc-15', LC_ALL='C',
               UV_CACHE_DIR=str(root / 'work/uv-cache'), SDL_VIDEODRIVER='dummy')
    env['PATH'] = os.pathsep.join([str(fw / '.venv/bin'),
                                  str(root / 'work/firmware-cargo/bin'),
                                  str(root / 'work/toolchain-downloads/protoc-31.1/bin'),
                                  '/opt/homebrew/opt/llvm/bin', env.get('PATH', '')])
    for key in ('CARGO_TARGET_DIR', 'RUSTUP_TOOLCHAIN', 'PYTEST_ADDOPTS', 'TREZOR_PATH', 'TREZOR_BLE'):
        env.pop(key, None)
    return env


def check_model(properties):
    if properties.get('internal_model') != 'T3W1':
        raise ValueError('Expected a T3W1 (Safe 7) emulator')


def check_junit(path, expected=9):
    """Count actual testcase nodes; empty/skipped/failed reports cannot pass."""
    cases = list(ET.parse(path).getroot().iter('testcase'))
    failures = sum(case.find('failure') is not None for case in cases)
    errors = sum(case.find('error') is not None for case in cases)
    skipped = sum(case.find('skipped') is not None for case in cases)
    if len(cases) != expected or failures or errors or skipped:
        raise ValueError(f'Expected {expected} passing tests; got {len(cases)} cases, '
                         f'{failures} failures, {errors} errors, {skipped} skipped')
    return {'tests_passed': len(cases), 'test_names': [case.attrib['name'] for case in cases]}


def run(root, stage):
    fw = root / 'work/firmware-t3w1'
    revision = json.loads((root / 'upstreams.lock.json').read_text())['repositories']['trezor-firmware']['revision']
    budget = budget_status(json.loads((root / 'ops/budget.json').read_text()))
    with verification_lock(root / 'work/firmware-verification.lock'):
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        directory = root / 'work/runs' / (timestamp + '-firmware-' + stage + '-' + uuid.uuid4().hex[:8])
        directory.mkdir(parents=True)
        report = {'lane': 'firmware-' + stage, 'started_utc': timestamp,
                  'revisions': {'trezor-firmware': revision}, 'budget': budget,
                  'commands': [], 'passed': False}
        print('Evidence: ' + str(directory), flush=True)
        env = firmware_env(root)
        env["TREZOR_PYTEST_LOGS_DIR"] = str(directory)

        def command(args, cwd, timeout=120):
            result = run_command(args, cwd, env, directory / f'{len(report["commands"]):02d}.log', timeout)
            result['cwd'] = str(cwd)
            report['commands'].append(result)
            if not result['passed']:
                raise ValueError('Command failed; inspect ' + result['log'])
            return Path(result['log']).read_text()

        try:
            check_checkout(fw, revision)
            uv = root / 'work/toolchain-downloads/uv-0.12.10/uv-aarch64-apple-darwin/uv'
            command([str(uv), 'sync', '--locked', '--python', '/usr/local/bin/python3'], fw, 600)
            rustc = command(['rustc', '--version'], fw)
            if '1.96.0-nightly (1e2183119 2026-03-15)' not in rustc:
                raise ValueError('Expected source-pinned nightly-2026-03-16')
            report['toolchain'] = {'rustc': rustc.strip(),
                                   'protoc': command(['protoc', '--version'], fw).strip(),
                                   'python': command([str(fw / '.venv/bin/python'), '--version'], fw).strip(),
                                   'cc': command([env['CC'], '--version'], fw).splitlines()[0],
                                   'sdl': command(['pkg-config', '--modversion', 'sdl3', 'sdl3-image'], fw).splitlines()}
            if stage == 'build':
                command(['cargo', 'run', '--locked', '--profile', 'xtask', '-p', 'xtask', '--',
                         'build', 'firmware', '--model', 't3w1', '--emulator', '--preset', 'test'],
                        fw / 'core/embed', 1200)
            binary = fw / 'core/build-xtask/artifacts/latest/firmware-emu'
            binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
            properties = json.loads(command([str(binary), '--emulator-properties'], fw / 'core/src'))
            check_model(properties)
            report['emulator'] = {'sha256': binary_hash, 'properties': properties}
            if stage == 'zcash':
                junit = directory / 'junit.xml'
                command([str(fw / '.venv/bin/python'), '-m', 'pytest',
                         'tests/device_tests/zcash/test_sign_tx.py', '--control-emulators',
                         '--model', 'core', '--random-order-seed=0', '--timeout=90',
                         '--junitxml=' + str(junit), '-q'], fw, 1200)
                report['tests'] = check_junit(junit)
                report['junit_sha256'] = hashlib.sha256(junit.read_bytes()).hexdigest()
            if hashlib.sha256(binary.read_bytes()).hexdigest() != binary_hash:
                raise ValueError('Emulator binary changed during verification')
            check_checkout(fw, revision)
            report['passed'] = True
        except (OSError, ValueError, KeyError, ET.ParseError, subprocess.SubprocessError) as error:
            report['error'] = str(error)
        finally:
            report['finished_utc'] = datetime.now(timezone.utc).isoformat()
            (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps(report), flush=True)
        return 0 if report['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('build', 'zcash'))
    args = parser.parse_args()
    try:
        sys.exit(run(ROOT, args.stage))
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
