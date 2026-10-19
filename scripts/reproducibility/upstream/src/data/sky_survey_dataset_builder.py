"""Sky-survey union builder.

This module concatenates two survey tables. It does not perform positional or
entity crossmatching; the class name makes that distinction explicit.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.load_sky_surveys import load_sky_surveys
from src.utils.astro_utils import clean_dataframe


class SkySurveyUnionBuilder:
    def __init__(self, downsample=None):
        self.downsample = downsample

    def build(self):
        df1, df2 = load_sky_surveys(downsample=self.downsample)
        union = pd.concat([df1, df2], ignore_index=True)
        return clean_dataframe(union)

    def save(self, path="data/processed/sky_surveys.parquet"):
        df = self.build()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path)
        return path


class SkySurveyDatasetBuilder(SkySurveyUnionBuilder):
    """Backward-compatible alias; this builder performs a union, not a match."""
