"""Numerically guarded admissibility constraints for symbolic regression."""

import numpy as np


class LawDiscoveryManifold:
    """Constrained symbolic-regression search space."""

    def __init__(self, max_depth=6):
        self.max_depth = max_depth
        self.primitives = ["add", "sub", "mul", "div", "log", "exp", "arctan"]

    def lipschitz_penalty(self, f_values, x_values):
        f_values = np.asarray(f_values, dtype=float)
        x_values = np.asarray(x_values, dtype=float)
        if not np.all(np.isfinite(f_values)) or not np.all(np.isfinite(x_values)):
            return np.inf

        penalties = []
        for i in range(len(x_values)):
            for j in range(i + 1, len(x_values)):
                dx = float(np.linalg.norm(x_values[i] - x_values[j]))
                if dx <= 0:
                    continue
                df = float(abs(f_values[i] - f_values[j]))
                penalty = df / dx
                if not np.isfinite(penalty):
                    return np.inf
                penalties.append(penalty)
        return float(np.mean(penalties)) if penalties else 0.0

    def isogeny_invariant(self, f, curves):
        for e1, e2 in curves:
            a = float(f(e1))
            b = float(f(e2))
            if not np.isfinite(a) or not np.isfinite(b):
                return False
            if abs(a - b) > 1e-6:
                return False
        return True

    def null_scramble(self, f, scrambled_data):
        outputs = np.asarray([f(x) for x in scrambled_data], dtype=float)
        if not np.all(np.isfinite(outputs)):
            return False
        variance = float(np.var(outputs))
        return np.isfinite(variance) and variance > 0.1

    def admissible(self, f, data, isogeny_pairs, scrambled):
        try:
            f_values = np.asarray([f(x) for x in data], dtype=float)
            if not np.all(np.isfinite(f_values)):
                return False
            return (
                self.lipschitz_penalty(f_values, data) < 10.0
                and self.isogeny_invariant(f, isogeny_pairs)
                and self.null_scramble(f, scrambled)
            )
        except (FloatingPointError, OverflowError, ValueError, TypeError):
            return False
