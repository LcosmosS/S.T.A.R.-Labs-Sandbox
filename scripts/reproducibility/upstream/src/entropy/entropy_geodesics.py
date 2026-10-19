"""
entropy_geodesics.py
--------------------
Implements entropy geodesics for the S.T.A.R. Model.

Geodesics follow:
d²x^k/dt² + Γ^k_ij (dx^i/dt)(dx^j/dt) = 0

where Γ^k_ij are derived from the entropy Hessian metric:
g_ij = ∂²M / ∂x_i ∂x_j
"""

import numpy as np
from .entropy_field import EntropyField
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class EntropyGeodesics:
    """
    Computes symbolic entropy geodesics on the manifold M_symbolic.
    """

    def __init__(self, entropy_field=None, step=0.01):
        self.M = entropy_field if entropy_field else EntropyField()
        self.step = step

    def metric(self, x):
        """
        g_ij = Hessian of entropy.
        """
        return self.M.hessian(x)

    def christoffel(self, x):
        """
        Compute Christoffel symbols Γ^k_ij.
        """
        H = self.metric(x)
        g_inv = np.linalg.pinv(H + np.eye(len(x)) * 1e-6)

        n = len(x)
        Gamma = np.zeros((n, n, n))

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    Gamma[k, i, j] = 0.5 * np.sum(
                        g_inv[k, :] * (H[:, i] + H[:, j] - H[i, j])
                    )
        return Gamma

    def geodesic_step(self, x, v):
        """
        Perform one geodesic integration step.
        """
        Gamma = self.christoffel(x)
        accel = np.zeros_like(x)

        for k in range(len(x)):
            accel[k] = -np.sum(Gamma[k] * np.outer(v, v))

        x_new = x + self.step * v
        v_new = v + self.step * accel
        return x_new, v_new

    def geodesic(self, x0, v0, steps=100):
        """
        Compute a full geodesic trajectory.
        """
        x = np.array(x0, dtype=float)
        v = np.array(v0, dtype=float)

        trajectory = [x.copy()]

        for _ in range(steps):
            x, v = self.geodesic_step(x, v)
            trajectory.append(x.copy())

        return np.array(trajectory)
