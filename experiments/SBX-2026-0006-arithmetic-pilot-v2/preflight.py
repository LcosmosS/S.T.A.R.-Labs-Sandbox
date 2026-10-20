"""Byte-pinned, exact arithmetic-only preflight for SBX-2026-0006.

This script deliberately NEVER computes the proposed inferential endpoint.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

SHA = "259f3846329395b371e8079c77a6f1097adaebc98a054974573e241416efa968"
SIZE = 2146401
COUNT = 64687
PAT = re.compile(r"(\d+)\s+([a-z]+)\s+(\d+)\s+\[(-?\d+(?:,-?\d+){4})\]\s+(\d+)\s+(\d+)")


def invariants(a):
    a1, a2, a3, a4, a6 = a
    b2 = a1*a1 + 4*a2
    b4 = 2*a4 + a1*a3
    b6 = a3*a3 + 4*a6
    b8 = a1*a1*a6 + 4*a2*a6 - a1*a3*a4 + a2*a3*a3 - a4*a4
    c4 = b2*b2 - 24*b4
    c6 = -b2**3 + 36*b2*b4 - 216*b6
    delta = -b2*b2*b8 - 8*b4**3 - 27*b6*b6 + 9*b2*b4*b6
    # Independent completed-square cubic discriminant formula.
    u, v, w = Fraction(b2, 4), Fraction(b4, 2), Fraction(b6, 4)
    cubic_disc = u*u*v*v - 4*v**3 - 4*u**3*w - 27*w*w + 18*u*v*w
    if delta == 0 or 16*cubic_disc != delta or c4**3-c6**2 != 1728*delta:
        raise ValueError("Singularity or exact invariant identity mismatch")
    return delta, Fraction(c4**3, delta)


def audit(source: Path):
    data = source.read_bytes()
    if len(data) != SIZE or hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError("ecdata bytes fail frozen SHA/size contract")
    lines = data.decode("ascii").splitlines()
    if len(lines) != COUNT:
        raise ValueError("Unexpected ecdata record count")
    groups = defaultdict(list)
    unique = set()
    for line, raw in enumerate(lines, start=1):
        m = PAT.fullmatch(raw)
        if m is None:
            raise ValueError("Malformed source line " + str(line))
        n, cls, num, ain, rank, torsion = m.groups()
        n, num, rank, torsion = map(int, (n,num,rank,torsion))
        if not (n>0 and num>0 and rank>=0 and torsion>0):
            raise ValueError("Invalid source arithmetic fields")
        label = (n, cls, num)
        if label in unique:
            raise ValueError("Duplicate curve label")
        unique.add(label)
        invariants(tuple(int(x) for x in ain.split(",")))
        groups[n].append((cls, rank))
    eligible = []
    for n, rows in groups.items():
        labels = Counter(c for c,_ in rows)
        within = sum(k*(k-1)//2 for k in labels.values())
        between = len(rows)*(len(rows)-1)//2 - within
        byrank = defaultdict(set)
        for cls, rank in rows:
            byrank[rank].add(cls)
        if len(labels)>=2 and within>0 and between>0 and any(len(s)>1 for s in byrank.values()):
            eligible.append(n)
    if not eligible:
        raise ValueError("No eligible conductor strata; abort without changing criteria")
    return {
        "experiment_id":"SBX-2026-0006","stage":"PREFLIGHT_ONLY",
        "primary_statistic_executed":False,"permutation_test_executed":False,
        "physical_claim":False,"scientific_status":"unverified",
        "full_source_sha256":SHA,"source_rows":len(lines),
        "eligible_conductor_count":len(eligible),
        "eligible_conductors_sha256":hashlib.sha256(
            (",".join(map(str,sorted(eligible)))+"\n").encode()).hexdigest(),
        "eligible_rows":sum(len(groups[n]) for n in eligible),
        "numerical_invariants":"PASS_EXACT_INTERNAL_IDENTITIES_ONLY",
        "external_sage_eclib_crosscheck":"NOT_RUN",
    }


def main():
    if len(sys.argv)==2 and sys.argv[1]=="--self-test":
        assert invariants((0,0,0,-1,0))==(64,Fraction(1728))
        assert invariants((0,0,0,0,1))==(-432,Fraction(0))
        print("SELF_TEST_PASS; no inference performed")
        return 0
    if len(sys.argv)!=2:
        print("Usage: preflight.py [--self-test | /path/to/allcurves.00000-09999]",file=sys.stderr)
        return 2
    print(json.dumps(audit(Path(sys.argv[1])),indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
