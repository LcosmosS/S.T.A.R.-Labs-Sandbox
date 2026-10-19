"""Regression tests for metadata-aware Planck chain semantics."""

import numpy as np
import pytest

from src.likelihoods.data.planck_compressed import (
    PLANCK_CHAIN_ENV,
    load_planck_chain,
    load_planck_compressed,
)


def _write_base_metadata(root, names=("a", "b", "c")):
    root.with_suffix(".paramnames").write_text(
        "\n".join(f"{name}\t{name}" for name in names) + "\n",
        encoding="utf-8",
    )
    root.with_suffix(".ranges").write_text(
        "\n".join(f"{name} 0 N" for name in names) + "\n",
        encoding="utf-8",
    )
    root.with_suffix(".properties.ini").write_text(
        "burn_removed=T\nplik_foregrounds=T\n",
        encoding="utf-8",
    )


def _write_chain(path, parameter_count, rows=2):
    values = np.arange(
        1, rows * (parameter_count + 2) + 1, dtype=float
    ).reshape(rows, parameter_count + 2)
    values[:, 0] = np.arange(1, rows + 1, dtype=float)
    values[:, 1] = 1395.0 + np.arange(rows, dtype=float)
    np.savetxt(path, values)
    return values


def test_planck_chain_uses_paramnames_and_metadata(tmp_path):
    chain = tmp_path / "base_test_1.txt"
    root = tmp_path / "base_test"
    _write_base_metadata(root)
    _write_chain(chain, parameter_count=3)

    frame = load_planck_chain(source_path=chain)

    assert list(frame.columns) == [
        "weight", "minus_log_posterior", "a", "b", "c"
    ]
    assert frame.attrs["schema_source"] == "direct-paramnames"
    assert frame.attrs["properties"]["burn_removed"] is True


def test_planck_chain_can_use_declared_environment_path(tmp_path, monkeypatch):
    chain = tmp_path / "base_test_1.txt"
    root = tmp_path / "base_test"
    _write_base_metadata(root)
    _write_chain(chain, parameter_count=3)
    monkeypatch.setenv(PLANCK_CHAIN_ENV, str(chain))

    assert len(load_planck_chain()) == 2


def test_planck_chain_rejects_nonfinite_values(tmp_path):
    chain = tmp_path / "base_test_1.txt"
    root = tmp_path / "base_test"
    _write_base_metadata(root)
    values = _write_chain(chain, parameter_count=3)
    values[0, 2] = np.inf
    np.savetxt(chain, values)

    with pytest.raises(ValueError, match="Non-finite"):
        load_planck_chain(source_path=chain)


def test_planck_chain_rejects_nonpositive_weight(tmp_path):
    chain = tmp_path / "base_test_1.txt"
    root = tmp_path / "base_test"
    _write_base_metadata(root)
    values = _write_chain(chain, parameter_count=3)
    values[0, 0] = 0.0
    np.savetxt(chain, values)

    with pytest.raises(ValueError, match="weights"):
        load_planck_chain(source_path=chain)


def test_planck_chain_rejects_metadata_width_mismatch(tmp_path):
    chain = tmp_path / "base_test_1.txt"
    root = tmp_path / "base_test"
    _write_base_metadata(root, names=("a", "b"))
    _write_chain(chain, parameter_count=3)

    with pytest.raises(ValueError, match="defines 2 parameters"):
        load_planck_chain(source_path=chain)


def test_legacy_compressed_interpretation_is_rejected():
    with pytest.raises(RuntimeError, match="sample chain"):
        load_planck_compressed()
