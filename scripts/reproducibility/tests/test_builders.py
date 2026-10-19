"""Explicitly synthetic builder/loader checks, never empirical inference."""
from pathlib import Path
import builtins

import numpy as np
import pandas as pd
import pytest

from src.data import load_sky_surveys as loader
from src.data.cremona_ecdata import CremonaDataError, parse_allcurves_line, representative_records
from src.data.sky_survey_dataset_builder import SkySurveyUnionBuilder
from src.tda import persistence
from src.entropy.entropy_geodesics import EntropyGeodesics


def test_union_builder_parquet_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, 'DATA', tmp_path)
    first = pd.DataFrame({'RAdeg': [1., 2., 3.], 'DEdeg': [-4., 5., 6.]})
    second = pd.DataFrame({'RAdeg': [1., 8.], 'DEdeg': [-4., 9.]})
    first.to_csv(tmp_path/'JApJ94494_2MASS_GAIADR3_EPOCH.csv', index=False)
    second.to_csv(tmp_path/'DESIDR8_SDSSDR16_SIMBAD.csv', index=False)
    tables = loader.load_sky_surveys(downsample=2, validate_schema=True)
    assert [len(t) for t in tables] == [2, 2]
    builder = SkySurveyUnionBuilder(downsample=2)
    expected = pd.concat(tables, ignore_index=True)
    # A union preserves the overlapping row; it does not certify a crossmatch.
    assert len(expected) == 4 and expected.duplicated().sum() == 1
    destination = tmp_path/'union.parquet'
    builder.save(destination)
    pd.testing.assert_frame_equal(pd.read_parquet(destination), expected, check_dtype=True)


def test_loader_missing_or_invalid_schema_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, 'DATA', tmp_path)
    with pytest.raises(FileNotFoundError):
        loader.load_sky_surveys(validate_schema=True)
    for name in ('JApJ94494_2MASS_GAIADR3_EPOCH.csv', 'DESIDR8_SDSSDR16_SIMBAD.csv'):
        (tmp_path/name).write_text('wrong\n1\n')
    with pytest.raises(ValueError, match='required columns'):
        loader.load_sky_surveys(validate_schema=True)


def test_real_persistence_backend_and_missing_backend_fail_closed(monkeypatch):
    points = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
    result = persistence.compute_persistence(points, max_dim=1)
    assert result['backend'] == 'gudhi'
    assert len(result['dgms']) == 2
    persistence._persistence_cache.clear()
    original = builtins.__import__
    def without_backend(name, *args, **kwargs):
        if name in ('gudhi', 'ripser'):
            raise ImportError('intentional missing backend control')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', without_backend)
    with pytest.raises(RuntimeError, match='placeholder diagrams are forbidden'):
        persistence.compute_persistence(points, max_dim=1)


def test_strict_arithmetic_parser_and_duplicate_representative():
    record = parse_allcurves_line('11 a 1 [0,-1,1,-10,-20] 0 5')
    assert record.label == '11a1' and record.rank == 0
    with pytest.raises(CremonaDataError):
        parse_allcurves_line('11 a 1 [0,-1] 0 5')
    with pytest.raises(CremonaDataError, match='duplicate'):
        representative_records([record, record])


def test_installed_imports_are_from_site_packages():
    import os
    import src
    if os.environ.get('SBX_INSTALLED') == '1':
        assert 'site-packages' in str(Path(src.__file__).resolve())


def test_known_legacy_geodesic_overflow_is_rejected():
    # The legacy shape-only smoke hid invalid arithmetic. Preserve the failure
    # as a negative control, not as a usable integration or physics result.
    with np.errstate(over='raise', invalid='raise'):
        with pytest.raises(FloatingPointError):
            EntropyGeodesics().geodesic([1., 2., 3.], [.1, -.1, .05], steps=10)
