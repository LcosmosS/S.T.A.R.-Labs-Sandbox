"""Strict symbolic-cosmology adapter used by controlled inference."""

from __future__ import annotations

import numpy as np
import sympy as sp

from src.physics.cosmology import Cosmology


class SymbolicCosmology:
    def __init__(self, H_expr, params):
        if isinstance(H_expr, sp.Expr):
            H_expr = str(H_expr)
        self.H_expr = str(H_expr)
        self.params = {str(k): float(v) for k, v in params.items()}
        self.cosmo = Cosmology(self.H_expr, self.params)

    def _required_param(self, *names):
        for name in names:
            if name in self.params:
                return float(self.params[name])
        raise KeyError(f"required cosmology parameter missing; expected one of {names}")

    def H(self, z):
        return self.cosmo.H_of_z(z)

    def H_of_z(self, z):
        return self.cosmo.H_of_z(z)

    def H0(self):
        return self._required_param("H0")

    def ombh2(self):
        h = self.H0() / 100.0
        omb = self._required_param("Ωb", "Ob")
        return omb * h**2

    def sound_horizon(self):
        value = self._required_param("r_s", "rs", "sound_horizon")
        if not np.isfinite(value) or value <= 0:
            raise ValueError("sound horizon must be finite and positive")
        return value

    def R(self):
        om = self._required_param("Ωm", "Om")
        if om <= 0:
            raise ValueError("Ωm must be positive for the shift parameter")
        return (
            np.sqrt(om)
            * self.H0()
            * self.comoving_distance(1089.0)
            / self.cosmo.c
        )

    def lA(self):
        return np.pi * self.comoving_distance(1089.0) / self.sound_horizon()

    def comoving_distance(self, z):
        return self.cosmo.comoving_distance(z)

    def DM(self, z):
        return self.cosmo.DM(z)

    def luminosity_distance(self, z):
        return self.cosmo.luminosity_distance(z)

    def distance_modulus(self, z):
        return self.cosmo.distance_modulus(z)

    def mu(self, z):
        return self.distance_modulus(z)

    def __getattr__(self, name):
        return getattr(self.cosmo, name)
