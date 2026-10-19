"""
entropy_potential.py
--------------------
Defines the entropy potential V_entropy(x) for the S.T.A.R. Model.

The entropy potential is defined as:
V_entropy(x) = |∇M(x)|² + λ * Tr(Hessian(M(x)))

This module:
- computes entropy potential
- computes symbolic force fields
- supports entropy-driven dynamics
"""

import numpy as np
from .entropy_field import EntropyField
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class EntropyPotential:
    """
    Computes entropy potential and symbolic force fields.
    """

    def __init__(self, lambda_coeff=0.1):
        self.lambda_coeff = lambda_coeff
        self.M = EntropyField()

    def potential(self, x):
        """
        V_entropy = |∇M|² + λ * Tr(Hessian)
        """
        grad = self.M.gradient(x)
        H = self.M.hessian(x)
        return np.dot(grad, grad) + self.lambda_coeff * np.trace(H)

    def force(self, x):
        """
        Symbolic force field:
        F = -∇V_entropy
        """
        eps = 1e-6
        n = len(x)
        F = np.zeros(n)

        for i in range(n):
            x_forward = x.copy()
            x_backward = x.copy()
            x_forward[i] += eps
            x_backward[i] -= eps

            V_forward = self.potential(x_forward)
            V_backward = self.potential(x_backward)

            F[i] = -(V_forward - V_backward) / (2 * eps)

        return F

    def flow(self, x, steps=50, step_size=0.01):
        """
        Integrate symbolic entropy flow under the potential.
        """
        trajectory = [x.copy()]
        for _ in range(steps):
            F = self.force(x)
            x = x + step_size * F
            trajectory.append(x.copy())
        return np.array(trajectory)
