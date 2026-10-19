import numpy as np
from src.physics.metric_perturbations import MetricPerturbations


def test_delta_g_shape():
    M = MetricPerturbations()
    x = np.array([1.0, 2.0, 3.0])
    dg = M.delta_g(x)
    assert dg.shape == (3, 3)
