"""Synthetic preservation regressions; never import archived research code."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/verify_archive.py'
spec = importlib.util.spec_from_file_location('archive_checker', SOURCE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ArchiveTests(unittest.TestCase):
    def test_inventory_cannot_be_rebound_to_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'sandbox').mkdir()
            original = b'original\n'
            oid = hashlib.sha1(f'blob {len(original)}\0'.encode() + original).hexdigest()
            entry = dict(original_path='legacy.txt', preserved_path='legacy.txt',
                         git_mode='100644', git_blob=oid, size_bytes=len(original),
                         sha256=hashlib.sha256(original).hexdigest())
            manifest = dict(baseline_commit=checker.BASELINE, files=[entry])
            target = root / 'sandbox/archive-manifest.json'
            target.write_text(json.dumps(manifest))
            (root / 'legacy.txt').write_bytes(original)
            with patch.object(checker, 'git_tree', return_value={'legacy.txt': ('100644', oid)}):
                self.assertEqual(checker.check_archive(root), 1)
                changed = b'rewritten\n'
                (root / 'legacy.txt').write_bytes(changed)
                entry.update(size_bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
                target.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, 'original Git blob'):
                    checker.check_archive(root)
                (root / 'legacy.txt').unlink()
                with self.assertRaisesRegex(ValueError, 'missing file'):
                    checker.check_archive(root)

    def test_missing_traversal_absolute_and_symlink_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'link').symlink_to('/etc/passwd')
            for path in ['missing', '../outside', '/etc/passwd', 'a/../b', 'a\\b', 'link']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    checker.safe_file(root, path)

    def test_new_research_cannot_bypass_experiment_intake(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ['new_research.py', 'R&D/new.pdf', 'release_packages/result.json',
                         'registry/promotions/claim.json', 'sandbox/experiments/unclassified.py']:
                with self.subTest(path=path), patch.object(checker, 'git_tree', return_value={}), \
                     patch.object(checker.subprocess, 'run') as run:
                    run.return_value.stdout = path.encode() + b'\0'
                    with self.assertRaisesRegex(ValueError, 'outside experiments'):
                        checker.check_layout(root)

    def test_duplicate_inventory_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{"baseline_commit":"a","baseline_commit":"b"}')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                checker.load(path)


if __name__ == '__main__':
    unittest.main()
