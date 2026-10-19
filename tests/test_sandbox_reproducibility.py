"""Negative and positive reproducibility tests; no scientific execution."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import importlib.util

SOURCE = Path(__file__).resolve().parents[1] / "scripts/reproducibility/candidates.py"
spec = importlib.util.spec_from_file_location("sandbox_repro_candidates", SOURCE)
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)


class ReproducibilityContractTests(unittest.TestCase):
    """Exercise strict artifact intake without input mutation or scientific gates."""

    def setUp(self):
        """Build a source-separated synthetic SBX fixture in a temporary path."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.root = self.repo / "experiments" / "SBX-2026-0004-demo"
        self.root.mkdir(parents=True)
        self.csv = b"objid,ra,dec,sfr\n1,42.5,8.0,1.2\n1,42.5,8.0,1.2\n2,43.5,9.0,\n"
        self.sql = b"SELECT TOP 10 p.objid FROM PhotoObj AS p\n"
        (self.root / "sample.csv").write_bytes(self.csv)
        (self.root / "probe.sql").write_bytes(self.sql)
        self.manifest = {
            "schema_version": 1, "experiment_id": "SBX-2026-0004",
            "scope": "sandbox-only", "status": "exploratory",
            "source_kind": "synthetic", "scientific_claim": False,
            "independently_reviewed": False, "automatic_promotion": False,
            "artifacts": [
                self.entry("sample.csv", self.csv, "csv",
                           rows=3, columns=["objid", "ra", "dec", "sfr"]),
                self.entry("probe.sql", self.sql, "sql"),
            ],
        }

    def entry(self, path, body, fmt, rows=None, columns=None):
        """Create exact source/size/hash pins from fixture bytes."""
        return {"path": path, "sha256": hashlib.sha256(body).hexdigest(),
                "size_bytes": len(body), "format": fmt, "columns": columns,
                "rows": rows, "source": "synthetic temporary unit-test fixture",
                "source_commit": None}

    def save(self):
        """Persist a proposed manifest to the disposable experiment directory."""
        (self.root / "reproducibility.json").write_text(json.dumps(self.manifest))

    def test_valid_contract_retains_duplicates_and_nulls(self):
        """Preserve all rows and describe missing values rather than dropping any."""
        before = (self.root / "sample.csv").read_bytes()
        x = repro.check_contract(self.root, self.manifest)
        self.assertEqual(x["artifacts"][0]["rows_retained"], 3)
        self.assertEqual(x["artifacts"][0]["duplicate_rows_retained"], 1)
        self.assertEqual(x["artifacts"][0]["null_count_by_column"]["sfr"], 1)
        self.assertEqual(x["artifacts"][1]["select_top"], 10)
        self.assertFalse(x["artifacts"][1]["sql_authorized_to_execute"])
        self.assertFalse(x["automatic_promotion"])
        self.assertFalse(x["scientific_claim"])
        self.assertFalse(x["execution_performed"])
        self.assertEqual((self.root / "sample.csv").read_bytes(), before)

    def test_byte_and_row_mutation_fail_closed(self):
        """Reject unrecorded dataset edits, even when row structure still parses."""
        (self.root / "sample.csv").write_bytes(self.csv + b"3,45,10,2.0\n")
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            repro.check_contract(self.root, self.manifest)
        self.manifest["artifacts"][0] = self.entry(
            "sample.csv", self.csv + b"3,45,10,2.0\n", "csv",
            rows=3, columns=["objid", "ra", "dec", "sfr"])
        with self.assertRaisesRegex(ValueError, "row count drift"):
            repro.check_contract(self.root, self.manifest)

    def test_unchanged_length_mutation_rejected_by_hash(self):
        """A same-length changed byte does not satisfy the declared SHA-256."""
        (self.root / "probe.sql").write_bytes(self.sql.replace(b"10", b"11"))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            repro.check_contract(self.root, self.manifest)

    def test_malformed_csv_and_duplicate_headers_fail(self):
        """Reject inconsistent fields or duplicate schema declarations."""
        bad = b"objid,ra,ra,sfr\n1,2,3,4\n"
        (self.root / "sample.csv").write_bytes(bad)
        self.manifest["artifacts"][0] = self.entry(
            "sample.csv", bad, "csv", rows=1,
            columns=["objid", "ra", "ra", "sfr"])
        with self.assertRaisesRegex(ValueError, "duplicate headers"):
            repro.check_contract(self.root, self.manifest)
        bad = b"objid,ra,dec,sfr\n1,2,3\n"
        (self.root / "sample.csv").write_bytes(bad)
        self.manifest["artifacts"][0] = self.entry(
            "sample.csv", bad, "csv", rows=1,
            columns=["objid", "ra", "dec", "sfr"])
        with self.assertRaisesRegex(ValueError, "malformed"):
            repro.check_contract(self.root, self.manifest)

    def test_forbidden_sql_and_multi_statements_rejected(self):
        """Block obvious DML, unbounded SQL and multiple statements."""
        for content in (
            b"SELECT * FROM PhotoObj",
            b"SELECT TOP 10 * INTO MyDB.table FROM PhotoObj",
            b"SELECT TOP 10 * FROM p; DROP TABLE q",
            b"UPDATE x SET y=1",
            b"SELECT TOP 10 * FROM p /* hidden */",
            b"SELECT TOP 200001 * FROM p",
        ):
            with self.subTest(sql=content):
                (self.root / "probe.sql").write_bytes(content)
                self.manifest["artifacts"][1] = self.entry(
                    "probe.sql", content, "sql")
                with self.assertRaisesRegex(ValueError, "SQL|SELECT"):
                    repro.check_contract(self.root, self.manifest)

    def test_scientific_authority_flags_are_unconditionally_false(self):
        """No user-supplied reproducibility receipt can self-certify a claim."""
        for field in ("scientific_claim", "independently_reviewed",
                      "automatic_promotion"):
            with self.subTest(field=field):
                self.manifest[field] = True
                with self.assertRaisesRegex(ValueError, field):
                    repro.check_contract(self.root, self.manifest)
                self.manifest[field] = False

    def test_path_traversal_and_symlink_inputs_forbidden(self):
        """Reject input substitution through absolute and symlinked paths."""
        original = self.manifest["artifacts"][0]["path"]
        for bad in ("../sample.csv", "/tmp/sample.csv", "nested/../sample.csv"):
            with self.subTest(path=bad):
                self.manifest["artifacts"][0]["path"] = bad
                with self.assertRaisesRegex(ValueError, "unsafe artifact"):
                    repro.check_contract(self.root, self.manifest)
        self.manifest["artifacts"][0]["path"] = "link.csv"
        (self.root / "link.csv").symlink_to(self.root / original)
        with self.assertRaisesRegex(ValueError, "symlink"):
            repro.check_contract(self.root, self.manifest)

    def test_discovers_only_opted_in_experiment_manifests(self):
        """Read only SBX manifests; no data or source code is executed."""
        self.save()
        report = repro.discover(self.repo)
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["experiment_id"], "SBX-2026-0004")
        self.assertEqual(report[0]["status"], "exploratory")
        (self.root / "reproducibility.json").unlink()
        self.assertEqual(repro.discover(self.repo), [])

    def test_duplicate_json_keys_are_rejected(self):
        """Detect conflicting duplicate keys in an otherwise plausible contract."""
        target = self.root / "duplicate.json"
        target.write_text('{"scientific_claim":false,"scientific_claim":true}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            repro.load(target)

    def test_unexpected_fields_and_boolean_sizes_rejected(self):
        """Reject schema expansion and booleans masquerading as integer sizes."""
        self.manifest["support_eligible"] = True
        with self.assertRaisesRegex(ValueError, "schema fields"):
            repro.check_contract(self.root, self.manifest)
        del self.manifest["support_eligible"]
        self.manifest["artifacts"][0]["size_bytes"] = True
        with self.assertRaisesRegex(ValueError, "size limit"):
            repro.check_contract(self.root, self.manifest)


if __name__ == "__main__":
    unittest.main()
