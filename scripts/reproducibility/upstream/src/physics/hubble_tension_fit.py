"""
hubble_tension_fit.py
---------------------
Implements a scale-dependent Hubble tension fitting routine for the
S.T.A.R. Model. Combines:

- ACSC arithmetic projection factors
- ECC entropy curvature corrections
- S.T.A.R. effective Hubble parameter H_eff(z)
- observational datasets (local vs CMB)

This module provides:
- model prediction H_eff(z)
- residual computation
- χ² minimization
- tension quantification
"""

import numpy as np
from .hubble_effective import HubbleEffective
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class HubbleTensionFit:
    """
    Fits the S.T.A.R. Model to local and CMB Hubble measurements.
    """

    def __init__(self, H0_local=73.0, H0_cmb=67.4):
        self.H0_local = H0_local
        self.H0_cmb = H0_cmb
        self.model = HubbleEffective()

    def model_prediction(self, z, invariants, entropy_curvature):
        """
        Compute H_eff(z) from the S.T.A.R. Model.
        """
        return self.model.H_eff(z, invariants, entropy_curvature)

    def residuals(self, z_values, invariants_list, entropy_curvatures, observed):
        """
        Compute residuals H_eff(z) - H_obs(z).
        """
        preds = [
            self.model_prediction(z, inv, curv)
            for z, inv, curv in zip(z_values, invariants_list, entropy_curvatures)
        ]
        return np.array(preds) - np.array(observed)

    def chi_squared(self, residuals, sigma):
        """
        χ² = Σ (residual / σ)^2
        """
        return np.sum((residuals / sigma) ** 2)

    def tension(self, H_eff_local, H_eff_cmb):
        """
        Quantify tension between local and CMB predictions.
        """
        return abs(H_eff_local - H_eff_cmb)

    def fit(self, z_local, z_cmb, inv_local, inv_cmb, curv_local, curv_cmb):
        """
        Compute S.T.A.R. predictions and tension.
        """
        H_local = self.model_prediction(z_local, inv_local, curv_local)
        H_cmb = self.model_prediction(z_cmb, inv_cmb, curv_cmb)
        return {
            "H_eff_local": H_local,
            "H_eff_cmb": H_cmb,
            "tension": self.tension(H_local, H_cmb),
        }
