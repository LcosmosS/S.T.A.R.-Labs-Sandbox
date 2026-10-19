"""Tests for opt-in exploratory tooling, never scientific truth or inference."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/playground/runner.py"
specification = importlib.util.spec_from_file_location("sandbox_workbench", SOURCE)
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)
EXAMPLE = ROOT / "experiments/SBX-2026-0002-first-principles-workbench"


class SandboxWorkbenchTests(unittest.TestCase):
    """Test reproducibility, invalid inputs and strict sandbox-only outputs."""

    def setUp(self):
        """Create an independent copy of the synthetic fixture."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.csv_path = self.root / "synthetic_invariants.csv"
        self.csv_path.write_bytes((EXAMPLE / "synthetic_invariants.csv").read_bytes())
        self.study_path = self.root / "study.json"
        self.spec = json.loads((EXAMPLE / "study.json").read_text())
        self.save()

    def save(self):
        """Write a local study revision without mutating the repository fixture."""
        self.study_path.write_text(json.dumps(self.spec, indent=2) + "\n")

    def test_deterministic_synthetic_null_result(self):
        """Repeat identical seeds and input bytes to obtain identical outcomes."""
        first = runner.run_study(self.study_path)
        second = runner.run_study(self.study_path)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "exploratory")
        self.assertEqual(first["input"]["rows_retained"], 12)
        self.assertEqual(first["null"]["n_permutations"], 199)
        self.assertEqual(len(first["null"]["statistics"]), 199)
        self.assertTrue(0 < first["null"]["empirical_p_plus_one"] <= 1)
        self.assertFalse(first["scientific_claim"])
        self.assertFalse(first["eligible_for_automatic_promotion"])
        self.assertEqual(first["mapping"]["coordinate_unit"], "dimensionless")

    def test_seed_controls_null_realizations(self):
        """Changing a seed alters permutations but not the observed statistic."""
        first = runner.run_study(self.study_path)
        self.spec["null"]["seed"] = 1730
        self.save()
        second = runner.run_study(self.study_path)
        self.assertEqual(first["statistic"], second["statistic"])
        self.assertNotEqual(first["null"]["statistics"], second["null"]["statistics"])

    def test_extra_or_authoritative_study_fields_rejected(self):
        """Reject false scientific promotion and unknown status claims."""
        self.spec["status"] = "validated"
        self.save()
        with self.assertRaisesRegex(ValueError, "study cannot claim"):
            runner.run_study(self.study_path)
        self.spec["status"] = "exploratory"
        self.spec["independently_verified"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "exactly the documented fields"):
            runner.run_study(self.study_path)

    def test_physical_units_cannot_be_inserted_without_calibration(self):
        """Require dimensionless mathematical coordinates in the current runner."""
        self.spec["mapping"]["coordinate_unit"] = "Mpc"
        self.save()
        with self.assertRaisesRegex(ValueError, "dimensionless"):
            runner.run_study(self.study_path)

    def test_duplicate_rows_retained_not_silently_removed(self):
        """Preserve duplicate rows and record their count."""
        with self.csv_path.open("a") as stream:
            stream.write("-11,11,0,2.1\n")
        result = runner.run_study(self.study_path)
        self.assertEqual(result["input"]["rows_retained"], 13)
        self.assertEqual(result["input"]["duplicate_rows_retained"], 1)

    def test_missing_values_fail_closed(self):
        """Refuse incomplete measurements without silent row filtering."""
        self.csv_path.write_text(
            self.csv_path.read_text().replace("-11,11,0,2.1", "-11,11,0,")
        )
        with self.assertRaisesRegex(ValueError, "not numeric|finite"):
            runner.run_study(self.study_path)

    def test_domain_restrictions(self):
        """Reject zero discriminant, invalid conductor and fractional rank."""
        original = self.csv_path.read_text()
        for wrong in ("0,11,0,2.1", "-11,0,0,2.1", "-11,11,0.5,2.1"):
            with self.subTest(wrong=wrong):
                self.csv_path.write_text(original.replace("-11,11,0,2.1", wrong))
                with self.assertRaises(ValueError):
                    runner.run_study(self.study_path)

    def test_exchangeability_null_is_explicitly_limited(self):
        """Decline unimplemented null models rather than fabricate significance."""
        self.spec["null"]["method"] = "sky_shift"
        self.save()
        with self.assertRaisesRegex(ValueError, "unsupported null"):
            runner.run_study(self.study_path)

    def test_boolean_seed_and_unbounded_simulations_rejected(self):
        """Keep reproducible randomization parameters finite and well typed."""
        self.spec["null"]["seed"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "seed"):
            runner.run_study(self.study_path)
        self.spec["null"]["seed"] = 1729
        self.spec["null"]["n_permutations"] = 1000000
        self.save()
        with self.assertRaisesRegex(ValueError, "n_permutations"):
            runner.run_study(self.study_path)

    def test_constant_response_rejected(self):
        """Reject undefined Pearson correlation for a constant target."""
        original = self.csv_path.read_text().splitlines()
        altered = [original[0]] + [",".join(row.split(",")[:3] + ["1"]) for row in original[1:]]
        self.csv_path.write_text("\n".join(altered) + "\n")
        with self.assertRaisesRegex(ValueError, "constant values"):
            runner.run_study(self.study_path)

    def test_csv_header_and_duplicate_json_keys_rejected(self):
        """Disallow conflicting schema fields and duplicate JSON bindings."""
        self.csv_path.write_text(self.csv_path.read_text().replace(
            "delta,conductor,rank,mock_signal",
            "delta,conductor,rank,mock_signal,mock_signal"
        ))
        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
            runner.run_study(self.study_path)
        self.csv_path.write_bytes((EXAMPLE / "synthetic_invariants.csv").read_bytes())
        self.study_path.write_text('{"seed":1,"seed":2}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            runner.run_study(self.study_path)

    def test_input_cannot_escape_experiment_directory(self):
        """Prevent file traversal, absolute paths and symlink input reads."""
        self.spec["input"]["path"] = "../other.csv"
        self.save()
        with self.assertRaisesRegex(ValueError, "safe relative"):
            runner.run_study(self.study_path)
        self.spec["input"]["path"] = "external.csv"
        self.save()
        (self.root / "external.csv").symlink_to(self.csv_path)
        with self.assertRaisesRegex(ValueError, "nonsymlink|symlink"):
            runner.run_study(self.study_path)

    def test_symlink_above_experiment_root_is_not_an_input_violation(self):
        """Allow a linked ancestor when neither root nor input subtree is linked."""
        real_parent = self.root / "real_parent"
        experiment = real_parent / "experiment"
        experiment.mkdir(parents=True)
        (experiment / "synthetic_invariants.csv").write_bytes(self.csv_path.read_bytes())
        (experiment / "study.json").write_bytes(self.study_path.read_bytes())
        linked_parent = self.root / "linked_parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        result = runner.run_study(linked_parent / "experiment" / "study.json")
        self.assertEqual(result["input"]["rows_retained"], 12)

    def test_symlink_within_experiment_root_is_still_rejected(self):
        """Reject linked input directories even when they resolve inside root."""
        nested = self.root / "real_data"
        nested.mkdir()
        (nested / "synthetic_invariants.csv").write_bytes(self.csv_path.read_bytes())
        (self.root / "linked_data").symlink_to(nested, target_is_directory=True)
        self.spec["input"]["path"] = "linked_data/synthetic_invariants.csv"
        self.save()
        with self.assertRaisesRegex(ValueError, "symlink"):
            runner.run_study(self.study_path)

    def test_output_writes_only_inside_runs(self):
        """Contain optional JSON outputs without changing experimental input."""
        output = runner.output_path(self.study_path, "runs/trial.json")
        self.assertEqual(output, self.root / "runs/trial.json")
        for unsafe in ("../metadata.json", "runs/../metadata.json",
                       "/tmp/report.json", "metadata.json"):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                runner.output_path(self.study_path, unsafe)

    def test_arithmetic_mapping_axes_are_reproducible(self):
        """Check basic logarithmic/rank identities independently of upstream."""
        row = {"delta": "-100", "conductor": "1000", "rank": "2"}
        self.assertAlmostEqual(runner.axis_value(row, "log10_abs_delta", 1), 2)
        self.assertAlmostEqual(runner.axis_value(row, "log10_conductor", 1), 3)
        self.assertAlmostEqual(runner.axis_value(row, "rank", 1), 2)
        self.assertAlmostEqual(runner.axis_value(row, "rank_saturation", 1),
                               2 * __import__("math").atan(2) / __import__("math").pi)

    def test_snapshot_is_exactly_pinned_source_without_gates(self):
        """Hash all five source snapshots against the recorded Git blob IDs."""
        manifest = json.loads((ROOT / "scripts/playground/upstream_snapshot/MANIFEST.json").read_text())
        self.assertEqual(manifest["origin"]["repository"], "LcosmosS/S.T.A.R.-Labs")
        self.assertEqual(manifest["origin"]["commit"], "51927a9b396cdfa880f3128440db4715acdec8dc")
        self.assertEqual(len(manifest["files"]), 5)
        for entry in manifest["files"]:
            file = ROOT / entry["snapshot_path"]
            contents = file.read_bytes()
            blob = hashlib.sha1(f"blob {len(contents)}\0".encode() + contents).hexdigest()
            self.assertEqual(blob, entry["git_blob"])
            self.assertTrue(entry["snapshot_path"].startswith("scripts/playground/upstream_snapshot/src/"))
        forbidden = ("controlled_execution", "preregistrations", "registry/",
                     "release_packages", "independent_gate_report")
        self.assertFalse(any(
            any(item in entry["snapshot_path"] for item in forbidden)
            for entry in manifest["files"]
        ))


if __name__ == "__main__":
    unittest.main()
