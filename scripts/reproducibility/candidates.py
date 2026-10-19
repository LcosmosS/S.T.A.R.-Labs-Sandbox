"""Sandbox-only reproducibility intake: pinned CSV/SQL artifacts, not scientific review.

This stdlib checker reads declared files without changing inputs, dropping rows,
running SQL, importing submitted Python, or authorizing any upstream promotion.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys

SHA = re.compile(r"^[a-f0-9]{64}$")
ID = re.compile(r"^SBX-[0-9]{4}-[0-9]{4}$")
BAD_SQL = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|MERGE|TRUNCATE|EXEC(?:UTE)?|"
    r"GRANT|REVOKE|INTO|OPENROWSET|BULK|BACKUP|RESTORE|WAITFOR)\b", re.I
)


def require(ok, message):
    """Reject malformed contracts without silent fallback or inference."""
    if not ok:
        raise ValueError(message)


def unique_pairs(items):
    """Reject ambiguous JSON keys rather than choosing the last occurrence."""
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def load(path):
    """Load a regular JSON manifest without allowing duplicate object keys."""
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def sha256(raw):
    """Calculate a canonical hex digest over actual file bytes."""
    return hashlib.sha256(raw).hexdigest()


def inside(root, rel):
    """Return a regular file inside the experiment without traversing symlinks."""
    require(isinstance(rel, str) and bool(rel), "empty artifact path")
    relative = PurePosixPath(rel)
    require(not relative.is_absolute() and ".." not in relative.parts
            and "\\" not in rel and str(relative) == rel,
            f"unsafe artifact path: {rel}")
    target = root.joinpath(*relative.parts)
    require(target.resolve().is_relative_to(root.resolve()),
            f"artifact outside experiment: {rel}")
    require(target.is_file(), f"missing artifact: {rel}")
    current = target
    while current != root:
        require(not current.is_symlink(), f"symlink artifact forbidden: {rel}")
        current = current.parent
    return target


def sql_tokens(raw):
    """Apply conservative static SQL lint, never an execution authorization."""
    require(len(raw) <= 65536, "SQL exceeds 64 KiB")
    try:
        body = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("SQL must be UTF-8") from exc
    # A conservative lexer refuses block comments/quotes to avoid disguising
    # an operation inside syntax this simple non-parser cannot interpret.
    require("/*" not in body and "*/" not in body,
            "SQL block comments are outside the lint contract")
    clean = "\n".join(line.split("--", 1)[0] for line in body.splitlines())
    clean = clean.strip()
    require(clean and re.match(r"(?is)^SELECT\s+TOP\s+[1-9][0-9]*\b", clean),
            "candidate SQL must start with bounded SELECT TOP")
    require(not BAD_SQL.search(clean), "SQL contains prohibited operation")
    require(";" not in clean, "multiple/terminated statements are not accepted")
    top = re.match(r"(?is)^SELECT\s+TOP\s+([0-9]+)\b", clean)
    require(top is not None and 0 < int(top.group(1)) <= 200000,
            "SQL TOP exceeds limit")
    return int(top.group(1))


def verify_csv(raw, entry):
    """Check exact CSV columns and every row without exclusions or deduplication."""
    try:
        contents = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("CSV must be UTF-8") from exc
    import io
    reader = csv.reader(io.StringIO(contents, newline=""), strict=True)
    columns = next(reader, [])
    require(columns == entry["columns"] and len(set(columns)) == len(columns)
            and all(columns), "CSV column header drift or duplicate headers")
    count = 0
    nulls = {column: 0 for column in columns}
    seen = set()
    duplicates = 0
    for row in reader:
        require(len(row) == len(columns), f"CSV malformed at row {count + 2}")
        count += 1
        require(count <= 200000, "CSV row limit exceeded")
        ident = tuple(row)
        duplicates += ident in seen
        seen.add(ident)
        for col, val in zip(columns, row):
            if val.strip() == "" or val.strip().lower() in {"nan", "null"}:
                nulls[col] += 1
    require(count == entry["rows"], "CSV row count drift")
    return {"rows_retained": count, "duplicate_rows_retained": duplicates,
            "null_count_by_column": nulls, "columns": columns}


def check_contract(root, contract):
    """Validate a single SBX contract and return only software-level diagnostics."""
    require(isinstance(contract, dict) and set(contract) == {
        "schema_version", "experiment_id", "scope", "status", "source_kind",
        "scientific_claim", "independently_reviewed",
        "automatic_promotion", "artifacts",
    }, "contract schema fields differ")
    require(type(contract["schema_version"]) is int
            and contract["schema_version"] == 1, "unknown schema version")
    require(isinstance(contract["experiment_id"], str)
            and ID.fullmatch(contract["experiment_id"]), "invalid SBX ID")
    require(contract["scope"] == "sandbox-only"
            and contract["status"] == "exploratory", "invalid sandbox status")
    for field in ("scientific_claim", "independently_reviewed", "automatic_promotion"):
        require(contract[field] is False, f"{field} must be false")
    require(contract["source_kind"] in ("synthetic", "publisher", "recovered", "mixed"),
            "unrecognized source_kind")
    entries = contract["artifacts"]
    require(isinstance(entries, list) and entries, "no reproducibility artifacts")
    require(len(entries) <= 25, "too many contract artifacts")
    used = set()
    output = []
    for entry in entries:
        require(isinstance(entry, dict) and set(entry) == {
            "path", "sha256", "size_bytes", "format", "columns", "rows",
            "source", "source_commit",
        }, "artifact schema fields differ")
        rel = entry["path"]
        require(rel not in used, "duplicate artifact path")
        used.add(rel)
        require(entry["format"] in ("csv", "sql", "json", "binary"), "unknown format")
        require(isinstance(entry["source"], str) and bool(entry["source"].strip()),
                "missing source provenance")
        require(entry["source_commit"] is None or
                (isinstance(entry["source_commit"], str)
                 and re.fullmatch(r"[a-f0-9]{40}", entry["source_commit"])),
                "invalid upstream commit reference")
        require(isinstance(entry["sha256"], str) and SHA.fullmatch(entry["sha256"]),
                "invalid SHA-256")
        require(type(entry["size_bytes"]) is int
                and 0 <= entry["size_bytes"] <= 100_000_000,
                "invalid size limit")
        data = inside(root, rel).read_bytes()
        require(len(data) == entry["size_bytes"], f"size mismatch: {rel}")
        require(sha256(data) == entry["sha256"], f"SHA-256 mismatch: {rel}")
        result = {"path": rel, "sha256": entry["sha256"],
                  "size_bytes": len(data), "format": entry["format"],
                  "source": entry["source"]}
        if entry["format"] == "csv":
            require(isinstance(entry["columns"], list)
                    and all(isinstance(col, str) for col in entry["columns"])
                    and type(entry["rows"]) is int and entry["rows"] >= 0,
                    "CSV requires declared columns and row count")
            result.update(verify_csv(data, entry))
        else:
            require(entry["columns"] is None and entry["rows"] is None,
                    "row/column contract only applies to CSV")
            if entry["format"] == "sql":
                result["select_top"] = sql_tokens(data)
                result["sql_authorized_to_execute"] = False
            elif entry["format"] == "json":
                json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs)
        output.append(result)
    return {
        "schema_version": 1, "experiment_id": contract["experiment_id"],
        "scope": "sandbox-only", "status": "exploratory",
        "scientific_claim": False, "independently_reviewed": False,
        "automatic_promotion": False, "remote_submission": False,
        "execution_performed": False, "artifacts": output,
        "disposition": "reproducibility_precheck_only_not_scientific_acceptance",
    }


def discover(root):
    """Assess only opt-in contract files in registered SBX experiment folders."""
    experiments = root / "experiments"
    reports = []
    if not experiments.is_dir():
        return reports
    for folder in sorted(experiments.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("SBX-"):
            continue
        contract = folder / "reproducibility.json"
        if contract.exists() or contract.is_symlink():
            require(contract.is_file() and not contract.is_symlink(),
                    "invalid experiment reproducibility manifest")
            value = load(contract)
            require(value.get("experiment_id") == folder.name[:13],
                    "contract experiment ID differs from folder")
            reports.append(check_contract(folder, value))
    return reports


def main(argv=None):
    """Report candidate input reproducibility, preserving all original data."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        reports = discover(args.root.resolve())
        value = {
            "scope": "sandbox-only",
            "source": "proposed_repository_checkout",
            "experiment_contracts_checked": len(reports),
            "scientific_review_performed": False,
            "automatic_promotion": False,
            "reports": reports,
        }
        result = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
        if args.output:
            require(not args.output.is_symlink(), "output symlink forbidden")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result, encoding="utf-8")
        print(result)
        return 0
    except (OSError, ValueError, TypeError, KeyError, csv.Error) as error:
        print(f"Sandbox reproducibility check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
