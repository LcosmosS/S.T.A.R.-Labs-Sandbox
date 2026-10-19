"""
hubble_effective.py
-------------------
Implements the effective Hubble parameter H_eff(z) predicted by
the S.T.A.R. Model, combining ACSC projection geometry with
ECC entropy curvature.

H_eff(z) = H0 * <Ω_E * r>_z * (1 + α * C_entropy(z))
"""

import numpy as np
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class HubbleEffective:
    """
    Computes the scale-dependent effective Hubble parameter.
    """

    def __init__(self, H0=70.0, alpha=0.01):
        self.H0 = H0
        self.alpha = alpha

    def arithmetic_factor(self, invariants):
        """
        Compute <Ω_E * r> contribution from arithmetic invariants.
        invariants = dict with keys: 'omega', 'rank'
        """
        return invariants["omega"] * invariants["rank"]

    def entropy_correction(self, entropy_curvature):
        """
        Compute entropy curvature correction term C_entropy(z).
        """
        return np.tanh(entropy_curvature)

    def H_eff(self, z, invariants, entropy_curvature):
        """
        Compute the effective Hubble parameter at redshift z.
        """
        A = self.arithmetic_factor(invariants)
        C = self.entropy_correction(entropy_curvature)
        return self.H0 * A * (1 + self.alpha * C)
