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


if __name__ == "__main__":
    unittest.main()
