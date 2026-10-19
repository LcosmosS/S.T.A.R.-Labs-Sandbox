"""Behavioral tests for production ACSC statistics."""

import numpy as np
import pytest

from src.acsc.statistics import effect_size, empirical_p_value, w2_between_diagrams


def test_empirical_p_value_has_finite_sample_correction():
    assert empirical_p_value(1.0, [0.5, 2.0, 3.0]) == pytest.approx(0.5)


def test_effect_size_direction_is_documented():
    value = effect_size(1.0, [2.0, 3.0, 4.0])
    assert value > 0


def test_statistics_reject_nonfinite_nulls():
    with pytest.raises(ValueError, match="finite"):
        empirical_p_value(1.0, [1.0, np.nan])


def test_cardinality_diagnostic_remains_explicitly_lightweight():
    assert w2_between_diagrams([[0.0, 1.0]], [[0.0, 1.0], [0.2, 0.7]]) == 1.0
