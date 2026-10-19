import sys
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "scripts" / "stewardship"),
)

from app import StewardshipError, StewardshipService


class LifecycleWebhookTests(unittest.TestCase):

    def setUp(self):
        self.service = object.__new__(StewardshipService)

    def test_lifecycle_events_without_repository_are_ignored(self):
        for event in (
            "ping",
            "installation",
            "installation_repositories",
        ):
            with self.subTest(event=event):
                result = self.service.validate_webhook(event, {})
                self.assertTrue(result["ignored"])

    def test_pr_without_repository_fails_closed(self):
        with self.assertRaises(StewardshipError):
            self.service.validate_webhook("pull_request", {})

    def test_review_without_repository_fails_closed(self):
        with self.assertRaises(StewardshipError):
            self.service.validate_webhook("pull_request_review", {})


if __name__ == "__main__":
    unittest.main()
