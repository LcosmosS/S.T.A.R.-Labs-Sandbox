import numpy as np
from src.physics.hubble_tension_fit import HubbleTensionFit


def test_tension_computation():
    F = HubbleTensionFit()
    inv = {"omega": 1.0, "rank": 2}
    result = F.fit(0.01, 1100, inv, inv, 0.2, 0.01)
    assert "tension" in result
