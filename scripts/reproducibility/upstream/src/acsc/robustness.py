"""Ablation and robustness utilities with explicit reproducible seeds."""

import numpy as np


def _validated_coords(coords):
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2:
        raise ValueError("coords must be a 2D array")
    if not np.all(np.isfinite(arr)):
        raise ValueError("coords must contain only finite values")
    return arr


def subsample_stability(coords, fractions=(0.5, 0.75, 0.9), *, seed: int):
    """Return deterministic subsamples for a declared seed."""
    arr = _validated_coords(coords)
    rng = np.random.default_rng(int(seed))
    results = {}
    for frac in fractions:
        frac = float(frac)
        if not 0 < frac <= 1:
            raise ValueError("subsample fractions must lie in (0, 1]")
        n_keep = max(1, int(len(arr) * frac)) if len(arr) else 0
        if n_keep:
            idx = rng.choice(len(arr), n_keep, replace=False)
        else:
            idx = np.array([], dtype=int)
        results[f"frac_{frac}"] = arr[idx]
    return results


def gaussian_jitter_test(coords, sigma=0.01, n_trials=10, *, seed: int):
    """Return deterministic Gaussian-jitter realizations for a declared seed."""
    arr = _validated_coords(coords)
    sigma = float(sigma)
    if sigma < 0 or n_trials < 0:
        raise ValueError("sigma and n_trials must be non-negative")
    rng = np.random.default_rng(int(seed))
    return [
        arr + rng.normal(0.0, sigma, arr.shape)
        for _ in range(int(n_trials))
    ]
