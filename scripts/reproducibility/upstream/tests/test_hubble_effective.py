import numpy as np
from src.physics.hubble_effective import HubbleEffective


def test_hubble_eff():
    H = HubbleEffective()
    invariants = {"omega": 1.0, "rank": 2}
    val = H.H_eff(0.1, invariants, entropy_curvature=0.5)
    assert val > 0
