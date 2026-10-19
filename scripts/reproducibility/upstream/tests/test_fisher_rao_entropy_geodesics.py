import math
import warnings

import numpy as np
import pytest

from src.entropy.fisher_rao_geodesics import FisherRaoEntropyGeodesics


def test_entropy_metric_is_positive_on_nonzero_simplex_tangent():
    model = FisherRaoEntropyGeodesics()
    p = np.array([0.2, 0.3, 0.5])
    u = np.array([0.1, -0.04, -0.06])

    value = model.metric_inner(p, u)

    assert value > 0.0


def test_square_root_embedding_is_an_isometry():
    model = FisherRaoEntropyGeodesics()
    p = np.array([0.2, 0.3, 0.5])
    u = np.array([0.01, -0.02, 0.01])

    sphere_tangent = model.tangent_embedding(p, u)
    fisher_norm_sq = model.metric_inner(p, u)

    assert np.dot(sphere_tangent, sphere_tangent) == pytest.approx(
        fisher_norm_sq,
        rel=1e-13,
        abs=1e-15,
    )


def test_weight_velocity_pushforward_is_tangent():
    model = FisherRaoEntropyGeodesics()
    x = np.array([1.0, 2.0, 3.0])
    v = np.array([0.1, -0.1, 0.05])

    p, u = model.weights_to_simplex(x, v)

    assert np.sum(p) == pytest.approx(1.0)
    assert np.sum(u) == pytest.approx(0.0, abs=1e-15)


def test_exact_geodesic_conserves_simplex_sphere_and_fisher_speed():
    model = FisherRaoEntropyGeodesics(step=0.01, invariant_tol=1e-11)

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = model.geodesic(
            np.array([1.0, 2.0, 3.0]),
            np.array([0.01, -0.02, 0.005]),
            steps=100,
        )

    assert result.probabilities.shape == (101, 3)
    assert np.all(result.probabilities > 0.0)
    assert np.allclose(
        np.sum(result.probabilities, axis=1),
        1.0,
        rtol=0.0,
        atol=1e-11,
    )
    assert np.max(result.fisher_speed_squared) - np.min(
        result.fisher_speed_squared
    ) < 1e-11
    assert result.diagnostics.max_simplex_error < 1e-11
    assert result.diagnostics.max_sphere_error < 4e-11
    assert result.diagnostics.max_speed_error < 1e-11
    assert result.diagnostics.terminated_at_boundary is False


def test_zero_velocity_produces_stationary_geodesic():
    model = FisherRaoEntropyGeodesics(step=0.2)
    p0 = np.array([0.2, 0.3, 0.5])
    u0 = np.zeros(3)

    result = model.geodesic_from_simplex(p0, u0, steps=5)

    assert np.allclose(result.probabilities, p0[None, :])
    assert np.allclose(result.tangent_velocities, 0.0)
    assert np.allclose(result.fisher_speed_squared, 0.0)
    assert math.isinf(result.diagnostics.boundary_time)
    assert result.diagnostics.terminated_at_boundary is False


def test_boundary_is_reported_and_not_crossed_or_clipped():
    model = FisherRaoEntropyGeodesics(step=0.5)
    p0 = np.array([0.5, 0.5])
    u0 = np.array([-0.5, 0.5])

    boundary_time = model.first_boundary_time(p0, u0)
    result = model.geodesic_from_simplex(p0, u0, steps=5)

    assert boundary_time == pytest.approx(math.pi / 2.0)
    assert result.diagnostics.boundary_time == pytest.approx(boundary_time)
    assert result.diagnostics.terminated_at_boundary is True
    assert result.times[-1] < boundary_time
    assert result.diagnostics.requested_end_time > boundary_time
    assert np.all(result.probabilities > 0.0)


def test_zero_weight_requires_explicit_pseudocount():
    unregularized = FisherRaoEntropyGeodesics(pseudocount=0.0)

    with pytest.raises(ValueError, match="pseudocount"):
        unregularized.weights_to_simplex(np.array([1.0, 0.0, 2.0]))


def test_explicit_pseudocount_interiorizes_zero_weight():
    model = FisherRaoEntropyGeodesics(pseudocount=1e-3)

    p = model.weights_to_simplex(np.array([1.0, 0.0, 2.0]))

    assert np.all(p > 0.0)
    assert np.sum(p) == pytest.approx(1.0)


def test_negative_raw_weights_are_rejected_even_with_pseudocount():
    model = FisherRaoEntropyGeodesics(pseudocount=10.0)

    with pytest.raises(ValueError, match="non-negative"):
        model.weights_to_simplex(np.array([1.0, -0.1, 2.0]))


def test_direct_simplex_velocity_must_be_tangent():
    model = FisherRaoEntropyGeodesics()
    p0 = np.array([0.2, 0.3, 0.5])

    with pytest.raises(ValueError, match="tangent"):
        model.geodesic_from_simplex(
            p0,
            np.array([0.1, 0.0, 0.0]),
            steps=1,
        )


def test_entropy_helper_rejects_unnormalized_positive_vector():
    model = FisherRaoEntropyGeodesics()

    with pytest.raises(ValueError, match="sum to 1"):
        model.entropy_of(np.array([2.0, 2.0]))
