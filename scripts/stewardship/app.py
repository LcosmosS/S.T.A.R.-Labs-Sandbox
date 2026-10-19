"""GitHub App publisher for the path-sensitive Sandbox stewardship check.

Run only from a reviewed/pinned deployment, never from a pull-request checkout.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from evaluate import classify_paths, evaluate, load_policy, validate_policy

API_BASE = "https://api.github.com"
CHECK_NAME = "sandbox-stewardship"
EXPECTED_REPOSITORY = "LcosmosS/S.T.A.R.-Labs-Sandbox"
EXPECTED_REPOSITORY_ID = 1069114334
PAGE_SIZE = 100
MAX_PAGES = 100
MAX_FILES = 3000


class StewardshipError(RuntimeError):
    """An authoritative input or API operation could not be verified."""


class GitHubApi:
    def __init__(self, *, app_id: str, private_key: str,
                 repository_full_name: str = EXPECTED_REPOSITORY,
                 repository_id: int = EXPECTED_REPOSITORY_ID,
                 api_base: str = API_BASE) -> None:
        self.app_id = app_id
        self.private_key = private_key
        self.repository_full_name = repository_full_name
        self.repository_id = int(repository_id)
        self.api_base = api_base.rstrip("/")
        self._app_jwt: tuple[str, float] | None = None

    def app_jwt(self) -> str:
        now = int(time.time())
        if self._app_jwt and self._app_jwt[1] > now + 60:
            return self._app_jwt[0]
        try:
            import jwt
            token = jwt.encode(
                {"iat": now - 30, "exp": now + 8 * 60, "iss": self.app_id},
                self.private_key, algorithm="RS256",
            )
        except Exception as exc:
            raise StewardshipError("could not construct GitHub App JWT") from exc
        self._app_jwt = (token, now + 7 * 60)
        return token

    def request(self, path: str, token: str, *, method: str = "GET",
                body: dict[str, Any] | None = None,
                query: dict[str, Any] | None = None) -> Any:
        url = self.api_base + path
        if query:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(query)
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "sandbox-stewardship-app/1.0",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read(2048).decode("utf-8", "replace")
            raise StewardshipError(
                f"GitHub API {method} {path} returned HTTP {exc.code}: {detail[:500]}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise StewardshipError(f"GitHub API request failed for {path}") from exc

    def installation_token(self, installation_id: int) -> str:
        result = self.request(
            f"/app/installations/{int(installation_id)}/access_tokens",
            self.app_jwt(), method="POST",
            body={
                "repository_ids": [self.repository_id],
                "permissions": {
                    "metadata": "read",
                    "pull_requests": "read",
                    "checks": "write",
                },
            },
        )
        token = result.get("token") if isinstance(result, dict) else None
        if not isinstance(token, str) or not token:
            raise StewardshipError("GitHub did not return an installation token")
        return token

    def list_all(self, path: str, token: str,
                 query: dict[str, Any] | None = None,
                 *, cap: int | None = None) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        query = dict(query or {})
        query.pop("page", None)
        query["per_page"] = PAGE_SIZE
        for page in range(1, MAX_PAGES + 1):
            result = self.request(path, token, query={**query, "page": page})
            if not isinstance(result, list) or any(not isinstance(item, dict) for item in result):
                raise StewardshipError(f"GitHub returned a malformed list for {path}")
            values.extend(result)
            if cap is not None and len(values) > cap:
                raise StewardshipError(f"GitHub result exceeded safe completeness cap for {path}")
            if len(result) < PAGE_SIZE:
                return values
            if cap is not None and len(values) >= cap:
                raise StewardshipError(f"cannot prove the full result is available for {path}")
        raise StewardshipError(f"pagination safety limit reached for {path}")

    def list_check_runs(self, head_sha: str, token: str) -> list[dict[str, Any]]:
        path = f"/repos/{self.repository_full_name}/commits/{head_sha}/check-runs"
        values: list[dict[str, Any]] = []
        for page in range(1, MAX_PAGES + 1):
            result = self.request(
                path, token, query={"check_name": CHECK_NAME, "per_page": PAGE_SIZE, "page": page}
            )
            if not isinstance(result, dict) or not isinstance(result.get("check_runs"), list):
                raise StewardshipError("GitHub returned malformed check-run data")
            runs = result["check_runs"]
            if any(not isinstance(item, dict) for item in runs):
                raise StewardshipError("GitHub returned malformed check-run entries")
            values.extend(runs)
            total = result.get("total_count")
            if not isinstance(total, int):
                raise StewardshipError("GitHub check-run result lacked total_count")
            if len(values) >= total:
                return values
            if len(runs) < PAGE_SIZE:
                raise StewardshipError("GitHub check-run pagination returned fewer rows than total_count")
        raise StewardshipError("check-run pagination safety limit reached")

    def list_open_pulls(self, token: str) -> list[dict[str, Any]]:
        return self.list_all(
            f"/repos/{self.repository_full_name}/pulls", token,
            {"state": "open", "sort": "updated", "direction": "desc"},
        )

    def get_pull(self, number: int, token: str) -> dict[str, Any]:
        result = self.request(f"/repos/{self.repository_full_name}/pulls/{int(number)}", token)
        if not isinstance(result, dict):
            raise StewardshipError(f"invalid PR metadata for #{number}")
        return result

    def list_files(self, number: int, token: str) -> list[dict[str, Any]]:
        return self.list_all(
            f"/repos/{self.repository_full_name}/pulls/{int(number)}/files",
            token, cap=MAX_FILES,
        )

    def list_reviews(self, number: int, token: str) -> list[dict[str, Any]]:
        return self.list_all(
            f"/repos/{self.repository_full_name}/pulls/{int(number)}/reviews", token,
        )

    def get_permission(self, login: str, token: str) -> str:
        safe_login = urllib.parse.quote(login, safe="")
        result = self.request(
            f"/repos/{self.repository_full_name}/collaborators/{safe_login}/permission",
            token,
        )
        permission = result.get("permission") if isinstance(result, dict) else None
        if not isinstance(permission, str):
            raise StewardshipError(f"could not verify repository permission for {login}")
        return permission.lower()

    def publish_check(self, *, head_sha: str, conclusion: str, summary: str,
                      details_url: str, token: str) -> None:
        checks_path = f"/repos/{self.repository_full_name}/check-runs"
        existing = self.list_check_runs(head_sha, token)
        own_run = next(
            (item for item in reversed(existing)
             if item.get("name") == CHECK_NAME
             and item.get("head_sha") == head_sha
             and isinstance(item.get("app"), dict)
             and str(item["app"].get("id")) == str(self.app_id)),
            None,
        )
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        body = {
            "name": CHECK_NAME,
            "head_sha": head_sha,
            "status": "completed",
            "conclusion": conclusion,
            "started_at": now,
            "completed_at": now,
            "details_url": details_url,
            "output": {
                "title": "Engineering stewardship evaluated",
                "summary": summary[:60000],
            },
        }
        if own_run and own_run.get("status") in {"queued", "in_progress"}:
            self.request(
                f"/repos/{self.repository_full_name}/check-runs/{own_run['id']}",
                token, method="PATCH", body=body,
            )
        else:
            self.request(checks_path, token, method="POST", body=body)


class DeliveryStore:
    """Durable SQLite webhook queue with deduplication, retry backoff, and leases."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS deliveries ("
                "delivery_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated REAL NOT NULL, "
                "event_name TEXT, payload TEXT, attempts INTEGER NOT NULL DEFAULT 0, "
                "next_attempt REAL NOT NULL DEFAULT 0)"
            )
            # Backward-compatible migration if the table exists from an earlier build.
            columns = {row[1] for row in db.execute("PRAGMA table_info(deliveries)")}
            for name, declaration in (
                ("event_name", "TEXT"), ("payload", "TEXT"),
                ("attempts", "INTEGER NOT NULL DEFAULT 0"),
                ("next_attempt", "REAL NOT NULL DEFAULT 0"),
            ):
                if name not in columns:
                    db.execute(f"ALTER TABLE deliveries ADD COLUMN {name} {declaration}")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def enqueue(self, delivery_id: str, event_name: str, payload: dict[str, Any]) -> bool:
        now = time.time()
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state, updated FROM deliveries WHERE delivery_id=?",
                (delivery_id,),
            ).fetchone()
            if row and row[0] == "done":
                return False
            if row and row[0] in {"queued", "processing"} and (
                row[0] == "queued" or now - row[1] < 900
            ):
                return False
            db.execute(
                "INSERT INTO deliveries(delivery_id,state,updated,event_name,payload,attempts,next_attempt) "
                "VALUES(?,?,?,?,?,0,0) ON CONFLICT(delivery_id) DO UPDATE SET "
                "state='queued',updated=excluded.updated,event_name=excluded.event_name,"
                "payload=excluded.payload,attempts=0,next_attempt=0",
                (delivery_id, "queued", now, event_name, encoded),
            )
            return True

    def take_next(self) -> dict[str, Any] | None:
        now = time.time()
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT delivery_id,event_name,payload,attempts FROM deliveries "
                "WHERE state='queued' AND next_attempt<=? ORDER BY updated LIMIT 1",
                (now,),
            ).fetchone()
            if not row:
                return None
            db.execute(
                "UPDATE deliveries SET state='processing',updated=?,attempts=attempts+1 "
                "WHERE delivery_id=? AND state='queued'",
                (now, row[0]),
            )
            return {"delivery_id": row[0], "event_name": row[1],
                    "payload": json.loads(row[2]), "attempts": row[3] + 1}

    def finish(self, delivery_id: str, success: bool) -> None:
        now = time.time()
        with self._lock, self._connect() as db:
            if success:
                db.execute(
                    "UPDATE deliveries SET state='done',updated=? WHERE delivery_id=?",
                    (now, delivery_id),
                )
                return
            row = db.execute(
                "SELECT attempts FROM deliveries WHERE delivery_id=?", (delivery_id,)
            ).fetchone()
            attempts = int(row[0]) if row else 1
            if attempts >= 8:
                db.execute(
                    "UPDATE deliveries SET state='failed',updated=? WHERE delivery_id=?",
                    (now, delivery_id),
                )
            else:
                delay = min(2 ** attempts, 300)
                db.execute(
                    "UPDATE deliveries SET state='queued',updated=?,next_attempt=? WHERE delivery_id=?",
                    (now, now + delay, delivery_id),
                )


class StewardshipService:
    def __init__(self, *, api: GitHubApi, policy: dict[str, Any] | None = None,
                 repository_id: int = EXPECTED_REPOSITORY_ID,
                 repository_full_name: str = EXPECTED_REPOSITORY,
                 installation_id: int | None = None,
                 delivery_store: DeliveryStore | None = None) -> None:
        self.api = api
        self.policy_error: str | None = None
        try:
            self.policy = load_policy() if policy is None else validate_policy(policy)
        except Exception as exc:
            # Keep the service available to publish explicit failure checks rather than
            # crashing before any PR can receive a result.
            self.policy = None
            self.policy_error = f"{type(exc).__name__}: {exc}"
        self.repository_id = int(repository_id)
        self.repository_full_name = repository_full_name.casefold()
        self.installation_id = int(installation_id) if installation_id else None
        self.delivery_store = delivery_store
        # One service process serializes reconciliation, webhook processing and publication.
        self._reconcile_lock = threading.Lock()

    def _check_pr(self, pr: dict[str, Any], token: str) -> tuple[str, str, str]:
        number = int(pr["number"])
        head_data = pr.get("head")
        base_data = pr.get("base")
        user_data = pr.get("user")
        if not isinstance(head_data, dict) or not isinstance(base_data, dict) or not isinstance(user_data, dict):
            raise StewardshipError(f"PR #{number} metadata has malformed head, base, or author data")
        head = head_data.get("sha")
        base = base_data.get("sha")
        author = user_data.get("login")
        if not isinstance(head, str) or not head or not isinstance(base, str) or not base:
            raise StewardshipError(f"PR #{number} metadata lacks head or base SHA")
        if not isinstance(author, str) or not author:
            raise StewardshipError(f"PR #{number} metadata lacks author")

        if self.policy_error is not None or self.policy is None:
            confirm = self.api.get_pull(number, token)
            if (not isinstance(confirm, dict)
                    or not isinstance(confirm.get("head"), dict)
                    or not isinstance(confirm.get("base"), dict)
                    or confirm["head"].get("sha") != head
                    or confirm["base"].get("sha") != base):
                raise StewardshipError(f"PR #{number} changed while policy failure was being published")
            return head, "failure", (
                f"PR #{number}: stewardship policy configuration invalid; fail closed. "
                f"{self.policy_error or 'policy is unavailable'}"
            )

        # Changed files are PR-scoped mutable data rather than SHA-addressed.
        # Capture head/base first, fetch all other inputs, then verify the snapshots.
        files_head_sha = head
        files_base_sha = base
        files = self.api.list_files(number, token)
        experiment_only, _ = classify_paths(files, complete=True, policy=self.policy)
        reviews: list[dict[str, Any]] = []
        permissions: dict[str, str] = {}
        if not experiment_only:
            reviews = self.api.list_reviews(number, token)
            permissions = {
                steward: self.api.get_permission(steward, token)
                for steward in self.policy["stewards"]
            }

        confirm = self.api.get_pull(number, token)
        if (not isinstance(confirm, dict)
                or not isinstance(confirm.get("head"), dict)
                or not isinstance(confirm.get("base"), dict)):
            raise StewardshipError(f"PR #{number} metadata became malformed during evaluation")
        if confirm.get("state") != "open":
            raise StewardshipError(f"PR #{number} is no longer open; retry reconciliation")
        if confirm["head"].get("sha") != files_head_sha:
            raise StewardshipError(f"PR #{number} head changed while collecting stewardship inputs")
        if confirm["base"].get("sha") != files_base_sha:
            raise StewardshipError(f"PR #{number} base changed while collecting changed-file inputs")

        if experiment_only:
            return head, "success", (
                f"PR #{number}: experiment-only paths; no stewardship approval required. "
                "This result does not assess scientific validity."
            )

        result = evaluate(
            author=author, head_sha=head, files=files, files_head_sha=files_head_sha,
            files_complete=True, reviews=reviews, reviews_complete=True,
            permissions=permissions, permissions_complete=True, policy=self.policy,
        )
        message = [f"PR #{number}: {result['summary']}"]
        message.extend(f"- {reason}" for reason in result.get("reasons", []))
        return head, result["conclusion"], "\n".join(message)

    def _reconcile_locked(self, installation_id: int | None = None) -> dict[str, Any]:
        install = int(installation_id or self.installation_id or 0)
        if not install:
            raise StewardshipError("installation ID is not configured")
        token = self.api.installation_token(install)
        first_inventory = self.api.list_open_pulls(token)
        second_inventory = self.api.list_open_pulls(token)

        def inventory_signature(items: list[dict[str, Any]]) -> tuple[tuple[int, str, str], ...]:
            signature = []
            for item in items:
                number = item.get("number")
                head_sha = item.get("head", {}).get("sha")
                base_sha = item.get("base", {}).get("sha", "")
                if not isinstance(number, int) or not isinstance(head_sha, str) or not head_sha:
                    raise StewardshipError("open-PR inventory contains incomplete metadata")
                signature.append((number, head_sha, str(base_sha or "")))
            return tuple(sorted(signature))

        first_signature = inventory_signature(first_inventory)
        second_signature = inventory_signature(second_inventory)
        seen_inventories = [first_inventory, second_inventory]
        inventory_unstable = first_signature != second_signature
        listed_by_number: dict[int, dict[str, Any]] = {}
        for item in first_inventory + second_inventory:
            listed_by_number[item["number"]] = item
        by_sha: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
        evaluation_errors: dict[str, list[str]] = defaultdict(list)
        if inventory_unstable:
            for item in first_inventory + second_inventory:
                sha = item.get("head", {}).get("sha")
                if isinstance(sha, str) and sha:
                    evaluation_errors[sha].append(
                        "open-PR inventory changed during reconciliation; retry required"
                    )
        for number, listed in {item["number"]: item for item in second_inventory}.items():
            fallback_sha = listed.get("head", {}).get("sha")
            try:
                pr = self.api.get_pull(number, token)
                if pr.get("state") != "open":
                    continue
                head, conclusion, summary = self._check_pr(pr, token)
                confirm = self.api.get_pull(number, token)
                if confirm.get("state") != "open":
                    continue
                if confirm.get("head", {}).get("sha") != head:
                    raise StewardshipError(f"PR #{number} head changed during evaluation")
                by_sha[head].append((number, conclusion, summary))
            except Exception as exc:
                if isinstance(fallback_sha, str) and fallback_sha:
                    evaluation_errors[fallback_sha].append(
                        f"PR #{number}: unable to verify stewardship; fail closed "
                        f"({type(exc).__name__}: {exc})"
                    )

        # Re-scan after evaluating all PRs to detect openings, closures, base updates,
        # or head pushes that raced pagination/evaluation.
        try:
            final_inventory = self.api.list_open_pulls(token)
            final_signature = inventory_signature(final_inventory)
            seen_inventories.append(final_inventory)
            listed_by_number.update({item["number"]: item for item in final_inventory})
            if final_signature != second_signature:
                inventory_unstable = True
        except Exception as exc:
            final_inventory = []
            inventory_unstable = True
            for sha in set(by_sha) | set(evaluation_errors):
                evaluation_errors[sha].append(
                    f"could not verify final open-PR inventory ({type(exc).__name__})"
                )
        if inventory_unstable:
            for inventory in seen_inventories:
                for item in inventory:
                    sha = item.get("head", {}).get("sha")
                    if isinstance(sha, str) and sha:
                        note = "open-PR inventory changed or could not be verified; retry required"
                        if note not in evaluation_errors[sha]:
                            evaluation_errors[sha].append(note)

        # A check run is commit-SHA scoped. All open PRs sharing a SHA must pass.
        groups = set(by_sha) | set(evaluation_errors)
        published: list[dict[str, Any]] = []
        for sha in sorted(groups):
            rows = by_sha.get(sha, [])
            errors = evaluation_errors.get(sha, [])
            # Check Runs are SHA-scoped, not PR-scoped. Distinct PRs sharing a
            # SHA can have different base-relative file sets, so always fail closed.
            shared_head = len(rows) > 1
            success = len(rows) == 1 and not errors and rows[0][1] == "success"
            lines = [
                f"Repository: {self.repository_full_name}",
                "Decision: " + ("PASS" if success else "FAIL"),
                "Engineering stewardship only; not scientific review.",
            ]
            if shared_head:
                lines.append(
                    "FAIL CLOSED: multiple open PRs share this head SHA; a commit-scoped "
                    "Check Run cannot distinguish their base-relative changed-file sets."
                )
            lines.extend(row[2] for row in rows)
            lines.extend("- " + error for error in errors)
            pr_number = rows[0][0] if rows else next(
                (n for n, item in listed_by_number.items()
                 if item.get("head", {}).get("sha") == sha), 0
            )
            url = f"https://github.com/{self.repository_full_name}/pull/{pr_number}" if pr_number else (
                f"https://github.com/{self.repository_full_name}"
            )
            self.api.publish_check(
                head_sha=sha, conclusion="success" if success else "failure",
                summary="\n\n".join(lines), details_url=url, token=token,
            )
            published.append({
                "head_sha": sha, "conclusion": "success" if success else "failure",
                "pull_requests": [row[0] for row in rows], "errors": errors,
            })
        return {"evaluated_open_prs": len(listed_by_number), "published_checks": published}

    def reconcile(self, installation_id: int | None = None) -> dict[str, Any]:
        # One process serializes evaluation/publication to reduce event races.
        with self._reconcile_lock:
            return self._reconcile_locked(installation_id)

    def validate_webhook(self, event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        repo = payload.get("repository")
        if not isinstance(repo, dict):
            raise StewardshipError("webhook payload has no repository metadata")
        if int(repo.get("id", -1)) != self.repository_id:
            raise StewardshipError("webhook repository ID does not match configured Sandbox")
        if str(repo.get("full_name", "")).casefold() != self.repository_full_name:
            raise StewardshipError("webhook repository name does not match configured Sandbox")
        installation = payload.get("installation")
        if not isinstance(installation, dict) or not isinstance(installation.get("id"), int):
            raise StewardshipError("webhook payload has no installation ID")
        if self.installation_id and installation["id"] != self.installation_id:
            raise StewardshipError("webhook installation ID is not allowlisted")
        if event_name == "pull_request":
            supported = {"opened", "reopened", "synchronize", "edited", "ready_for_review", "closed"}
            relevant = payload.get("action") in supported
        elif event_name == "pull_request_review":
            relevant = payload.get("action") in {"submitted", "edited", "dismissed"}
        else:
            relevant = False
        if not relevant:
            return {"ignored": True, "reason": "event type or action is not relevant"}
        return {"installation_id": installation["id"], "accepted": True}

    def process_queued_event(self, event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        validation = self.validate_webhook(event_name, payload)
        if validation.get("ignored"):
            return validation
        installation_id = validation["installation_id"]
        try:
            return self.reconcile(installation_id)
        except Exception:
            pr = payload.get("pull_request")
            sha = pr.get("head", {}).get("sha") if isinstance(pr, dict) else None
            if isinstance(sha, str) and sha:
                try:
                    token = self.api.installation_token(installation_id)
                    self.api.publish_check(
                        head_sha=sha, conclusion="failure",
                        summary="Unable to verify current open-PR/review state. Stewardship fails closed; retry reconciliation.",
                        details_url=f"https://github.com/{self.repository_full_name}/pulls",
                        token=token,
                    )
                except Exception:
                    pass
            raise

    def handle_webhook(self, event_name: str, delivery_id: str,
                       payload: dict[str, Any]) -> dict[str, Any]:
        # Convenience entry point for direct callers/tests; production requests
        # validate and persist the event before returning, then use the queue worker.
        return self.process_queued_event(event_name, payload)


def _read_private_key() -> str:
    path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH")
    if path:
        return Path(path).read_text(encoding="utf-8")
    value = os.environ.get("GITHUB_APP_PRIVATE_KEY")
    if value:
        return value.replace("\\n", "\n")
    raise RuntimeError("set GITHUB_APP_PRIVATE_KEY_PATH or GITHUB_APP_PRIVATE_KEY")


def create_server() -> ThreadingHTTPServer:
    app_id = os.environ["GITHUB_APP_ID"]
    repository_id = int(os.environ.get("STEWARDSHIP_REPOSITORY_ID", EXPECTED_REPOSITORY_ID))
    repository = os.environ.get("STEWARDSHIP_REPOSITORY", EXPECTED_REPOSITORY)
    installation_id = int(os.environ["GITHUB_APP_INSTALLATION_ID"])
    webhook_secret = os.environ["GITHUB_WEBHOOK_SECRET"].encode("utf-8")
    reconciliation_token = os.environ["STEWARDSHIP_RECONCILIATION_TOKEN"].encode("utf-8")
    db_path = os.environ.get("STEWARDSHIP_DELIVERY_DB", "stewardship-deliveries.sqlite3")
    if not app_id.isdigit() or installation_id <= 0:
        raise RuntimeError("GITHUB_APP_ID and GITHUB_APP_INSTALLATION_ID must be positive numeric IDs")
    if len(webhook_secret) < 32:
        raise RuntimeError("GITHUB_WEBHOOK_SECRET must contain at least 32 bytes of high-entropy secret material")
    if len(reconciliation_token) < 32:
        raise RuntimeError("STEWARDSHIP_RECONCILIATION_TOKEN must contain at least 32 bytes of high-entropy secret material")
    if repository_id != EXPECTED_REPOSITORY_ID or repository.casefold() != EXPECTED_REPOSITORY.casefold():
        raise RuntimeError("this build is pinned to LcosmosS/S.T.A.R.-Labs-Sandbox")
    api = GitHubApi(app_id=app_id, private_key=_read_private_key(),
                    repository_full_name=repository, repository_id=repository_id)
    delivery_store = DeliveryStore(db_path)
    service = StewardshipService(
        api=api, repository_id=repository_id, repository_full_name=repository,
        installation_id=installation_id, delivery_store=delivery_store,
    )

    class Handler(BaseHTTPRequestHandler):
        server_version = "SandboxStewardship/1.0"

        def _send(self, status: int, value: dict[str, Any]) -> None:
            data = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/healthz":
                self._send(200, {"status": "ok", "check": CHECK_NAME})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0") or 0)
            except ValueError:
                self._send(400, {"error": "invalid content length"})
                return
            if length < 0 or length > 1_000_000:
                self._send(413, {"error": "request body too large"})
                return
            raw = self.rfile.read(length)
            if self.path == "/webhook":
                signature = self.headers.get("X-Hub-Signature-256", "")
                expected = "sha256=" + hmac.new(webhook_secret, raw, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(signature, expected):
                    self._send(401, {"error": "invalid webhook signature"})
                    return
                delivery_id = self.headers.get("X-GitHub-Delivery", "")
                event_name = self.headers.get("X-GitHub-Event", "")
                if not delivery_id or not event_name:
                    self._send(400, {"error": "missing GitHub delivery/event headers"})
                    return
                try:
                    payload = json.loads(raw.decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("payload is not an object")
                    validation = service.validate_webhook(event_name, payload)
                    if validation.get("ignored"):
                        self._send(202, {"accepted": True, **validation})
                        return
                    queued = delivery_store.enqueue(delivery_id, event_name, payload)
                    self._send(202, {"accepted": True, "queued": queued, "duplicate": not queued})
                except Exception as exc:
                    self._send(503, {"accepted": False, "error": str(exc)[:500]})
                return
            if self.path == "/reconcile":
                supplied = self.headers.get("X-Reconciliation-Token", "").encode("utf-8")
                if not reconciliation_token or not hmac.compare_digest(supplied, reconciliation_token):
                    self._send(401, {"error": "unauthorized"})
                    return
                try:
                    result = service.reconcile(installation_id)
                    self._send(200, result)
                except Exception as exc:
                    self._send(503, {"error": str(exc)[:500]})
                return
            self._send(404, {"error": "not found"})

        def log_message(self, fmt: str, *args: Any) -> None:
            print("%s - %s" % (self.client_address[0], fmt % args), flush=True)

    def queue_worker() -> None:
        while True:
            item = delivery_store.take_next()
            if item is None:
                time.sleep(0.5)
                continue
            try:
                service.process_queued_event(item["event_name"], item["payload"])
                delivery_store.finish(item["delivery_id"], True)
            except Exception as exc:
                print(
                    f"Stewardship delivery {item['delivery_id']} failed on attempt "
                    f"{item['attempts']}: {type(exc).__name__}; will retry if budget remains",
                    flush=True,
                )
                delivery_store.finish(item["delivery_id"], False)

    threading.Thread(target=queue_worker, name="stewardship-queue", daemon=True).start()

    try:
        reconcile_interval = max(60, int(os.environ.get("STEWARDSHIP_RECONCILE_INTERVAL_SECONDS", "300")))
    except ValueError as exc:
        raise RuntimeError("STEWARDSHIP_RECONCILE_INTERVAL_SECONDS must be an integer >= 60") from exc

    def periodic_reconciler() -> None:
        # Permission changes need not emit a PR/review webhook. Poll open PRs so
        # losing steward access invalidates previously successful protected checks.
        while True:
            time.sleep(reconcile_interval)
            try:
                service.reconcile(installation_id)
            except Exception as exc:
                print(
                    f"Periodic stewardship reconciliation failed: {type(exc).__name__}; next retry scheduled",
                    flush=True,
                )

    threading.Thread(target=periodic_reconciler, name="stewardship-periodic-reconcile", daemon=True).start()
    return ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler)


if __name__ == "__main__":
    create_server().serve_forever()
