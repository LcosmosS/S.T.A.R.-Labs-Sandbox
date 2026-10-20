"""Optional, standard-library, deterministic SBX-2026-0006 arithmetic diagnostic.

NOT run by Sandbox CI. Does not use cosmological data or grant scientific support.
Run only after committing the frozen v2 protocol.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import random
import sys

from preflight import PAT, SHA, audit, invariants

HERE = Path(__file__).resolve().parent
SEED = 20261019
DRAWS = 1999
VARIANTS = ("primary", "delta_29", "delta_31", "rank_half",
            "rank_double", "j_20", "j_80")
MAX_PAIRS = 300000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_selected(source: Path):
    # Strong authentication and independent arithmetic identities, no inferential use.
    diagnostic = audit(source)
    by_conductor = defaultdict(list)
    rows = source.read_bytes().decode("ascii").splitlines()
    for line, raw in enumerate(rows, start=1):
        m = PAT.fullmatch(raw)
        if m is None:
            raise ValueError("Malformed pinned source row at line " + str(line))
        n, cls, number, ain, rank, torsion = m.groups()
        delta, j = invariants(tuple(map(int, ain.split(","))))
        n, rank, torsion = int(n), int(rank), int(torsion)
        by_conductor[n].append({
            "label": cls, "rank": rank, "torsion": torsion,
            "n": n, "delta": delta, "j": j, "source_line": line,
        })
    eligible = []
    for n in sorted(by_conductor):
        group = by_conductor[n]
        labels = Counter(r["label"] for r in group)
        within = sum(v*(v-1)//2 for v in labels.values())
        between = len(group)*(len(group)-1)//2 - within
        rank_groups = defaultdict(set)
        for row in group:
            rank_groups[row["rank"]].add(row["label"])
        if len(labels)>=2 and within and between and any(len(x)>1 for x in rank_groups.values()):
            eligible.append((n, group))
    if len(eligible) != diagnostic["eligible_conductor_count"]:
        raise ValueError("Cohort rule differs from independent preflight")
    row_count = sum(len(g) for _,g in eligible)
    if row_count != diagnostic["eligible_rows"]:
        raise ValueError("Cohort row census differs from exact preflight")
    return eligible, diagnostic


def coords(row, variant):
    dden = 29 if variant == "delta_29" else 31 if variant == "delta_31" else 30
    rankmult = 0.5 if variant == "rank_half" else 2.0 if variant == "rank_double" else 1.0
    jden = 20 if variant == "j_20" else 80 if variant == "j_80" else 40
    a = (math.log(abs(row["delta"])) / (dden*math.log(10.0)),
         math.log(row["n"]) / (9*math.log(10.0)),
         rankmult * row["rank"])
    try:
        jaxis = math.asinh(float(row["j"] / 1728)) / jden
    except OverflowError as e:
        raise ValueError("Unbounded j axis; fail rather than clip") from e
    b = (math.log(row["n"])/(9*math.log(10.0)),
         jaxis, math.log1p(row["torsion"]) / math.log(13.0))
    if not all(math.isfinite(x) for x in (*a,*b)):
        raise ValueError("Nonfinite arithmetic coordinate")
    return a,b


def pairwise(eligible):
    groups = []
    pair_total = 0
    for n,rows in eligible:
        labels = tuple(r["label"] for r in rows)
        rankblocks = defaultdict(list)
        for i,r in enumerate(rows):
            rankblocks[r["rank"]].append(i)
        embeddings = [[coords(r,v) for r in rows] for v in VARIANTS]
        pairs = []
        total = [0.0]*len(VARIANTS)
        within_count = 0
        for i in range(len(rows)):
            for j in range(i+1,len(rows)):
                value = tuple(math.dist(embeddings[k][i][0], embeddings[k][j][0])
                              - math.dist(embeddings[k][i][1], embeddings[k][j][1])
                              for k in range(len(VARIANTS)))
                if not all(math.isfinite(x) for x in value):
                    raise ValueError("Nonfinite distance difference")
                pairs.append((i,j,value))
                if labels[i] == labels[j]:
                    within_count+=1
                for k,v in enumerate(value):
                    total[k]+=v
        between_count=len(pairs)-within_count
        if not (within_count and between_count):
            raise ValueError("Degenerate within/between pairs; no silent exclusions")
        pair_total+=len(pairs)
        if pair_total>MAX_PAIRS:
            raise RuntimeError("Predeclared resource limit exceeded: abort all analysis without downsampling")
        groups.append({
            "conductor":n,"labels":labels,
            "blocks":[tuple(ids) for _,ids in sorted(rankblocks.items())],
            "pairs":pairs,"total":total,"within":within_count,"between":between_count,
        })
    return groups,pair_total


def statistic(groups, replacements=None):
    accum=[0.0]*len(VARIANTS)
    for idx,g in enumerate(groups):
        labels=g["labels"] if replacements is None else replacements[idx]
        if Counter(labels)!=Counter(g["labels"]):
            raise ValueError("Conditional label multiplicity changed")
        within=[0.0]*len(VARIANTS)
        for i,j,vals in g["pairs"]:
            if labels[i]==labels[j]:
                for k,v in enumerate(vals):
                    within[k]+=v
        for k in range(len(VARIANTS)):
            value=((g["total"][k]-within[k])/g["between"]
                   - within[k]/g["within"])
            accum[k]+=value
    if not groups:
        raise ValueError("Empty eligible cohort")
    return tuple(v/len(groups) for v in accum)


def shuffled(groups,rng):
    replacements=[]
    for g in groups:
        labels=list(g["labels"])
        for block in g["blocks"]:
            group=[labels[i] for i in block]
            rng.shuffle(group)
            for i,value in zip(block,group):
                labels[i]=value
        replacements.append(tuple(labels))
    return replacements


def run(source: Path, out: Path):
    if out.exists():
        raise FileExistsError("Never overwrite an existing run directory")
    eligible, preflight=load_selected(source)
    groups,pair_count=pairwise(eligible)
    observed=statistic(groups)
    rng=random.Random(SEED)
    counts=[0]*len(VARIANTS)
    nulls=[]
    for draw in range(1,DRAWS+1):
        result=statistic(groups,shuffled(groups,rng))
        nulls.append((draw,*result))
        for k,v in enumerate(result):
            if v >= observed[k]-1e-14:
                counts[k]+=1
    csvfile=io.StringIO(newline="")
    writer=csv.writer(csvfile,lineterminator="\n")
    writer.writerow(("draw",*VARIANTS))
    writer.writerows(nulls)
    distribution=csvfile.getvalue().encode()
    conclusions=[]
    for k,name in enumerate(VARIANTS):
        p=(counts[k]+1)/(DRAWS+1)
        conclusions.append({
            "variant":name,"T_observed":observed[k],
            "T_float_hex":observed[k].hex(),
            "null_at_least_as_extreme":counts[k],"p_one_sided":p,
            "monte_carlo_se":math.sqrt(p*(1-p)/(DRAWS+1)),
            "confirmatory":False,"physical_correspondence":False,
        })
    protocol=(HERE/"preanalysis_protocol.json").read_bytes()
    script=Path(__file__).read_bytes()
    report={
        "experiment_id":"SBX-2026-0006","stage":"EXPLORATORY_INFERENCE",
        "scope":"sandbox-only","independently_reviewed":False,
        "eligible_for_automatic_promotion":False,"physical_observations_used":0,
        "source_sha256":SHA,"source_rows":preflight["source_rows"],
        "eligible_rows":preflight["eligible_rows"],
        "eligible_conductors":preflight["eligible_conductor_count"],
        "pair_count":pair_count,"permutation_seed":SEED,"draws":DRAWS,
        "null":"label Fisher-Yates shuffles within (conductor,rank) blocks",
        "tail":"greater_or_equal_with_1e-14_tolerance",
        "alpha_descriptive":0.05,"sensitivity_design":"one_factor_at_a_time",
        "input_protocol_sha256":sha(protocol),"analysis_source_sha256":sha(script),
        "environment":{"python":platform.python_version(),"platform":platform.platform()},
        "primary":conclusions[0],"sensitivity":conclusions[1:],
        "unresolved":["Independent Sage/eclib crosscheck NOT_RUN",
                      "Independent null implementation NOT_RUN",
                      "Held-out observational comparison NOT_STARTED",
                      "No mathematical/physical support assertion"],
    }
    out.mkdir(parents=True,exist_ok=False)
    (out/"null_distribution.csv").write_bytes(distribution)
    result_bytes=(json.dumps(report,indent=2,sort_keys=True)+"\n").encode()
    (out/"result.json").write_bytes(result_bytes)
    manifest={
        "stage":"EXPLORATORY_OUTPUT_INTEGRITY_ONLY",
        "source_sha256":SHA,
        "protocol_sha256":sha(protocol),
        "analysis_source_sha256":sha(script),
        "artifacts":{"result.json":sha(result_bytes),
                     "null_distribution.csv":sha(distribution)},
        "scientific_support":False,
    }
    (out/"run_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=run(args.source,args.out)
    print(json.dumps({
        "experiment_id":report["experiment_id"],
        "output":str(args.out),"stage":report["stage"],
        "primary":report["primary"],
        "unresolved":report["unresolved"],
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
