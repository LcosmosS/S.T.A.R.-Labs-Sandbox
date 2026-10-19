"""Versioned C-03 fixture path regression. Historical v1/v2 files stay unchanged."""
import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'ecc_b01' / 'investigator_a_v3.py'


def test_c03_fails_via_same_record_path_for_wrong_comparator():
    ns = runpy.run_path(str(SCRIPT), run_name='ecc_b01_v3_regression')
    check = ns['c03_record']
    entropy = ns['S2']
    valid = check(entropy + 7, entropy)
    invalid = check(entropy + 7, 2 * entropy)
    assert valid['fixture_id'] == invalid['fixture_id'] == 'C-03'
    assert valid['observed'] == '0' and valid['pass_'] is True
    assert invalid['observed'] != '0' and invalid['pass_'] is False
    fixtures = {item['fixture_id']: item for item in ns['results']}
    assert fixtures['C-03']['pass_'] is True
    assert fixtures['C-03-NEG']['pass_'] is True


def test_v3_runner_source_binds_report_and_passes_16_fixtures(tmp_path):
    destination = tmp_path / 'v3.json'
    out = subprocess.run([sys.executable, str(SCRIPT), str(destination)],
                         text=True, capture_output=True)
    assert out.returncode == 0, out.stdout + out.stderr
    result = json.loads(destination.read_text())
    assert result['status'] == 'PASS'
    assert len(result['results']) == 16
    assert result['source_sha256'] == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
