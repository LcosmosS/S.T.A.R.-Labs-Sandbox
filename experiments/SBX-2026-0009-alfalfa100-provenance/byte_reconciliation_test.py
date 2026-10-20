"""Independent standard-library byte verification; never writes source bytes."""
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
FROZEN = '654217f9b3414856c1a8b09071c81eb834a0b0fbc6ec3aea9777e01fdaea1079'
LIVE = '008502caa196f15883f199dfdb8979cfb91f20b087fb63235cd5d26fecc5a4f2'
REPLACEMENTS = (
    (b'Date: 2026-10-20T04:16:54 [V7.6.1]', b'Date: 2026-10-09T07:47:29 [V7.6.1]'),
    (b'<INFO name="request_date" value="2026-10-20T04:16:55">', b'<INFO name="request_date" value="2026-10-09T07:47:29">'),
)

def reconcile(frozen, live, replacements=REPLACEMENTS):
    assert len(replacements) == 2, 'exactly two replacements required'
    result = live
    for old, new in replacements:
        assert len(old) == len(new), 'replacement length changed'
        assert live.count(old) == 1 and frozen.count(new) == 1, 'timestamp occurrence count'
        assert live.count(new) == 0 and frozen.count(old) == 0, 'unexpected timestamp'
        result = result.replace(old, new, 1)
    assert result == frozen, 'reconciled bytes differ'
    return result

def verify(frozen, live, expected_frozen=FROZEN, expected_live=LIVE, replacements=REPLACEMENTS):
    assert len(frozen) == len(live) == 10981088, 'source size'
    assert hashlib.sha256(frozen).hexdigest() == expected_frozen, 'frozen source hash'
    assert hashlib.sha256(live).hexdigest() == expected_live, 'live source hash'
    assert frozen != live, 'raw identity must FAIL'
    return reconcile(frozen, live, replacements)

class ReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = (ROOT / 'frozen.vot').read_bytes()
        cls.live = (ROOT / 'refetched.vot').read_bytes()

    def test_authenticated_reconciliation(self):
        self.assertEqual(hashlib.sha256(verify(self.frozen, self.live)).hexdigest(), FROZEN)

    def test_scientific_cell_mutation_rejected(self):
        match = re.search(rb'<TD>([0-9]+)</TD>', self.live)
        self.assertIsNotNone(match)
        pos = match.start(1)
        changed = self.live[:pos] + (b'1' if self.live[pos:pos+1] != b'1' else b'2') + self.live[pos+1:]
        with self.assertRaisesRegex(AssertionError, 'live source hash'):
            verify(self.frozen, changed)
        # Also prove reconciliation rejects a changed cell independently of hash authentication.
        with self.assertRaisesRegex(AssertionError, 'reconciled bytes differ'):
            reconcile(self.frozen, changed)

    def test_missing_replacement_rejected(self):
        with self.assertRaises(AssertionError):
            verify(self.frozen, self.live, replacements=REPLACEMENTS[:1])
        partly = self.live.replace(*REPLACEMENTS[0], 1)
        self.assertNotEqual(partly, self.frozen)

    def test_wrong_expected_hash_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'frozen source hash'):
            verify(self.frozen, self.live, expected_frozen='0' * 64)
        with self.assertRaisesRegex(AssertionError, 'live source hash'):
            verify(self.frozen, self.live, expected_live='0' * 64)

if __name__ == '__main__':
    unittest.main(verbosity=2)
