import numpy as np
from src.entropy.entropy_potential import EntropyPotential


def test_potential_positive():
    P = EntropyPotential()
    x = np.array([1.0, 2.0, 3.0])
    V = P.potential(x)
    assert V > 0
