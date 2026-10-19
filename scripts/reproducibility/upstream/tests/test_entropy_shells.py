import numpy as np
from src.entropy.entropy_shells import EntropyShells


def test_shell_assignment():
    S = EntropyShells()
    x = np.array([1.0, 2.0, 3.0])
    thresholds = [0, 1, 2, 3]
    shell = S.assign_shell(x, thresholds)
    assert shell in {0, 1, 2}
