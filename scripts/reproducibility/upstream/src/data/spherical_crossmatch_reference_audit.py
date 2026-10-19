"""Independent slow spherical crossmatch oracle for TEST FIXTURES ONLY.

No survey mask, association null, likelihood ratio or source manifest is supplied.
This cannot authorize EXP-DATA-A01, infer a physical match or replace real controls.
"""
from __future__ import annotations
import math

ARCSEC_PER_RADIAN = 180.0 * 3600.0 / math.pi


class ReferenceCrossmatchError(ValueError):
    pass


def unit_vector(coord):
    """Convert an ICRS coordinate in degrees to a Cartesian unit vector.

    Args:
        coord: A (RA, Dec) pair with RA in [0, 360) and Dec in [-90, 90].

    Returns:
        The three Cartesian components as a tuple.

    Raises:
        ReferenceCrossmatchError: The pair has the wrong length, nonfinite
            values, or coordinates outside the allowed bounds.
    """
    if len(coord) != 2:
        raise ReferenceCrossmatchError("coordinate must be (RA, Dec)")
    ra, dec = map(float, coord)
    if not (math.isfinite(ra) and math.isfinite(dec)):
        raise ReferenceCrossmatchError("nonfinite RA/Dec")
    if not (0.0 <= ra < 360.0 and -90.0 <= dec <= 90.0):
        raise ReferenceCrossmatchError("RA/Dec outside ICRS bounds")
    r = math.radians(ra)
    d = math.radians(dec)
    return math.cos(d)*math.cos(r), math.cos(d)*math.sin(r), math.sin(d)


def angular_distance_arcsec(left, right):
    """atan2(||u x v||, u dot v), independent of main haversine."""
    a,b = unit_vector(left),unit_vector(right)
    cx = a[1]*b[2]-a[2]*b[1]
    cy = a[2]*b[0]-a[0]*b[2]
    cz = a[0]*b[1]-a[1]*b[0]
    dot = sum(ai*bi for ai,bi in zip(a,b))
    return math.atan2(math.hypot(cx,cy,cz),dot)*ARCSEC_PER_RADIAN


def enumerate_reference_candidates(left, right, *, radius_arcsec=2.0):
    """O(n*m) all-candidates oracle; no nearest-only or fabricated sky null."""
    if radius_arcsec != 2.0:
        raise ReferenceCrossmatchError("radius must be locked to exploratory 2 arcsec")
    left,right=list(left),list(right)
    for p in left+right:
        unit_vector(p)
    matches=[]
    for i,a in enumerate(left):
        for j,b in enumerate(right):
            sep=angular_distance_arcsec(a,b)
            if sep <= radius_arcsec:
                matches.append((i,j,sep))
    return sorted(matches,key=lambda v:(v[0],v[2],v[1]))


def classify_strict_one_to_one(matches):
    """Diagnostic multiplicity counts, not a preregistered survey policy."""
    left_degree={}
    right_degree={}
    for i,j,_ in matches:
        left_degree[i]=left_degree.get(i,0)+1
        right_degree[j]=right_degree.get(j,0)+1
    unique,ambiguous=[],[]
    for edge in matches:
        (unique if left_degree[edge[0]]==1 and right_degree[edge[1]]==1 else ambiguous).append(edge)
    return unique,ambiguous
