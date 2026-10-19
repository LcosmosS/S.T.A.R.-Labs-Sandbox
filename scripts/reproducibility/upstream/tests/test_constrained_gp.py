import numpy as np
import pytest

from src.symbolic_regression.constrained_gp import ConstrainedGP, GPNode
from src.symbolic_regression.law_discovery_manifold import LawDiscoveryManifold


def test_gp_random_tree_sequence_is_reproducible_for_seed():
    a = ConstrainedGP(seed=7)
    b = ConstrainedGP(seed=7)

    seq_a = [a.random_tree().as_tuple() for _ in range(5)]
    seq_b = [b.random_tree().as_tuple() for _ in range(5)]

    assert seq_a == seq_b


def test_random_tree_respects_feature_width():
    gp = ConstrainedGP(seed=3)
    x = np.array([0.25])
    for _ in range(20):
        tree = gp.random_tree(n_features=1)
        try:
            tree.evaluate(x)
        except FloatingPointError:
            pass
        except IndexError as exc:
            pytest.fail(f"generated an out-of-range variable index: {exc}")


def test_population_two_still_generates_offspring(monkeypatch):
    gp = ConstrainedGP(population=2, seed=1)
    generated = {"count": 0}

    def counted_random_tree(*args, **kwargs):
        generated["count"] += 1
        return GPNode("var", value=0)

    monkeypatch.setattr(gp, "random_tree", counted_random_tree)
    monkeypatch.setattr(gp.manifold, "admissible", lambda *args, **kwargs: True)

    data = np.array([[0.0], [1.0], [2.0], [3.0]])
    scrambled = data[::-1].copy()
    gp.evolve(data, [], scrambled, generations=2)

    assert generated["count"] > gp.population


def test_evolve_rejects_search_with_no_admissible_candidate(monkeypatch):
    gp = ConstrainedGP(population=4, seed=1)
    monkeypatch.setattr(gp.manifold, "admissible", lambda *args, **kwargs: False)

    data = np.ones((4, 2))
    with pytest.raises(RuntimeError, match="no admissible candidate"):
        gp.evolve(data, [], data.copy(), generations=1)


def test_overflowing_expression_is_rejected_without_nan_scoring():
    huge = GPNode("const", value=1e6)
    node = GPNode("exp", children=[huge])
    with pytest.raises(FloatingPointError):
        node.evaluate(np.array([1.0, 2.0, 3.0]))

    manifold = LawDiscoveryManifold()
    assert not manifold.admissible(
        lambda x: node.evaluate(x),
        np.ones((3, 3)),
        [],
        np.ones((3, 3)),
    )
