"""Sandbox byte integrity helpers. Never extract archives or execute members."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

HERE = Path(__file__).resolve().parent


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object)


def safe_file(root, name):
    rel = PurePosixPath(name)
    if not name or rel.is_absolute() or '..' in rel.parts or '\\' in name:
        raise ValueError(f"unsafe path: {name}")
    current = Path(root)
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink: {name}")
    if not current.is_file():
        raise ValueError(f"missing regular file: {name}")
    return current


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources(root=HERE):
    manifest = load_json(Path(root) / 'SOURCE_MANIFEST.json')
    if (manifest['source_commit'] != '51927a9b396cdfa880f3128440db4715acdec8dc'
            or manifest['scope'] != 'sandbox-only'
            or any(manifest[k] is not False for k in
                   ('claim_of_truth', 'independently_reviewed', 'eligible_for_automatic_promotion'))):
        raise ValueError('source identity or non-promotion boundary changed')
    expected = set()
    for entry in manifest['files']:
        name = entry['snapshot_path']
        if name in expected:
            raise ValueError('duplicate source manifest path')
        expected.add(name)
        data = safe_file(root, name).read_bytes()
        blob = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        if hashlib.sha256(data).hexdigest() != entry['sha256'] or blob != entry['git_blob']:
            raise ValueError(f'source byte mismatch: {name}')
    adapter = b'"""Sandbox software-check package; no scientific admission authority."""\n'
    for name in manifest['local_package_adapters']:
        if name in expected or safe_file(root, name).read_bytes() != adapter:
            raise ValueError(f'package adapter mismatch: {name}')
        expected.add(name)
    for entry in manifest.get('derived_files', []):
        name = entry['snapshot_path']
        if name in expected or digest_file(safe_file(root, name)) != entry['sha256']:
            raise ValueError(f'derived helper mismatch: {name}')
        expected.add(name)
    actual = {p.relative_to(root).as_posix() for p in (Path(root)/'upstream').rglob('*.py')}
    if actual != {name for name in expected if name.endswith('.py')}:
        raise ValueError('unexpected or missing upstream Python files')
    test_paths = {'upstream/'+name for name in manifest['tests']}
    actual_tests = {p.relative_to(root).as_posix() for p in (Path(root)/'upstream/tests').glob('*.py')}
    if len(test_paths) != len(manifest['tests']) or test_paths != actual_tests:
        raise ValueError('executable test allowlist mismatch')
    return len(manifest['files'])


def inspect_tar(path, *, max_bytes=32 * 1024 * 1024, max_members=1000):
    """Bound streaming inspection; reject links, devices, duplicates and escapes."""
    names = set()
    total = 0
    with tarfile.open(path, 'r|gz') as archive:
        for member in archive:
            name = member.name
            rel = PurePosixPath(name)
            if (not name or rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in rel.parts[0]
                    or rel.as_posix() in names or not (member.isfile() or member.isdir())):
                raise ValueError(f'unsafe archive member: {name}')
            names.add(rel.as_posix())
            total += member.size
            if len(names) > max_members or member.size < 0 or total > max_bytes:
                raise ValueError('archive resource limit exceeded')
            if member.isfile():
                stream = archive.extractfile(member)
                remaining = member.size
                while remaining:
                    chunk = stream.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        raise ValueError('truncated archive member')
                    remaining -= len(chunk)
    if not names:
        raise ValueError('empty archive')
    return len(names)


def verify_artifacts(root, manifest):
    """Require exact inventory, sizes and hashes, including empty log files."""
    root = Path(root)
    entries = manifest['files']
    if not entries:
        raise ValueError('empty artifact inventory')
    names = [entry['path'] for entry in entries]
    if len(names) != len(set(names)):
        raise ValueError('duplicate artifact path')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if not p.is_dir()}
    if actual != set(names):
        raise ValueError('artifact inventory mismatch')
    for entry in entries:
        path = safe_file(root, entry['path'])
        if path.stat().st_size != entry['bytes'] or digest_file(path) != entry['sha256']:
            raise ValueError(f'artifact byte mismatch: {entry["path"]}')
    return len(entries)


if __name__ == '__main__':
    print(json.dumps({'scope': 'sandbox-only', 'source_files_checked': verify_sources(),
                      'claim_of_truth': False, 'eligible_for_automatic_promotion': False}))
