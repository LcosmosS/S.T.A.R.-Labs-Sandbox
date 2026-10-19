"""Constrained genetic-programming primitives for symbolic regression."""

import random

import numpy as np

from .law_discovery_manifold import LawDiscoveryManifold


class GPNode:
    """Node in a GP expression tree."""

    def __init__(self, op, children=None, value=None):
        self.op = op
        self.children = children or []
        self.value = value

    def evaluate(self, x):
        if self.op == "const":
            return self.value
        if self.op == "var":
            return x[self.value]

        vals = [child.evaluate(x) for child in self.children]

        with np.errstate(over="raise", invalid="raise", divide="raise"):
            if self.op == "add":
                return vals[0] + vals[1]
            if self.op == "sub":
                return vals[0] - vals[1]
            if self.op == "mul":
                return vals[0] * vals[1]
            if self.op == "div":
                return vals[0] / (vals[1] + 1e-12)
            if self.op == "log":
                return np.log(abs(vals[0]) + 1e-12)
            if self.op == "exp":
                return np.exp(vals[0])
            if self.op == "arctan":
                return np.arctan(vals[0])

        raise ValueError(f"Unknown operator: {self.op}")

    def depth(self):
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)

    def as_tuple(self):
        """Return a stable structural representation for deterministic tests."""
        return (
            self.op,
            self.value,
            tuple(child.as_tuple() for child in self.children),
        )


class ConstrainedGP:
    """Constrained GP engine with a private, reproducible random stream."""

    def __init__(
        self,
        max_depth=6,
        population=50,
        mutation_rate=0.1,
        *,
        seed: int = 0,
        n_features: int = 3,
    ):
        if population < 2:
            raise ValueError("population must be at least 2")
        if n_features < 1:
            raise ValueError("n_features must be at least 1")
        self.manifold = LawDiscoveryManifold(max_depth=max_depth)
        self.max_depth = int(max_depth)
        self.population = int(population)
        self.mutation_rate = float(mutation_rate)
        self.seed = int(seed)
        self.n_features = int(n_features)
        self.rng = random.Random(self.seed)

    def random_tree(self, depth=0, *, n_features=None):
        feature_count = self.n_features if n_features is None else int(n_features)
        if feature_count < 1:
            raise ValueError("n_features must be at least 1")

        if depth >= self.max_depth or self.rng.random() < 0.2:
            if self.rng.random() < 0.5:
                return GPNode("const", value=self.rng.uniform(-1, 1))
            return GPNode("var", value=self.rng.randrange(feature_count))

        op = self.rng.choice(self.manifold.primitives)
        if op in ["log", "exp", "arctan"]:
            return GPNode(
                op,
                children=[self.random_tree(depth + 1, n_features=feature_count)],
            )
        return GPNode(
            op,
            children=[
                self.random_tree(depth + 1, n_features=feature_count),
                self.random_tree(depth + 1, n_features=feature_count),
            ],
        )

    def mutate(self, tree, *, n_features=None):
        feature_count = self.n_features if n_features is None else int(n_features)
        if self.rng.random() < self.mutation_rate:
            return self.random_tree(n_features=feature_count)
        if tree.children:
            tree.children = [
                self.mutate(child, n_features=feature_count)
                for child in tree.children
            ]
        return tree

    def crossover(self, t1, t2):
        if self.rng.random() < 0.5:
            return t2
        if t1.children and t2.children:
            idx = self.rng.randint(0, len(t1.children) - 1)
            t1.children[idx] = self.crossover(
                t1.children[idx], self.rng.choice(t2.children)
            )
        return t1

    def evolve(self, data, isogeny_pairs, scrambled, generations=20):
        data = np.asarray(data, dtype=float)
        if data.ndim != 2 or data.shape[0] == 0 or data.shape[1] == 0:
            raise ValueError("GP data must be a non-empty 2D array with features")
        feature_count = int(data.shape[1])
        generations = int(generations)
        if generations < 1:
            raise ValueError("generations must be at least 1")

        population = [
            self.random_tree(n_features=feature_count)
            for _ in range(self.population)
        ]
        best_tree = None

        for _ in range(generations):
            scored = []
            for tree in population:
                f = lambda x, node=tree: node.evaluate(x)
                if self.manifold.admissible(f, data, isogeny_pairs, scrambled):
                    try:
                        values = np.asarray([f(x) for x in data], dtype=float)
                        score = float(np.var(values))
                        if not np.isfinite(score):
                            score = -np.inf
                    except (FloatingPointError, OverflowError, ValueError, IndexError):
                        score = -np.inf
                else:
                    score = -np.inf
                scored.append((score, tree))

            admissible = [
                (score, tree)
                for score, tree in scored
                if np.isfinite(score)
            ]
            if not admissible:
                raise RuntimeError(
                    "symbolic-regression search found no admissible candidate"
                )

            admissible.sort(key=lambda item: item[0], reverse=True)
            best_tree = admissible[0][1]

            parent_count = max(1, min(len(admissible), self.population // 2))
            population = [tree for _, tree in admissible[:parent_count]]

            while len(population) < self.population:
                if len(population) == 1:
                    child = self.random_tree(n_features=feature_count)
                else:
                    t1, t2 = self.rng.sample(population, 2)
                    child = self.crossover(t1, t2)
                    child = self.mutate(child, n_features=feature_count)
                population.append(child)

        return best_tree
