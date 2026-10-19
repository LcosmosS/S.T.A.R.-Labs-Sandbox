import sys
import tempfile
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
           date="2026-10-19T00:00:00Z"):
    return {"user": {"login": login}, "state": state,
            "commit_id": commit, "submitted_at": date}


def pr(number=1, sha=HEAD, author="contributor"):
    return {"number": number, "state": "open", "user": {"login": author},
            "head": {"sha": sha}, "html_url": f"https://github.com/{REPO}/pull/{number}"}


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

    def installation_token(self, installation_id):
        return "test-installation-token"

    def list_open_pulls(self, token):
        return list(self.prs.values())

    def get_pull(self, number, token):
        return self.prs[number]

    def list_files(self, number, token):
        return self.files[number]

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
    def service(self, api):
        return StewardshipService(
            api=api, policy=load_policy(), repository_id=REPO_ID,
            repository_full_name=REPO, installation_id=7,
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

if __name__ == "__main__":
    unittest.main()
