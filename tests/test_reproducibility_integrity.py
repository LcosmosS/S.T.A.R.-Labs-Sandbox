"""Adversarial byte/source/archive/dataset checks; no scientific code executed."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
import sys
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.reproducibility.integrity import (
    HERE, inspect_tar, load_json, verify_artifacts, verify_sources,
)
from scripts.reproducibility.datasets import check_bytes, check_csv


class ReproducibilityIntegrityTests(unittest.TestCase):
    def test_pinned_sources(self):
        self.assertGreaterEqual(verify_sources(), 45)

    def test_mutated_source_and_extra_module_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(HERE/'upstream', root/'upstream')
            shutil.copy2(HERE/'SOURCE_MANIFEST.json', root/'SOURCE_MANIFEST.json')
            extra = root/'upstream/src/extra.py'
            extra.write_text('raise RuntimeError("must never execute")')
            with self.assertRaisesRegex(ValueError, 'unexpected'):
                verify_sources(root)
            extra.unlink()
            source = root/'upstream/src/acsc/projection.py'
            source.write_bytes(source.read_bytes()+b'\n# drift\n')
            with self.assertRaisesRegex(ValueError, 'byte mismatch'):
                verify_sources(root)

    def test_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/'manifest.json'
            p.write_text('{"files":[],"files":[]}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON'):
                load_json(p)

    def test_artifact_empty_logs_inventory_and_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'stdout.log').write_bytes(b'')
            manifest = {'files': [{'path': 'stdout.log', 'bytes': 0,
                                  'sha256': hashlib.sha256(b'').hexdigest()}]}
            self.assertEqual(verify_artifacts(root, manifest), 1)
            (root/'stdout.log').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'byte mismatch'):
                verify_artifacts(root, manifest)
            (root/'stdout.log').unlink()
            with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
                verify_artifacts(root, manifest)

    def test_archive_traversal_links_duplicates_and_limits(self):
        for name, kind in [('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                           ('link', tarfile.SYMTYPE), ('hard', tarfile.LNKTYPE),
                           ('device', tarfile.CHRTYPE), ('duplicate', tarfile.REGTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                path = Path(temp)/'unsafe.tar.gz'
                with tarfile.open(path, 'w:gz') as archive:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    archive.addfile(member, io.BytesIO(b''))
                    if name == 'duplicate': archive.addfile(member, io.BytesIO(b''))
                with self.assertRaises(ValueError): inspect_tar(path)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'large.tar.gz'
            with tarfile.open(path, 'w:gz') as archive:
                member = tarfile.TarInfo('member')
                member.size = 2
                archive.addfile(member, io.BytesIO(b'ab'))
            with self.assertRaisesRegex(ValueError, 'limit'): inspect_tar(path, max_bytes=1)
            self.assertEqual(inspect_tar(path), 1)

    def test_csv_schema_count_width_keys_and_large_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'fixture.csv'
            contract = {'columns': ['id','value'], 'rows': 2, 'key': ['id']}
            path.write_text('id,value\n9999999999999999991,1\n9999999999999999992,2\n')
            self.assertEqual(check_csv(path, contract), 2)
            for bad in ('id,value\n1,1\n1,2\n', 'id,value\n1,1,extra\n',
                        'value,id\n1,1\n2,2\n', 'id,value\n1,1\n'):
                path.write_text(bad)
                with self.assertRaises(ValueError): check_csv(path, contract)

    def test_pointer_missing_and_hash_drift_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'data'
            pin = {'bytes': 1, 'sha256': hashlib.sha256(b'x').hexdigest()}
            with self.assertRaises(ValueError): check_bytes(path, pin)
            path.write_bytes(b'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1\n')
            with self.assertRaisesRegex(ValueError, 'unhydrated'): check_bytes(path, pin)
            path.write_bytes(b'y')
            with self.assertRaisesRegex(ValueError, 'mismatch'): check_bytes(path, pin)
            path.write_bytes(b'x')
            check_bytes(path, pin)

    def test_mismatching_input_emits_failure_receipt_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'different.csv'
            data = b'wrong,columns\n1,2\n'
            path.write_bytes(data)
            result = subprocess.run([sys.executable, str(HERE/'datasets.py'),
                                     '--dataset', 'DATA-SDSS18-200K', '--file', str(path)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt['status'], 'FAIL')
            self.assertEqual(receipt['observed_sha256'], hashlib.sha256(data).hexdigest())
            self.assertFalse(receipt['diagnostic_schema_match'])
            self.assertEqual(path.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
