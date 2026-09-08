#!/usr/bin/env python3
"""Prove the one exact experiment exception; never modify the shared checker."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/arena-probe'
CHECKSUM = '2b23ac50abb8261cb38c6e2a7192d3302e0836dac1628f6a93b82b4fad185897'
EXCEPTION = {'name': 'linked_list_allocator', 'version': '0.10.6',
             'source': 'registry+https://github.com/rust-lang/crates.io-index', 'checksum': CHECKSUM}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_projection(full, projected):
    check([p for p in full['package'] if p['name'] == EXCEPTION['name']] == [EXCEPTION],
          'wrong/multiple allocator exception')
    expected = dict(full, package=[p for p in full['package'] if p != EXCEPTION])
    check(projected == expected, 'projection differs from full lock minus ONLY allocator package')


def main():
    directory = Path(tempfile.mkdtemp(prefix='dependency-audit-', dir=WORK))
    report = {'passed': False}
    try:
        lock = ROOT/'experiments/arena-probe/Cargo.lock'
        text = lock.read_text()
        full = tomllib.loads(text)
        blocks = text.split('[[package]]')
        projected_text = blocks[0]+''.join('[[package]]'+b for b in blocks[1:]
                                         if tomllib.loads(b)['name'] != EXCEPTION['name'])
        projected = tomllib.loads(projected_text)
        validate_projection(full, projected)
        projection = directory/'existing-registry-only.lock'
        projection.write_text(projected_text)
        # Parse the actual saved projection again; bind it and the full build lock.
        validate_projection(full, tomllib.loads(projection.read_text()))
        archive = ROOT/'work/allocator-research/linked_list_allocator-0.10.6.crate'
        cache = ROOT/'work/arena-probe-cargo/registry/cache/index.crates.io-1949cf8c6b5b557f/linked_list_allocator-0.10.6.crate'
        index = ROOT/'work/arena-probe/allocator-index.jsonl'
        rows = [json.loads(line) for line in index.read_text().splitlines()]
        selected = [row for row in rows if row['vers'] == '0.10.6']
        check(len(selected) == 1 and selected[0]['name'] == EXCEPTION['name'] and selected[0]['cksum'] == CHECKSUM,
              'allocator metadata checksum mismatch')
        check(sha(archive) == sha(cache) == CHECKSUM, 'allocator archive checksum mismatch')
        # Resolve the current manifests; saved metadata cannot detect feature drift.
        manifest = ROOT/'experiments/arena-probe/Cargo.toml'
        before_manifest = sha(manifest)
        metadata_command = ['cargo', 'metadata', '--offline', '--locked',
                            '--manifest-path', str(manifest), '--format-version', '1']
        resolved = subprocess.run(metadata_command, cwd=ROOT, text=True,
                                  capture_output=True, timeout=60)
        metadata_path = directory/'metadata.json'
        metadata_path.write_text(resolved.stdout)
        (directory/'metadata.stderr').write_text(resolved.stderr)
        check(resolved.returncode == 0, 'fresh locked metadata resolution failed')
        check(sha(manifest) == before_manifest, 'manifest changed during metadata resolution')
        metadata = json.loads(resolved.stdout)
        packages = {p['id']:p for p in metadata['packages']}
        features = {p['id']:p['features'] for p in metadata['resolve']['nodes']}
        old = json.loads((ROOT/'work/arena-probe/metadata.stdout').read_text())
        old_packages = {p['id']:p for p in old['packages']}
        def graph(meta, inventory):
            return {(inventory[n['id']]['name'], inventory[n['id']]['version']):n['features']
                    for n in meta['resolve']['nodes'] if inventory[n['id']]['name'] != 'ironwood-arena-probe'}
        check(graph(metadata, packages) == graph(old, old_packages), 'dependency features changed from v1')
        alloc_nodes=[n for n in metadata['resolve']['nodes'] if packages[n['id']]['name']==EXCEPTION['name']]
        check(len(alloc_nodes)==1 and alloc_nodes[0]['features']==[] and alloc_nodes[0]['deps']==[],
              'new allocator enabled dependencies/features')
        command=['python3','scripts/check_approval_dependencies.py',str(projection)]
        process=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=30)
        (directory/'dependency-checker.stdout').write_text(process.stdout)
        (directory/'dependency-checker.stderr').write_text(process.stderr)
        check(process.returncode==0,'unchanged upstream checker rejected projected inventory')
        check(sha(lock)==hashlib.sha256(text.encode()).hexdigest(),'build lock changed during audit')
        report.update(passed=True, exception=EXCEPTION, full_build_lock_sha256=sha(lock),
                      exact_projection_sha256=sha(projection), projection_package_equality=True,
                      original_archive_sha256=sha(archive), cached_archive_sha256=sha(cache),
                      index_sha256=sha(index), selected_index_record=selected[0],
                      metadata_sha256=sha(metadata_path), metadata_command=metadata_command,
                      manifest_sha256=before_manifest, dependency_features_unchanged=True,
                      features=[{'name':packages[key]['name'],'version':packages[key]['version'],'features':value}
                                for key,value in features.items()], checker_command=command,
                      checker_sha256=sha(ROOT/'scripts/check_approval_dependencies.py'),
                      checker_exit=process.returncode, checker_output=process.stdout)
    except (ValueError,KeyError,OSError,subprocess.SubprocessError) as error:
        report['error']=str(error)
    finally:
        (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'report':str(directory/'report.json')}))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    sys.exit(main())
