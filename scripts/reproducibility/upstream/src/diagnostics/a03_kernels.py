"""Pure synthetic A03 kernels extracted from pinned legacy source; no dataset/runner/gate."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
MASK64=(1<<64)-1
K=10
class ProtocolViolation(ValueError):
    """Raised when input/configuration violates the locked preregistration."""

def _discriminant(ainvs: tuple[int, int, int, int, int]) -> int:
    a1, a2, a3, a4, a6 = ainvs
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = (
        a1 * a1 * a6
        + 4 * a2 * a6
        - a1 * a3 * a4
        + a2 * a3 * a3
        - a4 * a4
    )
    delta = -(b2 * b2) * b8 - 8 * (b4**3) - 27 * (b6**2) + 9 * b2 * b4 * b6
    if delta == 0:
        raise ProtocolViolation("singular curve: discriminant is zero")
    return int(delta)

class SplitMix64:
    def __init__(self, seed: int):
        if seed < 0 or seed > MASK64:
            raise ProtocolViolation("SplitMix64 seed must fit in uint64")
        self.state = int(seed) & MASK64

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        return (z ^ (z >> 31)) & MASK64

    def randbelow(self, upper: int) -> int:
        if upper <= 0:
            raise ProtocolViolation("randbelow upper bound must be positive")
        limit = ((1 << 64) // upper) * upper
        while True:
            value = self.next_u64()
            if value < limit:
                return value % upper

    def permutation(self, size: int) -> np.ndarray:
        values = list(range(size))
        for i in range(size - 1, 0, -1):
            j = self.randbelow(i + 1)
            values[i], values[j] = values[j], values[i]
        return np.asarray(values, dtype=np.int64)

class MCJProtocolError(ValueError):
    """Input, arithmetic, configuration, or output violates A03 preregistration."""

def mcj_neighbor_edges(frame: pd.DataFrame, k: int = K) -> np.ndarray:
    if k != K:
        raise MCJProtocolError("MCJ k=10 is locked")
    points = frame[["x", "y", "z"]].to_numpy(dtype=np.float64)
    labels = frame["label"].astype(str).tolist()
    if len(points) <= k or len(set(labels)) != len(labels) or not np.isfinite(points).all():
        raise MCJProtocolError("invalid MCJ graph input")
    tree = cKDTree(points)
    edges = set()
    for i, point in enumerate(points):
        distances, ids = tree.query(point, k=k + 1)
        initial = sorted(
            float(distance)
            for distance, neighbor in zip(np.atleast_1d(distances), np.atleast_1d(ids))
            if int(neighbor) != i
        )
        if len(initial) < k or not math.isfinite(initial[k - 1]):
            raise MCJProtocolError("missing neighbors")
        candidates = tree.query_ball_point(
            point, r=float(np.nextafter(initial[k - 1], np.inf))
        )
        ranked = []
        for neighbor in candidates:
            neighbor = int(neighbor)
            if neighbor == i:
                continue
            diff = points[neighbor] - point
            distance2 = float(np.dot(diff, diff))
            if not math.isfinite(distance2):
                raise MCJProtocolError("nonfinite squared distance")
            ranked.append((distance2, labels[neighbor], neighbor))
        ranked.sort(key=lambda item: (item[0], item[1]))
        if len(ranked) < k:
            raise MCJProtocolError("incomplete neighbor enumeration")
        for _, _, neighbor in ranked[:k]:
            edges.add(tuple(sorted((i, neighbor))))
    result = np.asarray(sorted(edges), dtype=np.int64)
    if result.ndim != 2 or result.shape[1] != 2 or len(result) == 0:
        raise MCJProtocolError("empty MCJ graph")
    return result

def rank_coherence(ranks: np.ndarray, edges: np.ndarray) -> float:
    if edges.ndim != 2 or edges.shape[1] != 2 or len(edges) == 0:
        raise MCJProtocolError("invalid edges")
    ranks = np.asarray(ranks, dtype=np.int64)
    value = -float(
        np.mean(np.abs(ranks[edges[:, 0]] - ranks[edges[:, 1]]), dtype=np.float64)
    )
    if not math.isfinite(value):
        raise MCJProtocolError("nonfinite coherence statistic")
    return value

def decile_groups(frame: pd.DataFrame) -> list[np.ndarray]:
    if len(frame) < 10:
        raise MCJProtocolError("too few curves for ten strata")
    keys = list(zip(frame["conductor"].astype(int), frame["label"].astype(str)))
    if keys != sorted(keys):
        raise MCJProtocolError("input not in frozen conductor-label order")
    size = len(frame)
    groups = [
        np.asarray([i for i in range(size) if 10 * i // size == s], dtype=np.int64)
        for s in range(10)
    ]
    if any(len(group) == 0 for group in groups):
        raise MCJProtocolError("empty conductor-order stratum")
    return groups

def _null_statistics_core(ranks, edges, groups, *, draws: int, seed: int) -> np.ndarray:
    rng = SplitMix64(seed)
    observed_ranks = np.asarray(ranks, dtype=np.int64)
    values = np.empty(draws, dtype=np.float64)
    for draw in range(draws):
        trial = observed_ranks.copy()
        for group in groups:
            trial[group] = observed_ranks[group][rng.permutation(len(group))]
        values[draw] = rank_coherence(trial, edges)
    return values
