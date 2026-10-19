import numpy as np
from src.entropy.entropy_geodesics import EntropyGeodesics


def test_geodesic_runs():
    G = EntropyGeodesics()
    x0 = np.array([1.0, 2.0, 3.0])
    v0 = np.array([0.1, -0.1, 0.05])
    traj = G.geodesic(x0, v0, steps=10)
    assert traj.shape == (11, 3)
