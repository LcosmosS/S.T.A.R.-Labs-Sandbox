"""
Sky Survey Dataset Loader
=========================

Centralized loader for the two large sky-survey crossmatch datasets:

- JApJ94494_2MASS_GAIADR3_EPOCH.csv
- DESIDR8_SDSSDR16_SIMBAD.csv

This loader is CI-safe, Docker-safe, and notebook-safe.
It resolves paths relative to the project root and provides optional
downsampling for fast CI runs.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

# Resolve project root → data/raw/
DATA = Path(__file__).resolve().parents[2] / "data" / "raw"


def load_sky_surveys(
    *, downsample: int | None = None, validate_schema: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the two sky-survey datasets used in the astronomy pipeline.

    Parameters
    ----------
    downsample : int | None
        If provided, returns only the first N rows of each dataset.
        Useful for CI jobs where full datasets are too large.
    validate_schema : bool
        If True, performs minimal schema validation (column existence).

    Returns
    -------
    (df_2mass_gaia, df_sdss_desi_simbad) : tuple[pd.DataFrame, pd.DataFrame]
    """

    file_2mass_gaia = DATA / "JApJ94494_2MASS_GAIADR3_EPOCH.csv"
    file_sdss_desi_simbad = DATA / "DESIDR8_SDSSDR16_SIMBAD.csv"

    if not file_2mass_gaia.exists():
        raise FileNotFoundError(f"Missing dataset: {file_2mass_gaia}")

    if not file_sdss_desi_simbad.exists():
        raise FileNotFoundError(f"Missing dataset: {file_sdss_desi_simbad}")

    df_2mass_gaia = pd.read_csv(file_2mass_gaia)
    df_sdss_desi_simbad = pd.read_csv(file_sdss_desi_simbad)

    # Optional downsampling for CI
    if downsample is not None:
        df_2mass_gaia = df_2mass_gaia.head(downsample)
        df_sdss_desi_simbad = df_sdss_desi_simbad.head(downsample)

    # Optional schema validation
    if validate_schema:
        required_cols_2mass = {"RAdeg", "DEdeg"}
        required_cols_sdss = {"RAdeg", "DEdeg"}

        if not required_cols_2mass.issubset(df_2mass_gaia.columns):
            raise ValueError("2MASS/GAIA dataset missing required columns")

        if not required_cols_sdss.issubset(df_sdss_desi_simbad.columns):
            raise ValueError("SDSS/DESI/SIMBAD dataset missing required columns")

    return df_2mass_gaia, df_sdss_desi_simbad
