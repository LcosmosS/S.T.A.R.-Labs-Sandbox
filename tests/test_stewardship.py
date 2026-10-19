import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "stewardship"))
from evaluate import (
    classify_paths, evaluate, load_policy, has_valid_steward_approval, validate_policy,
)

POLICY = load_policy()
HEAD = "a" * 40
OTHER = "b" * 40


def review(login="LibertySquared", state="APPROVED", commit=HEAD,
           date="2026-10-19T00:00:00Z", review_id=10):
    return {
        "id": review_id, "user": {"login": login}, "state": state,
        "commit_id": commit, "submitted_at": date,
    }


class StewardshipTests(unittest.TestCase):
    def approval(self, **overrides):
        args = dict(
            author="contributor", head_sha=HEAD, reviews=[review()],
            permissions={"LibertySquared": "write"}, policy=POLICY,
            reviews_complete=True, permissions_complete=True,
        )
        args.update(overrides)
        return has_valid_steward_approval(**args)

    def test_experiment_only_passes_without_review(self):
        result = evaluate(
            author="author", head_sha=HEAD, files_head_sha=HEAD,
            files=[{"filename": "experiments/SBX-2026-0001-demo/results.json", "status": "added"}],
            files_complete=True, reviews=[], reviews_complete=True, permissions={},
            permissions_complete=True, policy=POLICY,
        )
        self.assertEqual(result["conclusion"], "success")

    def test_experiment_plus_protected_fails_without_approval(self):
        result = evaluate(
            author="author", head_sha=HEAD, files_head_sha=HEAD,
            files=[{"filename": "experiments/SBX-2026-0001-demo/results.json"},
                   {"filename": "scripts/tool.py"}],
            files_complete=True, reviews=[], reviews_complete=True, permissions={},
            permissions_complete=True, policy=POLICY,
        )
        self.assertEqual(result["conclusion"], "failure")

    def test_file_snapshot_from_an_old_head_cannot_exempt_current_head(self):
        result = evaluate(
            author="author", head_sha=OTHER, files_head_sha=HEAD,
            files=[{"filename": "experiments/SBX-2026-0001-demo/results.json"}],
            files_complete=True, reviews=[], reviews_complete=True, permissions={},
            permissions_complete=True, policy=POLICY,
        )
        self.assertEqual(result["conclusion"], "failure")
        self.assertIn("not bound", result["reasons"][0])

    def test_author_cannot_approve_self(self):
        ok, _ = self.approval(author="LibertySquared")
        self.assertFalse(ok)

    def test_current_head_approval_passes(self):
        ok, _ = self.approval()
        self.assertTrue(ok)

    def test_stale_approval_fails(self):
        ok, _ = self.approval(reviews=[review(commit=OTHER)])
        self.assertFalse(ok)

    def test_dismissed_approval_does_not_count(self):
        ok, _ = self.approval(reviews=[review(state="DISMISSED")])
        self.assertFalse(ok)

    def test_change_request_blocks_even_with_other_approval(self):
        reviews = [
            review(login="LibertySquared", review_id=10, date="2026-10-18T00:00:00Z"),
            review(login="LcosmosS", state="CHANGES_REQUESTED",
                   review_id=20, date="2026-10-19T00:00:00Z"),
        ]
        ok, _ = self.approval(
            reviews=reviews,
            permissions={"LibertySquared": "write", "LcosmosS": "write"},
        )
        self.assertFalse(ok)

    def test_dismissal_does_not_clear_change_request(self):
        reviews = [
            review(login="LcosmosS", state="CHANGES_REQUESTED",
                   review_id=20, date="2026-10-18T00:00:00Z"),
            review(login="LcosmosS", state="DISMISSED",
                   review_id=21, date="2026-10-19T00:00:00Z"),
            review(login="LibertySquared", state="APPROVED",
                   review_id=22, date="2026-10-19T00:00:00Z"),
        ]
        ok, reason = self.approval(
            reviews=reviews,
            permissions={"LibertySquared": "write", "LcosmosS": "write"},
        )
        self.assertFalse(ok)
        self.assertIn("unresolved change request", reason)

    def test_review_order_uses_review_id_when_timestamps_tie(self):
        tied_time = "2026-10-19T00:00:00Z"
        reviews = [
            review(login="LcosmosS", state="CHANGES_REQUESTED",
                   review_id=51, date=tied_time),
            review(login="LcosmosS", state="APPROVED",
                   review_id=50, date=tied_time),
            review(login="LibertySquared", state="APPROVED",
                   review_id=52, date=tied_time),
        ]
        ok, reason = self.approval(
            reviews=reviews,
            permissions={"LibertySquared": "write", "LcosmosS": "write"},
        )
        self.assertFalse(ok)
        self.assertIn("unresolved change request", reason)

    def test_lost_write_permission_fails(self):
        ok, _ = self.approval(permissions={"LibertySquared": "read"})
        self.assertFalse(ok)

    def test_omitted_completeness_flags_fail_closed(self):
        ok, reason = has_valid_steward_approval(
            author="contributor", head_sha=HEAD, reviews=[review()],
            permissions={"LibertySquared": "write"}, policy=POLICY,
        )
        self.assertFalse(ok)
        self.assertIn("incomplete", reason)

    def test_malformed_changed_file_row_fails_closed(self):
        experiment_only, reasons = classify_paths([None], complete=True, policy=POLICY)
        self.assertFalse(experiment_only)
        self.assertIn("malformed", reasons[0])

    def test_malformed_review_rows_and_users_fail_closed(self):
        ok, reason = self.approval(reviews=[None])
        self.assertFalse(ok)
        self.assertIn("malformed", reason)
        ok, reason = self.approval(reviews=[{"id": 1, "user": None, "state": "APPROVED"}])
        self.assertFalse(ok)
        self.assertIn("malformed user", reason)

    def test_rename_checks_old_and_new_path(self):
        experiment_only, _ = classify_paths([{
            "filename": "experiments/SBX-2026-0001-demo/x.py",
            "previous_filename": "scripts/x.py", "status": "renamed",
        }], complete=True, policy=POLICY)
        self.assertFalse(experiment_only)

    def test_unknown_and_template_paths_are_protected(self):
        for path in ("experiments/README.md", "experiments/_template/example.py",
                     "random.txt", ".gitmodules"):
            with self.subTest(path=path):
                self.assertFalse(classify_paths(
                    [{"filename": path}], complete=True, policy=POLICY
                )[0])

    def test_incomplete_files_fail_closed(self):
        self.assertFalse(classify_paths([], complete=False, policy=POLICY)[0])

    def test_incomplete_review_or_permission_results_fail_closed(self):
        ok, _ = self.approval(reviews_complete=False)
        self.assertFalse(ok)
        ok, _ = self.approval(permissions_complete=False)
        self.assertFalse(ok)

    def test_invalid_policy_pattern_is_rejected_on_load(self):
        invalid = dict(POLICY)
        invalid["approval_free_path_pattern"] = "["
        with self.assertRaises(ValueError):
            validate_policy(invalid)

    def test_evaluate_returns_failed_result_for_invalid_policy(self):
        invalid = dict(POLICY)
        invalid["approval_free_path_pattern"] = "["
        result = evaluate(
            author="author", head_sha=HEAD, files_head_sha=HEAD,
            files=[{"filename": "experiments/SBX-2026-0001-demo/x.py"}],
            files_complete=True, reviews=[], reviews_complete=True, permissions={},
            permissions_complete=True, policy=invalid,
        )
        self.assertEqual(result["conclusion"], "failure")
        self.assertIn("policy configuration invalid", result["reasons"][0])


if __name__ == "__main__":
    unittest.main()
