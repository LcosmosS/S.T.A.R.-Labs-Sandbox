"""Offline allowlist and run preparation for SciServer MCP v0.2.

This module has NO network, authentication, or CasJobs submission operations.
The existing v0.1.1 server is deliberately not modified by the policy PR.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from pathlib import Path, PurePosixPath

from . import receipts

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "integrations/sciserver/query_catalog.json"
CATALOG_SCHEMA = "star-sciserver-query-catalog-v0.2"
PLAN_SCHEMA = "star-sciserver-run-plan-v0.2"
QUERY_IDS = frozenset({"DR18-CANARY-10", "DR18-DETERMINISTIC-200K"})
DESTINATION_RE = re.compile(r"^STAR_SCISERVER_(C10|D200K)_[A-F0-9]{16}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HEX_RUN_RE = re.compile(r"^[0-9a-f]{32}$")


class PolicyViolation(ValueError):
    """Fail-closed policy rejection; no remote request has been made."""


def _repo_relative_file(relative: str, repo_root: Path) -> Path:
    if not isinstance(relative, str) or "\\" in relative:
        raise PolicyViolation("SQL source must be a repository-relative POSIX path")
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or not parsed.parts or any(
        part in ("", ".", "..") for part in parsed.parts
    ):
        raise PolicyViolation("Unsafe SQL source path")
    if not relative.startswith("verification/datasets/casjobs/"):
        raise PolicyViolation("SQL outside the approved CasJobs directory")
    root = Path(os.path.abspath(repo_root))
    cursor = root
    for part in parsed.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise PolicyViolation("Symlinks are forbidden in approved SQL paths")
    return cursor


def _file_bytes(path: Path) -> bytes:
    if not hasattr(os, "O_NOFOLLOW"):
        raise PolicyViolation("Secure SQL source reading requires POSIX/WSL2")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
            raise PolicyViolation("SQL source must be a small regular file")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            return handle.read(65537)
    finally:
        if fd >= 0:
            os.close(fd)


def load_catalog(
    catalog_path: Path = CATALOG_PATH, repo_root: Path = REPO_ROOT
) -> dict:
    """Validate the entire catalog and each SQL byte digest before use."""
    catalog_path = Path(catalog_path)
    if catalog_path.is_symlink():
        raise PolicyViolation("Catalog symlinks are not allowed")
    raw = _file_bytes(catalog_path)
    try:
        catalog = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise PolicyViolation("Invalid catalog JSON") from exc
    if not isinstance(catalog, dict) or set(catalog) != {
        "schema_version", "queries", "remote_submission_enabled"
    } or catalog["schema_version"] != CATALOG_SCHEMA:
        raise PolicyViolation("Unexpected query catalog schema")
    if catalog["remote_submission_enabled"] is not False:
        raise PolicyViolation("Remote submissions must remain disabled")
    rows = catalog["queries"]
    if not isinstance(rows, list) or len(rows) != 2:
        raise PolicyViolation("Catalog must contain exactly two approved definitions")
    by_id = {}
    for row in rows:
        required = {
            "query_id", "dataset_id", "path", "context", "mode",
            "approved_sha256", "expected_columns", "max_rows",
            "preparation_enabled", "submission_enabled",
            "historical_replacement"
        }
        if not isinstance(row, dict) or set(row) != required:
            raise PolicyViolation("Unexpected query entry fields")
        ident = row["query_id"]
        if ident not in QUERY_IDS or ident in by_id:
            raise PolicyViolation("Unknown or duplicate query ID")
        if row["dataset_id"] != "DATA-SDSS18-200K" or row["context"] != "DR18":
            raise PolicyViolation("Dataset/context differs from frozen DR18 policy")
        canary = ident == "DR18-CANARY-10"
        if row["mode"] != ("canary" if canary else "deterministic-probe"):
            raise PolicyViolation("Query mode mismatch")
        if type(row["expected_columns"]) is not int or row["expected_columns"] != 18:
            raise PolicyViolation("Expected schema drift")
        if type(row["max_rows"]) is not int or row["max_rows"] != (10 if canary else 200000):
            raise PolicyViolation("Expected row limit drift")
        if row["preparation_enabled"] is not canary:
            raise PolicyViolation("Only the TOP 10 canary may be prepared in PR 1")
        if row["submission_enabled"] is not False or row["historical_replacement"] is not False:
            raise PolicyViolation("Remote submission or historical replacement enabled")
        if not isinstance(row["approved_sha256"], str) or not SHA256_RE.fullmatch(row["approved_sha256"]):
            raise PolicyViolation("Malformed SQL SHA-256")
        path = _repo_relative_file(row["path"], repo_root)
        if path.name != ("STAR_DR18_10_canary.sql" if canary
                         else "DATA-SDSS18-200K_deterministic_probe.sql"):
            raise PolicyViolation("Unexpected SQL filename")
        sql_bytes = _file_bytes(path)
        if hashlib.sha256(sql_bytes).hexdigest() != row["approved_sha256"]:
            raise PolicyViolation(f"SQL hash drift: {ident}")
        try:
            code = "\n".join(line.split("--", 1)[0] for line in
                             sql_bytes.decode("utf-8").splitlines()).upper()
        except UnicodeDecodeError as exc:
            raise PolicyViolation("SQL is not UTF-8") from exc
        if (f"SELECT TOP {row['max_rows']}" not in code
                or "ORDER BY" not in code
                or "FROM PHOTOOBJ AS P" not in code
                or "JOIN SPECOBJ AS S" not in code
                or any(re.search(r"\b" + word + r"\b", code) for word in
                       ("INTO", "DROP", "DELETE", "UPDATE", "ALTER", "INSERT"))
                or code.count(";") != 1):
            raise PolicyViolation("Approved SQL violates read-only query shape")
        by_id[ident] = dict(row)
    if set(by_id) != QUERY_IDS:
        raise PolicyViolation("Approved query IDs incomplete")
    return {"queries": by_id, "catalog_sha256": hashlib.sha256(raw).hexdigest()}


def list_approved_queries(
    catalog_path: Path = CATALOG_PATH, repo_root: Path = REPO_ROOT
) -> list[dict]:
    """Report only locked metadata; never return executable arbitrary SQL."""
    catalog = load_catalog(catalog_path, repo_root)
    return [dict(catalog["queries"][key]) for key in sorted(QUERY_IDS)]


def validate_destination(run_id: str, mode: str, destination: str) -> None:
    if not isinstance(run_id, str) or not HEX_RUN_RE.fullmatch(run_id):
        raise PolicyViolation("Invalid generated run ID")
    role = {"canary": "C10", "deterministic-probe": "D200K"}.get(mode)
    if role is None or not isinstance(destination, str):
        raise PolicyViolation("Invalid destination request")
    expected = f"STAR_SCISERVER_{role}_{run_id[:16].upper()}"
    if not DESTINATION_RE.fullmatch(destination) or destination != expected:
        raise PolicyViolation("Destination must match the generated run ID")


def require_submission_authorization(*_args, **_kwargs) -> None:
    """Deliberate fail-closed boundary; no execution API exists in v0.2 PR 1."""
    raise PermissionError(
        "SciServer async submissions are disabled; a separately reviewed "
        "operator approval implementation and live canary PR are required"
    )


def prepare_casjobs_run(
    query_id: str, *,
    catalog_path: Path = CATALOG_PATH,
    repo_root: Path = REPO_ROOT,
    state_root: Path = receipts.DEFAULT_STATE_ROOT,
) -> dict:
    """Create a local immutable plan; performs no network requests or MyDB writes."""
    catalog = load_catalog(catalog_path, repo_root)
    row = catalog["queries"].get(query_id)
    if row is None:
        raise PolicyViolation("Query ID not in the pinned allowlist")
    if not row["preparation_enabled"]:
        raise PolicyViolation("The 200k probe is blocked until canary review")
    run_id = secrets.token_hex(16)
    destination = f"STAR_SCISERVER_C10_{run_id[:16].upper()}"
    validate_destination(run_id, row["mode"], destination)
    plan = {
        "schema_version": PLAN_SCHEMA,
        "run_id": run_id,
        "query_id": query_id,
        "dataset_id": row["dataset_id"],
        "context": row["context"],
        "mode": row["mode"],
        "source_sql_path": row["path"],
        "source_sql_sha256": row["approved_sha256"],
        "catalog_sha256": catalog["catalog_sha256"],
        "mydb_destination": destination,
        "expected_columns": row["expected_columns"],
        "max_rows": row["max_rows"],
        "remote_submission_enabled": False,
        "operator_approval_recorded": False,
        "automatic_registry_promotion": False,
        "historical_dataset_replacement": False,
    }
    entry = receipts.append_event(
        state_root, run_id, "planned", plan, expected_previous_sha256=None
    )
    return {"plan": plan, "receipt_sha256": entry["record_sha256"]}
