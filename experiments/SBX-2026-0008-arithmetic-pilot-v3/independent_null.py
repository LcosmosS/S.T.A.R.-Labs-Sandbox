"""Independent v3 permutation-reconstruction verifier (stdlib-only).

Does NOT import v2/v3 analysis or reuse its permutations or pair distances.
Same frozen 64,687-row ecdata source, deterministic stratum selection and seed.
Separate implementation of Fisher-Yates with Python MT getrandbits rejection.

Cross-check both the 1,999 null distributions (all seven variants) and exact
conditioned upper-tail Monte Carlo counts. This is independent *software*
cross-validation, NOT external scientist review or cosmic evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys

SOURCE_HASH = "259f3846329395b371e8079c77a6f1097adaebc98a054974573e241416efa968"
EXPECTED_ROWS = 64687
EXPECTED_BYTES = 2146401
FULL_STRATA = 3323
SUBSET_STRATA = 208
SUBSET_ROWS = 3324
SUBSET_PAIRS = 67094
SEED = 20261019
DRAWS = 1999
TIE_EPSILON = 1e-14
FLOAT_TOLERANCE = 5e-12  # numerical audit tolerance; not the inferential tie rule
VARIANTS = ("primary", "delta_29", "delta_31", "rank_half",
            "rank_double", "j_20", "j_80")
ROW = re.compile(r"(\d+) ([a-z]+) (\d+) \[(-?\d+(?:,-?\d+){4})\] (\d+) (\d+)")


def curve_invariants(coeff):
    a, b, c, d, e = coeff
    B2 = a * a + 4 * b
    B4 = 2 * d + a * c
    B6 = c * c + 4 * e
    B8 = (a * a * e + 4 * b * e - a * c * d + b * c * c - d * d)
    C4 = B2 * B2 - 24 * B4
    C6 = -B2 ** 3 + 36 * B2 * B4 - 216 * B6
    D = -B2 * B2 * B8 - 8 * B4 ** 3 - 27 * B6 ** 2 + 9 * B2 * B4 * B6
    if D == 0 or C4 ** 3 - C6 ** 2 != 1728 * D:
        raise ValueError("Independent exact curve identity failure")
    return D, Fraction(C4 ** 3, D)


def make_cohort(source):
    data = source.read_bytes()
    if len(data) != EXPECTED_BYTES or hashlib.sha256(data).hexdigest() != SOURCE_HASH:
        raise ValueError("Source bytes/SHA-256 differ from locked protocol")
    by_n = defaultdict(list)
    for line, text in enumerate(data.decode("ascii").splitlines(), 1):
        match = ROW.fullmatch(text)
        if match is None:
            raise ValueError(f"Malformed source at line {line}")
        n_str, cls, curve, ain, rank, torsion = match.groups()
        n = int(n_str)
        delta, j = curve_invariants(tuple(int(v) for v in ain.split(",")))
        by_n[n].append({"n": n, "class": cls, "rank": int(rank),
                        "torsion": int(torsion), "delta": delta, "j": j})
    if sum(len(g) for g in by_n.values()) != EXPECTED_ROWS:
        raise ValueError("Pinned catalog row count differs")
    eligible = []
    for n in sorted(by_n):
        rows = by_n[n]
        labels = Counter(r["class"] for r in rows)
        within = sum(v * (v - 1) // 2 for v in labels.values())
        total = len(rows) * (len(rows) - 1) // 2
        ranks = defaultdict(set)
        for row in rows:
            ranks[row["rank"]].add(row["class"])
        if len(labels) >= 2 and 0 < within < total and any(len(v)>1 for v in ranks.values()):
            eligible.append((n, rows))
    if len(eligible) != FULL_STRATA:
        raise ValueError(f"Full eligible conductor census {len(eligible)}")
    chosen = eligible[0::16]
    pairs = sum(len(g) * (len(g) - 1) // 2 for _, g in chosen)
    if (len(chosen), sum(len(g) for _,g in chosen), pairs) != (
            SUBSET_STRATA, SUBSET_ROWS, SUBSET_PAIRS):
        raise ValueError("Independent predeclared cohort census mismatch")
    return chosen


def feature(row, variant):
    ln10 = math.log(10.0)
    dden = 29 if variant=="delta_29" else 31 if variant=="delta_31" else 30
    rmul = 0.5 if variant=="rank_half" else 2.0 if variant=="rank_double" else 1.0
    jden = 20 if variant=="j_20" else 80 if variant=="j_80" else 40
    x = (
        math.log(abs(row["delta"])) / (dden * ln10),
        math.log(row["n"]) / (9 * ln10),
        rmul * row["rank"],
    )
    y = (
        math.log(row["n"]) / (9 * ln10),
        math.asinh(float(row["j"] / 1728)) / jden,
        math.log1p(row["torsion"]) / math.log(13.0),
    )
    if not all(map(math.isfinite, x + y)):
        raise ValueError("Nonfinite independent coordinate")
    return x, y


def build_groups(cohort):
    compiled = []
    for conductor, rows in cohort:
        labels = tuple(r["class"] for r in rows)
        blocks = defaultdict(list)
        for index, row in enumerate(rows):
            blocks[row["rank"]].append(index)
        embedding = [[feature(row, variant) for row in rows]
                     for variant in VARIANTS]
        distances = []
        count_same = 0
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                deltas = []
                for k in range(len(VARIANTS)):
                    lhs_i, rhs_i = embedding[k][i]
                    lhs_j, rhs_j = embedding[k][j]
                    deltas.append(math.dist(lhs_i,lhs_j) - math.dist(rhs_i,rhs_j))
                distances.append((i,j,deltas))
                if labels[i] == labels[j]:
                    count_same += 1
        if count_same <= 0 or len(distances) == count_same:
            raise ValueError("Independent null degenerate in chosen stratum")
        compiled.append((labels, tuple(tuple(blocks[k]) for k in sorted(blocks)),
                         distances, count_same, len(distances)-count_same))
    return compiled


def independent_stat(groups, labels=None):
    aggregate = [0.0] * len(VARIANTS)
    for pos, (baseline, _, pairs, nw, nb) in enumerate(groups):
        active = baseline if labels is None else labels[pos]
        if Counter(active) != Counter(baseline):
            raise ValueError("Independent null changed original label multiplicities")
        within = [0.0] * len(VARIANTS)
        between = [0.0] * len(VARIANTS)
        for i,j,distances in pairs:
            target = within if active[i] == active[j] else between
            for k,v in enumerate(distances):
                target[k] += v
        for k in range(len(VARIANTS)):
            aggregate[k] += between[k] / nb - within[k] / nw
    return tuple(t / len(groups) for t in aggregate)


def randbelow(n, rng):
    # Independent reconstruction of Random.shuffle's rejection-sampled range.
    bits = n.bit_length()
    while True:
        k = rng.getrandbits(bits)
        if k < n:
            return k


def fisher_yates(items, rng):
    for i in range(len(items)-1, 0, -1):
        j = randbelow(i+1, rng)
        items[i], items[j] = items[j], items[i]


def independently_shuffle(groups, rng):
    all_labels = []
    for labels, blocks, _, _, _ in groups:
        modified = list(labels)
        for block in blocks:
            work = [modified[i] for i in block]
            fisher_yates(work, rng)
            for k,val in zip(block, work):
                modified[k] = val
        all_labels.append(tuple(modified))
    return all_labels


def self_test():
    for seed in (0, 20261019, 123456789):
        reference = random.Random(seed)
        independent = random.Random(seed)
        for n in (1,2,3,7,20):
            a,b = list(range(n)),list(range(n))
            reference.shuffle(a)
            fisher_yates(b, independent)
            if a != b:
                raise AssertionError("Independent Fisher-Yates deviates from MT reference")
    d, j = curve_invariants((0,0,1,-1,0))
    assert d==37 and j==Fraction(110592,37)
    assert ROW.fullmatch("37 a 1 [0,0,1,-1,0] 1 1") is not None
    assert VARIANTS[0]=="primary" and DRAWS==1999
    print("PASS_INDEPENDENT_NULL_STATIC_FISHER_YATES_AND_EXACT_ARITHMETIC")


def verify(source, canonical, out):
    if out.exists():
        raise FileExistsError("Never overwrite independent verification outputs")
    result = json.loads((canonical/"result.json").read_text())
    manifest = json.loads((canonical/"run_manifest.json").read_text())
    for name, digest in manifest.get("artifact_sha256", {}).items():
        raw=(canonical/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError("Canonical artifact digest mismatch: " + name)
    if result.get("experiment_id") != "SBX-2026-0008" or result.get("draws") != DRAWS:
        raise ValueError("Wrong canonical experiment or draw count")
    cohort = make_cohort(source)
    groups = build_groups(cohort)
    observed = independent_stat(groups)
    stated = (result["primary"],*result["sensitivity"])
    if tuple(x["variant"] for x in stated) != VARIANTS:
        raise ValueError("Canonical sensitivity ordering drift")
    observed_error = max(abs(x["T_observed"]-y) for x,y in zip(stated,observed))
    if observed_error>FLOAT_TOLERANCE:
        raise ValueError(f"Independent observed statistic mismatch: {observed_error}")
    null_path=canonical/"null_distribution.csv"
    with null_path.open(newline="",encoding="utf-8") as fh:
        actual=list(csv.DictReader(fh))
    if len(actual)!=DRAWS:
        raise ValueError("Canonical null distribution missing draws")
    counts=[0]*len(VARIANTS)
    max_error=0.0
    output=[]
    rng=random.Random(SEED)
    for draw in range(1,DRAWS+1):
        scrambled=independently_shuffle(groups,rng)
        stat=independent_stat(groups,scrambled)
        row=actual[draw-1]
        if int(row["draw"])!=draw:
            raise ValueError("Canonical null draw number not ordered")
        for k,name in enumerate(VARIANTS):
            err=abs(float(row[name])-stat[k])
            max_error=max(max_error,err)
            if err>FLOAT_TOLERANCE:
                raise ValueError(f"Independent null mismatch draw {draw} {name}: {err}")
            if stat[k]>=observed[k]-TIE_EPSILON:
                counts[k]+=1
        output.append((draw,*stat))
    mismatches=[]
    for k,name in enumerate(VARIANTS):
        if int(stated[k]["null_at_least_as_extreme"])!=counts[k]:
            mismatches.append(name)
        if abs((counts[k]+1)/2000-stated[k]["p_one_sided"])>1e-14:
            mismatches.append(name+":pvalue")
    if mismatches:
        raise ValueError("Independent tail classification mismatch: "+",".join(mismatches))
    out.mkdir(parents=True,exist_ok=False)
    nullfile=out/"null_distribution_independent.csv"
    with nullfile.open("w",newline="",encoding="utf-8") as fh:
        writer=csv.writer(fh)
        writer.writerow(("draw", *VARIANTS))
        writer.writerows(output)
    evidence={
        "schema_version":1,"experiment_id":"SBX-2026-0008",
        "stage":"INDEPENDENT_SOFTWARE_NULL_CROSSCHECK_PASS",
        "source_sha256":SOURCE_HASH,"draws":DRAWS,
        "full_eligible_strata":FULL_STRATA,"selected_strata":SUBSET_STRATA,
        "selected_rows":SUBSET_ROWS,"selected_pairs":SUBSET_PAIRS,
        "seed":SEED,"variant_order":VARIANTS,
        "tail_counts":dict(zip(VARIANTS,counts)),
        "observed_max_abs_error":observed_error,
        "null_max_abs_error":max_error,
        "max_allowed_float_error":FLOAT_TOLERANCE,
        "matched_all_draws":True,"matched_all_tail_counts":True,
        "independent_implementations":"standalone standard-library formulas, pair means and Fisher-Yates getrandbits; no import of v2/v3 analysis",
        "scientific_independent_review":False,"physical_support":False,
        "automatic_promotion":False,
    }
    summary=out/"independent_summary.json"
    summary.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    record={
        "experiment_id":"SBX-2026-0008",
        "stage":"CROSSCHECK_INTEGRITY_ONLY",
        "artifacts_sha256":{
            p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (summary,nullfile)
        },
        "scientific_support":False,
    }
    (out/"independent_manifest.json").write_text(
        json.dumps(record,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return evidence


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path)
    p.add_argument("--canonical",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test()
        return 0
    if a.source is None or a.canonical is None or a.out is None:
        p.error("--source, --canonical and --out required unless --self-test")
    verified=verify(a.source,a.canonical,a.out)
    print(json.dumps({"experiment_id":verified["experiment_id"],
        "status":verified["stage"],"matched_all_draws":True,
        "matched_all_tail_counts":True},sort_keys=True))


if __name__=="__main__":
    raise SystemExit(main())
