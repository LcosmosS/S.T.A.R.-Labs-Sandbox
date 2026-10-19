"""Validate a staged provenance-capture artifact before human review."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


EXPECTED_FIELDS = [
    "document_index",
    "document_id",
    "source_url",
    "output_path",
    "sha256",
    "content_type",
    "final_url",
]


def validate(capture_dir: Path):
    capture_dir = capture_dir.resolve()
    manifest = capture_dir / "google_docs_manifest.csv"
    if not manifest.is_file():
        raise ValueError(f"missing provenance manifest: {manifest}")

    with manifest.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise ValueError(f"unexpected provenance manifest schema: {reader.fieldnames}")
        rows = list(reader)

    if not rows:
        raise ValueError("provenance manifest contains no captured documents")

    seen_ids = set()
    seen_indices = set()
    for row in rows:
        doc_id = row["document_id"].strip()
        index = row["document_index"].strip()
        if not doc_id or doc_id in seen_ids:
            raise ValueError(f"missing or duplicate document_id: {doc_id!r}")
        if not index or index in seen_indices:
            raise ValueError(f"missing or duplicate document_index: {index!r}")
        seen_ids.add(doc_id)
        seen_indices.add(index)

        relative_output = Path(row["output_path"])
        if relative_output.is_absolute():
            raise ValueError(
                f"captured output_path must be artifact-relative: {relative_output}"
            )
        output = (capture_dir / relative_output).resolve()
        if capture_dir not in output.parents:
            raise ValueError(f"captured file escapes capture directory: {output}")
        if not output.is_file() or output.stat().st_size == 0:
            raise ValueError(f"missing or empty captured file: {output}")

        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            raise ValueError(f"SHA256 mismatch for {output}")
        if not row["content_type"].startswith("text/plain"):
            raise ValueError(f"unexpected content type for {doc_id}")
        if not row["source_url"].startswith("https://docs.google.com/document/d/"):
            raise ValueError(f"unexpected source URL for {doc_id}")

    print(f"validated_provenance_capture_count={len(rows)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_dir", type=Path)
    args = parser.parse_args()
    validate(args.capture_dir)


if __name__ == "__main__":
    main()
