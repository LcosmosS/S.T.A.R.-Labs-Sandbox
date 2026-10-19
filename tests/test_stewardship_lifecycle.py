import hashlib
import hmac
import http.client
import json
import os
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "scripts" / "stewardship"),
)

import app
from app import StewardshipError, StewardshipService


EVENTS = ("ping", "installation", "installation_repositories")


class LifecycleWebhookTests(unittest.TestCase):

    def setUp(self):
        self.service = object.__new__(StewardshipService)

    def test_lifecycle_events_without_repository_are_ignored(self):
        for event in EVENTS:
            with self.subTest(event=event):
                result = self.service.validate_webhook(event, {})
                self.assertTrue(result["ignored"])

    def test_pr_without_repository_fails_closed(self):
        with self.assertRaises(StewardshipError):
            self.service.validate_webhook("pull_request", {})

    def test_review_without_repository_fails_closed(self):
        with self.assertRaises(StewardshipError):
            self.service.validate_webhook("pull_request_review", {})

    def test_queued_lifecycle_events_skip_reconciliation(self):
        with patch.object(
            self.service,
            "reconcile",
            side_effect=AssertionError("Lifecycle event must not reconcile"),
        ) as reconcile:
            for event in EVENTS:
                with self.subTest(event=event):
                    result = self.service.process_queued_event(event, {})
                    self.assertTrue(result["ignored"])

            reconcile.assert_not_called()

    def test_http_lifecycle_events_return_202_without_enqueue(self):
        secret = b"test-webhook-secret-" + b"x" * 32

        environment = {
            "GITHUB_APP_ID": "123",
            "GITHUB_APP_INSTALLATION_ID": "7",
            "GITHUB_WEBHOOK_SECRET": secret.decode(),
            "STEWARDSHIP_RECONCILIATION_TOKEN": "r" * 64,
            "PORT": "0",
        }

        def loopback_server(_address, handler):
            return ThreadingHTTPServer(("127.0.0.1", 0), handler)

        # Disable production workers for this test. The HTTP server
        # itself uses an ephemeral loopback port.
        with (
            patch.dict(os.environ, environment),
            patch.object(app, "_read_private_key", return_value="unused"),
            patch.object(app, "DeliveryStore") as store_class,
            patch.object(app.threading, "Thread"),
            patch.object(
                app,
                "ThreadingHTTPServer",
                side_effect=loopback_server,
            ),
        ):
            server = app.create_server()

        def post_webhook(event, signed=True):
            body = b"{}"
            headers = {
                "Content-Type": "application/json",
                "X-GitHub-Event": event,
                "X-GitHub-Delivery": "lifecycle-test-" + event,
            }

            if signed:
                signature = hmac.new(
                    secret, body, hashlib.sha256
                ).hexdigest()
                headers["X-Hub-Signature-256"] = "sha256=" + signature

            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_port, timeout=3
            )
            try:
                connection.request(
                    "POST", "/webhook", body=body, headers=headers
                )
                response = connection.getresponse()
                return response.status, json.loads(response.read())
            finally:
                connection.close()

        thread = threading.Thread(
            target=server.serve_forever,
            daemon=True,
        )
        thread.start()

        try:
            for event in EVENTS:
                with self.subTest(event=event):
                    status, result = post_webhook(event)
                    self.assertEqual(status, 202)
                    self.assertTrue(result["accepted"])
                    self.assertTrue(result["ignored"])

            # Signed but malformed PR payloads must still fail closed.
            status, result = post_webhook("pull_request")
            self.assertEqual(status, 503)
            self.assertFalse(result["accepted"])

            # An unsigned lifecycle event must not bypass HMAC.
            status, _ = post_webhook("ping", signed=False)
            self.assertEqual(status, 401)

            store_class.return_value.enqueue.assert_not_called()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
