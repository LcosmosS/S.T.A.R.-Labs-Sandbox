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
        """Reject altered archived content despite a rewritten SHA-256 manifest."""
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
        """Reject unsafe or nonexistent archive file paths."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'link').symlink_to('/etc/passwd')
            for path in ['missing', '../outside', '/etc/passwd', 'a/../b', 'a\\b', 'link']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    checker.safe_file(root, path)

    def test_new_research_cannot_bypass_experiment_intake(self):
        """Reject unclassified research outside the sandbox experiment namespace."""
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
        """Reject conflicting duplicate keys in the archival manifest."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{"baseline_commit":"a","baseline_commit":"b"}')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                checker.load(path)



    def test_reference_verifies_original_bytes_and_detects_rebinding(self):
        """Detect altered reference hashes and modified upstream source bytes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "upstream"
            (root / "sandbox").mkdir()
            (upstream / ".github/workflows").mkdir(parents=True)
            source_path = ".github/workflows/example.yml"
            contents = b"name: pinned\n"
            (upstream / source_path).write_bytes(contents)
            source_url = (f"https://github.com/{checker.UPSTREAM_REPOSITORY}/"
                          f"blob/{checker.UPSTREAM_COMMIT}/{source_path}")
            item = {"path": source_path, "sha256": hashlib.sha256(contents).hexdigest(),
                    "url": source_url}
            manifest = {"schema_version": 1, "repository": checker.UPSTREAM_REPOSITORY,
                        "commit": checker.UPSTREAM_COMMIT, "authority": "reference_only",
                        "files": [item]}
            target = root / "sandbox/upstream-reference.json"
            target.write_text(json.dumps(manifest))
            from unittest.mock import Mock
            with patch.object(checker, "EXPECTED_UPSTREAM_PATHS", frozenset({source_path})), \
                 patch.object(checker.subprocess, "run",
                              return_value=Mock(stdout=checker.UPSTREAM_COMMIT + "\n")):
                self.assertEqual(checker.check_upstream_reference(root, upstream), 1)
                item["sha256"] = "0" * 64
                target.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    checker.check_upstream_reference(root, upstream)
                item["sha256"] = hashlib.sha256(contents).hexdigest()
                (upstream / source_path).write_bytes(b"tampered")
                target.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    checker.check_upstream_reference(root, upstream)

    def test_reference_rejects_wrong_checkout_revision(self):
        """Reject an upstream checkout whose Git HEAD is not the pinned commit."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "upstream"
            (root / "sandbox").mkdir()
            upstream.mkdir()
            source_path = "README.md"
            target = root / "sandbox/upstream-reference.json"
            target.write_text(json.dumps({
                "schema_version": 1, "repository": checker.UPSTREAM_REPOSITORY,
                "commit": checker.UPSTREAM_COMMIT, "authority": "reference_only",
                "files": [{"path": source_path, "sha256": "0" * 64,
                           "url": (f"https://github.com/{checker.UPSTREAM_REPOSITORY}/"
                                   f"blob/{checker.UPSTREAM_COMMIT}/{source_path}")}]
            }))
            from unittest.mock import Mock
            with patch.object(checker, "EXPECTED_UPSTREAM_PATHS", frozenset({source_path})), \
                 patch.object(checker.subprocess, "run",
                              return_value=Mock(stdout="f" * 40 + "\n")):
                with self.assertRaisesRegex(ValueError, "pinned commit"):
                    checker.check_upstream_reference(root, upstream)


    def test_mode_only_change_to_historical_file_is_rejected(self):
        """Reject chmod-only changes to a preserved file without altered bytes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sandbox").mkdir()
            original = b"historical bytes\n"
            oid = hashlib.sha1(f"blob {len(original)}\0".encode() + original).hexdigest()
            entry = {"original_path": "historical.py", "preserved_path": "historical.py",
                     "git_mode": "100644", "git_blob": oid,
                     "size_bytes": len(original),
                     "sha256": hashlib.sha256(original).hexdigest()}
            (root / "historical.py").write_bytes(original)
            (root / "sandbox/archive-manifest.json").write_text(json.dumps({
                "baseline_commit": checker.BASELINE, "files": [entry]}))
            def tree(_root, revision):
                """Return an unchanged baseline and a mode-only changed proposal."""
                mode = "100644" if revision == checker.BASELINE else "100755"
                return {"historical.py": (mode, oid)}
            with patch.object(checker, "git_tree", side_effect=tree):
                with self.assertRaisesRegex(ValueError, "archival Git mode changed"):
                    checker.check_archive(root)

    def test_relocated_readme_is_checked_but_live_readme_is_editable(self):
        """Apply archive mode checks to the relocated original README only."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sandbox").mkdir()
            (root / "archive").mkdir()
            original = b"\n"
            oid = hashlib.sha1(f"blob {len(original)}\0".encode() + original).hexdigest()
            (root / "archive/README.pre-sandbox.md").write_bytes(original)
            (root / "README.md").write_text("New sandbox landing page\n")
            entry = {"original_path": "README.md",
                     "preserved_path": "archive/README.pre-sandbox.md",
                     "git_mode": "100644", "git_blob": oid,
                     "size_bytes": len(original),
                     "sha256": hashlib.sha256(original).hexdigest()}
            (root / "sandbox/archive-manifest.json").write_text(json.dumps({
                "baseline_commit": checker.BASELINE, "files": [entry]}))
            proposed = {"archive/README.pre-sandbox.md": ("100644", oid),
                        "README.md": ("100644", "f" * 40)}
            def tree(_root, revision):
                """Return the baseline README or the relocated proposed copy."""
                return ({"README.md": ("100644", oid)}
                        if revision == checker.BASELINE else proposed)
            with patch.object(checker, "git_tree", side_effect=tree):
                self.assertEqual(checker.check_archive(root), 1)
                proposed["archive/README.pre-sandbox.md"] = ("100755", oid)
                with self.assertRaisesRegex(ValueError, "archival Git mode changed"):
                    checker.check_archive(root)

    def test_upstream_inventory_must_include_exactly_24_paths(self):
        """Reject missing and unexpected entries even when remaining hashes look valid."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sandbox").mkdir()
            upstream = root / "upstream"
            upstream.mkdir()
            self.assertEqual(len(checker.EXPECTED_UPSTREAM_PATHS), 24)
            def entry(path):
                """Make a syntactically valid pinned reference for the given path."""
                return {"path": path, "sha256": "0" * 64,
                        "url": (f"https://github.com/{checker.UPSTREAM_REPOSITORY}/"
                                f"blob/{checker.UPSTREAM_COMMIT}/{path}")}
            records = [entry(path) for path in sorted(checker.EXPECTED_UPSTREAM_PATHS)]
            manifest = {"schema_version": 1, "repository": checker.UPSTREAM_REPOSITORY,
                        "commit": checker.UPSTREAM_COMMIT, "authority": "reference_only",
                        "files": records}
            output = root / "sandbox/upstream-reference.json"
            output.write_text(json.dumps(manifest))
            with patch.object(checker.subprocess, "run") as run:
                run.return_value.stdout = "f" * 40 + "\n"
                with self.assertRaisesRegex(ValueError, "pinned commit"):
                    checker.check_upstream_reference(root, upstream)
                manifest["files"] = records[:-1]
                output.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "inventory"):
                    checker.check_upstream_reference(root, upstream)
                manifest["files"] = records[:-1] + [entry("README-extra.md")]
                output.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "missing or unexpected paths"):
                    checker.check_upstream_reference(root, upstream)

if __name__ == '__main__':
    unittest.main()
