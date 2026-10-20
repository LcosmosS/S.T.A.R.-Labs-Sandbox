"""SBX-2026-0008: optional locked v3 runner, not executed in CI.

Requires source-bound SBX-2026-0006 core and preflight at exact Git blob SHA.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import random
import sys
import subprocess
import math

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V2=ROOT/"experiments/SBX-2026-0006-arithmetic-pilot-v2"
ANALYSIS_BLOB="ccdf7676a5f9545886f015905ef9b5b4546b2c70"
PREFLIGHT_BLOB="577b6b6e37f29d375aabb1b61d15369f64fd5c37"
STRIDE=16
OFFSET=0
EXPECTED_CONDUCTORS=208
EXPECTED_CURVES=3324
EXPECTED_PAIRS=67094
DRAWS=1999
SEED=20261019
CAP=300000


def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def load_core():
    corefile=V2/"analysis.py"
    preflight=V2/"preflight.py"
    if git_blob(corefile.read_bytes()) != ANALYSIS_BLOB or git_blob(preflight.read_bytes()) != PREFLIGHT_BLOB:
        raise ValueError("V2 core/preflight Git blob identity drift; abort")
    sys.path.insert(0,str(V2))
    spec=importlib.util.spec_from_file_location("locked_arithmetic_v2",corefile)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(source,out):
    if out.exists():
        raise FileExistsError("Output directory must not exist; never overwrite runs")
    core=load_core()
    if core.DRAWS != 1999 or core.SEED != SEED or core.MAX_PAIRS != CAP:
        raise ValueError("Core environment/protocol semantics changed")
    all_eligible,preflight=core.load_selected(source)
    selected=all_eligible[OFFSET::STRIDE]
    count=sum(len(g) for _,g in selected)
    if len(all_eligible)!=3323 or len(selected)!=EXPECTED_CONDUCTORS or count!=EXPECTED_CURVES:
        raise ValueError("Unexpected source cohort census; no post-hoc filtering")
    groups,pair_count=core.pairwise(selected)
    if pair_count!=EXPECTED_PAIRS or pair_count>CAP:
        raise ValueError("Cohort pair budget mismatch")
    observed=core.statistic(groups)
    rng=random.Random(SEED)
    variants=core.VARIANTS
    if variants!=("primary","delta_29","delta_31","rank_half","rank_double","j_20","j_80"):
        raise ValueError("Unfrozen variant list")
    counts=[0]*len(variants)
    nulls=[]
    for i in range(1,DRAWS+1):
        vals=core.statistic(groups,core.shuffled(groups,rng))
        nulls.append((i,*vals))
        for k,v in enumerate(vals):
            if v>=observed[k]-1e-14:
                counts[k]+=1
    buffer=io.StringIO(newline="")
    w=csv.writer(buffer,lineterminator="\n")
    w.writerow(("draw",*variants))
    w.writerows(nulls)
    nulldist=buffer.getvalue().encode()
    results=[]
    for k,v in enumerate(variants):
        p=(counts[k]+1)/(DRAWS+1)
        results.append({"variant":v,"T_observed":observed[k],"T_float_hex":observed[k].hex(),
                        "p_one_sided":p,"null_at_least_as_extreme":counts[k],
                        "monte_carlo_se":math.sqrt(p*(1-p)/(DRAWS+1)),
                        "physical_support":False})
    protocol=(HERE/"protocol_v3.json").read_bytes()
    thisscript=Path(__file__).read_bytes()
    rawsrc=source.read_bytes()
    if hashlib.sha256(rawsrc).hexdigest()!=core.SHA:
        raise ValueError("Source digest drift")
    report={"experiment_id":"SBX-2026-0008","status":"exploratory","physical_observations":0,
            "automatic_promotion":False,"scientifically_reviewed":False,
            "source_sha256":core.SHA,"rows_in_pinned_source":preflight["source_rows"],
            "eligible_conductors_full":len(all_eligible),"selected_conductors":len(selected),
            "selected_curves":count,"pair_count":pair_count,"seed":SEED,"draws":DRAWS,
            "primary":results[0],"sensitivity":results[1:],
            "protocol_sha256":hashlib.sha256(protocol).hexdigest(),
            "runner_sha256":hashlib.sha256(thisscript).hexdigest(),
            "v2_analysis_git_blob":ANALYSIS_BLOB,"v2_preflight_git_blob":PREFLIGHT_BLOB,
            "environment":{"python":platform.python_version(),"platform":platform.platform()},
            "unresolved":["External Sage/eclib NOT_RUN","Independent null reconstruction NOT_RUN",
                          "Cosmic correspondence NOT_STARTED"]}
    out.mkdir(parents=True,exist_ok=False)
    (out/"null_distribution.csv").write_bytes(nulldist)
    result_data=(json.dumps(report,indent=2,sort_keys=True)+"\n").encode()
    (out/"result.json").write_bytes(result_data)
    hashes={"result.json":hashlib.sha256(result_data).hexdigest(),
            "null_distribution.csv":hashlib.sha256(nulldist).hexdigest()}
    manifest={"experiment_id":"SBX-2026-0008","scope":"sandbox-only","artifact_sha256":hashes,
              "protocol_sha256":report["protocol_sha256"],
              "runner_sha256":report["runner_sha256"],"status":"EXPLORATORY_NOT_VALIDATED",
              "scientific_support":False,"external_validation":"NOT_RUN"}
    (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        core=load_core()
        assert core.SHA == "259f3846329395b371e8079c77a6f1097adaebc98a054974573e241416efa968"
        assert core.DRAWS == DRAWS == 1999 and core.SEED == SEED == 20261019
        assert core.MAX_PAIRS == CAP == 300000
        assert core.VARIANTS == ("primary","delta_29","delta_31","rank_half","rank_double","j_20","j_80")
        d,j=core.invariants((0,0,1,-1,0))
        assert d == 37 and (j.numerator,j.denominator) == (110592,37)
        print("PASS_STATIC_V3_CORE_LOCK_AND_SOURCE_SHA_SYMBOL; NO INFERENCE")
        return 0
    if args.source is None or args.out is None:
        p.error("--source and --out required except --self-test")
    report=run(args.source,args.out)
    print(json.dumps({"experiment_id":report["experiment_id"],"primary":report["primary"],
                      "unresolved":report["unresolved"]},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
