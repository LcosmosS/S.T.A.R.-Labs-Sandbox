"""Write-once, hash-chained local provenance events for SciServer MCP v0.2.

These records are integrity-evident, NOT cryptographically authenticated
operator approvals. No network/database actions are implemented here.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE_ROOT = Path.home() / ".local/state/star-sciserver/runs"
SCHEMA = "star-sciserver-event-v0.2"
RUN_ID_RE = re.compile(r"^[a-f0-9]{32}$")
EVENT_NAME_RE = re.compile(r"^event_([0-9]{4})\.json$")
MAX_EVENT_BYTES = 1024 * 1024

# Future transitions are specified for negative/replay tests, not exposed
# as MCP submission or approval tools by this PR.
TRANSITIONS = {
    None: frozenset({"planned"}),
    "planned": frozenset({"operator_approved", "aborted"}),
    "operator_approved": frozenset({"submission_intent", "aborted"}),
    "submission_intent": frozenset({"job_accepted", "submission_ambiguous", "aborted"}),
    "submission_ambiguous": frozenset({"reconciled", "aborted"}),
    "reconciled": frozenset({"job_accepted", "aborted"}),
    "job_accepted": frozenset({"job_finished", "aborted"}),
    "job_finished": frozenset({"exported", "aborted"}),
    "exported": frozenset({"verified", "aborted"}),
    "verified": frozenset(),
    "aborted": frozenset(),
}


class ReceiptIntegrityError(ValueError):
    """Event history is malformed, inconsistent, or modified."""


def _canonical(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def _check_run_id(run_id: str) -> None:
    if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
        raise ReceiptIntegrityError("Run ID must be 32 lowercase hex characters")


def _check_directory(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ReceiptIntegrityError("State directory must be real, not a symlink")
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ReceiptIntegrityError("State directory must be user-owned and private")


def _root(root: Path) -> Path:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("SciServer provenance storage requires POSIX/WSL2")
    path = Path(os.path.abspath(root))
    if path.is_symlink():
        raise ReceiptIntegrityError("Symlinked state root forbidden")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    _check_directory(path)
    return path


def _digest(event: dict) -> str:
    return hashlib.sha256(_canonical(event)).hexdigest()


def _atomic_create(path: Path, value: dict) -> None:
    """Create-only publication: write, fsync, then hard-link into place."""
    payload = _canonical(value)
    if len(payload) > MAX_EVENT_BYTES:
        raise ReceiptIntegrityError("Receipt exceeds size limit")
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Receipt already exists: {path.name}")
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=path.parent, prefix=".receipt-", suffix=".tmp",
        delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)
        try:
            os.chmod(tmp_path, 0o600)
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
    try:
        os.link(tmp_path, path, follow_symlinks=False)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        tmp_path.unlink(missing_ok=True)


def _read_events_from_dir(run_dir: Path, run_id: str) -> list[dict]:
    names = []
    for path in run_dir.iterdir():
        if path.name.startswith("event_"):
            found = EVENT_NAME_RE.fullmatch(path.name)
            if not found or path.is_symlink() or not path.is_file():
                raise ReceiptIntegrityError("Unexpected event filename or symlink")
            names.append((int(found.group(1)), path))
    names.sort()
    events = []
    previous_sha = None
    previous_type = None
    for expected_idx, (number, path) in enumerate(names):
        if number != expected_idx:
            raise ReceiptIntegrityError("Event sequence gap or duplicate")
        raw = path.read_bytes()
        if len(raw) > MAX_EVENT_BYTES:
            raise ReceiptIntegrityError("Oversized event")
        try:
            event = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ReceiptIntegrityError("Invalid event JSON") from exc
        if not isinstance(event, dict) or set(event) != {
            "schema_version", "run_id", "sequence", "event_type",
            "recorded_at_utc", "previous_sha256", "data", "record_sha256"
        }:
            raise ReceiptIntegrityError("Malformed event schema")
        unsigned = {key: value for key, value in event.items() if key != "record_sha256"}
        if (event["schema_version"] != SCHEMA or event["run_id"] != run_id
                or event["sequence"] != expected_idx
                or event["previous_sha256"] != previous_sha
                or event["event_type"] not in TRANSITIONS.get(previous_type, frozenset())
                or not isinstance(event["record_sha256"], str)
                or _digest(unsigned) != event["record_sha256"]):
            raise ReceiptIntegrityError("Event hash, chain or transition mismatch")
        previous_sha = event["record_sha256"]
        previous_type = event["event_type"]
        events.append(event)
    return events


def read_events(root: Path, run_id: str) -> list[dict]:
    """Check the complete chain, including terminal state and missing numbers."""
    _check_run_id(run_id)
    root_path = _root(root)
    run_dir = root_path / run_id
    _check_directory(run_dir)
    events = _read_events_from_dir(run_dir, run_id)
    if not events:
        raise ReceiptIntegrityError("Run exists without a planned event")
    return events


def append_event(
    root: Path, run_id: str, event_type: str, data: dict, *,
    expected_previous_sha256: str | None,
) -> dict:
    """Serialize writers per run and reject stale/replayed state transitions."""
    _check_run_id(run_id)
    if event_type not in TRANSITIONS or event_type is None:
        raise ReceiptIntegrityError("Unrecognized event type")
    if not isinstance(data, dict):
        raise ReceiptIntegrityError("Event data must be an object")
    root_path = _root(root)
    run_dir = root_path / run_id
    if event_type == "planned":
        run_dir.mkdir(mode=0o700, exist_ok=False)
    _check_directory(run_dir)
    lock_flags = os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
    lock_fd = os.open(run_dir / ".append.lock", lock_flags, 0o600)
    try:
        lock_info = os.fstat(lock_fd)
        if (not stat.S_ISREG(lock_info.st_mode)
                or lock_info.st_uid != os.getuid()
                or stat.S_IMODE(lock_info.st_mode) & 0o077):
            raise ReceiptIntegrityError("Insecure receipt lock file")
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        history = _read_events_from_dir(run_dir, run_id)
        previous = history[-1] if history else None
        prior_hash = previous["record_sha256"] if previous else None
        prior_type = previous["event_type"] if previous else None
        if expected_previous_sha256 != prior_hash:
            raise ReceiptIntegrityError("Stale or replayed prior event hash")
        if event_type not in TRANSITIONS[prior_type]:
            raise ReceiptIntegrityError("Invalid or replayed state transition")
        unsigned = {
            "schema_version": SCHEMA,
            "run_id": run_id,
            "sequence": len(history),
            "event_type": event_type,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "previous_sha256": prior_hash,
            "data": data,
        }
        event = dict(unsigned, record_sha256=_digest(unsigned))
        _atomic_create(run_dir / f"event_{len(history):04d}.json", event)
        return event
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
