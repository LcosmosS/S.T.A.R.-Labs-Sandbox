import numpy as np
from src.entropy.differential_forms import DifferentialForms


def test_two_form_antisymmetry():
    D = DifferentialForms()
    x = np.array([1.0, 2.0, 3.0])
    omega = D.two_form(x)
    assert np.allclose(omega, -omega.T)
