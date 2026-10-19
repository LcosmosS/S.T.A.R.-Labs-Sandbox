"""Synthetic, non-scientific regression tests for the CoCalc intake auditor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from scripts.audit_cocalc_archive import ArchiveAuditError, inspect_archive


def _make_archive(path: Path, contents: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, payload in contents.items():
            z.writestr(name, payload)


def test_manifest_hashes_and_never_promotes_source(tmp_path):
    target = tmp_path / "source.zip"
    code = b"x = 1\n"
    notebook = json.dumps({
        "nbformat": 4, "cells": [
            {"cell_type": "code", "source": ["print(1)"],
             "outputs": [{"output_type": "stream", "text": ["1"]}],
             "execution_count": 1}
        ]
    }).encode()
    _make_archive(target, {
        "file.py": code, "historical.ipynb": notebook,
        "catalog.csv.partialupload-abcd": b"truncated,not,science\n",
    })
    audit = inspect_archive(target)
    assert audit["archive"]["memberCount"] == 3
    assert audit["archive"]["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert (audit["controlledExecutionEligible"],
            audit["controlledSupportEligible"],
            audit["physicalSupportEligible"]) == (False, False, False)
    by_name = {m["name"]: m for m in audit["members"]}
    assert by_name["file.py"]["syntax"] == "valid"
    assert by_name["file.py"]["sha256"] == hashlib.sha256(code).hexdigest()
    assert by_name["historical.ipynb"]["notebook"]["has_prior_outputs"] is True
    assert by_name["catalog.csv.partialupload-abcd"]["classification"] == "incomplete_upload_quarantine"


@pytest.mark.parametrize("bad_name", ["../escape.py", "/absolute.py", "a/../b.py", "C:/windows.py"])
def test_unsafe_paths_fail_closed(tmp_path, bad_name):
    target = tmp_path / "unsafe.zip"
    _make_archive(target, {bad_name: b"x=1\n"})
    with pytest.raises(ArchiveAuditError, match="unsafe archive"):
        inspect_archive(target)


def test_syntax_failure_is_preserved_as_negative_evidence(tmp_path):
    target = tmp_path / "invalid.zip"
    _make_archive(target, {"historical.py": b"def broken(:\n"})
    m = inspect_archive(target)["members"][0]
    assert m["syntax"] == "invalid"
    assert m["classification"] == "historical_invalid_python_quarantine"


def test_duplicate_names_abort(tmp_path):
    target = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(target, "w") as z:
        z.writestr("same.py", "x=1\n")
        z.writestr("same.py", "x=2\n")
    with pytest.raises(ArchiveAuditError, match="duplicate"):
        inspect_archive(target)
