import numpy as np

from src.tda.bootstrap_stability import BootstrapStability


def test_bootstrap_resampling_is_reproducible_for_declared_seed():
    X = np.arange(60, dtype=float).reshape(20, 3)
    a = BootstrapStability(num_bootstrap=5, seed=23)
    b = BootstrapStability(num_bootstrap=5, seed=23)

    assert np.array_equal(a.resample(X), b.resample(X))
