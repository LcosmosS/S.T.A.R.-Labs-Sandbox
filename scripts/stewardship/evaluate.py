"""Pure, fail-closed policy evaluator for Sandbox engineering stewardship.

This module has no GitHub credentials and never reads policy from a PR checkout.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

POLICY_PATH = Path(__file__).with_name("policy.json")


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "stewards", "approval_free_path_pattern",
                "unknown_paths", "renames", "protected_review_rule"}
    if not required.issubset(policy) or policy["schema_version"] != 1:
        raise ValueError("unsupported or incomplete stewardship policy")
    if policy["unknown_paths"] != "protected":
        raise ValueError("unknown paths must fail closed")
    return policy


def is_experiment_path(path: str, policy: dict[str, Any]) -> bool:
    if not path or path.startswith("/") or "\\" in path:
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return re.fullmatch(policy["approval_free_path_pattern"], path) is not None


def classify_paths(files: Iterable[dict[str, Any]], *, complete: bool,
                   policy: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return (experiment_only, reasons); incomplete API results are protected."""
    if not complete:
        return False, ["changed-file listing is incomplete"]
    rows = list(files)
    if not rows:
        return False, ["no changed files could be verified"]
    reasons: list[str] = []
    for item in rows:
        filename = item.get("filename")
        if not isinstance(filename, str) or not filename:
            return False, ["changed-file record is malformed"]
        paths = [filename]
        if item.get("status") == "renamed" or item.get("previous_filename"):
            old = item.get("previous_filename")
            if not isinstance(old, str) or not old:
                return False, [f"rename origin missing for {filename}"]
            paths.append(old)
        for path in paths:
            if not is_experiment_path(path, policy):
                reasons.append(f"protected path: {path}")
    return not reasons, reasons


def has_valid_steward_approval(*, author: str, head_sha: str,
                               reviews: Iterable[dict[str, Any]],
                               permissions: dict[str, str],
                               policy: dict[str, Any],
                               reviews_complete: bool = True,
                               permissions_complete: bool = True) -> tuple[bool, str]:
    """Validate effective reviews against current head and live collaborator access."""
    if not reviews_complete or not permissions_complete:
        return False, "review or permission API results are incomplete"
    stewards = {str(s).casefold() for s in policy["stewards"]}
    author_key = author.casefold()
    latest: dict[str, dict[str, Any]] = {}
    substantive = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}
    for review in reviews:
        login = review.get("user", {}).get("login")
        if not isinstance(login, str) or login.casefold() not in stewards:
            continue
        state = str(review.get("state", "")).upper()
        # Ordinary comments are not substantive and must not erase an approval.
        if state not in substantive:
            continue
        key = login.casefold()
        submitted = review.get("submitted_at") or ""
        previous = latest.get(key)
        if previous is None or submitted >= (previous.get("submitted_at") or ""):
            latest[key] = review

    for review in latest.values():
        if str(review.get("state", "")).upper() == "CHANGES_REQUESTED":
            return False, f"{review.get('user', {}).get('login')} has an unresolved change request"
    for steward, review in latest.items():
        login = review.get("user", {}).get("login", "")
        if login.casefold() == author_key:
            continue
        if str(review.get("state", "")).upper() != "APPROVED":
            continue
        if review.get("commit_id") != head_sha:
            continue
        if str(permissions.get(login, permissions.get(steward, "none"))).lower() not in {"write", "maintain", "admin"}:
            continue
        return True, f"current-head approval from authorized steward {login}"
    return False, "no eligible non-author steward approval for the current head"


def evaluate(*, author: str, head_sha: str, files: Iterable[dict[str, Any]],
             files_complete: bool, reviews: Iterable[dict[str, Any]],
             reviews_complete: bool, permissions: dict[str, str],
             permissions_complete: bool, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    experiment_only, path_reasons = classify_paths(files, complete=files_complete, policy=policy)
    if experiment_only:
        return {"conclusion": "success", "classification": "experiment-only",
                "summary": "Experiment-only paths; no stewardship approval required.",
                "reasons": []}
    approved, reason = has_valid_steward_approval(
        author=author, head_sha=head_sha, reviews=reviews, permissions=permissions,
        policy=policy, reviews_complete=reviews_complete,
        permissions_complete=permissions_complete)
    reasons = path_reasons + ([] if approved else [reason])
    return {"conclusion": "success" if approved else "failure",
            "classification": "protected",
            "summary": "Engineering stewardship only; this check does not assess scientific validity.",
            "reasons": reasons if not approved else path_reasons + [reason]}
