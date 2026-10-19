"""Tests for the public ACSC projection API."""

import numpy as np
import pytest

from src.acsc.projection import ArithmeticProjector, project


def test_project_exercises_production_api():
    records = [{"delta": -11, "conductor": 11, "rank": 0}]
    coords = project(records)
    assert coords.shape == (1, 3)
    assert np.isfinite(coords).all()


def test_embedding_is_reproducible_and_default_deterministic():
    records = [{"delta": -11, "conductor": 11, "rank": 1}]
    projector = ArithmeticProjector()
    base = projector.project(records)
    deterministic = projector.embed_to_cosmic(base)
    assert np.array_equal(deterministic, projector.embed_to_cosmic(base))
    noisy = projector.embed_to_cosmic(base, seed=7, noise_scale=0.05)
    assert np.array_equal(
        noisy,
        projector.embed_to_cosmic(base, seed=7, noise_scale=0.05),
    )
    assert not np.array_equal(noisy, deterministic)


def test_fixed_bounds_make_coordinate_independent_of_companion_records():
    bounds = {
        "delta_log10": (0.0, 4.0),
        "conductor_log10": (0.0, 4.0),
    }
    e1 = {"delta": -11, "conductor": 11, "rank": 1}
    e2 = {"delta": -37, "conductor": 37, "rank": 2}
    e3 = {"delta": -101, "conductor": 101, "rank": 0}

    pair = project([e1, e2], normalization_bounds=bounds)
    triple = project([e1, e2, e3], normalization_bounds=bounds)
    assert np.allclose(pair[0], triple[0])
    assert np.allclose(pair[1], triple[1])


def test_projection_rejects_missing_or_invalid_arithmetic_inputs():
    with pytest.raises(KeyError, match="rank"):
        project([{"delta": -11, "conductor": 11}])
    with pytest.raises(ValueError, match="conductor"):
        project([{"delta": -11, "conductor": 0, "rank": 0}])
