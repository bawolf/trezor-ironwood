#!/usr/bin/env python3
"""Strict bounded native checks; all command failures survive in the final report."""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/arena-probe/v2'
FIXTURES = ROOT / 'work/runs/20260908T080145Z-resources-71a70bee/fixtures'
ORACLE = ROOT / 'work/resource-target/release/ironwood-resource-fixtures'
BINARY = WORK / 'arena-probe'
CAPACITY, LARGE_BLOCK = 131072, 65536
OK, REJECTED, OUTPUT_TOO_SMALL = 0, 1, 2
INVARIANT, OOM = 84, 86
PHASES = ('constructor', 'begin', 'approve', 'sign', 'serialize', 'teardown')
FIELDS = ('attempts', 'allocations', 'deallocations', 'failures', 'requested_total',
          'rounded_total', 'live_requested', 'live_blocks', 'peak_requested',
          'peak_used', 'largest_request', 'used', 'free')
LIVE = ('live_requested', 'live_blocks', 'used', 'free')
EVENTS = ('attempts', 'allocations', 'deallocations', 'failures', 'requested_total',
          'rounded_total', 'peak_requested', 'peak_used', 'largest_request')


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_counts(counts):
    check(isinstance(counts, dict) and set(counts) == set(FIELDS), 'invalid counter fields')
    check(all(type(counts[k]) is int and counts[k] >= 0 for k in FIELDS), 'invalid counter value')
    c = counts
    check(c['used'] + c['free'] == CAPACITY, 'arena total mismatch')
    check(c['attempts'] == c['allocations'] + c['failures'], 'attempts do not balance')
    check(c['allocations'] - c['deallocations'] == c['live_blocks'], 'live blocks do not balance')
    check(c['live_requested'] <= c['used'] <= c['peak_used'] <= CAPACITY, 'invalid used peak')
    check(c['live_requested'] <= c['peak_requested'] <= c['peak_used'], 'invalid requested peak')
    check(c['largest_request'] <= c['requested_total'], 'invalid largest request')


def same_live(a, b):
    return all(a[k] == b[k] for k in LIVE)


def monotonic(a, b):
    check(all(a[k] <= b[k] for k in EVENTS), 'event counters decreased')


def validate_startup(startup):
    cold, ready = startup['cold'], startup['ready']
    for c in (cold, ready, startup['repeat_before'], startup['repeat_after']):
        validate_counts(c)
    check(cold == dict.fromkeys(FIELDS, 0) | {'free': CAPACITY}, 'startup was not cold')
    check(ready == startup['repeat_before'] == startup['repeat_after'], 'repeat init changed counters')
    sizes, aligns = [1098, 8192, 8192, 8192, 4128], [1, 8, 8, 8, 8]
    word = struct.calcsize('P')
    expected = [{'size': n, 'alignment': a, 'rounded': (max(n, 2*word)+word-1)//word*word}
                for n, a in zip(sizes, aligns)]
    check(startup['layouts'] == expected, 'public layouts differ from pinned host types')
    check(ready['live_blocks'] == 5 and ready['live_requested'] == sum(sizes), 'public baseline mismatch')
    check(ready['used'] == sum(x['rounded'] for x in expected), 'rounded public baseline mismatch')
    check(ready['attempts'] > 5 and ready['deallocations'] > 0 and ready['failures'] == 0,
          'missing cold initialization instrumentation')
    return ready


def validate_report(report, kind, signatures, previous=None):
    check(report['schema_version'] == 2, 'wrong report schema')
    for key in ('status', 'phase_mask', 'serialized_bytes', 'signatures', 'recovered_large_block'):
        check(type(report[key]) is int and report[key] >= 0, 'invalid report scalar')
    expected_status = {'reject': REJECTED, 'small-output': OUTPUT_TOO_SMALL}.get(kind, OK)
    mask = {'cancel': 35, 'replace': 35, 'reject': 32}.get(kind, 63)
    check(report['status'] == expected_status and report['phase_mask'] == mask, 'wrong status/phase state')
    ready = validate_startup(report['startup'])
    check(report['baseline'] == ready, 'request rebased public constants')
    start, recovery = report['start'], report['recovery']
    check(set(report['phases']) == set(PHASES), 'missing phases')
    for c in (start, recovery, *report['phases'].values()):
        validate_counts(c)
        check(c['failures'] == 0, 'unexpected allocator failure')
    check(same_live(start, ready) and same_live(recovery, ready), 'request baseline changed')
    prior = ready if previous is None else previous['recovery']
    check(all(start[k] == prior[k] + 1 for k in ('attempts', 'allocations', 'deallocations')),
          'missing initial large allocation/free')
    check(start['requested_total'] == prior['requested_total'] + LARGE_BLOCK, 'wrong initial probe layout')
    if previous is not None:
        check(report['startup'] == previous['startup'], 'repeat restarted image')
    cursor = start
    for index, phase in enumerate(PHASES):
        current = report['phases'][phase]
        if mask & (1 << index):
            monotonic(cursor, current)
            if phase in ('constructor', 'begin', 'sign', 'serialize'):
                check(current['allocations'] > cursor['allocations'], 'zero '+phase+' instrumentation')
            if phase == 'approve':
                check(current == cursor, 'approval unexpectedly allocated')
            cursor = current
        else:
            check(current == start, 'skipped phase contains fabricated work')
    end = report['phases']['teardown']
    check(same_live(end, ready), 'request owners retained')
    check(end['allocations'] - start['allocations'] == end['deallocations'] - start['deallocations'],
          'request allocation/free delta mismatch')
    check(report['recovered_large_block'] == LARGE_BLOCK, 'wrong recovered Layout')
    check(all(recovery[k] == end[k] + 1 for k in ('attempts', 'allocations', 'deallocations')),
          'missing final large allocation/free')
    check(recovery['requested_total'] == end['requested_total'] + LARGE_BLOCK, 'wrong final probe layout')
    monotonic(end, recovery)
    if kind == 'reject':
        check(end == start, 'admission allocated')
    if kind in ('cancel', 'replace', 'reject'):
        check(report['serialized_bytes'] == report['signatures'] == 0, 'unexpected signing work')
    elif kind == 'small-output':
        check(report['serialized_bytes'] == 0 and report['signatures'] == signatures, 'wrong capacity rejection')
    else:
        check(0 < report['serialized_bytes'] <= 65536 and report['signatures'] == signatures,
              'missing serialized signing result')


def validate_reports(raw, kind, signatures):
    expected = 3 if kind == 'repeat' else 1
    lines = raw.splitlines()
    check(len(lines) == expected and len(signatures) == expected, 'wrong report count')
    reports = [json.loads(line) for line in lines]
    previous = None
    for report, count in zip(reports, signatures):
        validate_report(report, kind, count, previous)
        previous = report
    return reports


def validate_oracle(out, err):
    lines = out.splitlines()
    check(not err and lines and lines[-1] ==
          b'verified 15 fixtures, 43 real-spend signatures; all fields and digests preserved',
          'oracle success census missing')


def invariant_diagnostic(raw, version=2):
    """84 is generic. Only a complete, validated payload is ownership evidence."""
    words = 81 if version == 1 else 121
    if len(raw) != words * struct.calcsize('P'):
        return {'kind': 'generic_invariant', 'diagnostic': 'absent_or_incomplete', 'bytes': len(raw)}
    try:
        values = struct.unpack('@'+str(words)+'N', raw)
        offset = 0 if version == 1 else 26
        phases = {name: dict(zip(FIELDS, values[offset+i*13:offset+(i+1)*13]))
                  for i, name in enumerate(PHASES)}
        for c in phases.values():
            validate_counts(c)
        if version == 1:
            mask, size, signatures, recovered = 63, *values[78:81]
            baseline = dict.fromkeys(FIELDS, 0) | {'free': CAPACITY}
        else:
            baseline = dict(zip(FIELDS, values[:13]))
            validate_counts(baseline)
            start = dict(zip(FIELDS, values[13:26]))
            validate_counts(start)
            check(same_live(start, baseline), 'diagnostic starts outside baseline')
            check(all(v == 0 for v in values[104:117]), 'diagnostic claims completed recovery')
            mask, size, signatures, recovered = values[117:121]
        check(mask in (32, 35, 63) and recovered == 0, 'invalid failed-teardown state')
        check(0 <= size <= 65536 and 0 <= signatures <= 8, 'invalid serialized metadata')
        if size:
            check(mask == 63 and signatures > 0, 'serialized output lacks complete phases')
        cursor = None
        for i, phase in enumerate(PHASES):
            if mask & (1 << i):
                if cursor is not None:
                    monotonic(cursor, phases[phase])
                cursor = phases[phase]
        end = phases['teardown']
        check(end['live_blocks'] > baseline['live_blocks'] and end['used'] > baseline['used'],
              'not a retained-owner payload')
        check(end['allocations'] > 0, 'no ownership instrumentation')
        return {'kind': 'retained_ownership', 'phases': phases, 'bytes': len(raw)}
    except (ValueError, KeyError, TypeError, struct.error) as error:
        return {'kind': 'generic_invariant', 'diagnostic': 'invalid_payload', 'error': str(error), 'bytes': len(raw)}


def capture(directory, name, args, expected):
    start = time.monotonic()
    timeout = 120 if Path(args[0]) == ORACLE else 30
    try:
        p = subprocess.run(list(map(str, args)), cwd=ROOT, capture_output=True, timeout=timeout)
        code, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as error:
        code, out, err = 'timeout', error.stdout or b'', error.stderr or b''
    except OSError as error:
        code, out, err = 'launch_error', b'', str(error).encode()
    (directory / (name+'.stdout')).write_bytes(out)
    (directory / (name+'.stderr')).write_bytes(err)
    record = {'name': name, 'command': list(map(str, args)), 'exit_code': code,
              'expected_exit': expected, 'exit_matched': code == expected,
              'seconds': time.monotonic()-start, 'timeout_seconds': timeout, 'passed': False}
    if code == INVARIANT:
        record['diagnostic'] = invariant_diagnostic(err, 1 if name == 'cold-v1' else 2)
    return record, out, err
def nine_actions(original):
    """Duplicate a complete first action in the pinned v2 Postcard encoding.

    Only constructs a hostile admission test, never a signing fixture or oracle.
    The byte walk matches the pinned core's wire.rs; no crypto is implemented.
    """
    data = original
    at = 8
    check(data[:8] == b'PCZT\x02\x00\x00\x00', 'invalid pinned Postcard test input')

    def integer():
        nonlocal at
        value = 0
        for shift in range(0, 70, 7):
            byte = data[at]
            at += 1
            value |= (byte & 127) << shift
            if not byte & 128:
                return value
        raise ValueError('invalid varint')

    def skip(count):
        nonlocal at
        at += count
        check(at <= len(data), 'invalid pinned Postcard test input')

    def optional(count):
        tag = integer()
        check(tag in (0, 1), 'invalid pinned Postcard test input')
        if tag:
            skip(count)
    for _ in range(3):
        integer()
    if integer():
        integer()
    integer()
    integer()
    check([integer() for _ in range(5)] == [0, 0, 0, 0, 0], 'invalid pinned Postcard test input')
    check(integer() == 1, 'invalid pinned Postcard test input')
    count_at = at
    check(integer() == 8, 'invalid pinned Postcard test input')
    start = at
    for count in (32, 32, 32, 64, 43):
        optional(count)
    check(integer() == 1, 'invalid pinned Postcard test input')
    integer()
    for count in (32, 32, 96):
        optional(count)
    check(integer() == 0, 'invalid pinned Postcard test input')
    optional(32)
    check([integer() for _ in range(3)] == [0, 0, 0], 'invalid pinned Postcard test input')
    optional(32)
    skip(32)
    check(integer() == 0, 'invalid pinned Postcard test input')
    for expected in (580, 80):
        check(integer() == expected, 'invalid pinned Postcard test input')
        skip(expected)
    optional(43)
    check(integer() == 1, 'invalid pinned Postcard test input')
    integer()
    optional(32)
    optional(32)
    check([integer() for _ in range(3)] == [0, 0, 0], 'invalid pinned Postcard test input')
    optional(32)
    return data[:count_at] + b'\t' + data[start:at] + data[start:]


def main():
    directory = WORK / (sys.argv[1] if len(sys.argv) == 2 else 'verification')
    directory.mkdir()  # Never overwrite prior evidence.
    results, reports = [], {}
    summary = {'passed': False, 'results': results, 'reports': reports, 'errors': []}

    def case(name, args, expected, validate):
        record, out, err = capture(directory, name, args, expected)
        try:
            check(record['exit_matched'], 'process exit did not match')
            value = validate(out, err)
            if value is not None:
                reports[name] = value
            record['passed'] = True
        except (ValueError, KeyError, TypeError, OSError) as error:
            record['error'] = str(error)
        results.append(record)
        with (directory/'commands.jsonl').open('a') as file:
            file.write(json.dumps(record)+'\n')
        return record['passed']

    def quiet(out, err):
        check(not out, 'fatal process emitted stdout')

    def request(out, err, kind, counts, paths, export):
        check(not err, 'successful request emitted diagnostics')
        value = validate_reports(out, kind, counts)
        for path, report in zip(paths, value):
            check(path.is_file() if export else not path.exists(), 'wrong export state')
            if export:
                check(path.stat().st_size == report['serialized_bytes'], 'wrong serialized file length')
        return value

    try:
        manifest = json.loads((FIXTURES/'manifest.json').read_text())
        fixtures = manifest['fixtures']
        names = {f'outputs-{n}.pczt' for n in range(1, 9)} | {f'inputs-{n}.pczt' for n in range(2, 9)}
        check(len(fixtures) == 15 and {f['name'] for f in fixtures} == names, 'wrong saved corpus')
        frozen = {p.name: digest(p) for p in FIXTURES.iterdir()}
        check(all(frozen[f['name']] == f['sha256'] for f in fixtures), 'fixture hash mismatch')
        binaries = {str(p): digest(p) for p in (BINARY, ORACLE, WORK/'arena-probe-v1')}
        lock = ROOT/'experiments/arena-probe/Cargo.lock'
        lock_sha256 = digest(lock)
        summary.update(fixtures_sha256=frozen, binaries_sha256=binaries,
                       cargo_lock_sha256=lock_sha256)
        signed = directory/'signed'; signed.mkdir()
        def layouts(out, err):
            check(not err and len(out.splitlines()) == 1, 'missing layout report')
            # Rust require calls and exit 0 gate success; this JSON is a status.
            check(json.loads(out) == {'valid_layout_tests': 'passed'}, 'wrong layout result')
        case('layouts', [BINARY, 'layouts'], 0, layouts)
        for mode, code in [('preinit',81),('double-init',82),('reentry',83),('panic',85),
                           ('personality',87),('sealed-free',INVARIANT),('late-owner',INVARIANT)]:
            case(mode, [BINARY, mode], code, quiet)
        cold_output = directory/'cold.pczt'
        def cold(out, err):
            quiet(out, err)
            check(not cold_output.exists(), 'cold gate exported a signature')
            # Optional diagnostics never decide whether the observed fail-stop passed.
        case('cold-v1', [WORK/'arena-probe-v1','sign',FIXTURES/'outputs-1.pczt',cold_output], INVARIANT, cold)
        for fixture in fixtures:
            name, count = fixture['name'], fixture['required_signature_count']
            destination = signed/name
            case(name, [BINARY,'sign',FIXTURES/name,destination], 0,
                 lambda out,err,count=count,destination=destination: request(out,err,'sign',[count],[destination],True))
        maximum = FIXTURES/'inputs-8.pczt'
        for mode in ('cancel','replace','small-output'):
            destination = directory/(mode+'.pczt')
            case(mode, [BINARY,mode,maximum,destination], 0,
                 lambda out,err,mode=mode,destination=destination: request(out,err,mode,[8],[destination],False))
        for mode in ('oom-begin','oom-sign'):
            destination = directory/(mode+'.pczt')
            def oom(out,err,destination=destination):
                quiet(out,err); check(not destination.exists(), 'OOM exported output')
            case(mode,[BINARY,mode,maximum,destination],OOM,oom)
        for name,data in [('oversize',bytes(65537)),('nine-actions',nine_actions(maximum.read_bytes())),('malformed',b'bad')]:
            source,destination=directory/(name+'.input'),directory/(name+'.pczt')
            source.write_bytes(data)
            case(name,[BINARY,'reject',source,destination],0,
                 lambda out,err,destination=destination: request(out,err,'reject',[0],[destination],False))
        case('oracle',[ORACLE,'verify',FIXTURES,signed],0,validate_oracle)
        repeat_signed=directory/'repeat-signed';repeat_signed.mkdir()
        chosen=['outputs-1.pczt','inputs-8.pczt','outputs-3.pczt']
        paths=[repeat_signed/name for name in chosen]
        repeated_ok=case('repeat',[BINARY,'repeat',*[FIXTURES/name for name in chosen],repeat_signed],0,
                        lambda out,err: request(out,err,'repeat',[1,8,1],paths,True))
        if repeated_ok and all((signed/name).is_file() for name in names):
            for name in names-set(chosen):
                shutil.copy2(signed/name,repeat_signed/name)
        case('repeat-oracle',[ORACLE,'verify',FIXTURES,repeat_signed],0,validate_oracle)
        check(frozen == {p.name:digest(p) for p in FIXTURES.iterdir()}, 'saved fixture changed')
        check(binaries == {name:digest(Path(name)) for name in binaries}, 'binary changed during verification')
        summary['signed_sha256']={p.name:digest(p) for p in signed.iterdir()}
        summary['repeat_signed_sha256']={p.name:digest(p) for p in repeat_signed.iterdir()}
        for name in chosen:
            check(summary['repeat_signed_sha256'][name] == summary['signed_sha256'][name],
                  'repeat output differs from primary: '+name)
        check(digest(lock) == lock_sha256, 'Cargo.lock changed during verification')
    except (ValueError, KeyError, TypeError, OSError) as error:
        summary['errors'].append(str(error))
    finally:
        summary['passed']=not summary['errors'] and len(results)==35 and all(r['passed'] for r in results)
        summary['limits']='Synthetic native only; target compilation is separate. No GC, MCU runtime, production or independent-review acceptance claim.'
        (directory/'report.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps({'passed':summary['passed'],'cases':len(results),'report':str(directory/'report.json')}))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
