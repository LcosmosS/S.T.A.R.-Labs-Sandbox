"""
Astro Utilities
===============

General-purpose utilities for:
- coordinate conversions
- magnitude/flux conversions
- table cleaning
"""

import numpy as np
import pandas as pd


def mag_to_flux(mag):
    return 10 ** (-0.4 * mag)


def flux_to_mag(flux):
    return -2.5 * np.log10(flux)


def clean_dataframe(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(how="all")
    return df
