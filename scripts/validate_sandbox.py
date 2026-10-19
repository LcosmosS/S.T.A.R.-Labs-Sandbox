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
RESERVED = ("controlled_execution", "preregistrations", "release_packages", "verified_evidence", "registry")
ID_PATTERN = re.compile(r"^(SBX-\d{4}-\d{4})(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?$")


def load_metadata(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate metadata key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def inspect(root: Path) -> list[str]:
    errors: list[str] = []
    for name in RESERVED:
        if (root / name).exists():
            errors.append(f"Reserved upstream-only root path exists: {name}/")

    readme = root / "README.md"
    disclaimer = root / "DISCLAIMER.md"
    if readme.is_symlink() or not readme.is_file() or "SANDBOX" not in readme.read_text(encoding="utf-8").upper():
        errors.append("README.md must visibly say SANDBOX")
    if disclaimer.is_symlink() or not disclaimer.is_file():
        errors.append("DISCLAIMER.md is required")
    else:
        body = disclaimer.read_text(encoding="utf-8").lower()
        if "not" not in body or "verified" not in body or "upstream" not in body:
            errors.append("DISCLAIMER.md must state unverified and upstream limits")

    experiments = root / "experiments"
    if experiments.is_symlink() or not experiments.is_dir():
        errors.append("experiments/ is required")
        return errors

    seen: set[str] = set()
    for folder in sorted(experiments.iterdir()):
        if folder.name == "README.md" and folder.is_file() and not folder.is_symlink():
            continue
        if folder.is_symlink() or not folder.is_dir():
            errors.append(f"{folder.name}: unexpected or symlink experiment entry")
            continue
        if any(p.is_symlink() for p in folder.rglob("*")):
            errors.append(f"{folder.name}: experiment symlinks are not allowed")
            continue
        if folder.name == "_template":
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
            data = load_metadata(meta)
        except (OSError, ValueError) as exc:
            errors.append(f"{folder.name}: unreadable metadata.json: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{folder.name}: metadata must be an object")
            continue
        fields = {"schema_version", "id", "title", "status", "scope", "epistemic_status",
                  "proposition", "falsifier", "provenance", "limitations"}
        if set(data) != fields:
            errors.append(f"{folder.name}: missing or unexpected metadata fields")
        if type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
            errors.append(f"{folder.name}: schema_version must equal 1")
        if data.get("id") != expected_id:
            errors.append(f"{folder.name}: metadata id must equal {expected_id}")
        if not isinstance(data.get("title"), str) or len(data["title"].strip()) < 4:
            errors.append(f"{folder.name}: nonempty title required")
        status = data.get("status")
        if not isinstance(status, str) or status not in ALLOWED:
            errors.append(f"{folder.name}: forbidden/unknown status {status!r}")
        if data.get("scope") != "sandbox-only":
            errors.append(f"{folder.name}: scope must equal sandbox-only")
        epistemic = data.get("epistemic_status")
        if not isinstance(epistemic, dict):
            errors.append(f"{folder.name}: epistemic_status object is required")
        else:
            if set(epistemic) != {"eligible_for_automatic_promotion", "claim_of_truth", "independently_reviewed"}:
                errors.append(f"{folder.name}: missing or unexpected epistemic fields")
            if epistemic.get("eligible_for_automatic_promotion") is not False:
                errors.append(f"{folder.name}: automatic promotion must explicitly equal false")
            if epistemic.get("claim_of_truth") is not False:
                errors.append(f"{folder.name}: claim_of_truth must equal false in sandbox")
            if epistemic.get("independently_reviewed") is not False:
                errors.append(f"{folder.name}: independently_reviewed must equal false for sandbox admission")
        for field in ("proposition", "falsifier"):
            if not isinstance(data.get(field), str) or len(data[field].strip()) < 8:
                errors.append(f"{folder.name}: nonempty {field} required")
        provenance = data.get("provenance")
        if not isinstance(provenance, dict):
            errors.append(f"{folder.name}: provenance object required")
        else:
            if (not {"input_kind", "sources"} <= set(provenance)
                    or not set(provenance) <= {"input_kind", "sources", "upstream_commit"}):
                errors.append(f"{folder.name}: missing or unexpected provenance fields")
            if (not isinstance(provenance.get("input_kind"), str)
                    or provenance["input_kind"] not in {"synthetic", "observed", "mixed", "none"}
                    or not isinstance(provenance.get("sources"), list)
                    or not all(isinstance(x, str) for x in provenance.get("sources", []))):
                errors.append(f"{folder.name}: input_kind and textual source list required")
            commit = provenance.get("upstream_commit")
            if commit is not None and (not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit)):
                errors.append(f"{folder.name}: upstream_commit must be null or a full Git SHA")
        if (not isinstance(data.get("limitations"), list) or not data["limitations"]
                or not all(isinstance(x, str) and x.strip() for x in data["limitations"])):
            errors.append(f"{folder.name}: nonempty textual limitations list required")

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
