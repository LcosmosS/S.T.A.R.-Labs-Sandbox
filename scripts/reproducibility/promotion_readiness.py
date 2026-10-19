"""Non-blocking, read-only completeness audit; it grants no scientific status.

No untrusted experiment code execution, no external services, no registry writes.
A missing field is a reported gap, never a CI exception that blocks Sandbox admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
FIELDS = (
    ('mathematical_objects','first_principles.objects'),
    ('domain_and_assumptions','first_principles.domain_and_assumptions'),
    ('coordinate_rules','first_principles.coordinate_rules'),
    ('dimensional_analysis','first_principles.dimensional_analysis'),
    ('known_no_go','first_principles.known_no_go'),
    ('primary_endpoint','primary_endpoint.definition'),
    ('conditional_null','primary_endpoint.null'),
    ('null_seed','primary_endpoint.seed'),
    ('null_draws','primary_endpoint.draws'),
    ('numerical_uncertainty','numerical_uncertainty'),
    ('falsifiers','falsifiers'),
    ('controls','controls'),
    ('source_identity','input_source.sha256'),
    ('source_commit','input_source.commit'),
    ('frozen_output','frozen_output'),
    ('explicit_discrepancy_register','unresolved_discrepancies'),
    ('observational_stage_status','observational_stage.status'),
)


def present(item):
    return isinstance(item,(str,list,dict)) and bool(item) or type(item) is int


def safe_load(root, rel):
    p=PurePosixPath(rel)
    if p.is_absolute() or '..' in p.parts or str(p)!=rel or '\\' in rel:
        raise ValueError('Unsafe relative path')
    root=root.resolve()
    path=root.joinpath(*p.parts)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError('Untrusted path or missing file')
    return path.read_bytes()


def get(nested,path):
    for key in path.split('.'):
        if not isinstance(nested,dict): return None
        nested=nested.get(key)
    return nested


def examine(experiment):
    gaps=[]; present_fields=[]; artifacts=[]
    ex_id=experiment.name[:13]
    try: meta=json.loads(safe_load(experiment,'metadata.json'))
    except (OSError,ValueError,UnicodeError,json.JSONDecodeError) as error:
        meta={};gaps.append('invalid_or_missing_metadata: '+str(error))
    if meta.get('id')!=ex_id or meta.get('scope')!='sandbox-only':
        gaps.append('experiment_identity_and_scope')
    try: protocol=json.loads(safe_load(experiment,'study_protocol.json'))
    except (OSError,ValueError,UnicodeError,json.JSONDecodeError):
        protocol={};gaps.append('frozen_study_protocol')
    if protocol and protocol.get('experiment_id')!=ex_id:
        gaps.append('protocol_id_mismatch')
    for label, field in FIELDS:
        value=get(protocol,field)
        if present(value): present_fields.append(label)
        else: gaps.append(label)
    try: contract=json.loads(safe_load(experiment,'reproducibility.json'))
    except (OSError,ValueError,UnicodeError,json.JSONDecodeError):
        contract={};gaps.append('hash_locked_reproducibility_contract')
    if contract and (contract.get('experiment_id')!=ex_id or contract.get('scope')!='sandbox-only'):
        gaps.append('contract_identity_and_scope')
    for entry in contract.get('artifacts',[]) if isinstance(contract.get('artifacts',[]),list) else []:
        path=entry.get('path') if isinstance(entry,dict) else None
        try:
            if not isinstance(path,str): raise ValueError('invalid path')
            data=safe_load(experiment,path)
            ok=(entry.get('sha256')==hashlib.sha256(data).hexdigest()
                and entry.get('size_bytes')==len(data))
        except (ValueError,OSError,UnicodeError): ok=False
        artifacts.append({'path':path or '(invalid)', 'bytes_and_sha256_match':ok})
        if not ok: gaps.append('artifact_hash_or_size:'+str(path))
    if not artifacts: gaps.append('no_hashed_artifacts')
    frozen=protocol.get('frozen_output')
    if frozen and not any(a['path']==frozen and a['bytes_and_sha256_match'] for a in artifacts):
        gaps.append('frozen_output_not_hashed')
    stage=get(protocol,'observational_stage.status')
    physical_stage_complete=(stage=='complete')
    if not physical_stage_complete:
        gaps.append('physical_observational_stage_incomplete')
    return {
        'experiment_id':ex_id,'scope':'sandbox-only',
        'documented_fields':present_fields,'artifact_checks':artifacts,
        'gaps':sorted(set(gaps)),
        'documentation_complete_except_observations':
            not any(k!='physical_observational_stage_incomplete' for k in gaps),
        'physical_observational_stage_complete':physical_stage_complete,
        'independent_review_performed':False,
        'automatic_promotion':False,'approval_or_eligibility_granted':False,
        'disposition':'read_only_completeness_diagnostic_not_a_gate',
    }


def scan(root):
    exdir=root/'experiments'
    if not exdir.is_dir(): return []
    return [examine(x) for x in sorted(exdir.iterdir()) if x.is_dir() and x.name.startswith('SBX-')]


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,default=None)
    options=parser.parse_args(argv)
    data={'scope':'sandbox-only','evaluation':'report_only',
          'independent_scientific_review':False,'automatic_promotion':False,
          'approval_gate':False,'experiments':scan(options.root)}
    text=json.dumps(data,indent=2,sort_keys=True)+'\n'
    if options.output:
        if options.output.is_symlink(): raise SystemExit('Symlink report path forbidden')
        options.output.write_text(text,encoding='utf-8')
    else: print(text,end='')
    return 0  # Incomplete science must NOT block Sandbox admission.

if __name__=='__main__':raise SystemExit(main())
