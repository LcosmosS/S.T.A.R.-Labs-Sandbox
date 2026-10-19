from __future__ import annotations

from functools import lru_cache

import numpy as np
import sympy as sp
from scipy.integrate import quad


_PARAM_ALIASES = {"Ωm": "Om", "ΩΛ": "OL", "Ωb": "Ob"}


def _normalize_param_name(name: str) -> str:
    return _PARAM_ALIASES.get(name, name)


def _normalize_expression(expr: str) -> str:
    normalized = expr
    for original, replacement in _PARAM_ALIASES.items():
        normalized = normalized.replace(original, replacement)
    return normalized


class Cosmology:
    """Cosmology engine with a strict symbolic H(z)."""

    c = 299792.458

    def __init__(self, H_expr: str, params: dict):
        if not isinstance(H_expr, str) or not H_expr.strip():
            raise ValueError("H_expr must be a non-empty string")

        self.H_expr = H_expr.strip()
        self.params = {str(k): float(v) for k, v in (params or {}).items()}
        self.normalized_params = {}

        for key, value in self.params.items():
            normalized = _normalize_param_name(key)
            if (
                normalized in self.normalized_params
                and self.normalized_params[normalized] != value
            ):
                raise ValueError(f"Conflicting values supplied for parameter {normalized}")
            self.normalized_params[normalized] = value

        z_sym = sp.symbols("z")
        try:
            self.H_sym = sp.sympify(_normalize_expression(self.H_expr))
        except Exception as exc:
            raise ValueError(f"Failed to parse H_expr: {exc}") from exc

        required = {str(symbol) for symbol in self.H_sym.free_symbols if symbol != z_sym}
        missing = sorted(required - set(self.normalized_params))
        if missing:
            raise ValueError(f"H_expr references parameters with no value: {missing}")

        keys = tuple(sorted(required))
        symbols = tuple(sp.Symbol(key) for key in keys)
        self._parameter_keys = keys
        self.H_func = sp.lambdify((z_sym, *symbols), self.H_sym, modules="numpy")

    @staticmethod
    def _validate_redshift(z):
        if z is Ellipsis or isinstance(z, type(...)):
            raise TypeError("redshift cannot be Ellipsis")
        try:
            arr = np.asarray(z, dtype=float)
        except (TypeError, ValueError) as exc:
            raise TypeError("redshift must be numeric") from exc
        if not np.all(np.isfinite(arr)):
            raise ValueError("redshift must contain only finite values")
        if np.any(arr < 0):
            raise ValueError("redshift must be non-negative")
        return arr

    def H_of_z(self, z):
        """Evaluate H(z), requiring finite strictly positive output."""
        z_arr = self._validate_redshift(z)
        values = [self.normalized_params[key] for key in self._parameter_keys]
        try:
            evaluated = np.asarray(self.H_func(z_arr, *values), dtype=float)
        except Exception as exc:
            raise ValueError(f"Failed to evaluate H(z): {exc}") from exc

        if evaluated.ndim == 0 and z_arr.ndim > 0:
            evaluated = np.full(z_arr.shape, float(evaluated))
        if not np.all(np.isfinite(evaluated)):
            raise FloatingPointError("H(z) produced non-finite values")
        if np.any(evaluated <= 0):
            raise FloatingPointError("H(z) must be strictly positive")
        return float(evaluated) if evaluated.ndim == 0 else evaluated

    def H(self, z):
        return self.H_of_z(z)

    @lru_cache(maxsize=4096)
    def _comoving_scalar(self, zi: float) -> float:
        zi = float(zi)
        self._validate_redshift(zi)
        if zi == 0.0:
            return 0.0

        def integrand(zp):
            return self.c / float(self.H_of_z(zp))

        result, error = quad(
            integrand, 0.0, zi, limit=300, epsabs=1e-9, epsrel=1e-9
        )
        if not np.isfinite(result) or not np.isfinite(error):
            raise FloatingPointError("comoving-distance integration failed")
        if result < 0:
            raise FloatingPointError("comoving distance cannot be negative")
        return float(result)

    def comoving_distance(self, z):
        z_arr = self._validate_redshift(z)
        if z_arr.ndim == 0:
            return self._comoving_scalar(float(z_arr))
        flat = [self._comoving_scalar(float(zi)) for zi in z_arr.ravel()]
        return np.asarray(flat, dtype=float).reshape(z_arr.shape)

    def DM(self, z):
        return self.comoving_distance(z)

    def luminosity_distance(self, z):
        z_arr = self._validate_redshift(z)
        return self.comoving_distance(z_arr) * (1.0 + z_arr)

    def distance_modulus(self, z):
        dl = np.asarray(self.luminosity_distance(z), dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            mu = 5.0 * (np.log10(dl * 1e6) - 1.0)
        if np.any((dl < 0) | np.isnan(mu)):
            raise FloatingPointError("invalid luminosity distance in distance modulus")
        return float(mu) if mu.ndim == 0 else mu

    def mu(self, z):
        return self.distance_modulus(z)
