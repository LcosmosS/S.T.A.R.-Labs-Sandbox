"""Verify that the 18 authorized root research objects reside in historical/.

This checks repository organization and exact Git object identities, not the
scientific validity or execution of archived scripts and PDFs.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/verify_archive.py"
spec = importlib.util.spec_from_file_location("archive_checker_for_move", CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class HistoricalOrganizationTests(unittest.TestCase):
    """Validate that only the pinned root research paths were reorganized."""

    def test_exactly_eighteen_original_root_files_are_relocated(self):
        """Confirm all permitted PDF/Python/CSV files live only in historical/."""
        self.assertEqual(len(checker.HISTORICAL_ROOT_RELOCATIONS), 18)
        manifest = json.loads((ROOT / "sandbox/archive-manifest.json").read_text())
        by_original = {e["original_path"]: e for e in manifest["files"]}
        self.assertEqual(len(manifest["files"]), 221)
        proposed = checker.git_tree(ROOT, "HEAD")
        baseline = checker.git_tree(ROOT, checker.BASELINE)
        for name in checker.HISTORICAL_ROOT_RELOCATIONS:
            with self.subTest(path=name):
                target = f"historical/{name}"
                self.assertFalse((ROOT / name).exists(), f"old root copy remains: {name}")
                self.assertNotIn(name, proposed)
                self.assertTrue((ROOT / target).is_file())
                self.assertIn(target, proposed)
                self.assertEqual(proposed[target], baseline[name])
                self.assertEqual(by_original[name]["preserved_path"], target)
                raw = (ROOT / target).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),
                                 by_original[name]["sha256"])
                self.assertEqual(len(raw), by_original[name]["size_bytes"])

    def test_root_contains_no_pdf_py_or_csv_files(self):
        """Ensure no targeted extension is still presented on the root page."""
        remaining = sorted(p.name for p in ROOT.iterdir()
                           if p.is_file() and p.suffix.lower() in {".pdf", ".py", ".csv"})
        self.assertEqual(remaining, [])



    def test_second_stage_root_contains_only_allowed_documentation(self):
        """Retain Markdown, license, ignorefile and only pinned Git metadata."""
        root_files = sorted(p.name for p in ROOT.iterdir() if p.is_file())
        allowed = {".gitignore", "LICENSE"}
        if ".gitmodules" in root_files:
            # An actual submodule checkout requires the Git metadata at root;
            # the trusted archive checker binds all three exact gitlink SHAs.
            proposed = checker.git_tree(ROOT, "HEAD")
            for path, sha in checker.EXTERNAL_GITLINKS.items():
                self.assertEqual(proposed.get(path), ("160000", sha))
            allowed.add(".gitmodules")
        unexpected = [p for p in root_files if p not in allowed
                      and not p.lower().endswith(".md")]
        self.assertEqual(unexpected, [])
        self.assertIn(".gitignore", root_files)
        self.assertIn("LICENSE", root_files)

    def test_second_stage_all_additional_files_preserve_original_git_identity(self):
        """Check exactly 29 original baseline files, blob IDs, modes and hashes."""
        self.assertEqual(len(checker.ADDITIONAL_HISTORICAL_ROOT_RELOCATIONS), 29)
        manifest = json.loads((ROOT / "sandbox/archive-manifest.json").read_text())
        by_original = {e["original_path"]: e for e in manifest["files"]}
        self.assertEqual(len(by_original), 221)
        proposed = checker.git_tree(ROOT, "HEAD")
        baseline = checker.git_tree(ROOT, checker.BASELINE)
        for name in checker.ADDITIONAL_HISTORICAL_ROOT_RELOCATIONS:
            with self.subTest(path=name):
                dest = f"historical/{name}"
                self.assertNotIn(name, proposed)
                self.assertFalse((ROOT / name).exists())
                self.assertIn(dest, proposed)
                self.assertEqual(proposed[dest], baseline[name])
                self.assertEqual(by_original[name]["preserved_path"], dest)
                data = (ROOT / dest).read_bytes()
                self.assertEqual(len(data), by_original[name]["size_bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(),
                                 by_original[name]["sha256"])

    def test_historical_index_contains_all_47_original_moved_files(self):
        """Prevent incomplete historical navigation after both cleanup stages."""
        manifest = json.loads((ROOT / "sandbox/archive-manifest.json").read_text())
        moved = [e for e in manifest["files"]
                 if e["preserved_path"].startswith("historical/")]
        self.assertEqual(len(moved), 47)
        index = (ROOT / "historical/README.md").read_text(encoding="utf-8")
        for entry in moved:
            with self.subTest(path=entry["preserved_path"]):
                self.assertIn(entry["original_path"], index)

if __name__ == "__main__":
    unittest.main()
