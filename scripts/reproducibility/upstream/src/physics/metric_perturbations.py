"""
metric_perturbations.py
-----------------------
Implements symbolic metric perturbations for the S.T.A.R. Model.

The metric perturbation is defined as:
δg_ij = α * ∂²M/∂x_i∂x_j + β * ω_ij

where:
- Hessian(M) encodes entropy curvature
- ω = dθ is the entropy flux 2-form

This module:
- computes δg_ij
- computes scalar perturbations Φ, Ψ
- computes symbolic power spectra
"""

import numpy as np
from ..entropy.entropy_field import EntropyField
from ..entropy.differential_forms import DifferentialForms
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class MetricPerturbations:
    """
    Computes symbolic metric perturbations δg_ij.
    """

    def __init__(self, alpha=0.01, beta=0.01):
        self.alpha = alpha
        self.beta = beta
        self.M = EntropyField()
        self.forms = DifferentialForms()

    def delta_g(self, x):
        """
        δg_ij = α * Hessian(M) + β * ω
        """
        H = self.M.hessian(x)
        omega = self.forms.two_form(x)
        return self.alpha * H + self.beta * omega

    def scalar_modes(self, x):
        """
        Compute symbolic scalar perturbations Φ and Ψ.
        """
        dg = self.delta_g(x)
        trace = np.trace(dg)
        phi = 0.5 * trace
        psi = -0.5 * trace
        return phi, psi

    def power_spectrum(self, X):
        """
        Compute symbolic power spectrum P(k) from δg_ij.
        """
        modes = []
        for x in X:
            phi, psi = self.scalar_modes(x)
            modes.append(phi + psi)

        modes = np.array(modes)
        fft = np.fft.rfft(modes)
        return np.abs(fft) ** 2
