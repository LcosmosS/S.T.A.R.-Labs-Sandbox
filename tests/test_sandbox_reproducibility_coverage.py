"""Review coverage of upstream software CI without misrepresenting review gates."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "scripts/reproducibility/coverage.json"
AUTO = ROOT / ".github/workflows/sandbox-reproducibility.yml"
EXTENDED = ROOT / ".github/workflows/sandbox-extended-reproducibility.yml"

ORIGINAL = {
    "a01-activation-preflight.yml",
    "a01_primary_evidence.yml",
    "a01_release_package.yml",
    "a03_preexecution_release_review.yml",
    "a03_preexecution_verification.yml",
    "build-image.yml",
    "ci.yml",
    "codeql.yml",
    "independent_dataset_verification.yml",
    "main.yml",
    "notebooks.yml",
    "observational_dataset_intake.yml",
    "recovered-intake.yml",
    "sciserver-approval-offline.yml",
    "sciserver-v02-policy.yml",
    "sky_surveys.yml",
    "starmap.yml",
    "test.yml",
}
OPTIONAL = {
    "observational-lfs", "publisher-refetch", "recovered-lfs",
    "sage-notebooks", "sage-sky", "starmap-browser",
    "build-image", "legacy-unit-suite",
}
AUTO_JOBS = {
    "candidate-input-contracts", "upstream-dataset-sql",
    "upstream-sciserver-offline", "upstream-deterministic-numerics",
    "upstream-saved-packages", "pinned-arithmetic-source", "sandbox-codeql",
}


class CoverageIntegrityTests(unittest.TestCase):
    """Reject omitted workflows and unsupported claims of automatic verification."""

    def setUp(self):
        """Read the mapping and both workflow definitions."""
        self.value = json.loads(MATRIX.read_text(encoding="utf-8"))
        self.auto = AUTO.read_text(encoding="utf-8")
        self.extended = EXTENDED.read_text(encoding="utf-8")

    def test_exactly_eighteen_original_workflows_are_accounted_for(self):
        """Require a one-to-one inventory of the upstream workflow names."""
        rows = self.value["workflows"]
        self.assertEqual(len(rows), 18)
        self.assertEqual(
            {r["path"] for r in rows},
            {".github/workflows/" + p for p in ORIGINAL},
        )
        self.assertEqual(self.value["schema_version"], 1)
        self.assertEqual(
            self.value["upstream_commit"],
            "51927a9b396cdfa880f3128440db4715acdec8dc",
        )

    def test_every_automatic_claim_has_a_real_ci_job(self):
        """Identify every mapped check by its actual workflow job ID."""
        for row in self.value["workflows"]:
            with self.subTest(original=row["path"]):
                self.assertIn(row["coverage"], {
                    "automatic_subset", "partial_plus_on_demand",
                    "on_demand_only", "not_ported",
                })
                self.assertIsInstance(row["excluded_functions"], list)
                self.assertTrue(row["notes"])
                for job in row["automatic_checks"]:
                    self.assertIn(job, AUTO_JOBS)
                    if job != "sandbox-codeql":
                        self.assertIn("  " + job + ":\n", self.auto)
                option = row["on_demand_suite"]
                if option is not None:
                    self.assertIn(option, OPTIONAL)
                    self.assertIn("  " + option + ":\n", self.extended)
                    self.assertIn("inputs.suite == '" + option + "'", self.extended)

    def test_extended_checks_require_explicit_manual_selection(self):
        """Require no push/PR trigger and no privileged write or secret tokens."""
        self.assertIn("workflow_dispatch:", self.extended)
        self.assertIn("contents: read", self.extended)
        self.assertNotIn("pull_request_target", self.extended)
        self.assertNotIn("packages: write", self.extended)
        self.assertNotIn("secrets.", self.extended)
        self.assertNotIn("on:\n  push:", self.extended)
        self.assertNotIn("on:\n  pull_request:", self.extended)
        for mode in OPTIONAL:
            self.assertIn("  " + mode + ":\n", self.extended)
            self.assertIn("inputs.suite == '" + mode + "'", self.extended)

    def test_scientific_gates_are_never_claimed_by_coding_checks(self):
        """Do not grant scientific review or promotion from a passing pipeline."""
        for flag in (
            "automatic_promotion", "independent_scientific_review",
            "remote_sql_submission", "production_publication",
        ):
            self.assertIs(self.value[flag], False)
        self.assertIn("not", self.value["default_ci"].lower())
        self.assertIn("on_demand", self.value["default_ci"])

    def test_user_documentation_has_actual_code_fences(self):
        """Reject escaped backticks that break documented commands/examples."""
        content = (ROOT / "scripts/reproducibility/README.md").read_text()
        self.assertIn(chr(96) * 3 + "json", content)
        self.assertIn(chr(96) * 3 + "bash", content)
        self.assertNotIn(chr(92) + chr(96), content)


if __name__ == "__main__":
    unittest.main()
