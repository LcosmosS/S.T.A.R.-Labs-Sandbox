"""Null-model generation with explicit reproducible RNG state."""

import numpy as np


def generate_null_point_cloud(
    n_points: int,
    dimension: int = 3,
    *,
    seed: int,
) -> np.ndarray:
    """Generate a deterministic Gaussian null point cloud for a declared seed."""
    if n_points < 0 or dimension < 1:
        raise ValueError("n_points must be non-negative and dimension must be positive")
    rng = np.random.default_rng(int(seed))
    return rng.standard_normal((int(n_points), int(dimension)))


def compute_null_metric(null_cloud, metric_func):
    """Compute a declared metric on a null cloud."""
    return metric_func(null_cloud)
