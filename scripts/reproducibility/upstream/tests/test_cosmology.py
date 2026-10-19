"""Strict cosmology regression tests."""

import numpy as np
import pytest

from src.physics.cosmology import Cosmology
from src.physics.symbolic_cosmology import SymbolicCosmology


LCDM = "H0*sqrt(Ωm*(1+z)**3 + ΩΛ)"
PARAMS = {"H0": 70, "Ωm": 0.3, "ΩΛ": 0.7}


def test_lcdm_basic():
    lcdm = Cosmology(LCDM, PARAMS)
    assert lcdm.H_of_z(0) == pytest.approx(70.0)


def test_distance_monotonicity_including_zero():
    lcdm = Cosmology(LCDM, PARAMS)
    z = np.linspace(0, 2, 50)
    d = lcdm.comoving_distance(z)
    assert d[0] == pytest.approx(0.0)
    assert np.all(np.diff(d) > 0)


def test_symbolic_model_uses_strict_engine():
    star = SymbolicCosmology(
        "H0*sqrt(Ωm*(1+z)**3 + ΩΛ + a*z)",
        {"H0": 70, "Ωm": 0.3, "ΩΛ": 0.7, "a": -0.05},
    )
    assert star.H(0) > 0
    assert star.distance_modulus(0.5) > 0


@pytest.mark.parametrize("bad_z", [Ellipsis, np.nan, np.inf, -0.01])
def test_invalid_redshift_is_rejected_instead_of_replaced(bad_z):
    lcdm = Cosmology(LCDM, PARAMS)
    with pytest.raises((TypeError, ValueError)):
        lcdm.comoving_distance(bad_z)


def test_nonpositive_hubble_model_fails_fast():
    model = Cosmology("H0*(1-z)", {"H0": 70})
    with pytest.raises(FloatingPointError, match="strictly positive"):
        model.H_of_z(2.0)


def test_planck_auxiliary_parameters_are_explicit():
    model = SymbolicCosmology(LCDM, PARAMS)
    with pytest.raises(KeyError, match="required cosmology parameter"):
        model.ombh2()
    with pytest.raises(KeyError, match="required cosmology parameter"):
        model.sound_horizon()
