"""Tests for independent great-circle oracle, all on synthetic coordinates."""
import math
import random
import pytest

from src.data.spherical_crossmatch_reference_audit import (
    angular_distance_arcsec, enumerate_reference_candidates,
    classify_strict_one_to_one, ReferenceCrossmatchError,
)
from src.data.spherical_match_candidate import (
    angular_separation_arcsec, enumerate_candidates, unique_nonambiguous_pairs,
)


def test_ra_wrap_pole_and_identity():
    """Verify spherical distances at RA wraparound, the pole, and identity."""
    assert abs(angular_distance_arcsec((359.9999, 0), (0.0001, 0)) - .72) < 1e-7
    assert angular_distance_arcsec((0, 90), (180, 90)) < 1e-6
    assert angular_distance_arcsec((20, -15), (20, -15)) < 1e-9


def test_independent_geometry_agrees_randomly_with_existing_haversine():
    """Compare the oracle with haversine distances on seeded synthetic pairs."""
    rng = random.Random(20261009)
    for _ in range(100):
        ra = rng.random()*360
        dec = rng.uniform(-89.999, 89.999)
        ra2 = (ra + rng.uniform(-.001, .001)) % 360
        dec2 = max(-90, min(90, dec + rng.uniform(-.001, .001)))
        a, b = (ra, dec), (ra2, dec2)
        assert abs(angular_distance_arcsec(a,b)
                   - angular_separation_arcsec(*a,*b)) < 1e-7


def test_candidate_identity_multiplicity_crosscheck():
    """Cross-check candidate distances and unique versus ambiguous pair counts."""
    left = [(10., 0.), (10.0001, 0.), (30., 0.)]
    right = [(10.00002, 0.), (30.00001, 0.)]
    pairs = enumerate_reference_candidates(left, right)
    implementation = enumerate_candidates(left, right)
    assert {(i,j) for i,j,_ in pairs} == {(i,j) for i,j,_ in implementation}
    for (i,j,sep) in pairs:
        direct = next(d for a,b,d in implementation if a==i and b==j)
        assert abs(sep-direct)<1e-7
    accepted, ambiguous = classify_strict_one_to_one(pairs)
    original_accepted, original_ambiguous = unique_nonambiguous_pairs(left, right)
    assert len(accepted)==len(original_accepted)==1
    assert len(ambiguous)==len(original_ambiguous)==2


def test_boundary_and_invalid_input_do_not_promote():
    """Check radius filtering and rejection of invalid coordinates or radius."""
    a = [(0.,0.)]
    b = [(0.,1./3600.),(0.,3./3600.)]
    assert len(enumerate_reference_candidates(a,b))==len(enumerate_candidates(a,b))==1
    with pytest.raises(ReferenceCrossmatchError):
        enumerate_reference_candidates(a,b,radius_arcsec=3)
    with pytest.raises(ReferenceCrossmatchError):
        enumerate_reference_candidates([(float("nan"),0)],b)
    with pytest.raises(ReferenceCrossmatchError):
        enumerate_reference_candidates([(360.,0)],b)
