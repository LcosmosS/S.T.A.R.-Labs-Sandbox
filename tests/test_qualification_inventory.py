"""Static P0 qualification audit remains fail-closed about executions."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/reproducibility/qualification_inventory.py"
spec = importlib.util.spec_from_file_location("qualification_inventory", MODULE)
qualify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualify)


class QualificationInventoryTests(unittest.TestCase):
    def test_eighteen_workflows_and_eight_optional_suites(self):
        receipt = qualify.inspect(ROOT)
        self.assertEqual(receipt["historical_workflows_inventoried"], 18)
        self.assertEqual(len(receipt["optional_suites"]), 8)
        self.assertFalse(receipt["scientific_validation"])
        self.assertTrue(all(s["execution_status"] == "NOT_RUN" for s in receipt["optional_suites"]))
        self.assertTrue(all(s["result"] == "NO_PASS_CLAIM" for s in receipt["optional_suites"]))

    def test_digest_pinned_sage_and_remaining_runtime_blockers(self):
        rows = {s["suite"]: s for s in qualify.inspect(ROOT)["optional_suites"]}
        for suite in ("sage-notebooks", "sage-sky"):
            self.assertNotIn("container_image_not_digest_pinned", rows[suite]["reasons"])
            self.assertIn("upstream_requirements_not_hash_locked", rows[suite]["reasons"])
            self.assertEqual(rows[suite]["environment_status"], "BLOCKED")
            self.assertEqual(rows[suite]["execution_status"], "NOT_RUN")
        workflow = (ROOT / ".github/workflows/sandbox-extended-reproducibility.yml").read_text()
        immutable = "sagemath/sagemath@sha256:310dfe23fc786f3a5a06a7b0387c60201ec79b32c0db941b7624505ee5edb565"
        self.assertEqual(workflow.count("image: " + immutable), 2)
        self.assertEqual(workflow.count("PINNED_SAGE_IMAGE: " + immutable), 1)
        self.assertNotIn("image: sagemath/sagemath:latest", workflow)


    def test_recovered_lfs_includes_pinned_audit_dependencies(self):
        workflow = (ROOT/".github/workflows/sandbox-extended-reproducibility.yml").read_text()
        recovered = workflow.split("  recovered-lfs:", 1)[1].split("  sage-notebooks:", 1)[0]
        self.assertIn("ref: 51927a9b396cdfa880f3128440db4715acdec8dc", recovered)
        self.assertIn("sparse-checkout-cone-mode: false", recovered)
        for name, blob in (
            ("preregistrations/EXP-MAP-A01/dataset_manifest.json",
             "108c6058e3c8f20477bea1a492ff54332d57c0c4"),
            ("data/provenance/publisher_byte_verification_2026-10-08.json",
             "36220a651872e509b7772d1c7bae46c679cdf35f"),
        ):
            self.assertIn("            " + name + "\n", recovered)
            self.assertIn("git hash-object " + name + ')" = ' + blob, recovered)
        self.assertIn("python3 -B scripts/validate_audit_registries.py 2>&1 | tee ../results/registry-audit.log", recovered)

    def test_coverage_manifest_defect_fails(self):
        # The inventory must not succeed if the 18-workflow census drifts.
        self.assertEqual(len(json.loads((ROOT/"scripts/reproducibility/coverage.json").read_text())["workflows"]), 18)


if __name__ == "__main__":
    unittest.main()
