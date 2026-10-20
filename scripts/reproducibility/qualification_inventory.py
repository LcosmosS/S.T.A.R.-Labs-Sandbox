"""Static coverage qualification inventory; never infers execution from a workflow definition.

This audit intentionally cannot return PASS for optional scientific suites.
Run receipts must be provided and verified separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = (
    "observational-lfs", "publisher-refetch", "recovered-lfs",
    "sage-notebooks", "sage-sky", "starmap-browser",
    "build-image", "legacy-unit-suite",
)


def inspect(root: Path) -> dict:
    wf_path = root / ".github/workflows/sandbox-extended-reproducibility.yml"
    coverage_path = root / "scripts/reproducibility/coverage.json"
    workflow = wf_path.read_text(encoding="utf-8")
    coverage_bytes = coverage_path.read_bytes()
    coverage = json.loads(coverage_bytes)
    if coverage.get("scope") != "sandbox-only-reproducibility":
        raise ValueError("Unexpected coverage boundary")
    records = coverage.get("workflows")
    if not isinstance(records, list) or len(records) != 18:
        raise ValueError("Expected 18 historic workflow coverage records")
    advertised = set()
    for record in records:
        name = record.get("on_demand_suite")
        if name is not None:
            advertised.add(name)
    if advertised != set(EXPECTED):
        raise ValueError("Unrecognized or missing extended suite mapping")
    sections = {}
    headings = list(re.finditer(r"(?m)^  ([a-z][a-z0-9-]*):\s*$", workflow))
    for i, heading in enumerate(headings):
        name = heading.group(1)
        if name in EXPECTED:
            end = headings[i + 1].start() if i + 1 < len(headings) else len(workflow)
            sections[name] = workflow[heading.start():end]
    if set(sections) != set(EXPECTED):
        raise ValueError("Missing executable extended suite job definitions")
    suites = []
    for name in EXPECTED:
        block = sections[name]
        if "if: inputs.suite == '" + name + "'" not in block:
            raise ValueError("Unrecognized suite dispatch condition: " + name)
        reasons = []
        images = re.findall(r"(?m)^\s*image:\s*([^\s#]+)", block)
        if any("@sha256:" not in image for image in images):
            reasons.append("container_image_not_digest_pinned")
        if re.search(r"(?m)\bpip\s+install\s+-r\s+requirements\.txt\b", block):
            reasons.append("upstream_requirements_not_hash_locked")
        if "python-version: \"3.12\"" in block or "python-version: '3.12'" in block:
            reasons.append("python_runtime_minor_only")
        suites.append({
            "suite": name,
            "execution_status": "NOT_RUN",
            "environment_status": "BLOCKED" if reasons else "QUALIFICATION_NOT_PROVEN",
            "reasons": sorted(set(reasons)),
            "result": "NO_PASS_CLAIM",
            "required_next_evidence": [
                "exact_workflow_run_id_and_commit_sha",
                "immutable_container_digest_and_lockfile_hashes",
                "input_and_output_sha256_manifest",
                "explicit_success_failure_or_skip_receipt",
            ],
        })
    return {
        "schema_version": 1,
        "scope": "sandbox-only",
        "scientific_validation": False,
        "upstream_promotion": False,
        "source_workflow_sha256": hashlib.sha256(workflow.encode()).hexdigest(),
        "coverage_manifest_sha256": hashlib.sha256(coverage_bytes).hexdigest(),
        "historical_workflows_inventoried": len(records),
        "optional_suites": suites,
        "qualifier": "static_source_inventory_not_a_execution_receipt",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = inspect(args.root)
    body = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
