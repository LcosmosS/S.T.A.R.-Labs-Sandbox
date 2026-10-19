import copy
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "scripts" / "stewardship"
sys.path.insert(0, str(HERE))
from app import DeliveryStore, GitHubApi, StewardshipService
from evaluate import load_policy

HEAD = "a" * 40
OTHER_SHA = "b" * 40
REPO = "LcosmosS/S.T.A.R.-Labs-Sandbox"
REPO_ID = 1069114334


def review(login="LibertySquared", state="APPROVED", commit=HEAD,
           date="2026-10-19T00:00:00Z", review_id=10):
    return {"id": review_id, "user": {"login": login}, "state": state,
            "commit_id": commit, "submitted_at": date}


def pr(number=1, sha=HEAD, author="contributor", base="c" * 40):
    return {"number": number, "state": "open", "user": {"login": author},
            "head": {"sha": sha}, "base": {"sha": base},
            "html_url": f"https://github.com/{REPO}/pull/{number}"}


class FakeGitHub:
    app_id = "test-app-id"

    def __init__(self, prs, files, reviews=None, permissions=None):
        self.prs = {item["number"]: item for item in prs}
        self.files = files
        self.reviews = reviews or {}
        self.permissions = permissions or {"LcosmosS": "write", "LibertySquared": "write"}
        self.published = []
        self.review_reads = []
        self.permission_reads = []
        self.mutate_after_files = {}

    def installation_token(self, installation_id):
        return "test-installation-token"

    def list_open_pulls(self, token):
        return [copy.deepcopy(item) for item in self.prs.values()]

    def get_pull(self, number, token):
        return copy.deepcopy(self.prs[number])

    def list_files(self, number, token):
        result = copy.deepcopy(self.files[number])
        if number in self.mutate_after_files:
            self.prs[number] = copy.deepcopy(self.mutate_after_files.pop(number))
        return result

    def list_reviews(self, number, token):
        self.review_reads.append(number)
        return self.reviews.get(number, [])

    def get_permission(self, login, token):
        self.permission_reads.append(login)
        if login not in self.permissions:
            raise RuntimeError("permission unavailable")
        return self.permissions[login]

    def publish_check(self, **kwargs):
        self.published.append(kwargs)


class AppIntegrationTests(unittest.TestCase):
    def service(self, api, policy=None):
        return StewardshipService(
            api=api, policy=load_policy() if policy is None else policy,
            repository_id=REPO_ID, repository_full_name=REPO, installation_id=7,
        )

    def test_dismissed_approval_fails_protected_pr(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": ".github/CODEOWNERS", "status": "modified"}]},
            reviews={1: [review(state="DISMISSED")]},
        )
        result = self.service(api).reconcile()
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")
        self.assertEqual(api.published[0]["conclusion"], "failure")
        self.assertIn("no eligible non-author steward approval", api.published[0]["summary"])

    def test_experiment_only_pr_passes_without_review_or_permission_reads(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": "experiments/SBX-2026-0001-demo/output.json",
                         "status": "added"}]},
            reviews={},
        )
        result = self.service(api).reconcile()
        self.assertEqual(result["published_checks"][0]["conclusion"], "success")
        self.assertEqual(api.published[0]["conclusion"], "success")
        self.assertEqual(api.review_reads, [])
        self.assertEqual(api.permission_reads, [])

    def test_current_head_approval_passes_protected_pr(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": "scripts/tool.py", "status": "modified"}]},
            reviews={1: [review(state="APPROVED", commit=HEAD)]},
        )
        result = self.service(api).reconcile()
        self.assertEqual(result["published_checks"][0]["conclusion"], "success")

    def test_stale_approval_fails_protected_pr(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": "scripts/tool.py", "status": "modified"}]},
            reviews={1: [review(state="APPROVED", commit=OTHER_SHA)]},
        )
        result = self.service(api).reconcile()
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")

    def test_same_sha_protected_pr_failure_prevents_experiment_sibling_leak(self):
        api = FakeGitHub(
            [pr(1, HEAD), pr(2, HEAD)],
            {
                1: [{"filename": "experiments/SBX-2026-0001-demo/output.json"}],
                2: [{"filename": "scripts/tool.py"}],
            },
            reviews={2: [review(state="DISMISSED")]},
        )
        result = self.service(api).reconcile()
        self.assertEqual(len(result["published_checks"]), 1)
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")
        self.assertEqual(set(result["published_checks"][0]["pull_requests"]), {1, 2})

    def test_incomplete_reviewer_permission_fails_closed(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": "scripts/tool.py"}]},
            reviews={1: [review(state="APPROVED")]}, permissions={"LibertySquared": "write"},
        )
        result = self.service(api).reconcile()
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")

    def test_dismissed_review_webhook_recomputes_protected_pr(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": ".github/CODEOWNERS", "status": "modified"}]},
            reviews={1: [review(state="DISMISSED")]},
        )
        service = self.service(api)
        payload = {
            "repository": {"id": REPO_ID, "full_name": REPO},
            "installation": {"id": 7},
            "action": "dismissed",
            "pull_request": pr(),
        }
        result = service.handle_webhook("pull_request_review", "delivery-1", payload)
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")

    def test_delivery_queue_deduplicates_and_completes_durably(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = DeliveryStore(str(Path(tmp) / "deliveries.sqlite3"))
            payload = {"repository": {"id": REPO_ID}}
            self.assertTrue(store.enqueue("delivery-1", "pull_request_review", payload))
            self.assertFalse(store.enqueue("delivery-1", "pull_request_review", payload))
            item = store.take_next()
            self.assertEqual(item["delivery_id"], "delivery-1")
            self.assertEqual(item["event_name"], "pull_request_review")
            self.assertEqual(item["payload"], payload)
            store.finish("delivery-1", True)
            self.assertFalse(store.enqueue("delivery-1", "pull_request_review", payload))
            self.assertIsNone(store.take_next())

    def test_check_publisher_uses_dedicated_name_and_app_source(self):
        api = GitHubApi(app_id="123", private_key="unused")
        calls = []
        def fake_request(path, token, *, method="GET", body=None, query=None):
            calls.append((path, method, body, query))
            if method == "GET":
                return {"total_count": 0, "check_runs": []}
            return {"id": 42}
        api.request = fake_request
        api.publish_check(head_sha=HEAD, conclusion="failure",
                          summary="Dismissed approval is invalid",
                          details_url=f"https://github.com/{REPO}/pull/1",
                          token="test-token")
        self.assertEqual(calls[0][0], f"/repos/{REPO}/commits/{HEAD}/check-runs")
        self.assertEqual(calls[1][1], "POST")
        self.assertEqual(calls[1][2]["name"], "sandbox-stewardship")
        self.assertEqual(calls[1][2]["conclusion"], "failure")


    def test_shared_head_sha_fails_closed_even_when_both_prs_are_experiment_only(self):
        api = FakeGitHub(
            [pr(1, HEAD, base="c" * 40), pr(2, HEAD, base="d" * 40)],
            {
                1: [{"filename": "experiments/SBX-2026-0001-demo/out.json"}],
                2: [{"filename": "experiments/SBX-2026-0002-demo/out.json"}],
            },
        )
        result = self.service(api).reconcile()
        self.assertEqual(len(result["published_checks"]), 1)
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")
        self.assertEqual(set(result["published_checks"][0]["pull_requests"]), {1, 2})
        self.assertIn("cannot distinguish", api.published[0]["summary"])

    def test_head_change_after_file_listing_fails_closed(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": "experiments/SBX-2026-0001-demo/out.json"}]},
        )
        api.mutate_after_files[1] = pr(1, OTHER_SHA)
        result = self.service(api).reconcile()
        self.assertTrue(result["published_checks"])
        self.assertTrue(all(item["conclusion"] == "failure" for item in result["published_checks"]))

    def test_periodic_reconciliation_catches_permission_revocation(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": "scripts/tool.py"}]},
            reviews={1: [review(state="APPROVED", commit=HEAD)]},
        )
        service = self.service(api)
        first = service.reconcile()
        self.assertEqual(first["published_checks"][0]["conclusion"], "success")
        api.permissions["LibertySquared"] = "read"
        second = service.reconcile()
        self.assertEqual(second["published_checks"][0]["conclusion"], "failure")

    def test_invalid_deployed_policy_publishes_failure_instead_of_crashing(self):
        api = FakeGitHub([pr()], {1: [{"filename": "scripts/tool.py"}]})
        bad_policy = load_policy()
        bad_policy["approval_free_path_pattern"] = "["
        service = self.service(api, policy=bad_policy)
        result = service.reconcile()
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")
        self.assertIn("policy configuration invalid", api.published[0]["summary"])

    def test_malformed_file_and_review_rows_publish_failure(self):
        file_api = FakeGitHub([pr()], {1: [None]})
        file_result = self.service(file_api).reconcile()
        self.assertEqual(file_result["published_checks"][0]["conclusion"], "failure")

        review_api = FakeGitHub(
            [pr()], {1: [{"filename": "scripts/tool.py"}]}, reviews={1: [None]}
        )
        review_result = self.service(review_api).reconcile()
        self.assertEqual(review_result["published_checks"][0]["conclusion"], "failure")


    def test_stale_webhook_payload_cannot_restore_a_dismissed_approval(self):
        api = FakeGitHub(
            [pr()], {1: [{"filename": "scripts/tool.py"}]},
            reviews={1: [review(state="DISMISSED")]},
        )
        payload = {
            "repository": {"id": REPO_ID, "full_name": REPO},
            "installation": {"id": 7},
            "action": "submitted",
            "pull_request": pr(),
            # This old event payload claims an approval; the authoritative API says dismissed.
            "review": review(state="APPROVED", commit=HEAD, review_id=11),
        }
        result = self.service(api).handle_webhook(
            "pull_request_review", "stale-approval-delivery", payload
        )
        self.assertEqual(result["published_checks"][0]["conclusion"], "failure")

    def test_reconciliations_are_serialized_against_out_of_order_workers(self):
        class BlockingGitHub(FakeGitHub):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.first_entered = threading.Event()
                self.release_first = threading.Event()
                self.second_entered = threading.Event()
                self.guard = threading.Lock()
                self.block_once = True

            def list_open_pulls(self, token):
                if threading.current_thread().name == "stewardship-first":
                    with self.guard:
                        should_block = self.block_once
                        self.block_once = False if should_block else self.block_once
                    if should_block:
                        self.first_entered.set()
                        if not self.release_first.wait(timeout=2):
                            raise RuntimeError("test timed out waiting to release first reconcile")
                elif threading.current_thread().name == "stewardship-second":
                    self.second_entered.set()
                return super().list_open_pulls(token)

        api = BlockingGitHub(
            [pr()], {1: [{"filename": "experiments/SBX-2026-0001-demo/out.json"}]}
        )
        service = self.service(api)
        results = []
        errors = []

        def run_reconcile():
            try:
                results.append(service.reconcile())
            except Exception as exc:
                errors.append(exc)

        first = threading.Thread(target=run_reconcile, name="stewardship-first")
        second = threading.Thread(target=run_reconcile, name="stewardship-second")
        first.start()
        self.assertTrue(api.first_entered.wait(timeout=1))
        second.start()
        try:
            self.assertFalse(api.second_entered.wait(timeout=0.1))
        finally:
            api.release_first.set()
        first.join(timeout=2)
        second.join(timeout=2)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)

if __name__ == "__main__":
    unittest.main()
