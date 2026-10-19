"""Sandbox scientific source-port integrity and offline-operation tests.

Tests intentionally do not initialize third-party submodules, run ECC
numerical scripts or submit any remotely executable SciServer SQL.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTS = ROOT / "scripts" / "playground" / "ports"
MANIFEST = PORTS / "MANIFEST.json"
EXTERNAL = ROOT / "scripts" / "playground" / "external"
EXPECTED = {
    "sciserver": 8,
    "ecc": 9,
    "acsc": 6,
    "ansatz": 1,
}
SUBMODULE_COMMITS = {
    "scripts/playground/external/ecdata":
        "25cec5ecfec8b9f016eb1631ac633194c2bed39f",
    "scripts/playground/external/eclib":
        "39b3909a36d7d611b2d98e3751048b5ef8f5a2e2",
    "scripts/playground/external/lmfdb":
        "3c09a5f981d5fc3a841430d017ad8b2ab9cc1f15",
}


def git_blob_sha1(contents: bytes) -> str:
    """Return the object ID for Git's SHA-1 blob framing."""
    return hashlib.sha1(f"blob {len(contents)}\0".encode() + contents).hexdigest()


def load_manifest() -> dict:
    """Read the non-authoritative source-port manifest."""
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def pinned_policy():
    """Import the offline-only SciServer policy from the isolated port."""
    if str(PORTS) not in sys.path:
        sys.path.insert(0, str(PORTS))
    return importlib.import_module("integrations.sciserver.query_policy")


class PortIntegrityTests(unittest.TestCase):
    """Verify source immutability and explicit sandbox epistemic boundaries."""

    def test_24_files_match_pinned_upstream_git_blobs(self):
        """Reject altered source copies or missing mapped files."""
        manifest = load_manifest()
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["scope"], "sandbox-only")
        self.assertFalse(manifest["scientific_claim"])
        self.assertFalse(manifest["independently_reviewed"])
        self.assertFalse(manifest["eligible_for_automatic_promotion"])
        self.assertEqual(len(manifest["files"]), 24)
        expected_paths = set()
        group_counts = dict.fromkeys(EXPECTED, 0)
        source_commits = manifest["source_commits"]
        for entry in manifest["files"]:
            with self.subTest(path=entry["source_path"]):
                self.assertIn(entry["group"], group_counts)
                group_counts[entry["group"]] += 1
                self.assertEqual(entry["source_commit"],
                                 source_commits[entry["group"]])
                self.assertRegex(entry["source_commit"], r"^[0-9a-f]{40}$")
                rel = Path(entry["snapshot_path"])
                self.assertEqual(rel, Path("scripts/playground/ports")
                                 / entry["source_path"])
                self.assertNotIn("..", rel.parts)
                expected_paths.add(rel.as_posix())
                source_file = ROOT / rel
                self.assertTrue(source_file.is_file())
                self.assertFalse(source_file.is_symlink())
                self.assertEqual(git_blob_sha1(source_file.read_bytes()),
                                 entry["git_blob"])
        self.assertEqual(group_counts, EXPECTED)
        self.assertEqual(len(expected_paths), len(manifest["files"]))
        # Compare tracked source files, not interpreter-generated __pycache__.
        tracked = subprocess.run(
            ["git", "ls-files", "-z", "--", "scripts/playground/ports"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout.decode("utf-8").split("\0")
        actual_ports = {
            path for path in tracked if path and path not in {
                "scripts/playground/ports/MANIFEST.json",
                "scripts/playground/ports/README.md",
            }
        }
        self.assertEqual(actual_ports, expected_paths)

    def test_critical_source_origins_and_nonclaims(self):
        """Do not silently label an unmerged ECC draft or manuscript ACSC v2."""
        manifest = load_manifest()
        self.assertEqual(manifest["origin_repository"],
                         "LcosmosS/S.T.A.R.-Labs")
        self.assertEqual(
            manifest["source_commits"]["ecc"],
            "264faed10173d0e8db6822692d50333eee0af547")
        self.assertEqual(
            manifest["source_commits"]["sciserver"],
            "222a550b357bcbde8d6d5a0c7d0cbc9f05fa3bef")
        self.assertIn("unmerged", manifest["scientific_boundaries"]["ecc"])
        self.assertIn("not a release explicitly labeled ACSC v2",
                      manifest["scientific_boundaries"]["acsc"])
        self.assertIn("disabled",
                      manifest["scientific_boundaries"]["sciserver"])

    def test_real_git_submodules_match_exact_upstream_pins(self):
        """Assert real 160000 gitlinks and the published opt-in remote URLs."""
        manifest = load_manifest()
        actual = {v["path"]: v for v in manifest["submodules"]}
        self.assertEqual(set(actual), set(SUBMODULE_COMMITS))
        gitmodules = (ROOT / ".gitmodules").read_text(encoding="utf-8")
        for path, expected_sha in SUBMODULE_COMMITS.items():
            with self.subTest(path=path):
                self.assertEqual(actual[path]["commit"], expected_sha)
                self.assertEqual(actual[path]["git_mode"], "160000")
                self.assertFalse(actual[path]["initialized_by_ci"])
                self.assertIn(f'\tpath = {path}\n', gitmodules)
                self.assertIn(
                    f'\turl = https://github.com/{actual[path]["repo"]}.git\n',
                    gitmodules)
                raw = subprocess.run(
                    ["git", "ls-tree", "HEAD", path], cwd=ROOT, check=True,
                    capture_output=True, text=True,
                ).stdout.strip()
                self.assertEqual(raw,
                                 f"160000 commit {expected_sha}\t{path}")
        self.assertEqual(gitmodules.count('[submodule "'), 3)

    def test_ecc_control_is_not_executed_or_promoted(self):
        """Require the corrected v3 negative-control code as a pinned source."""
        script = (PORTS / "ecc_b01/investigator_a_v3.py").read_text()
        self.assertIn("def c03_record(", script)
        self.assertIn("C-03-NEG", script)
        self.assertIn("not c03_invalid['pass_']", script)
        self.assertIn("v3", (PORTS / "ecc_b01/protocol.md").read_text())

    def test_p0_ansatz_has_all_five_frozen_candidates(self):
        """Verify the exact closed search-frame identities are preserved."""
        doc = (PORTS / "preregistrations/P0-ANSATZ-001/protocol.md").read_text()
        self.assertIn("preregistered_closed", doc)
        for i in range(1, 6):
            self.assertIn(f"P0-T{i:03d}", doc)
        self.assertIn("Controlled execution: **disabled**", doc)


class OfflineSciServerTests(unittest.TestCase):
    """Exercise source policy and safe local receipts without live CasJobs."""

    def test_catalog_is_pinned_and_remote_submission_disabled(self):
        """Validate exact DR18 SQL sources and both blocked submission flags."""
        policy = pinned_policy()
        catalog = policy.load_catalog()
        self.assertFalse(json.loads(
            policy.CATALOG_PATH.read_text(encoding="utf-8")
        )["remote_submission_enabled"])
        self.assertEqual(set(catalog["queries"]),
                         {"DR18-CANARY-10", "DR18-DETERMINISTIC-200K"})
        self.assertTrue(catalog["queries"]["DR18-CANARY-10"]
                        ["preparation_enabled"])
        for record in catalog["queries"].values():
            self.assertFalse(record["submission_enabled"])
            self.assertRegex(record["approved_sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(catalog["queries"]
                         ["DR18-DETERMINISTIC-200K"]["preparation_enabled"])

    def test_prepare_only_canary_locally_with_private_receipt(self):
        """Create only local canary receipt files and reject the 200k plan."""
        policy = pinned_policy()
        with tempfile.TemporaryDirectory() as folder:
            location = Path(folder) / "private-state"
            planned = policy.prepare_casjobs_run(
                "DR18-CANARY-10", state_root=location)
            self.assertFalse(planned["plan"]["remote_submission_enabled"])
            self.assertFalse(planned["plan"]["automatic_registry_promotion"])
            self.assertEqual(planned["plan"]["max_rows"], 10)
            self.assertRegex(planned["receipt_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(location.stat().st_mode & 0o077, 0)
            with self.assertRaises(policy.PolicyViolation):
                policy.prepare_casjobs_run(
                    "DR18-DETERMINISTIC-200K", state_root=location)
            with self.assertRaises(policy.PolicyViolation):
                policy.prepare_casjobs_run(
                    "UNREGISTERED-QUERY", state_root=location)

    def test_catalog_tampering_is_rejected_before_execution(self):
        """Reject a forged catalog with remote submission switched on."""
        policy = pinned_policy()
        original = policy.CATALOG_PATH.read_text()
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "catalog.json"
            document = json.loads(original)
            document["remote_submission_enabled"] = True
            target.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(policy.PolicyViolation):
                policy.load_catalog(catalog_path=target, repo_root=policy.REPO_ROOT)
            document["remote_submission_enabled"] = False
            document["queries"][0]["approved_sha256"] = "0" * 64
            target.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(policy.PolicyViolation):
                policy.load_catalog(catalog_path=target, repo_root=policy.REPO_ROOT)

    def test_cli_list_and_validate_do_not_create_local_receipts(self):
        """Exercise CLI read paths without giving it credentials or a state dir."""
        for command in ("list", "validate"):
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, "-m", "scripts.playground.sciserver_offline",
                     command],
                    cwd=ROOT, capture_output=True, text=True, timeout=12,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                record = json.loads(result.stdout)
                self.assertEqual(record["scope"], "sandbox-only")
                self.assertEqual(record["execution"], "disabled")


if __name__ == "__main__":
    unittest.main()
