"""Build/install checked software outside checkout; emit a bounded receipt."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from integrity import digest_file, inspect_tar, load_json, verify_artifacts, verify_sources

HERE = Path(__file__).resolve().parent


def run(args, **kwargs):
    subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    artifacts = args.output/'artifacts'
    artifacts.mkdir()
    verify_sources()
    env = {**os.environ, 'SOURCE_DATE_EPOCH': '1792368000',
           'PYTHONHASHSEED': '0', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
           'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'}
    # Work on disposable build inputs so the pinned checkout stays unchanged.
    with tempfile.TemporaryDirectory(prefix='sbx-build-') as temporary:
        work = Path(temporary)
        project = work/'project'
        shutil.copytree(HERE/'upstream', project, ignore=shutil.ignore_patterns('__pycache__', '*.egg-info', 'build', 'dist'))
        # Windows-mounted checkouts expose executable mode on ordinary files;
        # normalize disposable build inputs to Git's regular source-file mode.
        for path in project.rglob('*'):
            path.chmod(0o755 if path.is_dir() else 0o644)
        run([sys.executable, '-m', 'build', '--no-isolation', '--outdir', artifacts, project], env=env)
        second = work/'second'
        run([sys.executable, '-m', 'build', '--wheel', '--no-isolation', '--outdir', second, project], env=env)
        wheel = next(artifacts.glob('*.whl'))
        if digest_file(wheel) != digest_file(second/wheel.name):
            raise ValueError('wheel rebuild is not byte reproducible')
        inspect_tar(next(artifacts.glob('*.tar.gz')))
        run([sys.executable, '-m', 'venv', work/'installed'])
        python = work/'installed/bin/python'
        run([python, '-m', 'pip', 'install', '--require-hashes', '--only-binary=:all:',
             '-r', HERE/'requirements-linux-py312.lock'])
        run([python, '-m', 'pip', 'install', '--no-deps', wheel])
        run([python, '-m', 'pip', 'check'])
        tests = work/'tests'
        shutil.copytree(HERE/'upstream/tests', tests/'upstream')
        shutil.copytree(HERE/'tests', tests/'local')
        shutil.copy2(HERE/'conftest.py', tests/'conftest.py')
        shutil.copy2(HERE/'pytest.ini', tests/'pytest.ini')
        installed_env = {k:v for k,v in env.items() if k != 'PYTHONPATH'}
        installed_env['SBX_INSTALLED'] = '1'
        run([python, '-I', '-m', 'pytest', '-q', '-c', tests/'pytest.ini', '--import-mode=importlib', tests,
             '--junitxml', artifacts/'installed-tests.xml'], cwd=work, env=installed_env)
    manifest = {'files': [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': digest_file(p)}
                           for p in sorted(artifacts.iterdir())]}
    verify_artifacts(artifacts, manifest)
    receipt = {'schema_version': 1, 'scope': 'sandbox-only', 'status': 'PASS',
               'claim_of_truth': False, 'independently_reviewed': False,
               'eligible_for_automatic_promotion': False,
               'sandbox_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=HERE, text=True).strip(),
               'source_commit': load_json(HERE/'SOURCE_MANIFEST.json')['source_commit'],
               'python': sys.version, 'wheel_byte_rebuild_equal': True,
               'installed_tests_outside_checkout': True,
               'source_manifest_sha256': digest_file(HERE/'SOURCE_MANIFEST.json'),
               'tool_lock_sha256': digest_file(HERE/'requirements-linux-py312.lock'),
               'environment': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
               'artifacts': manifest}
    (args.output/'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
