import numpy as np

from src.tda.witness_complex import WitnessComplex


def test_witness_complex_is_reproducible_for_declared_seed():
    X = np.arange(150, dtype=float).reshape(50, 3)
    a = WitnessComplex(num_landmarks=5, seed=17).build_complex(X)
    b = WitnessComplex(num_landmarks=5, seed=17).build_complex(X)

    assert np.array_equal(a["landmarks"], b["landmarks"])
    assert a["edges"] == b["edges"]
