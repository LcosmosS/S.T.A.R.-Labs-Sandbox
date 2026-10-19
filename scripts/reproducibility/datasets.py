"""Verify explicitly pinned input bytes; no registry, claims or SQL execution."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import urllib.request

try:
    from .integrity import digest_file, load_json
    from .formats import fits_hdus, _stream_votable
except ImportError:
    from integrity import digest_file, load_json
    from formats import fits_hdus, _stream_votable

HERE = Path(__file__).resolve().parent


def check_bytes(path, contract):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('missing or symlink dataset')
    with path.open('rb') as stream:
        if stream.read(128).startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise ValueError('unhydrated Git LFS pointer')
    if path.stat().st_size != contract['bytes'] or digest_file(path) != contract['sha256']:
        raise ValueError('dataset size/SHA-256 mismatch; preserve and investigate differing bytes')


def check_csv(path, contract):
    """Exact schema and row width; IDs stay strings to avoid 64-bit rounding."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, [])
        if header != contract['columns'] or len(header) != len(set(header)):
            raise ValueError('CSV schema mismatch')
        count = 0
        seen = set()
        for row in reader:
            count += 1
            if len(row) != len(header):
                raise ValueError('CSV row width mismatch')
            if contract.get('key'):
                key = tuple(row[header.index(k)] for k in contract['key'])
                if any(not v.strip() for v in key) or key in seen:
                    raise ValueError('empty or duplicate CSV key')
                seen.add(key)
        if count != contract['rows']:
            raise ValueError('CSV row count mismatch')
    return count


def check_format(path, contract):
    if contract['format'] == 'allcurves':
        return check_arithmetic(path)
    if contract['format'] == 'csv':
        return {'rows': check_csv(path, contract)}
    if contract['format'] == 'fits':
        tables = [h for h in fits_hdus(path) if h.get('XTENSION') in {'BINTABLE', 'TABLE'}]
        if len(tables) != contract['tables']:
            raise ValueError('FITS table count mismatch')
        if 'rows' in contract and tables[0].get('NAXIS2') != contract['rows']:
            raise ValueError('FITS row count mismatch')
        if 'fields' in contract and tables[0].get('TFIELDS') != contract['fields']:
            raise ValueError('FITS field count mismatch')
        return {'tables': [{'name': h.get('EXTNAME'), 'rows': h.get('NAXIS2'),
                            'fields': h.get('TFIELDS')} for h in tables]}
    if contract['format'] == 'votable':
        spec = contract['schema']
        parsed = _stream_votable(path, spec)
        if (parsed['rows'] != spec['expected_rows']
                or len(parsed['fields']) != spec['expected_fields']
                or len(set(parsed['names'])) != len(parsed['names'])
                or not set(spec['required_fields']).issubset(parsed['names'])
                or parsed['blank_agc_ids'] != 0
                or any(parsed[key] != expected for key,expected in spec['expected_invariants'].items())):
            raise ValueError('VOTable schema/missingness/identity/quality mismatch')
        for name, attributes in spec['coordinate_contract'].items():
            if any(parsed['field_by_name'][name].get(k) != v for k,v in attributes.items()):
                raise ValueError('VOTable coordinate metadata mismatch')
        return {k:v for k,v in parsed.items() if k not in ('fields','names','field_by_name')}
    raise ValueError('unknown dataset format')


def check_arithmetic(path):
    # Parse all rows, count number-1 representatives and reject duplicate labels.
    pattern = re.compile(r'(\d+) ([a-z]+) (\d+) \[(-?\d+(?:,-?\d+){4})\] (\d+) (\d+)')
    labels, representatives = set(), set()
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            match = pattern.fullmatch(line.strip())
            if not match:
                raise ValueError('invalid allcurves schema')
            conductor, iso, number, _, rank, torsion = match.groups()
            key = (int(conductor), iso, int(number))
            if not 11 <= key[0] <= 9999 or key[2] < 1 or int(torsion) < 1 or key in labels:
                raise ValueError('invalid or duplicate curve')
            labels.add(key)
            if key[2] == 1:
                representatives.add(key[:2])
    if len(labels) != 64687 or len(representatives) != 38042:
        raise ValueError('arithmetic cohort count mismatch')
    return {'source_rows': len(labels), 'number_1_representatives': len(representatives)}


def fetch_pinned(contract, destination):
    """Explicit public read only. Size-bound HTTPS fetch; no credential access."""
    url = contract['url']
    if not isinstance(url, str) or not url.startswith('https://'):
        raise ValueError('pinned HTTPS source unavailable; supply frozen local bytes')
    digest = hashlib.sha256()
    total = 0
    # Never overwrite an existing source or receipt.
    with urllib.request.urlopen(url, timeout=90) as response, Path(destination).open('xb') as output:
        if not response.geturl().startswith('https://'):
            raise ValueError('non-HTTPS source redirect')
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > contract['bytes']:
                raise ValueError('download exceeds pinned size')
            digest.update(chunk)
            output.write(chunk)
    if total != contract['bytes'] or digest.hexdigest() != contract['sha256']:
        raise ValueError('publisher bytes differ from the frozen source')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--file', type=Path)
    parser.add_argument('--download', type=Path, help='Explicit public-source fetch to NEW file')
    options = parser.parse_args()
    path = None
    contract = None
    result = {'scope': 'sandbox-only', 'claim_of_truth': False,
              'eligible_for_automatic_promotion': False, 'dataset': options.dataset}
    try:
        contracts = load_json(HERE/'DATA_CONTRACTS.json')['datasets']
        contract = contracts[options.dataset]
        if bool(options.file) == bool(options.download):
            raise ValueError('choose exactly one of --file or --download')
        path = options.file or options.download
        if options.download:
            fetch_pinned(contract, path)
        check_bytes(path, contract)
        result.update(check_format(path, contract))
        result.update(status='PASS', verification_scope='pinned-byte-identity-and-declared-schema',
                      sha256=contract['sha256'], bytes=contract['bytes'])
    except Exception as exc:
        # Parser/network failures must still produce a failure receipt; never
        # reinterpret malformed or unavailable inputs as a successful check.
        result.update(status='FAIL', error=str(exc))
        if path is not None and path.is_file() and not path.is_symlink():
            result.update(observed_sha256=digest_file(path), observed_bytes=path.stat().st_size,
                          differing_input_preserved=True)
            if contract is not None:
                result.update(expected_sha256=contract['sha256'], expected_bytes=contract['bytes'])
                try:
                    # Diagnostic agreement cannot turn a hash mismatch into PASS.
                    result['diagnostic_schema'] = check_format(path, contract)
                    result['diagnostic_schema_match'] = True
                except Exception as format_error:
                    result['diagnostic_schema_match'] = False
                    result['diagnostic_schema_error'] = str(format_error)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
