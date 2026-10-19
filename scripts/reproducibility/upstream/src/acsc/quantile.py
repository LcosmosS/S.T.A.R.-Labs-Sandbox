import numpy as np
import json
from pathlib import Path
from src.data.load_sky_surveys import load_sky_surveys


def test_sky_surveys_load():
    df1, df2 = load_sky_surveys(downsample=100, validate_schema=True)
    assert len(df1) > 0
    assert len(df2) > 0


class QuantileAligner:
    def __init__(self):
        self._fitted = False
        self._quantiles = None
        self._axis_maps = None

    def fit(self, ref_coords: np.ndarray, n_quantiles: int = 200):
        ref_coords = np.asarray(ref_coords, dtype=float)
        if ref_coords.ndim != 2 or ref_coords.shape[1] != 3:
            raise ValueError("ref_coords must be (n,3)")
        q = np.linspace(0.0, 1.0, n_quantiles)
        self._quantiles = q.tolist()
        self._axis_maps = []
        for axis in range(3):
            vals = ref_coords[:, axis]
            vals_sorted = np.sort(vals[~np.isnan(vals)])
            if vals_sorted.size == 0:
                self._axis_maps.append([0.0] * n_quantiles)
            else:
                # compute empirical quantiles via interpolation
                qs = np.quantile(vals_sorted, q)
                self._axis_maps.append(qs.tolist())
        self._fitted = True
        return self

    def transform(self, src_coords: np.ndarray):
        if not self._fitted:
            raise RuntimeError("QuantileAligner not fitted")
        src = np.asarray(src_coords, dtype=float)
        if src.ndim != 2 or src.shape[1] != 3:
            raise ValueError("src_coords must be (m,3)")
        out = np.empty_like(src)
        q = np.array(self._quantiles)
        for axis in range(3):
            axis_map = np.array(self._axis_maps[axis])
            # map each src value to its empirical quantile in axis_map, then map to axis_map value
            # we compute the quantile of src value relative to axis_map via linear interpolation
            # first compute CDF-like mapping by inverting axis_map
            # handle constant axis_map
            if np.allclose(axis_map, axis_map[0]):
                out[:, axis] = axis_map[0]
                continue
            # for each value, find its fractional position in axis_map
            # use np.interp: given x=src_val, xp=axis_map, fp=q
            src_vals = src[:, axis]
            # clamp src_vals to axis_map range
            minv, maxv = axis_map[0], axis_map[-1]
            src_clamped = np.clip(src_vals, minv, maxv)
            frac = np.interp(src_clamped, axis_map, q)
            # now map frac back to axis_map (identity here) — effectively we are projecting onto ref quantiles
            out[:, axis] = np.interp(frac, q, axis_map)
        return out

    def fit_transform(self, ref_coords, src_coords, n_quantiles=200):
        """Fit on ref_coords and transform src_coords in one step."""
        self.fit(ref_coords, n_quantiles=n_quantiles)
        return self.transform(src_coords)

    def save(self, path):
        d = {"quantiles": self._quantiles, "axis_maps": self._axis_maps}
        Path(path).write_text(json.dumps(d))

    def load(self, path):
        d = json.loads(Path(path).read_text())
        self._quantiles = d["quantiles"]
        self._axis_maps = d["axis_maps"]
        self._fitted = True
        return self
