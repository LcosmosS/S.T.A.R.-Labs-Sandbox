"""Tests for structural sandbox admission rules, not for hypothesis truth."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "validate_sandbox.py"
spec = importlib.util.spec_from_file_location("sandbox_validator", SOURCE)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def baseline(root):
    (root / "README.md").write_text("SANDBOX", encoding="utf-8")
    (root / "DISCLAIMER.md").write_text("not verified upstream", encoding="utf-8")
    (root / "experiments").mkdir()
    exp = root / "experiments" / "SBX-2026-0001-demo"
    exp.mkdir()
    (exp / "README.md").write_text("SANDBOX / intentionally FALSE control", encoding="utf-8")
    meta = {
        "schema_version": 1,
        "id": "SBX-2026-0001",
        "title": "Example",
        "status": "intentionally-false-control",
        "scope": "sandbox-only",
        "epistemic_status": {"eligible_for_automatic_promotion": False},
        "proposition": "Deliberately false universal assertion.",
        "falsifier": "Explicit integer counterexample.",
        "provenance": {"input_kind": "synthetic", "sources": []},
        "limitations": ["Demonstration only"]
    }
    (exp / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    return exp, meta


class PolicyTests(unittest.TestCase):
    def test_valid_sample_and_legacy_archive(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            baseline(root)
            (root / "R&D").mkdir()
            (root / "R&D" / "Proof Sketch.pdf").write_text("legacy", encoding="utf-8")
            self.assertEqual(validator.inspect(root), [])

    def test_prohibits_self_certification(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, meta = baseline(root)
            meta["status"] = "validated"
            (exp / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            self.assertTrue(any("status" in e for e in validator.inspect(root)))

    def test_prohibits_automatic_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, meta = baseline(root)
            meta["epistemic_status"]["eligible_for_automatic_promotion"] = True
            (exp / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            self.assertTrue(any("promotion" in e for e in validator.inspect(root)))

    def test_missing_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, _ = baseline(root)
            (exp / "metadata.json").unlink()
            self.assertTrue(any("missing metadata" in e for e in validator.inspect(root)))

    def test_upstream_authority_directory_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            baseline(root)
            (root / "controlled_execution").mkdir()
            self.assertTrue(any("Reserved upstream" in e for e in validator.inspect(root)))


if __name__ == "__main__":
    unittest.main()
