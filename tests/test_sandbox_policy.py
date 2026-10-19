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
    """Construct a valid miniature sandbox fixture for policy tests."""
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
        "epistemic_status": {"claim_of_truth": False, "independently_reviewed": False, "eligible_for_automatic_promotion": False},
        "proposition": "Deliberately false universal assertion.",
        "falsifier": "Explicit integer counterexample.",
        "provenance": {"input_kind": "synthetic", "sources": []},
        "limitations": ["Demonstration only"]
    }
    (exp / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    return exp, meta


class PolicyTests(unittest.TestCase):
    def test_valid_sample_and_legacy_archive(self):
        """Allow valid experiment metadata without reclassifying old archive files."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            baseline(root)
            (root / "R&D").mkdir()
            (root / "R&D" / "Proof Sketch.pdf").write_text("legacy", encoding="utf-8")
            self.assertEqual(validator.inspect(root), [])

    def test_prohibits_self_certification(self):
        """Prevent experiments from asserting validated scientific status."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, meta = baseline(root)
            meta["status"] = "validated"
            (exp / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            self.assertTrue(any("status" in e for e in validator.inspect(root)))

    def test_prohibits_automatic_promotion(self):
        """Reject any attempt to enable automatic upstream promotion."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, meta = baseline(root)
            meta["epistemic_status"]["eligible_for_automatic_promotion"] = True
            (exp / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            self.assertTrue(any("promotion" in e for e in validator.inspect(root)))

    def test_prevents_claim_of_truth_and_review_self_attestation(self):
        """Reject self-certified truth and independent-review claims."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, meta = baseline(root)
            meta["epistemic_status"]["claim_of_truth"] = True
            meta["epistemic_status"]["independently_reviewed"] = True
            (exp / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            messages = validator.inspect(root)
            self.assertTrue(any("claim_of_truth" in e for e in messages))
            self.assertTrue(any("independently_reviewed" in e for e in messages))

    def test_missing_metadata_rejected(self):
        """Require metadata for each new experiment."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, _ = baseline(root)
            (exp / "metadata.json").unlink()
            self.assertTrue(any("missing metadata" in e for e in validator.inspect(root)))

    def test_upstream_authority_directory_rejected(self):
        """Reject the reserved controlled-execution authority namespace."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            baseline(root)
            (root / "controlled_execution").mkdir()
            self.assertTrue(any("Reserved upstream" in e for e in validator.inspect(root)))


class AdditionalBoundaryTests(unittest.TestCase):
    def test_unknown_keys_and_boolean_schema_version_are_rejected(self):
        """Reject schema violations and malformed metadata field types."""
        for update in [{"verified": True}, {"schema_version": True},
                       {"status": []}, {"limitations": [""]},
                       {"provenance": {"input_kind": "synthetic", "sources": [123]}}]:
            with self.subTest(update=update), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                exp, meta = baseline(root)
                meta.update(update)
                (exp / 'metadata.json').write_text(json.dumps(meta))
                self.assertTrue(validator.inspect(root))

    def test_nested_authority_fields_are_rejected(self):
        """Reject unapproved nested authority flags and unpinned revisions."""
        for section, key, value in [('epistemic_status', 'physical_support', True),
                                    ('provenance', 'verified', True),
                                    ('provenance', 'upstream_commit', 'main')]:
            with self.subTest(section=section, key=key), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                exp, meta = baseline(root)
                meta[section][key] = value
                (exp / 'metadata.json').write_text(json.dumps(meta))
                self.assertTrue(validator.inspect(root))

    def test_duplicate_json_keys_rejected(self):
        """Reject ambiguous experiment JSON containing duplicate keys."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, meta = baseline(root)
            text = json.dumps(meta)
            (exp / 'metadata.json').write_text(text[:-1] + ', "scope":"sandbox-only"}')
            self.assertTrue(any('duplicate' in error for error in validator.inspect(root)))

    def test_file_and_symlink_experiment_entries_rejected(self):
        """Reject unclassified files and symlinks within experiments."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, _ = baseline(root)
            rogue = root / 'experiments/unclassified.py'
            rogue.write_text('raise AssertionError("must not execute")')
            self.assertTrue(any('unexpected' in error for error in validator.inspect(root)))
            rogue.unlink()
            (exp / 'metadata.json').unlink()
            (exp / 'metadata.json').symlink_to('/etc/passwd')
            self.assertTrue(any('symlink' in error for error in validator.inspect(root)))

    def test_false_control_requires_visible_false_label(self):
        """Require deliberately false controls to be visibly disclosed."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exp, _ = baseline(root)
            (exp / 'README.md').write_text('SANDBOX only')
            self.assertTrue(any('FALSE' in error for error in validator.inspect(root)))


if __name__ == "__main__":
    unittest.main()
