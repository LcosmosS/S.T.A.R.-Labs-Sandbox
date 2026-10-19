"""Tests for fail-closed scientific runtime behavior."""

import builtins

import numpy as np
import pytest

from src.tda import persistence


def test_persistence_does_not_manufacture_placeholder_diagrams(monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        root = name.split(".", 1)[0]
        if root in {"ripser", "gudhi"}:
            raise ImportError(f"blocked optional dependency: {root}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    points = np.array([[101.0, 0.0], [102.0, 1.0], [103.0, 0.0]])
    with pytest.raises(RuntimeError, match="placeholder diagrams are forbidden"):
        persistence.compute_persistence(points, max_dim=1)


def test_persistence_rejects_nonfinite_input_before_backend_selection():
    points = np.array([[0.0, 0.0], [np.nan, 1.0]])
    with pytest.raises(ValueError, match="finite"):
        persistence.compute_persistence(points, max_dim=1)


def test_gudhi_fallback_uses_declared_edge_threshold(monkeypatch):
    original_import = builtins.__import__

    def block_ripser(name, *args, **kwargs):
        if name.split(".", 1)[0] == "ripser":
            raise ImportError("force GUDHI fallback")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block_ripser)
    points = np.array(
        [[11.0, 0.0], [11.2, 0.0], [12.0, 0.0], [12.2, 0.0]]
    )
    result = persistence.compute_persistence(
        points,
        max_dim=1,
        max_edge_length=0.37,
    )

    assert result["backend"] == "gudhi"
    assert result["max_edge_length"] == pytest.approx(0.37)
