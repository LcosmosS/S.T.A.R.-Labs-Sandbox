"""Read-only recovery validation and isolated diagnostic processing.

No recovered Python, Sage, GP, notebook or pickle is imported or executed.
No catalogue is merged into a controlled input or existing output directory.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
from collections import Counter

INTAKE = 'data/intake/recovered/2026-10-08/manifest.json'
CODE = 'historical/r&d/code_log/2026-10-08_recovered/manifest.json'
QUARANTINE = 'data/quarantine/2026-10-03_audit/relocation.json'
ENVIRONMENT_HISTORY = 'historical/r&d/docs/recovered_corpus_audit_2026-10-08/upstream_environment_integrity.json'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def source_path(repo, relative):
    path = (repo / relative).resolve()
    if not path.is_relative_to(repo.resolve()) or not path.is_file():
        raise ValueError(f'Invalid or missing source path: {relative}')
    return path


def read_json(repo, relative):
    return json.loads(source_path(repo, relative).read_text(encoding='utf-8'))


def verify(repo, records):
    seen = {}
    for record in records:
        relative = record['path']
        if relative in seen and seen[relative] != record['sha256']:
            raise ValueError(f'Conflicting digest for {relative}')
        seen[relative] = record['sha256']
        path = source_path(repo, relative)
        with path.open('rb') as stream:
            if stream.read(128).startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                raise ValueError(f'LFS payload absent: {relative}; fetch real LFS objects')
        if digest(path) != record['sha256']:
            raise ValueError(f'SHA256 mismatch: {relative}')
        if 'bytes' in record and path.stat().st_size != record['bytes']:
            raise ValueError(f'Size mismatch: {relative}')
        for key in ('controlled_execution_eligible', 'controlled_support_eligible', 'physical_support_eligible'):
            if record.get(key, False) is not False:
                raise ValueError(f'Recovered artifact cannot grant eligibility: {relative} {key}')
    return seen


def csv_profile(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if not header or len(header) != len(set(header)):
            raise ValueError(f'Empty or duplicate CSV header: {path.name}')
        keys = {i: Counter() for i, name in enumerate(header)
                if name.casefold() in {'objid', 'specobjid', 'mangaid', 'plateifu'}}
        missing = [0] * len(header)
        count = 0
        for row in reader:
            count += 1
            if len(row) != len(header):
                raise ValueError(f'CSV row width mismatch at row {count + 1}: {path.name}')
            for i, value in enumerate(row):
                if value.strip().casefold() in {'', 'nan', 'null', 'none'}:
                    missing[i] += 1
            for i, values in keys.items():
                if row[i].strip():
                    values[row[i]] += 1
    return {'format': 'csv', 'rows': count, 'columns': header,
            'missing_cells_by_column': dict(zip(header, missing)),
            'key_profiles': {header[i]: {'unique_nonempty': len(v),
                'duplicate_rows_beyond_first': sum(n - 1 for n in v.values())} for i, v in keys.items()},
            'numeric_ids_coerced': False, 'crossmatched': False}


def fits_profile(path):
    # Structural recognition only; do not infer release, units, HDUs or schema
    # from a filename. Detailed FITS semantics remain a separate review.
    with path.open('rb') as stream:
        card = stream.read(80)
    if not card.startswith(b'SIMPLE  =') or path.stat().st_size % 2880:
        raise ValueError(f'Invalid/truncated primary FITS structure: {path.name}')
    return {'format': 'fits', 'primary_simple_card_present': True,
            'size_multiple_of_2880': True, 'full_hdu_validation': False}


def verify_overlay(repo, overlay, baseline, id_column):
    def rows(relative):
        with source_path(repo, relative).open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream))

    expected = {row[id_column] for row in rows(baseline)}
    recovered = rows(overlay)
    identifiers = [row['Qualified_ID'] for row in recovered]
    if len(identifiers) != len(set(identifiers)) or set(identifiers) != expected:
        raise ValueError(f'Recovery overlay identifier mismatch: {overlay}')
    for row in recovered:
        if row['Recovery_Status'] != 'historical_recovered_pending_lineage_review':
            raise ValueError(f'Unreviewed recovery status changed: {overlay}')
        for flag in ('Controlled_Support_Eligible', 'Physical_Support_Eligible'):
            if row[flag] != 'false':
                raise ValueError(f'Recovery overlay cannot grant eligibility: {overlay}')
        source_path(repo, row['Audit_Reference'])
    return len(recovered)


def verify_recovery_registries(repo):
    specifications = (
        ('claim_evidence_recovery_2026-10-08.csv', 'claim_evidence_audit_v0.3.csv', 'Qualified_Claim_ID'),
        ('experiment_recovery_2026-10-08.csv', 'experiment_audit_v0.3.csv', 'Qualified_Experiment_ID'),
        ('crosswalk_recovery_2026-10-08.csv', 'claim_experiment_crosswalk_audit_v0.3.csv', 'Qualified_Claim_ID'),
    )
    return {overlay: verify_overlay(repo, 'registry/' + overlay, 'registry/' + baseline, column)
            for overlay, baseline, column in specifications}


def process(repo, output=None):
    intake = read_json(repo, INTAKE)
    code = read_json(repo, CODE)
    quarantine = read_json(repo, QUARANTINE)
    records = intake['assets'] + code['artifacts'] + code['queries'] + quarantine['files']
    records += [{'path': n['output_path'], 'sha256': n['output_sha256']} for n in code['notebooks']]
    seen = verify(repo, records)
    environment_history = verify(repo, read_json(repo, ENVIRONMENT_HISTORY)['files'])
    result = {'schema_version': 1, 'verified_payload_paths': len(seen),
              'verified_archived_environment_paths': len(environment_history),
              'verified_recovery_overlay_rows': verify_recovery_registries(repo),
              'recovered_programs_executed': False, 'models_deserialized': False,
              'eligibility_promoted': False, 'source_manifest_sha256': digest(repo / INTAKE)}
    if output is None:
        return result
    output = output.resolve()
    # Prevent new diagnostics from being mistaken for an intake or source file.
    for protected in ('data', 'registry', 'historical', 'src', 'controlled_execution', '.git'):
        if output.is_relative_to((repo / protected).resolve()):
            raise ValueError('Diagnostic output must be outside repository source directories')
    output.mkdir(parents=True, exist_ok=False)
    status = output / 'run_status.json'
    status.write_text('{"status":"incomplete"}\n', encoding='utf-8')
    profiles = []
    for asset in intake['assets']:
        path = source_path(repo, asset['path'])
        profile = csv_profile(path) if asset['format'] == 'csv' else fits_profile(path)
        profiles.append({'artifact_id': asset['artifact_id'], 'sha256': asset['sha256'], **profile})
    # A source change during diagnostics invalidates the entire run.
    verify(repo, records)
    (output / 'profiles.json').write_text(json.dumps(profiles, indent=2) + '\n', encoding='utf-8')
    status.write_text(json.dumps({'status': 'complete', **result}, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, help='New directory for diagnostic profiles; reuse is refused')
    args = parser.parse_args()
    print(json.dumps(process(args.repo.resolve(), args.output), indent=2))
