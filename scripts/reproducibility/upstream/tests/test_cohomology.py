import numpy as np
from src.entropy.entropy_field import EntropyField
from src.entropy.cohomology import EntropyCohomology


def test_two_form_closedness():
    M = EntropyField()
    C = EntropyCohomology(M)
    x = np.array([1.0, 2.0, 3.0])
    theta = M.gradient(x)
    omega = C.exterior_derivative_1form(theta, x)
    assert C.is_closed(omega)
