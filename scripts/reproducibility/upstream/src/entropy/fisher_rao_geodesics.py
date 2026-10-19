"""Exact Fisher-Rao geodesics for the Shannon-entropy simplex.

Model: ECC-ENTROPY-GEODESIC-FR-v0.1

This module is an additive candidate stabilization treatment. It does not
replace the historical entropy_geodesics.py prototype and does not promote any
scientific claim or evidence status.

Mathematical definition
-----------------------
For p in the open probability simplex and tangent vectors u, v with zero sum,

    g_p(u, v) = sum_i u_i v_i / p_i

is the positive metric -D^2 S induced by Shannon entropy

    S(p) = -sum_i p_i log p_i.

The square-root map

    q_i = 2 sqrt(p_i)

is an isometry to the positive orthant of the sphere of radius 2. Geodesics are
therefore evaluated as exact great circles until the first simplex-boundary
contact. No Euler stepping, velocity clipping, or hidden coordinate flooring is
used.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


MODEL_ID = "ECC-ENTROPY-GEODESIC-FR-v0.1"


@dataclass(frozen=True)
class GeodesicDiagnostics:
    """Numerical and domain diagnostics for one exact geodesic evaluation."""

    model_id: str
    pseudocount: float
    requested_end_time: float
    returned_end_time: float
    boundary_time: float
    terminated_at_boundary: bool
    max_simplex_error: float
    max_sphere_error: float
    max_speed_error: float


@dataclass(frozen=True)
class EntropyGeodesicResult:
    """Structured result for a stabilized entropy-geodesic trajectory."""

    times: np.ndarray
    probabilities: np.ndarray
    tangent_velocities: np.ndarray
    entropy: np.ndarray
    fisher_speed_squared: np.ndarray
    diagnostics: GeodesicDiagnostics


class FisherRaoEntropyGeodesics:
    """Exact geodesics of the Shannon-entropy Fisher-Rao simplex."""

    model_id = MODEL_ID

    def __init__(
        self,
        *,
        step: float = 0.01,
        pseudocount: float = 0.0,
        invariant_tol: float = 1e-10,
    ):
        self.step = float(step)
        self.pseudocount = float(pseudocount)
        self.invariant_tol = float(invariant_tol)

        if not np.isfinite(self.step) or self.step <= 0:
            raise ValueError("step must be finite and strictly positive")
        if not np.isfinite(self.pseudocount) or self.pseudocount < 0:
            raise ValueError("pseudocount must be finite and non-negative")
        if not np.isfinite(self.invariant_tol) or self.invariant_tol <= 0:
            raise ValueError("invariant_tol must be finite and strictly positive")

    @staticmethod
    def _as_finite_vector(value, name: str) -> np.ndarray:
        arr = np.asarray(value, dtype=float)
        if arr.ndim != 1 or arr.size < 2:
            raise ValueError(f"{name} must be a one-dimensional vector of length >= 2")
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{name} must contain only finite values")
        return arr

    def _validate_simplex(self, p) -> np.ndarray:
        p = self._as_finite_vector(p, "p")
        if np.any(p <= 0):
            raise ValueError("p must lie in the open simplex: every component > 0")
        error = abs(float(np.sum(p)) - 1.0)
        if error > self.invariant_tol:
            raise ValueError(
                "p must sum to 1 within invariant_tol; "
                f"normalization error={error:.3e}"
            )
        return p

    def _validate_tangent(self, p: np.ndarray, u) -> np.ndarray:
        u = self._as_finite_vector(u, "u")
        if u.shape != p.shape:
            raise ValueError("u must have the same shape as p")
        tangent_error = abs(float(np.sum(u)))
        scale = max(1.0, float(np.linalg.norm(u)))
        if tangent_error > self.invariant_tol * scale:
            raise ValueError(
                "u must be tangent to the simplex: sum(u)=0 within tolerance; "
                f"error={tangent_error:.3e}"
            )
        return u

    def entropy_of(self, p) -> float:
        """Evaluate Shannon entropy only on a validated open-simplex state."""
        p = self._validate_simplex(p)
        return float(-np.sum(p * np.log(p)))

    def metric_matrix(self, p) -> np.ndarray:
        """Return diag(1/p), the positive metric -D^2 S in ambient coordinates."""
        p = self._validate_simplex(p)
        return np.diag(1.0 / p)

    def metric_inner(self, p, u, v=None) -> float:
        """Evaluate g_p(u,v) on simplex tangent vectors."""
        p = self._validate_simplex(p)
        u = self._validate_tangent(p, u)
        if v is None:
            v = u
        else:
            v = self._validate_tangent(p, v)
        return float(np.sum((u * v) / p))

    def weights_to_simplex(self, x, v=None):
        """Map raw nonnegative weights and velocity to simplex state and tangent.

        The optional pseudocount is explicit. With pseudocount=0, every raw
        weight must already be strictly positive. Negative weights are rejected
        for all pseudocount values.
        """
        x = self._as_finite_vector(x, "x")
        if np.any(x < 0):
            raise ValueError("raw entropy weights must be non-negative")

        adjusted = x + self.pseudocount
        if np.any(adjusted <= 0):
            raise ValueError(
                "raw weights must be strictly positive when pseudocount=0; "
                "declare pseudocount>0 explicitly to interiorize zero weights"
            )

        total = float(np.sum(adjusted))
        if not np.isfinite(total) or total <= 0:
            raise ValueError("normalized weight total must be finite and positive")

        p = adjusted / total

        if v is None:
            return p

        v = self._as_finite_vector(v, "v")
        if v.shape != x.shape:
            raise ValueError("v must have the same shape as x")

        u = (v - p * float(np.sum(v))) / total

        # Algebraically exact; this check guards implementation/numerical errors.
        tangent_error = abs(float(np.sum(u)))
        scale = max(1.0, float(np.linalg.norm(u)))
        if tangent_error > self.invariant_tol * scale:
            raise FloatingPointError(
                "weight-normalization pushforward failed tangent constraint"
            )
        return p, u

    def square_root_embedding(self, p) -> np.ndarray:
        """Map the open simplex isometrically to the positive radius-2 sphere."""
        p = self._validate_simplex(p)
        return 2.0 * np.sqrt(p)

    def tangent_embedding(self, p, u) -> np.ndarray:
        """Push a simplex tangent vector through the square-root embedding."""
        p = self._validate_simplex(p)
        u = self._validate_tangent(p, u)
        return u / np.sqrt(p)

    def first_boundary_time(self, p, u) -> float:
        """Return the first t>0 at which the great circle reaches q_i=0.

        The model is defined only on the positive orthant of the sphere, which
        corresponds to the open probability simplex. A return value of +inf
        denotes a stationary trajectory.
        """
        p = self._validate_simplex(p)
        u = self._validate_tangent(p, u)
        q0 = 2.0 * np.sqrt(p)
        w0 = u / np.sqrt(p)
        speed = float(np.linalg.norm(w0))

        if speed == 0.0:
            return math.inf

        b = 2.0 * w0 / speed
        roots = []
        for a_i, b_i in zip(q0, b):
            # q_i = a_i cos(theta) + b_i sin(theta), theta=speed*t/2.
            # atan2(-a_i, b_i) returns a root modulo pi. Because a_i>0,
            # the principal angle is non-positive; adding pi gives the first
            # strictly positive root.
            theta = math.atan2(-float(a_i), float(b_i))
            if theta <= 0.0:
                theta += math.pi
            roots.append(2.0 * theta / speed)

        return float(min(roots))

    def geodesic_from_simplex(self, p0, u0, *, steps: int = 100) -> EntropyGeodesicResult:
        """Evaluate the exact Fisher-Rao geodesic on a regular time grid."""
        if isinstance(steps, bool) or int(steps) != steps or steps < 0:
            raise ValueError("steps must be a non-negative integer")
        steps = int(steps)

        p0 = self._validate_simplex(p0)
        u0 = self._validate_tangent(p0, u0)

        q0 = 2.0 * np.sqrt(p0)
        w0 = u0 / np.sqrt(p0)
        speed = float(np.linalg.norm(w0))
        speed_sq = speed * speed

        boundary_time = self.first_boundary_time(p0, u0)
        requested_times = np.arange(steps + 1, dtype=float) * self.step

        if math.isfinite(boundary_time):
            # Stay strictly inside the chart; do not include or cross a metric
            # singularity. nextafter avoids treating a rounded boundary value
            # as interior.
            interior_limit = np.nextafter(boundary_time, 0.0)
            mask = requested_times < interior_limit
            times = requested_times[mask]
            terminated = len(times) < len(requested_times)
        else:
            times = requested_times
            terminated = False

        if times.size == 0:
            # t=0 is always an interior point for a validated p0.
            raise FloatingPointError("no valid interior time samples were produced")

        if speed == 0.0:
            q = np.repeat(q0[None, :], len(times), axis=0)
            w = np.zeros_like(q)
        else:
            theta = 0.5 * speed * times
            cos_theta = np.cos(theta)[:, None]
            sin_theta = np.sin(theta)[:, None]
            q = cos_theta * q0[None, :] + (2.0 / speed) * sin_theta * w0[None, :]
            w = (
                -(speed / 2.0) * sin_theta * q0[None, :]
                + cos_theta * w0[None, :]
            )

        if not np.all(np.isfinite(q)) or not np.all(np.isfinite(w)):
            raise FloatingPointError("exact geodesic evaluation produced non-finite values")
        if np.any(q <= 0):
            raise FloatingPointError(
                "geodesic left the positive square-root chart before reported boundary"
            )

        probabilities = 0.25 * q * q
        tangent_velocities = 0.5 * q * w

        entropy = -np.sum(probabilities * np.log(probabilities), axis=1)
        fisher_speed_squared = np.sum(
            (tangent_velocities * tangent_velocities) / probabilities,
            axis=1,
        )

        simplex_error = np.abs(np.sum(probabilities, axis=1) - 1.0)
        sphere_error = np.abs(np.sum(q * q, axis=1) - 4.0)
        speed_error = np.abs(fisher_speed_squared - speed_sq)

        max_simplex_error = float(np.max(simplex_error))
        max_sphere_error = float(np.max(sphere_error))
        max_speed_error = float(np.max(speed_error))

        if max_simplex_error > self.invariant_tol:
            raise FloatingPointError(
                f"simplex invariant drifted by {max_simplex_error:.3e}"
            )
        if max_sphere_error > 4.0 * self.invariant_tol:
            raise FloatingPointError(
                f"sphere invariant drifted by {max_sphere_error:.3e}"
            )
        if max_speed_error > self.invariant_tol * max(1.0, speed_sq):
            raise FloatingPointError(
                f"Fisher-speed invariant drifted by {max_speed_error:.3e}"
            )

        diagnostics = GeodesicDiagnostics(
            model_id=self.model_id,
            pseudocount=self.pseudocount,
            requested_end_time=float(requested_times[-1]),
            returned_end_time=float(times[-1]),
            boundary_time=float(boundary_time),
            terminated_at_boundary=terminated,
            max_simplex_error=max_simplex_error,
            max_sphere_error=max_sphere_error,
            max_speed_error=max_speed_error,
        )

        return EntropyGeodesicResult(
            times=times,
            probabilities=probabilities,
            tangent_velocities=tangent_velocities,
            entropy=entropy,
            fisher_speed_squared=fisher_speed_squared,
            diagnostics=diagnostics,
        )

    def geodesic(self, x0, v0, *, steps: int = 100) -> EntropyGeodesicResult:
        """Normalize raw weights, push forward v0, and evaluate the exact geodesic."""
        p0, u0 = self.weights_to_simplex(x0, v0)
        return self.geodesic_from_simplex(p0, u0, steps=steps)
