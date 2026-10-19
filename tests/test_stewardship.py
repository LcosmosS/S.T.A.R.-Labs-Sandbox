import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "stewardship"))
from evaluate import classify_paths, evaluate, load_policy, has_valid_steward_approval

POLICY = load_policy()
HEAD = "a" * 40

def review(login="LibertySquared", state="APPROVED", commit=HEAD, date="2026-10-19T00:00:00Z"):
    return {"user": {"login": login}, "state": state, "commit_id": commit, "submitted_at": date}

class StewardshipTests(unittest.TestCase):
    def approval(self, **overrides):
        args = dict(author="contributor", head_sha=HEAD, reviews=[review()],
                    permissions={"LibertySquared": "write"}, policy=POLICY)
        args.update(overrides)
        return has_valid_steward_approval(**args)

    def test_experiment_only_passes_without_review(self):
        result = evaluate(author="author", head_sha=HEAD,
            files=[{"filename":"experiments/SBX-2026-0001-demo/results.json","status":"added"}],
            files_complete=True, reviews=[], reviews_complete=True, permissions={},
            permissions_complete=True, policy=POLICY)
        self.assertEqual(result["conclusion"], "success")

    def test_experiment_plus_protected_fails_without_approval(self):
        result = evaluate(author="author", head_sha=HEAD,
            files=[{"filename":"experiments/SBX-2026-0001-demo/results.json"},
                   {"filename":"scripts/tool.py"}], files_complete=True, reviews=[],
            reviews_complete=True, permissions={}, permissions_complete=True, policy=POLICY)
        self.assertEqual(result["conclusion"], "failure")

    def test_author_cannot_approve_self(self):
        ok, _ = self.approval(author="LibertySquared")
        self.assertFalse(ok)

    def test_current_head_approval_passes(self):
        ok, _ = self.approval()
        self.assertTrue(ok)

    def test_stale_approval_fails(self):
        ok, _ = self.approval(reviews=[review(commit="b" * 40)])
        self.assertFalse(ok)

    def test_dismissed_approval_does_not_count(self):
        ok, _ = self.approval(reviews=[review(state="DISMISSED")])
        self.assertFalse(ok)

    def test_change_request_blocks_even_with_other_approval(self):
        reviews = [review(login="LibertySquared", date="2026-10-18T00:00:00Z"),
                   review(login="LcosmosS", state="CHANGES_REQUESTED", date="2026-10-19T00:00:00Z")]
        ok, _ = self.approval(reviews=reviews, permissions={"LibertySquared":"write","LcosmosS":"write"})
        self.assertFalse(ok)

    def test_lost_write_permission_fails(self):
        ok, _ = self.approval(permissions={"LibertySquared":"read"})
        self.assertFalse(ok)

    def test_rename_checks_old_and_new_path(self):
        experiment_only, _ = classify_paths([{"filename":"experiments/SBX-2026-0001-demo/x.py",
            "previous_filename":"scripts/x.py","status":"renamed"}], complete=True, policy=POLICY)
        self.assertFalse(experiment_only)

    def test_unknown_and_template_paths_are_protected(self):
        for path in ("experiments/README.md", "experiments/_template/example.py",
                     "random.txt", ".gitmodules"):
            self.assertFalse(classify_paths([{"filename":path}], complete=True, policy=POLICY)[0])

    def test_incomplete_files_fail_closed(self):
        self.assertFalse(classify_paths([], complete=False, policy=POLICY)[0])

    def test_incomplete_review_or_permission_results_fail_closed(self):
        ok, _ = self.approval(reviews_complete=False)
        self.assertFalse(ok)
        ok, _ = self.approval(permissions_complete=False)
        self.assertFalse(ok)

if __name__ == "__main__":
    unittest.main()
