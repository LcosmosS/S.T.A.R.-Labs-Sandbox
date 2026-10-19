"""
differential_forms.py
---------------------
Implements differential-form operations for the symbolic manifold:

- entropy 1-form θ = dM
- entropy 2-form ω = dθ
- wedge products
- exterior derivatives
"""

import numpy as np
from .entropy_field import EntropyField
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class DifferentialForms:
    """
    Differential form machinery for ECC.
    """

    def __init__(self, entropy_field=None):
        self.M = entropy_field if entropy_field else EntropyField()

    def one_form(self, x):
        """
        θ = dM
        """
        return self.M.gradient(x)

    def two_form(self, x):
        """
        ω = dθ = Hessian antisymmetrization.
        """
        H = self.M.hessian(x)
        return H - H.T

    def wedge(self, a, b):
        """
        Compute wedge product of two 1-forms.
        """
        n = len(a)
        W = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                W[i, j] = a[i] * b[j] - a[j] * b[i]
        return W

    def exterior_derivative(self, form):
        """
        Placeholder for general exterior derivative.
        """
        return form  # extended later for k-forms
