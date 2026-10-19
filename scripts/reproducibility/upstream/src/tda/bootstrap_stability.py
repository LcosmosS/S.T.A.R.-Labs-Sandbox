"""Seeded bootstrap stability utilities for S.T.A.R. TDA."""

import numpy as np

from .persistence_landscape import PersistenceLandscape
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class BootstrapStability:
    """Bootstrap persistence landscapes with an explicit private RNG."""

    def __init__(self, num_bootstrap=50, resolution=200, *, seed: int = 0):
        self.num_bootstrap = int(num_bootstrap)
        self.seed = int(seed)
        if self.num_bootstrap < 1:
            raise ValueError("num_bootstrap must be positive")
        self.rng = np.random.default_rng(self.seed)
        self.landscape = PersistenceLandscape(resolution=resolution)

    def resample(self, X):
        """Bootstrap-resample a point cloud reproducibly."""
        X = np.asarray(X)
        if X.ndim != 2 or len(X) == 0:
            raise ValueError("X must be a non-empty 2D array")
        idx = self.rng.choice(len(X), len(X), replace=True)
        return X[idx]

    def compute_landscape(self, barcodes):
        return self.landscape.landscape(barcodes)

    def bootstrap_landscapes(self, barcode_fn, X):
        landscapes = []
        for _ in range(self.num_bootstrap):
            X_resampled = self.resample(X)
            barcodes = barcode_fn(X_resampled)
            landscapes.append(self.compute_landscape(barcodes))
        return landscapes

    def average_landscape(self, landscapes):
        return np.mean(np.asarray(landscapes), axis=0)

    def landscape_variance(self, landscapes):
        return np.var(np.asarray(landscapes), axis=0)
