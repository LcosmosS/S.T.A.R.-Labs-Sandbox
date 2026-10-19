import numpy as np
from src.tda.persistence_landscape import PersistenceLandscape


def test_landscape_shape():
    L = PersistenceLandscape()
    barcodes = [(0.0, 1.0), (0.2, 0.8)]
    landscape = L.landscape(barcodes)
    assert landscape.shape[1] == L.resolution
