#!/usr/bin/env python3
"""Validate new sandbox experiment metadata and non-promotion boundaries.

This checker intentionally never reads or executes historical R&D code.
It does not attempt to validate scientific truth.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"speculative", "intentionally-false-control", "exploratory", "inconclusive", "refuted", "archived"}
RESERVED = ("controlled_execution", "preregistrations", "release_packages", "verified_evidence")
ID_PATTERN = re.compile(r"^(SBX-\d{4}-\d{4})(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?$")


def inspect(root: Path) -> list[str]:
    errors: list[str] = []
    for name in RESERVED:
        if (root / name).exists():
            errors.append(f"Reserved upstream-only root path exists: {name}/")

    readme = root / "README.md"
    disclaimer = root / "DISCLAIMER.md"
    if not readme.is_file() or "SANDBOX" not in readme.read_text(encoding="utf-8").upper():
        errors.append("README.md must visibly say SANDBOX")
    if not disclaimer.is_file():
        errors.append("DISCLAIMER.md is required")
    else:
        body = disclaimer.read_text(encoding="utf-8").lower()
        if "not" not in body or "verified" not in body or "upstream" not in body:
            errors.append("DISCLAIMER.md must state unverified and upstream limits")

    experiments = root / "experiments"
    if not experiments.is_dir():
        errors.append("experiments/ is required")
        return errors

    seen: set[str] = set()
    for folder in sorted(experiments.iterdir()):
        if not folder.is_dir() or folder.name == "_template":
            continue
        match = ID_PATTERN.fullmatch(folder.name)
        if not match:
            errors.append(f"{folder.name}: expected SBX-YYYY-NNNN-short-slug directory")
            continue
        expected_id = match.group(1)
        if expected_id in seen:
            errors.append(f"{folder.name}: duplicated experiment ID {expected_id}")
        seen.add(expected_id)

        meta = folder / "metadata.json"
        if not meta.is_file():
            errors.append(f"{folder.name}: missing metadata.json")
            continue
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{folder.name}: unreadable metadata.json: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{folder.name}: metadata must be an object")
            continue
        if data.get("schema_version") != 1:
            errors.append(f"{folder.name}: schema_version must equal 1")
        if data.get("id") != expected_id:
            errors.append(f"{folder.name}: metadata id must equal {expected_id}")
        if not isinstance(data.get("title"), str) or not data["title"].strip():
            errors.append(f"{folder.name}: nonempty title required")
        status = data.get("status")
        if status not in ALLOWED:
            errors.append(f"{folder.name}: forbidden/unknown status {status!r}")
        if data.get("scope") != "sandbox-only":
            errors.append(f"{folder.name}: scope must equal sandbox-only")
        epistemic = data.get("epistemic_status")
        if not isinstance(epistemic, dict) or epistemic.get("eligible_for_automatic_promotion") is not False:
            errors.append(f"{folder.name}: automatic promotion must explicitly equal false")
        for field in ("proposition", "falsifier"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                errors.append(f"{folder.name}: nonempty {field} required")
        provenance = data.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("input_kind") not in {"synthetic", "observed", "mixed", "none"} or not isinstance(provenance.get("sources"), list):
            errors.append(f"{folder.name}: input_kind and source list required")
        if not isinstance(data.get("limitations"), list) or not data["limitations"]:
            errors.append(f"{folder.name}: nonempty limitations list required")

        description = folder / "README.md"
        if not description.is_file() or "SANDBOX" not in description.read_text(encoding="utf-8").upper():
            errors.append(f"{folder.name}: README.md must visibly identify SANDBOX")
        if status == "intentionally-false-control" and description.is_file():
            upper = description.read_text(encoding="utf-8").upper()
            if "FALSE" not in upper:
                errors.append(f"{folder.name}: false control must be visibly labeled FALSE")
    return errors


def main() -> int:
    errors = inspect(ROOT)
    for issue in errors:
        print("ERROR:", issue, file=sys.stderr)
    if errors:
        return 1
    print("Sandbox policy checks passed. This does NOT certify scientific truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
