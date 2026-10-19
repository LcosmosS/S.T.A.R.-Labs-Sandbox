"""Regression tests for portable provenance-capture artifacts."""

import csv
import hashlib

from scripts.validate_provenance_capture import EXPECTED_FIELDS, validate


def test_capture_paths_resolve_under_artifact_root(tmp_path, monkeypatch):
    capture = tmp_path / "downloaded" / "provenance_capture"
    raw = capture / "raw"
    raw.mkdir(parents=True)
    payload = raw / "doc_001_example.txt"
    payload.write_text("captured provenance\n", encoding="utf-8")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()

    manifest = capture / "google_docs_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=EXPECTED_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "document_index": "1",
                "document_id": "example",
                "source_url": "https://docs.google.com/document/d/example/edit",
                "output_path": "raw/doc_001_example.txt",
                "sha256": digest,
                "content_type": "text/plain",
                "final_url": "https://docs.google.com/document/d/example/export",
            }
        )

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    validate(capture)
