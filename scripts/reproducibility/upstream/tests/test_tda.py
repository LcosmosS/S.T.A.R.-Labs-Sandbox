"""Behavioral tests for the production ACSC TDA pipeline."""

import numpy as np
import pytest

from src.acsc.tda_pipeline import compute_persistence, persistence_wasserstein


def test_compute_persistence_uses_production_pipeline():
    pytest.importorskip("gudhi")
    points = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    result = compute_persistence(points, maxdim=1, thresh=2.0)
    assert set(result) == {"dgms"}
    assert len(result["dgms"]) == 2


def test_wasserstein_is_zero_for_identical_finite_diagrams():
    pytest.importorskip("gudhi")
    pytest.importorskip("ot")
    diagram = np.array([[0.0, 1.0], [0.2, 0.8]])
    assert persistence_wasserstein(diagram, diagram) == pytest.approx(0.0)


def test_compute_persistence_rejects_non_matrix_input():
    with pytest.raises(ValueError, match="2D"):
        compute_persistence(np.array([0.0, 1.0]), maxdim=1)
