"""Frozen arithmetic pilot and read-only promotion audit regression."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class ArithmeticPilotTests(unittest.TestCase):
    def setUp(self):
        self.p=module('scripts/reproducibility/arithmetic_pilot.py','frozen_arith_pilot')
        self.exp=ROOT/'experiments/SBX-2026-0004-arithmetic-isogeny-geometry'

    def test_expected_real_arithmetic_calculation_is_byte_identical(self):
        raw=(self.exp/'curves.csv').read_bytes()
        self.assertEqual(self.p.compute(raw),(self.exp/'result.json').read_bytes())
        self.assertEqual(len(self.p.curves_from_bytes(raw)),38)

    def test_general_weierstrass_arithmetic(self):
        rows=self.p.curves_from_bytes((self.exp/'curves.csv').read_bytes())
        self.assertEqual(self.p.invariants(rows[0])[0],-17576)  # 26.a1
        self.assertEqual(self.p.invariants(rows[5])[0],37)    # 37.a1
        for row in rows:
            self.assertNotEqual(self.p.invariants(row)[0],0)

    def test_source_and_input_tampering_rejected(self):
        rows=self.p.curves_from_bytes((self.exp/'curves.csv').read_bytes())
        with self.assertRaises(ValueError):
            self.p.curves_from_bytes((self.exp/'curves.csv').read_bytes().replace(b'26,a,1',b'26,a,2'))
        self.assertEqual(self.p.canonical_line(rows[0]),'26 a 1 [1,0,1,-5,-8] 0 3')

    def test_numerical_result_is_nonconfirmatory(self):
        obj=json.loads((self.exp/'result.json').read_text())
        self.assertGreater(obj['statistics']['empirical_p'],0.05)
        self.assertEqual(obj['statistics']['earlier_unconditioned_p_unsafe_diagnostic_only'],0.005)
        self.assertTrue(obj['method']['selected_after_seeing_results'])
        self.assertEqual(obj['observational_stage'],'not_started')
        self.assertFalse(obj['scientific_claim'])

    def test_readiness_report_nonblocking_and_hashes(self):
        readiness=module('scripts/reproducibility/promotion_readiness.py','readiness_report')
        reports=readiness.scan(ROOT)
        hit={o['experiment_id']:o for o in reports}
        self.assertIn('SBX-2026-0004',hit)
        self.assertFalse(hit['SBX-2026-0004']['approval_or_eligibility_granted'])
        self.assertFalse(hit['SBX-2026-0004']['physical_observational_stage_complete'])
        self.assertTrue(all(t['bytes_and_sha256_match'] for t in hit['SBX-2026-0004']['artifact_checks']))
        self.assertEqual(readiness.main(['--root',str(ROOT),'--output',str(ROOT/'ready-test-temp.json')]),0)
        (ROOT/'ready-test-temp.json').unlink()

if __name__=='__main__':unittest.main()
