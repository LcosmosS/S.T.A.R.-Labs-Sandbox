import numpy as np
from src.entropy.symbolic_manifold import SymbolicManifold


def test_projection_vector_field():
    M = SymbolicManifold()
    x = np.array([1.0, 2.0, 3.0])
    v = M.projection_vector_field(x)
    assert np.isclose(np.linalg.norm(v), 1.0)
