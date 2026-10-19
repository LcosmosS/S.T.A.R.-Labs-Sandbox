"""Metadata-aware Planck chain loader and compressed-view guard.

The tracked ``base_plikHM_TTTEEE_lowl_lowE*.txt`` objects are GetDist/CosmoMC
sample-chain tables. They are not three-column ``z, mu, sigma_mu`` observations.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd


PLANCK_CHAIN_ENV = "STAR_PLANCK_CHAIN_PATH"
DEFAULT_PLANCK_CHAIN_RELATIVE = Path(
    "data/planck/base_plikHM_TTTEEE_lowl_lowE_1.txt"
)


def _chain_root(path: Path) -> Path:
    stem = path.stem
    match = re.match(r"^(.*)_\d+$", stem)
    if match:
        stem = match.group(1)
    return path.with_name(stem)


def _resolve_chain_path(source_path=None):
    candidate = source_path or os.environ.get(PLANCK_CHAIN_ENV)
    if candidate:
        path = Path(candidate).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Planck chain source is missing: {path}")
        return path

    checkout_candidate = (
        Path(__file__).resolve().parents[3] / DEFAULT_PLANCK_CHAIN_RELATIVE
    )
    if checkout_candidate.is_file():
        return checkout_candidate

    raise FileNotFoundError(
        "Planck chain source is not available. Pass source_path=..., set "
        f"{PLANCK_CHAIN_ENV}, or run from a checkout containing "
        f"{DEFAULT_PLANCK_CHAIN_RELATIVE}."
    )


def _parse_bool_or_text(value):
    value = value.strip()
    if value == "T":
        return True
    if value == "F":
        return False
    return value


def load_planck_properties(path):
    """Parse a GetDist ``.properties.ini`` file."""
    result = {}
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise ValueError(
                f"invalid Planck properties line {line_number}: {line!r}"
            )
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in result:
            raise ValueError(
                f"empty or duplicate Planck property at line {line_number}"
            )
        result[key] = _parse_bool_or_text(value)

    if not result:
        raise ValueError(f"Planck properties file is empty: {path}")
    return result


def _parse_bound(token):
    token = token.strip()
    if token.upper() == "N":
        return None
    value = float(token)
    if not np.isfinite(value):
        raise ValueError(f"non-finite Planck range bound: {token}")
    return value


def load_planck_ranges(path):
    """Parse a GetDist ``.ranges`` file while preserving row order."""
    rows = []
    seen = set()
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 3:
            raise ValueError(
                f"invalid Planck ranges line {line_number}: {line!r}"
            )
        name = parts[0]
        if name in seen:
            raise ValueError(f"duplicate Planck range name: {name}")
        seen.add(name)
        rows.append(
            {
                "name": name,
                "lower": _parse_bound(parts[1]),
                "upper": _parse_bound(parts[2]),
            }
        )

    if not rows:
        raise ValueError(f"Planck ranges file is empty: {path}")
    return rows


def load_planck_paramnames(path):
    """Parse GetDist parameter names, labels, and derived ``*`` markers."""
    definitions = []
    seen = set()
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split(None, 1)
        raw_name = parts[0]
        derived = raw_name.endswith("*")
        name = raw_name[:-1] if derived else raw_name
        if not name or name in seen:
            raise ValueError(
                f"empty or duplicate Planck parameter at line {line_number}"
            )
        seen.add(name)
        label = parts[1].strip() if len(parts) > 1 else name
        definitions.append(
            {"name": name, "label": label, "derived": derived}
        )

    if not definitions:
        raise ValueError(f"Planck paramnames file is empty: {path}")
    return definitions


def _metadata_paths(
    source,
    *,
    paramnames_path=None,
    ranges_path=None,
    properties_path=None,
):
    root = _chain_root(source)
    direct_paramnames = root.with_suffix(".paramnames")
    direct_ranges = root.with_suffix(".ranges")
    direct_properties = root.with_suffix(".properties.ini")

    if paramnames_path is None and root.name.endswith("_post_BAO"):
        # Importance-sampled post-BAO chains reuse the base parameter schema.
        # A caller may override this only by passing paramnames_path explicitly.
        base_root = root.with_name(root.name.removesuffix("_post_BAO"))
        direct_paramnames = base_root.with_suffix(".paramnames")

    resolved = {
        "paramnames": (
            Path(paramnames_path).expanduser().resolve()
            if paramnames_path
            else direct_paramnames.resolve()
        ),
        "ranges": (
            Path(ranges_path).expanduser().resolve()
            if ranges_path
            else direct_ranges.resolve()
        ),
        "properties": (
            Path(properties_path).expanduser().resolve()
            if properties_path
            else direct_properties.resolve()
        ),
    }

    for kind, path in resolved.items():
        if not path.is_file():
            raise FileNotFoundError(f"Planck {kind} metadata is missing: {path}")
    return root, resolved


def _extra_derived(name, label):
    return {"name": name, "label": label, "derived": True}


def _post_bao_schema(param_defs, range_defs, n_params):
    names = [definition["name"] for definition in param_defs]
    expected_tail = [
        "chi2_simall",
        "chi2_lowl",
        "chi2_plik",
        "chi2_prior",
        "chi2_CMB",
    ]
    if names[-5:] != expected_tail:
        raise ValueError(
            "base Planck paramnames do not have the expected CMB chi-square tail"
        )

    range_names = {row["name"] for row in range_defs}
    required = {"chi2_6DF", "chi2_MGS", "chi2_DR12BAO", "chi2_BAO"}
    missing = sorted(required - range_names)
    if missing:
        raise ValueError(
            "post-BAO ranges metadata is missing: " + ", ".join(missing)
        )

    schema = (
        param_defs[:-2]
        + [
            _extra_derived("chi2_6DF", r"\chi^2_{\rm 6DF}"),
            _extra_derived("chi2_MGS", r"\chi^2_{\rm MGS}"),
            _extra_derived("chi2_DR12BAO", r"\chi^2_{\rm DR12BAO}"),
        ]
        + [param_defs[-2]]
        + [_extra_derived("chi2_BAO", r"\chi^2_{\rm BAO}")]
        + [param_defs[-1]]
    )
    if len(schema) != n_params:
        raise ValueError(
            f"post-BAO schema has {len(schema)} parameters but chain has "
            f"{n_params}"
        )
    return schema


def _parameter_schema(root, param_defs, range_defs, n_params):
    if len(param_defs) == n_params:
        return param_defs, "direct-paramnames"

    if root.name.endswith("_post_BAO"):
        return (
            _post_bao_schema(param_defs, range_defs, n_params),
            "base-paramnames-plus-post-BAO-ranges",
        )

    raise ValueError(
        f"Planck metadata defines {len(param_defs)} parameters but chain "
        f"contains {n_params}"
    )


def load_planck_chain(
    source_path=None,
    *,
    paramnames_path=None,
    ranges_path=None,
    properties_path=None,
):
    """Load a Planck GetDist/CosmoMC chain with validated metadata.

    The first two table columns are sample weight and ``-log(posterior)``.
    Scientific parameter names are loaded from ``.paramnames`` metadata.
    Post-BAO chains reuse the base parameter file and add four BAO chi-square
    quantities whose presence is validated against the post-processing
    ``.ranges`` metadata.
    """
    source = _resolve_chain_path(source_path)
    root, metadata_paths = _metadata_paths(
        source,
        paramnames_path=paramnames_path,
        ranges_path=ranges_path,
        properties_path=properties_path,
    )
    param_defs = load_planck_paramnames(metadata_paths["paramnames"])
    range_defs = load_planck_ranges(metadata_paths["ranges"])
    properties = load_planck_properties(metadata_paths["properties"])

    frame = pd.read_csv(
        source,
        sep=r"\s+",
        comment="#",
        header=None,
        engine="python",
    )
    if frame.empty:
        raise ValueError(f"Planck chain source is empty: {source}")

    for column in frame.columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"Non-finite or non-numeric values found in {source}")
    if (frame.iloc[:, 0] <= 0).any():
        raise ValueError("Planck chain weights must be strictly positive")

    schema, schema_source = _parameter_schema(
        root,
        param_defs,
        range_defs,
        frame.shape[1] - 2,
    )
    frame.columns = [
        "weight",
        "minus_log_posterior",
        *[definition["name"] for definition in schema],
    ]

    ranges = {
        row["name"]: {"lower": row["lower"], "upper": row["upper"]}
        for row in range_defs
    }
    frame.attrs.update(
        {
            "source_path": str(source),
            "schema_source": schema_source,
            "parameter_metadata": schema,
            "ranges": ranges,
            "properties": properties,
            "metadata_paths": {
                key: str(path) for key, path in metadata_paths.items()
            },
        }
    )
    return frame.reset_index(drop=True)


def load_planck_compressed(*args, **kwargs):
    """Reject the legacy three-column interpretation."""
    raise RuntimeError(
        "base_plikHM_TTTEEE_lowl_lowE*.txt is a Planck sample chain, not a "
        "three-column compressed z/mu/sigma_mu dataset. Use load_planck_chain()."
    )


class _LazyPlanckChain:
    def __init__(self):
        self._frame = None

    def _load(self):
        if self._frame is None:
            self._frame = load_planck_chain()
        return self._frame

    def __getitem__(self, key):
        return self._load()[key]

    def __getattr__(self, name):
        return getattr(self._load(), name)

    def __len__(self):
        return len(self._load())


class _RejectedCompressedView:
    def _raise(self):
        load_planck_compressed()

    def __getitem__(self, key):
        self._raise()

    def __getattr__(self, name):
        self._raise()

    def __len__(self):
        self._raise()


PLANCK_CHAIN = _LazyPlanckChain()
PLANCK_COMPRESSED = _RejectedCompressedView()
