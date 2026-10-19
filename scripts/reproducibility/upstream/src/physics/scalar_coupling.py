"""
scalar_coupling.py
------------------
Implements the arithmetic–entropy scalar field coupling used in the
S.T.A.R. Model.

The scalar field φ obeys:
□φ = α * ρ_arith + β * K_entropy

This module computes:
- arithmetic density ρ_arith
- entropy curvature source term
- scalar field evolution (toy model)
"""

import numpy as np
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class ScalarCoupling:
    """
    Computes scalar-field coupling terms for ACSC + ECC.
    """

    def __init__(self, alpha=0.01, beta=0.01, mass=1e-3):
        self.alpha = alpha
        self.beta = beta
        self.mass = mass

    def arithmetic_density(self, invariants):
        """
        ρ_arith = Ω_E * r / (1 + log N)
        """
        omega = invariants["omega"]
        rank = invariants["rank"]
        N = invariants["conductor"]
        return (omega * rank) / (1 + np.log(1 + N))

    def entropy_source(self, entropy_curvature):
        """
        Source term from entropy curvature.
        """
        return np.tanh(entropy_curvature)

    def scalar_field(self, invariants, entropy_curvature):
        """
        φ = α * ρ_arith + β * entropy_source - m^2 φ (toy model)
        """
        rho = self.arithmetic_density(invariants)
        S = self.entropy_source(entropy_curvature)
        return self.alpha * rho + self.beta * S - self.mass**2
