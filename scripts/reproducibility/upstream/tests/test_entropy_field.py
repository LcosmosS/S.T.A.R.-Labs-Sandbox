import numpy as np
from src.entropy.entropy_field import EntropyField


def test_entropy_computation():
    M = EntropyField()
    x = np.array([1.0, 2.0, 3.0])
    value = M.entropy(x)
    assert value > 0


def test_gradient_shape():
    M = EntropyField()
    x = np.array([1.0, 2.0, 3.0])
    grad = M.gradient(x)
    assert grad.shape == x.shape


def test_hessian_shape():
    M = EntropyField()
    x = np.array([1.0, 2.0, 3.0])
    H = M.hessian(x)
    assert H.shape == (3, 3)
