import hashlib
import json
from pathlib import Path
import pytest
from tools.recovery_intake import verify, csv_profile, source_path


def test_rejects_missing_lfs_payload_and_corrupt_bytes(tmp_path):
    path = tmp_path / 'data.csv'
    raw = b'a,b\n1,2\n'
    record = {'path': path.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    path.write_bytes(raw)
    assert verify(tmp_path, [record])
    path.write_bytes(b'version https://git-lfs.github.com/spec/v1\noid sha256:fake\n')
    with pytest.raises(ValueError, match='LFS payload absent'):
        verify(tmp_path, [record])
    path.write_bytes(b'changed')
    with pytest.raises(ValueError, match='SHA256 mismatch'):
        verify(tmp_path, [record])


def test_keeps_large_identifiers_and_detects_bad_rows(tmp_path):
    path = tmp_path / 'data.csv'
    path.write_text('objid,value\n1234567890123456789,1\n1234567890123456789,\n')
    result = csv_profile(path)
    assert result['key_profiles']['objid'] == {'unique_nonempty': 1, 'duplicate_rows_beyond_first': 1}
    assert result['missing_cells_by_column']['value'] == 1
    path.write_text('a,b\n1,2,3\n')
    with pytest.raises(ValueError, match='row width mismatch'):
        csv_profile(path)


def test_rejects_source_escape_and_eligibility(tmp_path):
    with pytest.raises(ValueError, match='Invalid or missing source'):
        source_path(tmp_path, '../outside.csv')
    path = tmp_path / 'safe.txt'
    path.write_bytes(b'bytes')
    with pytest.raises(ValueError, match='cannot grant eligibility'):
        verify(tmp_path, [{'path': path.name, 'sha256': hashlib.sha256(b'bytes').hexdigest(), 'physical_support_eligible': True}])


def test_processing_refuses_existing_output_and_source_directories(tmp_path, monkeypatch):
    import tools.recovery_intake as intake
    repo = tmp_path / 'repo'
    repo.mkdir()
    fake = {'assets': [], 'artifacts': [], 'queries': [], 'files': [], 'notebooks': []}
    monkeypatch.setattr(intake, 'read_json', lambda *args: fake)
    monkeypatch.setattr(intake, 'digest', lambda *args: '0' * 64)
    monkeypatch.setattr(intake, 'verify_recovery_registries', lambda *args: {})
    output = tmp_path / 'existing'
    output.mkdir()
    sentinel = output / 'keep.txt'
    sentinel.write_text('unchanged')
    with pytest.raises(FileExistsError):
        intake.process(repo, output)
    assert sentinel.read_text() == 'unchanged'
    with pytest.raises(ValueError, match='outside repository source'):
        intake.process(repo, repo / 'data' / 'new')


def test_overlay_preserves_qualified_namespace_and_refuses_promotion(tmp_path):
    import csv
    from tools.recovery_intake import verify_overlay
    (tmp_path / 'audit.md').write_text('evidence limits', encoding='utf-8')
    (tmp_path / 'base.csv').write_text('Qualified_Claim_ID\nPDF:CLAIM-001\n', encoding='utf-8')
    row = {'Qualified_ID': 'PDF:CLAIM-001', 'Recovery_Status': 'historical_recovered_pending_lineage_review',
           'Controlled_Support_Eligible': 'false', 'Physical_Support_Eligible': 'false',
           'Audit_Reference': 'audit.md'}

    def write():
        with (tmp_path / 'overlay.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=row)
            writer.writeheader()
            writer.writerow(row)

    write()
    assert verify_overlay(tmp_path, 'overlay.csv', 'base.csv', 'Qualified_Claim_ID') == 1
    row['Physical_Support_Eligible'] = 'true'
    write()
    with pytest.raises(ValueError, match='cannot grant eligibility'):
        verify_overlay(tmp_path, 'overlay.csv', 'base.csv', 'Qualified_Claim_ID')
    row['Physical_Support_Eligible'] = 'false'
    row['Qualified_ID'] = 'REPO:CLAIM-001'
    write()
    with pytest.raises(ValueError, match='identifier mismatch'):
        verify_overlay(tmp_path, 'overlay.csv', 'base.csv', 'Qualified_Claim_ID')
