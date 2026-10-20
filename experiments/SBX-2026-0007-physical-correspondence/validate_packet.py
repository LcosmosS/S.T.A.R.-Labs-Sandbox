"""Fail-closed Sandbox packet preflight. Does NOT authorize Legacy submission.

No upstream API mutation, network, scientific execution, or physical validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
HASH = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = (
    "source_manifest.json", "cohort_manifest.json", "crossmatch_audit.json",
    "selection_function.json", "physical_operator.md",
    "preanalysis_lock.json", "environment_manifest.json",
    "null_distribution.csv", "primary_endpoint.json", "sensitivity.json",
    "failures.json", "run_manifest.json", "negative_results.md",
)


def validate(packet_path: Path, root: Path = HERE):
    errors = []
    gate = json.loads((HERE/"stage_gate.json").read_text(encoding="utf-8"))
    for p in gate["prerequisites"]:
        if p.get("complete") is not True:
            errors.append("open_prerequisite:" + str(p["id"]))
        receipt = p.get("evidence")
        if p.get("complete") is True and (
            not isinstance(receipt,dict)
            or not HASH.fullmatch(str(receipt.get("sha256","")))
            or not re.fullmatch(r"[0-9a-f]{40}",str(receipt.get("commit","")))):
            errors.append("missing_exact_prerequisite_evidence:" + str(p["id"]))
    if gate.get("observational_execution_allowed") is not True:
        errors.append("observational_execution_blocked")
    if gate.get("legacy_pr_allowed") is not True:
        errors.append("legacy_pr_blocked")
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        packet = {}
        errors.append("packet_missing_or_invalid:" + type(exc).__name__)
    if packet.get("experiment_id") != "SBX-2026-0007":
        errors.append("experiment_identity")
    if packet.get("automatic_promotion") is not False:
        errors.append("automatic_promotion_must_be_false")
    if packet.get("independently_reviewed") is not False:
        errors.append("cannot_claim_independent_review_in_sandbox")
    if not re.fullmatch(r"[0-9a-f]{40}",str(packet.get("sandbox_commit",""))):
        errors.append("sandbox_commit_not_exact")
    for name in ("source_dataset_sha256","cohort_sha256","protocol_sha256",
                 "analysis_code_sha256","run_manifest_sha256","independent_verifier_digest"):
        if not HASH.fullmatch(str(packet.get(name,""))):
            errors.append("missing_hash:" + name)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}",str(packet.get("environment_digest",""))):
        errors.append("missing_container_digest")
    if not isinstance(packet.get("nonclaims"),list) or not packet["nonclaims"]:
        errors.append("missing_nonclaims")
    if not isinstance(packet.get("negative_result_inventory"),list) or not packet["negative_result_inventory"]:
        errors.append("missing_negative_inventory")
    artifacts = packet.get("artifacts",{})
    if not isinstance(artifacts,dict):
        artifacts={}
        errors.append("artifacts_not_dictionary")
    base = root.resolve()
    for rel in REQUIRED:
        expected=artifacts.get(rel)
        if not HASH.fullmatch(str(expected)):
            errors.append("missing_artifact_sha256:" + rel)
            continue
        pos=PurePosixPath(rel)
        path=root.joinpath(*pos.parts)
        if pos.is_absolute() or ".." in pos.parts or path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(base):
            errors.append("missing_or_unsafe_artifact:" + rel)
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append("artifact_digest_mismatch:" + rel)
    return {"scope":"sandbox-only","packet_structurally_complete":not errors,
            "independent_review_conferred":False,"legacy_status_changed":False,
            "status":"STRUCTURALLY_COMPLETE_NOT_SCIENTIFIC_APPROVAL" if not errors else "BLOCKED",
            "errors":sorted(set(errors))}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--packet",type=Path)
    parser.add_argument("--root",type=Path,default=HERE)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        result=validate(HERE/"packet_template.json",HERE)
        assert result["status"]=="BLOCKED"
        assert "legacy_pr_blocked" in result["errors"]
        print("PASS: blocking incomplete/unverified P2 packet; no scientific approval")
        return 0
    if args.packet is None:
        parser.error("--packet is required outside --self-test")
    result=validate(args.packet,args.root)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["status"]=="STRUCTURALLY_COMPLETE_NOT_SCIENTIFIC_APPROVAL" else 2


if __name__=="__main__":
    raise SystemExit(main())
