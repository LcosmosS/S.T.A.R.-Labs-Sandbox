"""Pure, fail-closed policy evaluator for Sandbox engineering stewardship.

This module performs no network access and never reads configuration from a PR checkout.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_PATH = Path(__file__).with_name("policy.json")
REVIEW_EVENTS = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}
SUBSTANTIVE_REVIEWS = {"APPROVED", "CHANGES_REQUESTED"}
PERMITTED_ROLES = {"write", "maintain", "admin"}


def validate_policy(policy: Any) -> dict[str, Any]:
    """Validate and compile policy fields before any path is considered safe."""
    if not isinstance(policy, Mapping):
        raise ValueError("stewardship policy must be a JSON object")
    required = {
        "schema_version", "stewards", "approval_free_path_pattern",
        "unknown_paths", "renames", "protected_review_rule",
    }
    if not required.issubset(policy) or policy.get("schema_version") != 1:
        raise ValueError("unsupported or incomplete stewardship policy")
    if policy.get("unknown_paths") != "protected":
        raise ValueError("unknown paths must fail closed")
    stewards = policy.get("stewards")
    if (not isinstance(stewards, list) or not stewards
            or any(not isinstance(item, str) or not item.strip() for item in stewards)
            or len({item.casefold() for item in stewards}) != len(stewards)):
        raise ValueError("policy stewards must be a non-empty list of unique login names")
    pattern = policy.get("approval_free_path_pattern")
    if not isinstance(pattern, str) or not pattern:
        raise ValueError("approval_free_path_pattern must be a non-empty string")
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"approval_free_path_pattern is invalid: {exc}") from exc
    if policy.get("renames") != "inspect_old_and_new_paths":
        raise ValueError("rename policy must inspect both old and new paths")
    if policy.get("protected_review_rule") != "one_non_author_approved_current_head":
        raise ValueError("unsupported protected review rule")
    return dict(policy)


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not load stewardship policy: {exc}") from exc
    return validate_policy(raw)


def is_experiment_path(path: str, policy: dict[str, Any]) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    try:
        validated = validate_policy(policy)
        return re.fullmatch(validated["approval_free_path_pattern"], path) is not None
    except (ValueError, TypeError, re.error):
        return False


def classify_paths(files: Iterable[dict[str, Any]], *, complete: bool,
                   policy: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return (experiment_only, reasons); malformed/incomplete data is protected."""
    try:
        validated = validate_policy(policy)
    except (ValueError, TypeError, re.error) as exc:
        return False, [f"invalid stewardship policy: {exc}"]
    if complete is not True:
        return False, ["changed-file listing is incomplete"]
    try:
        rows = list(files)
    except Exception:
        return False, ["changed-file listing could not be materialized"]
    if not rows:
        return False, ["no changed files could be verified"]

    reasons: list[str] = []
    for item in rows:
        if not isinstance(item, Mapping):
            return False, ["changed-file record is malformed"]
        filename = item.get("filename")
        if not isinstance(filename, str) or not filename:
            return False, ["changed-file record is malformed"]
        paths = [filename]
        previous = item.get("previous_filename")
        if item.get("status") == "renamed" or previous is not None:
            if not isinstance(previous, str) or not previous:
                return False, [f"rename origin missing for {filename}"]
            paths.append(previous)
        for path in paths:
            if not is_experiment_path(path, validated):
                reasons.append(f"protected path: {path}")
    return not reasons, reasons


def _review_order(review: Mapping[str, Any]) -> tuple[float, int] | None:
    submitted = review.get("submitted_at")
    review_id = review.get("id")
    if not isinstance(submitted, str) or not submitted:
        return None
    if isinstance(review_id, bool) or not isinstance(review_id, int) or review_id < 0:
        return None
    try:
        parsed = datetime.fromisoformat(submitted.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        timestamp = parsed.astimezone(timezone.utc).timestamp()
    except (ValueError, OverflowError):
        return None
    return timestamp, review_id


def has_valid_steward_approval(*, author: str, head_sha: str,
                               reviews: Iterable[dict[str, Any]],
                               permissions: dict[str, str],
                               policy: dict[str, Any],
                               reviews_complete: bool = False,
                               permissions_complete: bool = False) -> tuple[bool, str]:
    """Validate approvals; omitted completeness attestations never authorize merging."""
    if reviews_complete is not True or permissions_complete is not True:
        return False, "review or permission API results are incomplete"
    if not isinstance(author, str) or not author or not isinstance(head_sha, str) or not head_sha:
        return False, "PR author or head SHA is malformed"
    if not isinstance(permissions, Mapping):
        return False, "repository permission result is malformed"
    try:
        validated = validate_policy(policy)
        review_rows = list(reviews)
    except Exception as exc:
        return False, f"review or policy data is malformed: {type(exc).__name__}"
    stewards = {str(s).casefold() for s in validated["stewards"]}
    by_steward: dict[str, list[tuple[tuple[float, int], str, Mapping[str, Any]]]] = {
        steward: [] for steward in stewards
    }

    for review in review_rows:
        if not isinstance(review, Mapping):
            return False, "review API returned a malformed record"
        user = review.get("user")
        if not isinstance(user, Mapping):
            return False, "review API returned a record with malformed user data"
        login = user.get("login")
        if not isinstance(login, str) or not login.strip():
            return False, "review API returned a record with missing reviewer identity"
        key = login.casefold()
        if key not in stewards:
            continue
        state = review.get("state")
        if not isinstance(state, str):
            return False, f"review state for authorized steward {login} is malformed"
        state = state.upper()
        # Ordinary comments do not erase an approval; unsupported states fail closed.
        if state == "COMMENTED":
            continue
        if state not in REVIEW_EVENTS:
            return False, f"unsupported review state for authorized steward {login}"
        order = _review_order(review)
        if order is None:
            return False, f"review ordering is incomplete for authorized steward {login}"
        by_steward[key].append((order, state, review))

    latest_event: dict[str, tuple[tuple[float, int], str, Mapping[str, Any]]] = {}
    latest_substantive: dict[str, tuple[tuple[float, int], str, Mapping[str, Any]]] = {}
    for steward, events in by_steward.items():
        events.sort(key=lambda item: item[0])
        # Equal IDs and timestamps with conflicting states cannot be safely ordered.
        for first, second in zip(events, events[1:]):
            if first[0] == second[0] and first[1] != second[1]:
                return False, f"conflicting steward reviews have indistinguishable order for {steward}"
        if events:
            latest_event[steward] = events[-1]
        substantive = [item for item in events if item[1] in SUBSTANTIVE_REVIEWS]
        if substantive:
            latest_substantive[steward] = substantive[-1]

    for steward, (_, state, review) in latest_substantive.items():
        if state == "CHANGES_REQUESTED":
            login = review.get("user", {}).get("login", steward)
            return False, f"{login} has an unresolved change request"

    normalized_permissions = {
        key.casefold(): value for key, value in permissions.items()
        if isinstance(key, str)
    }
    for steward, (event_order, state, review) in latest_event.items():
        login = review.get("user", {}).get("login", "")
        latest_substantive_review = latest_substantive.get(steward)
        # Dismissal revokes that steward's approval but never clears a prior change
        # request: only a later APPROVED/CHANGES_REQUESTED substantive review can.
        if state != "APPROVED" or latest_substantive_review is None:
            continue
        if latest_substantive_review[1] != "APPROVED" or latest_substantive_review[0] != event_order:
            continue
        # An approval must explicitly apply to the exact head currently being evaluated.
        if latest_substantive_review[2].get("commit_id") != head_sha:
            continue
        if login.casefold() == author.casefold():
            continue
        permission = normalized_permissions.get(login.casefold(), normalized_permissions.get(steward))
        if not isinstance(permission, str) or permission.lower() not in PERMITTED_ROLES:
            continue
        return True, f"current-head approval from authorized steward {login}"
    return False, "no eligible non-author steward approval for the current head"


def failed_result(reason: str) -> dict[str, Any]:
    return {
        "conclusion": "failure",
        "classification": "protected",
        "summary": "Stewardship could not be verified; failing closed.",
        "reasons": [reason],
    }


def evaluate(*, author: str, head_sha: str, files: Iterable[dict[str, Any]],
             files_head_sha: str, files_complete: bool,
             reviews: Iterable[dict[str, Any]], reviews_complete: bool,
             permissions: dict[str, str], permissions_complete: bool,
             policy: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        resolved_policy = load_policy() if policy is None else validate_policy(policy)
    except Exception as exc:
        return failed_result(f"policy configuration invalid: {type(exc).__name__}: {exc}")
    try:
        file_rows = list(files)
    except Exception:
        return failed_result("changed-file listing could not be materialized")
    if not isinstance(files_head_sha, str) or not files_head_sha or files_head_sha != head_sha:
        return failed_result("changed-file listing is not bound to the evaluated PR head SHA")

    experiment_only, path_reasons = classify_paths(
        file_rows, complete=files_complete, policy=resolved_policy
    )
    if experiment_only:
        return {
            "conclusion": "success",
            "classification": "experiment-only",
            "summary": "Experiment-only paths; no stewardship approval required.",
            "reasons": [],
        }
    approved, reason = has_valid_steward_approval(
        author=author, head_sha=head_sha, reviews=reviews, permissions=permissions,
        policy=resolved_policy, reviews_complete=reviews_complete,
        permissions_complete=permissions_complete,
    )
    reasons = path_reasons + ([] if approved else [reason])
    return {
        "conclusion": "success" if approved else "failure",
        "classification": "protected",
        "summary": "Engineering stewardship only; this check does not assess scientific validity.",
        "reasons": reasons if not approved else path_reasons + [reason],
    }
