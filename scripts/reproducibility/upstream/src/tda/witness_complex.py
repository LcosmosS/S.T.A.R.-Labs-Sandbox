"""Deterministic witness-complex utilities for S.T.A.R. TDA."""

import numpy as np
from scipy.spatial.distance import cdist

from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class WitnessComplex:
    """Build a witness complex with an explicit private random stream."""

    def __init__(self, num_landmarks=20, *, seed: int = 0):
        self.num_landmarks = int(num_landmarks)
        self.seed = int(seed)
        if self.num_landmarks < 1:
            raise ValueError("num_landmarks must be positive")
        self.rng = np.random.default_rng(self.seed)

    def select_landmarks(self, X):
        """Select landmark points reproducibly."""
        X = np.asarray(X)
        if X.ndim != 2 or len(X) == 0:
            raise ValueError("X must be a non-empty 2D array")
        if self.num_landmarks > len(X):
            raise ValueError("num_landmarks cannot exceed the number of points")
        idx = self.rng.choice(len(X), self.num_landmarks, replace=False)
        return X[idx]

    def assign_witnesses(self, X, L):
        """Assign each point in X to its nearest landmark."""
        D = cdist(X, L)
        return np.argmin(D, axis=1)

    def build_complex(self, X):
        """Construct the witness complex (0- and 1-simplices)."""
        X = np.asarray(X)
        L = self.select_landmarks(X)
        W = self.assign_witnesses(X, L)

        edges = set()
        for i in range(len(X)):
            for j in range(i + 1, len(X)):
                if W[i] == W[j]:
                    edges.add((i, j))

        return {"landmarks": L, "edges": sorted(edges)}
