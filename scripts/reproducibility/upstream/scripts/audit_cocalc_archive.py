"""Read-only, fail-closed provenance inventory for quarantined CoCalc ZIP exports.

This does not extract or execute files and does not confer source acceptance,
scientific reproducibility, dataset identity, or controlled support. Python
syntax parsing and notebook JSON inspection are diagnostics, not experiment runs.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


class ArchiveAuditError(ValueError):
    """Archive must not enter a source-evidence pipeline."""


MAX_TOTAL = 256 * 1024 * 1024
MAX_MEMBER = 128 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def _safe_path(name: str) -> bool:
    candidate = PurePosixPath(name)
    return bool(name and not name.startswith("/") and "\\" not in name
                and ":" not in name.split("/")[0]
                and not candidate.is_absolute()
                and all(part not in ("", ".", "..") for part in name.split("/")))


def _sha256_stream(stream) -> str:
    h = hashlib.sha256()
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            return h.hexdigest()
        h.update(chunk)


def inspect_archive(archive: Path) -> dict:
    archive = Path(archive)
    digest = _sha256_stream(archive.open("rb"))
    rows = []
    with zipfile.ZipFile(archive) as z:
        infos = [entry for entry in z.infolist() if not entry.is_dir()]
        names = [entry.filename for entry in infos]
        if len(names) != len(set(names)):
            raise ArchiveAuditError("duplicate archive member names")
        total = sum(info.file_size for info in infos)
        if total > MAX_TOTAL:
            raise ArchiveAuditError("archive uncompressed size exceeds bound")
        for info in infos:
            name = info.filename
            if not _safe_path(name):
                raise ArchiveAuditError(f"unsafe archive member path: {name!r}")
            if info.file_size > MAX_MEMBER:
                raise ArchiveAuditError(f"oversized member: {name!r}")
            unix_type = (info.external_attr >> 16) & 0o170000
            if unix_type == stat.S_IFLNK:
                raise ArchiveAuditError(f"symbolic-link member forbidden: {name!r}")
            with z.open(info, "r") as member:
                sha = _sha256_stream(member)
            ext = PurePosixPath(name).suffix.lower()
            record = {
                "name": name, "bytes": info.file_size, "sha256": sha,
                "type": ext, "classification": "historical_quarantine_unreviewed",
            }
            if ".partialupload" in name.lower():
                record["classification"] = "incomplete_upload_quarantine"
            elif ext == ".py":
                with z.open(info, "r") as member:
                    try:
                        ast.parse(member.read().decode("utf-8-sig"), filename=name)
                        record["syntax"] = "valid"
                    except (SyntaxError, UnicodeError, ValueError):
                        record["syntax"] = "invalid"
                        record["classification"] = "historical_invalid_python_quarantine"
            elif ext == ".ipynb":
                with z.open(info, "r") as member:
                    try:
                        nb = json.loads(member.read().decode("utf-8-sig"))
                        if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
                            raise ValueError("invalid notebook structure")
                        cells = nb["cells"]
                        output_cells = sum(bool(c.get("outputs")) for c in cells
                                           if isinstance(c, dict) and c.get("cell_type") == "code")
                        record["notebook"] = {
                            "cells": len(cells), "output_cells": output_cells,
                            "has_prior_outputs": output_cells > 0,
                        }
                        if output_cells:
                            record["classification"] = "notebook_with_historical_outputs_quarantine"
                    except (ValueError, TypeError, UnicodeError):
                        record["classification"] = "invalid_notebook_quarantine"
            rows.append(record)
    return {
        "schemaVersion": "star-cocalc-provenance-v1",
        "archive": {
            "filename": archive.name, "sha256": digest,
            "bytes": archive.stat().st_size, "uncompressedBytes": total,
            "memberCount": len(rows),
        },
        "authority": "uploaded_archive_unverified_upstream",
        "controlledExecutionEligible": False,
        "controlledSupportEligible": False,
        "physicalSupportEligible": False,
        "countsByClassification": dict(sorted(Counter(x["classification"] for x in rows).items())),
        "members": sorted(rows, key=lambda x: x["name"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="source ZIP file; read-only")
    parser.add_argument("--output", type=Path, required=True, help="new JSON manifest")
    args = parser.parse_args()
    if args.output.resolve() == args.archive.resolve():
        parser.error("output must not overwrite archive")
    try:
        manifest = inspect_archive(args.archive)
        if args.output.exists():
            raise ArchiveAuditError("output already exists; manifests are immutable")
    except (ArchiveAuditError, OSError, zipfile.BadZipFile, RuntimeError) as exc:
        parser.exit(2, f"REJECTED: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"QUARANTINED INVENTORY: {manifest['archive']['memberCount']} entries; no eligibility granted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
