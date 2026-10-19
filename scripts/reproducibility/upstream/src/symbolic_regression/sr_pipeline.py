"""High-level reproducible symbolic-regression orchestration."""

import numpy as np

from .constrained_gp import ConstrainedGP
from .law_discovery_manifold import LawDiscoveryManifold


class SRPipeline:
    """Orchestrate symbolic regression with an explicit random seed."""

    def __init__(
        self,
        max_depth=6,
        population=50,
        generations=20,
        *,
        seed: int = 0,
    ):
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.gp = ConstrainedGP(
            max_depth=max_depth,
            population=population,
            seed=self.seed,
        )
        self.manifold = LawDiscoveryManifold(max_depth=max_depth)
        self.generations = int(generations)

    def prepare_data(self, x):
        x = np.asarray(x, dtype=float)
        if x.ndim != 2 or x.shape[0] == 0 or x.shape[1] == 0:
            raise ValueError(
                "symbolic-regression input must be a non-empty 2D array with features"
            )
        if not np.all(np.isfinite(x)):
            raise ValueError("symbolic-regression input must be finite")
        scale = np.max(np.abs(x), axis=0)
        scale = np.where(scale > 0, scale, 1.0)
        return x / scale

    def scramble(self, x):
        x = np.asarray(x, dtype=float)
        return x[self.rng.permutation(len(x))].copy()

    def run(self, x, isogeny_pairs):
        x = self.prepare_data(x)
        scrambled = self.scramble(x)
        return self.gp.evolve(
            data=x,
            isogeny_pairs=isogeny_pairs,
            scrambled=scrambled,
            generations=self.generations,
        )
