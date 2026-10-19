import numpy as np
from src.physics.scalar_coupling import ScalarCoupling


def test_scalar_field_output():
    S = ScalarCoupling()
    invariants = {"omega": 1.0, "rank": 2, "conductor": 11}
    phi = S.scalar_field(invariants, entropy_curvature=0.5)
    assert isinstance(phi, float)
