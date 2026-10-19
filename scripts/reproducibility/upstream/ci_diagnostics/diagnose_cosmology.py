"""Fail-fast cosmology smoke diagnostics for CI."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.physics.cosmology import Cosmology
from src.physics.symbolic_cosmology import SymbolicCosmology


def _check_hubble(model, name, zgrid):
    hz = np.asarray(model.H_of_z(zgrid), dtype=float)
    if hz.shape != zgrid.shape:
        raise AssertionError(f"{name}: H(z) returned shape {hz.shape}, expected {zgrid.shape}")
    if not np.all(np.isfinite(hz)):
        raise AssertionError(f"{name}: H(z) contains non-finite values")
    if np.any(hz <= 0):
        raise AssertionError(f"{name}: H(z) contains non-positive values")
    print(f"{name}: H(z) finite and positive on diagnostic grid")


def _check_distances(model, name, zgrid):
    for zi in zgrid:
        dc = float(model.comoving_distance(float(zi)))
        dl = float(model.luminosity_distance(float(zi)))
        if not np.isfinite(dc) or not np.isfinite(dl):
            raise AssertionError(
                f"{name}: non-finite distance at z={zi}: Dc={dc}, DL={dl}"
            )
        if zi == 0.0:
            if dc != 0.0 or dl != 0.0:
                raise AssertionError(
                    f"{name}: distances at z=0 must be exactly zero; Dc={dc}, DL={dl}"
                )
        elif dc <= 0 or dl <= 0:
            raise AssertionError(
                f"{name}: positive redshift requires positive distances at z={zi}; "
                f"Dc={dc}, DL={dl}"
            )
    print(f"{name}: distances valid on diagnostic grid")


def run():
    lcdm = Cosmology(
        "H0*sqrt(Ωm*(1+z)**3 + ΩΛ)",
        {"H0": 70, "Ωm": 0.3, "ΩΛ": 0.7},
    )
    star = SymbolicCosmology(
        "H0*sqrt(Ωm*(1+z)**3 + ΩΛ + a*z + b*z**2)",
        {"H0": 70, "Ωm": 0.3, "ΩΛ": 0.7, "a": -0.05, "b": 0.01},
    )

    zgrid = np.linspace(0.0, 2.0, 201)
    _check_hubble(lcdm, "lcdm", zgrid)
    _check_hubble(star, "star", zgrid)
    _check_distances(lcdm, "lcdm", zgrid)
    _check_distances(star, "star", zgrid)
    print("cosmology diagnostics passed")


if __name__ == "__main__":
    run()
