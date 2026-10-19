"""Deterministic arithmetic-to-coordinate projection primitives."""

from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd


def _safe_log10(x, floor=1.0):
    x = np.asarray(x, dtype=float)
    out = np.empty_like(x)
    mask = ~np.isfinite(x) | (x == 0)
    out[mask] = np.log10(float(floor))
    out[~mask] = np.log10(np.abs(x[~mask]))
    return out


def _scale_to_range(arr, out_min, out_max, *, bounds=None):
    arr = np.asarray(arr, dtype=float)
    if arr.size == 0:
        return arr
    if bounds is None:
        mn, mx = np.nanmin(arr), np.nanmax(arr)
    else:
        if len(bounds) != 2:
            raise ValueError("normalization bounds must be (min, max)")
        mn, mx = map(float, bounds)
    if not np.isfinite(mn) or not np.isfinite(mx) or mn >= mx:
        if bounds is not None:
            raise ValueError("fixed normalization bounds must be finite with min < max")
        return np.full_like(arr, 0.5 * (out_min + out_max))
    return out_min + (arr - mn) / (mx - mn) * (out_max - out_min)


def _saturating_rank_map(ranks, v0=1.0):
    if v0 <= 0:
        raise ValueError("V0 must be positive")
    r = np.asarray(ranks, dtype=float)
    if not np.all(np.isfinite(r)):
        raise ValueError("rank values must be finite")
    if np.any(r < 0):
        raise ValueError("rank values must be non-negative")
    return np.clip(np.arctan(r / float(v0)) / (0.5 * np.pi), 0.0, 1.0)


def project(
    records: Sequence[Dict[str, Any]],
    method="primary",
    Amax=1.0,
    Nmax=1.0,
    V0=1.0,
    *,
    normalization_bounds: Mapping[str, Sequence[float]] | None = None,
):
    """Project arithmetic records deterministically into R^3."""
    if records is None:
        return np.zeros((0, 3), dtype=float)
    df = pd.DataFrame.from_records(records)
    if df.empty:
        return np.zeros((0, 3), dtype=float)

    for col in ("delta", "conductor", "rank"):
        if col not in df:
            raise KeyError(f"arithmetic record missing required field: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if not np.all(np.isfinite(df["delta"])) or np.any(df["delta"] == 0):
        raise ValueError("delta must contain finite non-zero values")
    if not np.all(np.isfinite(df["conductor"])) or np.any(df["conductor"] <= 0):
        raise ValueError("conductor must contain finite positive values")

    bounds = dict(normalization_bounds or {})
    x = _scale_to_range(
        _safe_log10(df["delta"].to_numpy()),
        0.0,
        float(Amax),
        bounds=bounds.get("delta_log10"),
    )
    y = _scale_to_range(
        _safe_log10(df["conductor"].to_numpy()),
        0.0,
        float(Nmax),
        bounds=bounds.get("conductor_log10"),
    )
    z = _saturating_rank_map(df["rank"].to_numpy(), float(V0)) * float(V0)
    return np.column_stack([x, y, z])


class ArithmeticProjector:
    def __init__(
        self,
        method="primary",
        Amax=1.0,
        Nmax=1.0,
        V0=1.0,
        *,
        normalization_bounds=None,
    ):
        self.method = method
        self.Amax = Amax
        self.Nmax = Nmax
        self.V0 = V0
        self.normalization_bounds = normalization_bounds

    def project(self, records):
        return project(
            records,
            self.method,
            self.Amax,
            self.Nmax,
            self.V0,
            normalization_bounds=self.normalization_bounds,
        )

    def embed_to_cosmic(self, coords, seed=0, noise_scale=0.0, depth_scale=1.8):
        embedded = np.asarray(coords, dtype=float).copy()
        if noise_scale:
            rng = np.random.default_rng(int(seed))
            embedded += rng.normal(0.0, noise_scale, embedded.shape)
        if embedded.ndim == 2 and embedded.shape[1] >= 3:
            embedded[:, 2] *= float(depth_scale)
        return embedded
