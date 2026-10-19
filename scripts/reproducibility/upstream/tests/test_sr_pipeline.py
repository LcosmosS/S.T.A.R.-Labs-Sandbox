import numpy as np
import pytest

from src.symbolic_regression.sr_pipeline import SRPipeline


def test_scramble_sequence_is_reproducible_for_seed():
    x = np.arange(60, dtype=float).reshape(20, 3)
    a = SRPipeline(seed=42)
    b = SRPipeline(seed=42)

    seq_a = [a.scramble(x) for _ in range(4)]
    seq_b = [b.scramble(x) for _ in range(4)]

    assert all(np.array_equal(left, right) for left, right in zip(seq_a, seq_b))


def test_prepare_data_rejects_zero_feature_columns():
    sr = SRPipeline(seed=1)
    with pytest.raises(ValueError, match="with features"):
        sr.prepare_data(np.empty((20, 0)))


def test_sr_pipeline_runs_on_finite_fixture():
    rng = np.random.default_rng(11)
    x = rng.random((20, 3))
    sr = SRPipeline(seed=11)
    best = sr.run(x, [])
    assert best is not None
