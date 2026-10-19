"""Off-path arithmetic/graph/null verification; synthetic inputs only."""
import importlib.util
from pathlib import Path

import pytest

from src.diagnostics import a03_reference as reference


def test_symbolic_discriminant_identity():
    """Check the exact symbolic equality of both discriminant formulas."""
    reference.symbolic_identity()


def test_reference_algorithms_agree_on_synthetic_inputs():
    """Check all three synthetic fixtures and PRNG rejection boundary."""
    result = reference.fixture_checks()
    assert len(result["fixtures"]) == 3
    assert result["rejection_boundary_checked"] is True


def test_reference_detects_bad_graph(monkeypatch):
    """Require a synthetic brute-force graph mismatch to fail closed."""
    monkeypatch.setattr(reference.production, "mcj_neighbor_edges", lambda frame: reference.np.zeros((1, 2), dtype=int))
    with pytest.raises(ValueError, match="brute-force graph mismatch"):
        reference.fixture_checks()


def test_reference_detects_bad_null_stream(monkeypatch):
    """Reject deliberately incorrect synthetic null-statistic output."""
    monkeypatch.setattr(reference.production, "_null_statistics_core", lambda *args, **kwargs: reference.np.zeros(3))
    with pytest.raises(ValueError, match="three-draw null disagrees"):
        reference.fixture_checks()


def test_brute_force_reference_refuses_actual_cohort_sized_input():
    """Reject oversized input before graph construction or data access."""
    with pytest.raises(ValueError, match="restricted to synthetic fixtures"):
        reference.reference_edges([None] * 65)


def test_singular_arithmetic_fails_reference():
    """Reject singular curve invariants instead of dividing by zero."""
    with pytest.raises(ValueError, match="singular reference curve"):
        reference.reference_invariants([0, 0, 0, 0, 0])
