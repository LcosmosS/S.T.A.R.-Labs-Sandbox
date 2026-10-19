"""Synthetic algorithm reference only; no registry/cohort/preflight entrypoints."""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from unittest.mock import patch
import hashlib
import json
import numpy as np
import pandas as pd
import sympy as sp
from . import a03_kernels as production
from .a03_kernels import SplitMix64
def require(condition, message):
    """Raise a verification error when a required integrity check fails."""
    if not condition:
        raise ValueError(message)

def reference_invariants(a):
    """Compute Delta through c6 rather than the production b8 formula."""
    a1, a2, a3, a4, a6 = a
    b2 = a1**2 + 4*a2
    b4 = a1*a3 + 2*a4
    b6 = a3**2 + 4*a6
    c4 = b2**2 - 24*b4
    c6 = -b2**3 + 36*b2*b4 - 216*b6
    numerator = c4**3 - c6**2
    require(numerator % 1728 == 0, "non-integral reference discriminant")
    delta = numerator // 1728
    require(delta != 0, "singular reference curve")
    return c4, delta, Fraction(c4**3, delta)

def symbolic_identity():
    """Prove the c4/c6 and b8 discriminant formulas agree symbolically.

    This checks an exact polynomial identity without loading observed ranks."""
    a1,a2,a3,a4,a6 = sp.symbols("a1 a2 a3 a4 a6")
    b2=a1**2+4*a2; b4=a1*a3+2*a4; b6=a3**2+4*a6
    b8=a1**2*a6+4*a2*a6-a1*a3*a4+a2*a3**2-a4**2
    c4=b2**2-24*b4; c6=-b2**3+36*b2*b4-216*b6
    delta=-b2**2*b8-8*b4**3-27*b6**2+9*b2*b4*b6
    require(sp.expand(c4**3-c6**2-1728*delta) == 0,
            "symbolic discriminant identity failed")

def fixture(kind):
    """Construct a deterministic 40-row synthetic graph/null test fixture.

    The kind selects tied, duplicate, or seeded asymmetric coordinates.
    Synthetic ranks are diagnostic only, not observed cohort data."""
    n=40
    if kind=="duplicates":
        points=[(0.0,0.0,0.0) if i<14 else (float(i%5),float(i//5),0.0) for i in range(n)]
    elif kind=="ties":
        points=[(float(i%5),float(i//5),0.0) for i in range(n)]
    else:
        rng=np.random.default_rng(710)
        points=rng.normal(size=(n,3))
    frame=pd.DataFrame(points,columns=["x","y","z"])
    frame["conductor"]=[101+i//2 for i in range(n)]
    # a10 sorts before a2: numeric suffix ordering must not replace ASCII.
    frame["label"]=[f"{101+i//2}a{10 if i%2==0 else 2}" for i in range(n)]
    frame["rank"]=[(i*i+i//3)%5 for i in range(n)]
    return frame.sort_values(["conductor","label"]).reset_index(drop=True)

def reference_edges(frame):
    """Enumerate the undirected k=10 graph on at most 64 synthetic rows.

    Use squared Euclidean distances and ASCII labels to break ties.
    Refuse production-cohort sizes before accessing coordinate columns."""
    require(len(frame)<=64, "reference graph is restricted to synthetic fixtures")
    points=frame[["x","y","z"]].to_numpy(dtype=np.float64)
    labels=frame.label.tolist(); edges=set()
    for i,p in enumerate(points):
        candidates=[]
        for j,q in enumerate(points):
            if i!=j:
                d=q-p
                candidates.append((float(np.dot(d,d)),labels[j],j))
        for _,_,j in sorted(candidates)[:10]:
            edges.add(tuple(sorted((i,j))))
    return sorted(edges)

def reference_words(seed):
    """Yield an independent SplitMix64 unsigned 64-bit word stream.

    Keep the RNG state continuous across calls and use 64-bit modular
    arithmetic with the frozen SplitMix64 shift/multiply constants."""
    state=seed
    while True:
        state=(state+int("9e3779b97f4a7c15",16)) % (2**64)
        z=state
        z=((z^(z>>30))*int("bf58476d1ce4e5b9",16)) % (2**64)
        z=((z^(z>>27))*int("94d049bb133111eb",16)) % (2**64)
        yield z^(z>>31)

def reference_permutation(size,stream):
    """Generate a Fisher-Yates index permutation from an existing stream.

    Use rejection sampling to avoid modulo bias; do not reseed the
    stream between successive permutations or conductor strata."""
    values=list(range(size))
    for i in reversed(range(1,size)):
        upper=i+1; cutoff=(2**64//upper)*upper
        value=next(stream)
        while value>=cutoff:
            value=next(stream)
        j=value%upper
        values[i],values[j]=values[j],values[i]
    return values

def fixture_checks():
    """Compare reference PRNG, kNN, strata, and nulls on synthetic inputs.

    Check published-style vectors, rejection boundaries, rank-blind
    graph membership, continuing-stream permutations, and three-draw
    synthetic rank nulls. Never evaluate the registered cohort endpoint."""
    vectors=[0xe220a8397b1dcdaf,0x6e789e6aa1b965f4,0x06c45d188009454f]
    rng=SplitMix64(0)
    require([rng.next_u64() for _ in vectors]==vectors,"published-style seed-zero vectors failed")
    rng=SplitMix64(4103); stream=reference_words(4103)
    words=[next(stream) for _ in range(128)]
    require([rng.next_u64() for _ in words]==words, "PRNG word disagreement")
    rng=SplitMix64(4103); stream=reference_words(4103)
    for size in [0,1,2,10,17,40,3,13]:
        require(rng.permutation(size).tolist()==reference_permutation(size,stream),
                "continuing-stream Fisher-Yates disagreement")
    cutoff=(2**64//3)*3
    with patch.object(SplitMix64,"next_u64",side_effect=[cutoff,2**64-1,4]) as mocked:
        require(SplitMix64(4103).randbelow(3)==1 and mocked.call_count==3,
                "rejection boundary was accepted")
    records=[]
    for kind in ["ties","duplicates","asymmetric"]:
        frame=fixture(kind); edges=reference_edges(frame)
        require(production.mcj_neighbor_edges(frame).tolist()==[list(x) for x in edges],
                f"brute-force graph mismatch: {kind}")
        changed=frame.copy(); changed["rank"]=changed["rank"].iloc[::-1].tolist()
        require(np.array_equal(production.mcj_neighbor_edges(changed),production.mcj_neighbor_edges(frame)),
                "graph depends on rank")
        groups=[list(range(s*4,(s+1)*4)) for s in range(10)]
        require([g.tolist() for g in production.decile_groups(frame)]==groups,
                "stratum mismatch")
        ranks=frame["rank"].tolist(); stream=reference_words(4103); expected=[]
        trials=[]
        for _ in range(3):
            trial=ranks.copy()
            for group in groups:
                perm=reference_permutation(len(group),stream)
                for local,index in enumerate(group):
                    trial[index]=ranks[group[perm[local]]]
                require(Counter(trial[i] for i in group)==Counter(ranks[i] for i in group),
                        "within-stratum ranks changed")
            trials.append(trial)
            expected.append(float(-Fraction(sum(abs(trial[i]-trial[j]) for i,j in edges),len(edges))))
        actual=production._null_statistics_core(np.asarray(ranks),np.asarray(edges),
            [np.asarray(g) for g in groups],draws=3,seed=4103)
        require(np.allclose(actual,expected,rtol=0,atol=1e-15),
                f"three-draw null disagrees with original-rank continuing stream: {kind}")
        records.append({"fixture":kind,"rows":40,"edges":len(edges),
                        "null_draws":3,"null_statistics":actual.tolist(),
                        "permuted_rank_sha256":hashlib.sha256(json.dumps(trials).encode()).hexdigest()})
    # Unequal sizes exercise the exact floor(10*i/n) boundary rule.
    uneven=fixture("ties").iloc[:37]
    expected=[[i for i in range(37) if 10*i//37==s] for s in range(10)]
    require([g.tolist() for g in production.decile_groups(uneven)]==expected,"unequal stratum boundaries")
    return {"prng_words_checked":128,"seed_zero_vectors":vectors,
            "rejection_boundary_checked":True,"unequal_strata_checked":True,
            "fixtures":records}
