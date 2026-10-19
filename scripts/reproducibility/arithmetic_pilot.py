"""Audited, standard-library-only REAL arithmetic pilot; no physical correspondence test.

Run only this allowlisted instrument, not arbitrary programs from SBX directories.
The publication/evidence gate is deliberately absent.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import random
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/SBX-2026-0004-arithmetic-isogeny-geometry'
ORIGIN_SHA256 = '259f3846329395b371e8079c77a6f1097adaebc98a054974573e241416efa968'
ORIGIN_COMMIT = '25cec5ecfec8b9f016eb1631ac633194c2bed39f'
COLS = ['source_line','conductor','isogeny','number','a1','a2','a3','a4','a6','rank','torsion_order']
SEED = 20261019
DRAWS = 999


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def curves_from_bytes(data: bytes):
    text = data.decode('utf-8')
    reader = csv.DictReader(io.StringIO(text, newline=''))
    if reader.fieldnames != COLS:
        raise ValueError('Input columns are not exactly the frozen schema')
    rows = []
    for item in reader:
        row = {key: int(v) if key != 'isogeny' else v for key,v in item.items()}
        if any(row[k] < 0 for k in ('rank','number','torsion_order','conductor')):
            raise ValueError('Invalid nonnegative arithmetic field')
        if not (row['conductor'] > 0 and row['torsion_order'] > 0 and row['isogeny'].isalpha()):
            raise ValueError('Invalid arithmetic curve field')
        if 0 < row['source_line'] <= 64687:
            rows.append(row)
        else:
            raise ValueError('Invalid source line')
    if len(rows) != 38 or len({r['source_line'] for r in rows}) != 38:
        raise ValueError('Frozen cohort must contain exactly 38 distinct source lines')
    if [r['source_line'] for r in rows] != sorted(r['source_line'] for r in rows):
        raise ValueError('Cohort has been reordered')
    if len({(r['conductor'],r['isogeny'],r['number']) for r in rows}) != len(rows):
        raise ValueError('Duplicate curve label')
    return rows


def canonical_line(r):
    a = ','.join(str(r[f'a{i}']) for i in (1,2,3,4,6))
    return f"{r['conductor']} {r['isogeny']} {r['number']} [{a}] {r['rank']} {r['torsion_order']}"


def verify_source(rows, full_source: Path):
    raw = full_source.read_bytes()
    if len(raw) != 2146401 or digest(raw) != ORIGIN_SHA256:
        raise ValueError('Pinned ecdata source bytes or digest differ')
    lines = raw.decode('ascii').splitlines()
    if len(lines) != 64687:
        raise ValueError('Source row census differs')
    for row in rows:
        if lines[row['source_line']-1] != canonical_line(row):
            raise ValueError('Source row differs at line %s' % row['source_line'])


def invariants(r):
    a1,a2,a3,a4,a6 = (r[f'a{i}'] for i in (1,2,3,4,6))
    b2 = a1*a1 + 4*a2
    b4 = 2*a4 + a1*a3
    b6 = a3*a3 + 4*a6
    b8 = a1*a1*a6 + 4*a2*a6 - a1*a3*a4 + a2*a3*a3 - a4*a4
    delta = -b2*b2*b8-8*b4**3-27*b6*b6+9*b2*b4*b6
    c4 = b2*b2-24*b4
    if delta == 0:
        raise ValueError('Singular input elliptic curve')
    return delta, c4**3/delta


def embeddings(rows):
    acsc, mcj = [], []
    for r in rows:
        delta, j = invariants(r)
        # Frozen ACSC-like normalized longitude/latitude/rank.
        # Original altitude 200m * rank is divided by fixed 200m for a
        # dimensionless arithmetic metric; NOT a physical 3D embedding.
        acsc.append((math.log(abs(delta))/math.log(10**30),
                     math.log(r['conductor'])/math.log(10**9),
                     float(r['rank'])))
        # Explicitly MODIFIED MCJ-inspired BSD-independent competitor:
        # asinh(j/1728) avoids undefined log(j) at j=0/negative rational j.
        # The torsion axis replaces degenerate Im(log(j)) for E/Q.
        mcj.append((math.log(r['conductor'])/math.log(10**9),
                    math.asinh(j/1728)/40.0,
                    math.log1p(r['torsion_order'])/math.log(13)))
    return acsc, mcj


def groups(rows):
    output = {}
    for i, row in enumerate(rows):
        output.setdefault(row['conductor'], []).append(i)
    if any(len({rows[i]['isogeny'] for i in ids}) < 2 for ids in output.values()):
        raise ValueError('All frozen conductor strata need >=2 isogeny classes')
    return output


def contrast(coords, labels, strata):
    # For each conductor: within-class vs between-class Euclidean distances.
    # Conductor is constant in both groups, avoiding trivial cross-N purity.
    values = []
    for ids in strata.values():
        within, between = [], []
        for ii, i in enumerate(ids):
            for k in ids[ii+1:]:
                dist = math.dist(coords[i],coords[k])
                (within if labels[i]==labels[k] else between).append(dist)
        if not within or not between:
            raise ValueError('Missing within/between pairs')
        values.append(mean(between)-mean(within))
    return mean(values)


def compute(source_bytes):
    rows=curves_from_bytes(source_bytes)
    strata=groups(rows)
    a,b=embeddings(rows)
    labels=[r['isogeny'] for r in rows]
    aobs=contrast(a,labels,strata)
    bobs=contrast(b,labels,strata)
    stat=aobs-bobs   # SINGLE primary endpoint, positive favors ACSC-like geometry
    # Rank is an ACSC coordinate and an isogeny invariant. Preserve it
    # inside the null to avoid awarding ACSC trivial rank-class separation.
    conditional={}
    for i,r in enumerate(rows):
        conditional.setdefault((r['conductor'], r['rank']),[]).append(i)
    if sum(len({labels[i] for i in ids})>1 for ids in conditional.values())<4:
        raise ValueError('Insufficient within-(conductor,rank) contrasts for null')
    rng=random.Random(SEED)
    samples=[]
    for _ in range(DRAWS):
        perm=labels.copy()
        for ids in conditional.values():
            values=[perm[i] for i in ids]
            rng.shuffle(values)
            for i,v in zip(ids,values):
                perm[i]=v
        samples.append(contrast(a,perm,strata)-contrast(b,perm,strata))
    count=sum(s >= stat-1e-14 for s in samples)
    p=(count+1)/(DRAWS+1)
    # Transparently preserve the earlier inappropriate exploratory null result.
    # Not a second primary endpoint; no multiple-testing claim.
    uncond_rng=random.Random(SEED)
    uncond=[]
    for _ in range(DRAWS):
        perm=labels.copy()
        for ids in strata.values():
            values=[perm[i] for i in ids]
            uncond_rng.shuffle(values)
            for i,v in zip(ids,values): perm[i]=v
        uncond.append(contrast(a,perm,strata)-contrast(b,perm,strata))
    exploratory_unconditioned_p=(1+sum(t >= stat-1e-14 for t in uncond))/(DRAWS+1)
    result={
      'experiment_id':'SBX-2026-0004','status':'exploratory','scope':'sandbox-only',
      'scientific_claim':False,'observational_stage':'not_started',
      'source':{'repo':'JohnCremona/ecdata','commit':ORIGIN_COMMIT,
                'file':'allcurves/allcurves.00000-09999',
                'file_sha256':ORIGIN_SHA256,'rows_in_full_source':64687,
                'frozen_subset_sha256':digest(source_bytes),
                'subset_rows':len(rows),'source_lines':[r['source_line'] for r in rows]},
      'method':{'statistic':'mean_per_conductor(between_minus_within_distance)_ACSC_minus_modified_MCJ',
        'distances':'ordinary Euclidean distances in frozen dimensionless coordinates',
        'null':'999 label shuffles within each (conductor, rank) stratum, retaining class sizes and all features; rank is a coordinate and isogeny invariant',
        'seed':SEED,'null_draws':DRAWS,'tail':'greater_or_equal',
        'p_rule':'(1 + count(null >= observed - 1e-14))/(B+1)',
        'alpha_descriptive':0.05,'selected_after_seeing_results':True,
        'analysis_history':'An initial unconditioned conductor-only label shuffle gave p=0.005; rank conditioning was added after inspecting that result because rank is explicitly encoded in ACSC. Neither analysis is confirmatory.'},
      'statistics':{'acsc_contrast':round(aobs,12),'modified_mcj_contrast':round(bobs,12),
          'primary_difference':round(stat,12),'null_ge_observed':count,
          'earlier_unconditioned_p_unsafe_diagnostic_only':exploratory_unconditioned_p,
          'empirical_p':p,'monte_carlo_standard_error':round(math.sqrt(p*(1-p)/(DRAWS+1)),8),
          'null_mean':round(mean(samples),12),'null_min':round(min(samples),12),
          'null_max':round(max(samples),12)},
      'interpretation':('arithmetic_only_no_cosmological_observation',
          'selected_low_conductor_subset_not_representative',
          'isogeny_label_is_arithmetic_grouping_not_physical_response',
          'small_p_value_is_not_physical_ACSC_support'),
      'promoted':False,'independently_reviewed':False,
    }
    return (json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,help='optional exact pinned 64,687-line source for full-row verification')
    parser.add_argument('--check',action='store_true',help='fail on frozen result drift')
    parser.add_argument('--output',type=Path,help='write output to a NEW non-symlink path')
    opts=parser.parse_args()
    raw=(EXP/'curves.csv').read_bytes()
    rows=curves_from_bytes(raw)
    if opts.source: verify_source(rows,opts.source)
    result=compute(raw)
    if opts.check:
        if (EXP/'result.json').read_bytes()!=result:
            raise SystemExit('FAIL: frozen arithmetic pilot result drift')
        print('PASS: frozen real-arithmetic pilot reproduces exact output')
    elif opts.output:
        if opts.output.exists() or opts.output.is_symlink():
            raise SystemExit('Refusing to overwrite existing result')
        opts.output.write_bytes(result)
        print('Wrote exploratory result to',opts.output)
    else: print(result.decode(),end='')

if __name__=='__main__': main()
