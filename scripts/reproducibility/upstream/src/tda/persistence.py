"""Fail-closed persistence computation for current S.T.A.R. code."""

from __future__ import annotations

import numpy as np

_persistence_cache = {}


def _validate_point_cloud(point_cloud, max_dim, max_edge_length):
    points = np.asarray(point_cloud, dtype=float)
    if points.ndim != 2:
        raise ValueError("point_cloud must be a 2D array")
    if points.shape[0] == 0 or points.shape[1] == 0:
        raise ValueError("point_cloud must contain at least one point and feature")
    if not np.all(np.isfinite(points)):
        raise ValueError("point_cloud must contain only finite values")

    max_dim = int(max_dim)
    if max_dim < 0:
        raise ValueError("max_dim must be non-negative")

    max_edge_length = float(max_edge_length)
    if not np.isfinite(max_edge_length) or max_edge_length <= 0:
        raise ValueError("max_edge_length must be finite and positive")
    return points, max_dim, max_edge_length


def compute_persistence(point_cloud, max_dim=2, max_edge_length=2.0):
    """Compute persistence diagrams using Ripser or GUDHI.

    Both backends use the same finite distance threshold. Missing TDA
    dependencies are an execution error; placeholder diagrams are forbidden.
    """
    points, max_dim, max_edge_length = _validate_point_cloud(
        point_cloud, max_dim, max_edge_length
    )
    key = (
        points.shape,
        points.dtype.str,
        points.tobytes(),
        max_dim,
        max_edge_length,
    )
    if key in _persistence_cache:
        return _persistence_cache[key]

    try:
        from ripser import ripser
    except ImportError:
        try:
            import gudhi
        except ImportError as gudhi_error:
            raise RuntimeError(
                "Ripser or GUDHI is required for persistence computation; "
                "placeholder diagrams are forbidden"
            ) from gudhi_error

        rips = gudhi.RipsComplex(
            points=points,
            max_edge_length=max_edge_length,
        )
        st = rips.create_simplex_tree(max_dimension=max_dim + 1)
        st.compute_persistence()
        diagrams = [
            np.asarray(st.persistence_intervals_in_dimension(dim), dtype=float)
            for dim in range(max_dim + 1)
        ]
        result = {
            "dgms": diagrams,
            "betti": [len(d) for d in diagrams],
            "persistence_intervals": diagrams,
            "backend": "gudhi",
            "max_edge_length": max_edge_length,
        }
    else:
        result = ripser(
            points,
            maxdim=max_dim,
            thresh=max_edge_length,
        )
        diagrams = result["dgms"]
        result = dict(result)
        result.update(
            {
                "betti": [len(d) for d in diagrams],
                "persistence_intervals": diagrams,
                "backend": "ripser",
                "max_edge_length": max_edge_length,
            }
        )

    _persistence_cache[key] = result
    return result


compute_persistence_diagrams = compute_persistence
