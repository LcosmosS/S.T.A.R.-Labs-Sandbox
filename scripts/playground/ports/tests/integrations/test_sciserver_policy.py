"""Offline policy/replay/receipt regression tests; no SciServer SDK or network."""
import json
import os
import shutil
from pathlib import Path

import pytest

from integrations.sciserver import query_policy as policy
from integrations.sciserver import receipts


@pytest.fixture
def sandbox(tmp_path):
    """Replicate only frozen SQL files and the catalog for mutation tests."""
    root = tmp_path / "checkout"
    sql_dir = root / "verification/datasets/casjobs"
    sql_dir.mkdir(parents=True)
    catalog_dir = root / "integrations/sciserver"
    catalog_dir.mkdir(parents=True)
    for filename in (
        "STAR_DR18_10_canary.sql",
        "DATA-SDSS18-200K_deterministic_probe.sql",
    ):
        shutil.copy2(policy.REPO_ROOT / "verification/datasets/casjobs" / filename,
                     sql_dir / filename)
    catalog = catalog_dir / "query_catalog.json"
    shutil.copy2(policy.CATALOG_PATH, catalog)
    return root, catalog, sql_dir


def test_real_catalog_pins_both_sql_files():
    result = policy.load_catalog()
    assert set(result["queries"]) == policy.QUERY_IDS
    assert result["queries"]["DR18-CANARY-10"]["max_rows"] == 10
    assert result["queries"]["DR18-DETERMINISTIC-200K"]["submission_enabled"] is False


def test_catalog_rejects_hash_drift(sandbox):
    root, catalog, sql_dir = sandbox
    path = sql_dir / "STAR_DR18_10_canary.sql"
    path.write_bytes(path.read_bytes() + b"\n-- unexpected edit\n")
    with pytest.raises(policy.PolicyViolation, match="SQL hash drift"):
        policy.load_catalog(catalog, root)


def test_catalog_rejects_unapproved_context_or_activation(sandbox):
    root, catalog, _ = sandbox
    data = json.loads(catalog.read_text())
    data["queries"][0]["context"] = "MyDB"
    catalog.write_text(json.dumps(data))
    with pytest.raises(policy.PolicyViolation, match="Dataset/context"):
        policy.load_catalog(catalog, root)
    data["queries"][0]["context"] = "DR18"
    data["remote_submission_enabled"] = True
    catalog.write_text(json.dumps(data))
    with pytest.raises(policy.PolicyViolation, match="disabled"):
        policy.load_catalog(catalog, root)


def test_catalog_rejects_path_escape(sandbox):
    root, catalog, _ = sandbox
    data = json.loads(catalog.read_text())
    data["queries"][0]["path"] = "../../somewhere.sql"
    catalog.write_text(json.dumps(data))
    with pytest.raises(policy.PolicyViolation):
        policy.load_catalog(catalog, root)


def test_catalog_rejects_symlinked_sql(sandbox):
    root, catalog, sql_dir = sandbox
    path = sql_dir / "STAR_DR18_10_canary.sql"
    destination = sql_dir / "target.sql"
    path.rename(destination)
    path.symlink_to(destination)
    with pytest.raises(policy.PolicyViolation, match="Symlinks"):
        policy.load_catalog(catalog, root)


def test_unapproved_query_cannot_be_prepared(tmp_path):
    with pytest.raises(policy.PolicyViolation, match="allowlist"):
        policy.prepare_casjobs_run("SELECT * FROM MyDB", state_root=tmp_path / "state")


def test_deterministic_probe_stays_preparation_blocked(tmp_path):
    with pytest.raises(policy.PolicyViolation, match="blocked"):
        policy.prepare_casjobs_run("DR18-DETERMINISTIC-200K",
                                   state_root=tmp_path / "state")
    assert not (tmp_path / "state").exists()


def test_canary_preparation_is_local_write_once(tmp_path):
    root = tmp_path / "state"
    result = policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)
    plan = result["plan"]
    assert plan["context"] == "DR18"
    assert plan["max_rows"] == 10
    assert plan["remote_submission_enabled"] is False
    assert plan["mydb_destination"] == (
        f"STAR_SCISERVER_C10_{plan['run_id'][:16].upper()}"
    )
    events = receipts.read_events(root, plan["run_id"])
    assert len(events) == 1 and events[0]["event_type"] == "planned"
    assert events[0]["record_sha256"] == result["receipt_sha256"]
    assert events[0]["data"] == plan
    assert list((root / plan["run_id"]).glob("event_*.json")) == [
        root / plan["run_id"] / "event_0000.json"
    ]


def test_destination_rejects_user_supplied_name():
    with pytest.raises(policy.PolicyViolation):
        policy.validate_destination("a" * 32, "canary", "mydb.MyTable")
    with pytest.raises(policy.PolicyViolation):
        policy.validate_destination("a" * 32, "canary",
                                    "STAR_SCISERVER_C10_" + "B" * 16)


def test_collision_rejects_second_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(policy.secrets, "token_hex", lambda n: "a" * 32)
    root = tmp_path / "state"
    policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)
    with pytest.raises(FileExistsError):
        policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)


def test_root_symlink_rejected(tmp_path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    root = tmp_path / "alias"
    root.symlink_to(real, target_is_directory=True)
    with pytest.raises(receipts.ReceiptIntegrityError, match="Symlink"):
        policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)


def test_receipt_tamper_is_detected(tmp_path):
    root = tmp_path / "state"
    plan = policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)["plan"]
    path = root / plan["run_id"] / "event_0000.json"
    data = json.loads(path.read_text())
    data["data"]["context"] = "MyDB"
    path.write_text(json.dumps(data))
    with pytest.raises(receipts.ReceiptIntegrityError, match="hash"):
        receipts.read_events(root, plan["run_id"])


def test_stale_hash_and_duplicate_event_rejected(tmp_path):
    root = tmp_path / "state"
    prepared = policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)
    run = prepared["plan"]["run_id"]
    initial_hash = prepared["receipt_sha256"]
    approved = receipts.append_event(root, run, "operator_approved",
                                     {"test_only": True},
                                     expected_previous_sha256=initial_hash)
    with pytest.raises(receipts.ReceiptIntegrityError, match="Stale"):
        receipts.append_event(root, run, "submission_intent", {},
                              expected_previous_sha256=initial_hash)
    with pytest.raises(receipts.ReceiptIntegrityError, match="transition"):
        receipts.append_event(root, run, "operator_approved", {},
                              expected_previous_sha256=approved["record_sha256"])


def test_ambiguous_submission_cannot_be_replayed(tmp_path):
    """Mocked future events, not an actual remote submission or approval."""
    root = tmp_path / "state"
    prepared = policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)
    run = prepared["plan"]["run_id"]
    sha = prepared["receipt_sha256"]
    for kind in ("operator_approved", "submission_intent", "submission_ambiguous"):
        sha = receipts.append_event(root, run, kind, {"mock": True},
                                    expected_previous_sha256=sha)["record_sha256"]
    with pytest.raises(receipts.ReceiptIntegrityError):
        receipts.append_event(root, run, "submission_intent", {"mock": True},
                              expected_previous_sha256=sha)
    events = receipts.read_events(root, run)
    assert len(events) == 4
    assert events[-1]["event_type"] == "submission_ambiguous"


def test_terminal_abort_rejects_further_events(tmp_path):
    root = tmp_path / "state"
    prepared = policy.prepare_casjobs_run("DR18-CANARY-10", state_root=root)
    run = prepared["plan"]["run_id"]
    stopped = receipts.append_event(root, run, "aborted", {"reason": "mock"},
                                    expected_previous_sha256=prepared["receipt_sha256"])
    with pytest.raises(receipts.ReceiptIntegrityError):
        receipts.append_event(root, run, "operator_approved", {},
                              expected_previous_sha256=stopped["record_sha256"])


def test_submission_boundary_is_unconditionally_closed():
    with pytest.raises(PermissionError, match="disabled"):
        policy.require_submission_authorization()
    with pytest.raises(PermissionError):
        policy.require_submission_authorization("operator_approved", True)
