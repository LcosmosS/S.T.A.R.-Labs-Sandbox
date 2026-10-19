"""Spherical association diagnostics; NOT an activated experiment.

This intentionally does not implement a sky-shift null or assign significance.
It never uses the historical flat-RA/Dec KDTree coordinates as arcseconds.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.spatial import cKDTree

class CrossmatchGateError(ValueError):
    pass

ARCSEC_PER_RADIAN = 180 * 3600 / math.pi

def validate_radec(coords):
    a = np.asarray(coords, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 2:
        raise CrossmatchGateError("coordinates must be Nx2 in degrees [RA,Dec]")
    if not np.isfinite(a).all():
        raise CrossmatchGateError("missing/nonfinite RA/Dec; refuse silent exclusion")
    if np.any((a[:,0] < 0) | (a[:,0] >= 360) | (a[:,1] < -90) | (a[:,1] > 90)):
        raise CrossmatchGateError("RA/Dec degrees outside ICRS coordinate bounds")
    return a

def angular_separation_arcsec(ra1, dec1, ra2, dec2):
    """Numerically stable great-circle haversine; handles poles and RA wrapping."""
    deg = math.pi / 180
    dra = ((float(ra2) - float(ra1) + 180) % 360 - 180) * deg
    ddec = (float(dec2) - float(dec1)) * deg
    d1, d2 = float(dec1) * deg, float(dec2) * deg
    h = math.sin(ddec/2)**2 + math.cos(d1)*math.cos(d2)*math.sin(dra/2)**2
    return 2 * math.asin(math.sqrt(min(1., max(0.,h)))) * ARCSEC_PER_RADIAN

def _unit_vectors(coords):
    ra, dec = np.deg2rad(coords[:,0]),np.deg2rad(coords[:,1])
    c=np.cos(dec)
    return np.column_stack([c*np.cos(ra),c*np.sin(ra),np.sin(dec)])

def enumerate_candidates(left_coords, right_coords, *, radius_arcsec=2.0):
    """Return all within-radius pairs, not an arbitrary nearest-only or first join.

    No null realization, footprint-aware false-match model or galaxy-class
    selection is asserted. A repeated coordinate stays an ambiguous candidate.
    """
    left=validate_radec(left_coords);right=validate_radec(right_coords)
    if radius_arcsec != 2.0:
        raise CrossmatchGateError("primary candidate radius is 2 arcsec; sensitivity requires separate review")
    unit_l,unit_r=_unit_vectors(left),_unit_vectors(right)
    chord=2*math.sin(radius_arcsec/(2*ARCSEC_PER_RADIAN))
    tree=cKDTree(unit_r) if len(right) else None
    pairs=[]
    if tree is None: return pairs
    for i,pt in enumerate(unit_l):
        neighbors=tree.query_ball_point(pt,r=float(np.nextafter(chord,np.inf)))
        for j in neighbors:
            sep=angular_separation_arcsec(*left[i],*right[int(j)])
            if sep <= radius_arcsec:
                pairs.append((i,int(j),sep))
    return sorted(pairs, key=lambda x:(x[0],x[2],x[1]))

def unique_nonambiguous_pairs(left_coords,right_coords):
    """Exploratory strict 1:1 policy: reject any ambiguous left or right identity."""
    pairs=enumerate_candidates(left_coords,right_coords)
    lc,rc={},{}
    for i,j,_ in pairs:lc[i]=lc.get(i,0)+1;rc[j]=rc.get(j,0)+1
    accepted=[p for p in pairs if lc[p[0]]==1 and rc[p[1]]==1]
    ambiguous=[p for p in pairs if lc[p[0]]!=1 or rc[p[1]]!=1]
    return accepted,ambiguous

def prohibit_controlled_matching():
    raise CrossmatchGateError(
        "EXP-DATA-A01 is planned: source release, epoch and sky-mask-aware shift null "
        "are not registered. Fixture diagnostics cannot be promoted to controlled matches.")
