"""Protect the new CI's low-privilege and explicit-execution boundary."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowBoundaryTests(unittest.TestCase):
    def test_actions_are_pinned_and_no_privileged_acquisition_exists(self):
        workflow = (ROOT/'.github/workflows/reproducibility.yml').read_text()
        uses = re.findall(r'^\s+uses:\s*(\S+)', workflow, re.MULTILINE)
        # List items put "uses" on the same line as the leading dash.
        uses += re.findall(r'^\s+- uses:\s*(\S+)', workflow, re.MULTILINE)
        self.assertGreater(len(uses), 5)
        for action in uses:
            self.assertRegex(action, r'^[\w./-]+@[0-9a-f]{40}$')
        for forbidden in ('pull_request_target:', 'packages: write', 'contents: write',
                          'secrets.', 'submodules: true', 'lfs: true',
                          'persist-credentials: true', 'star-controlled-experiment',
                          'run_protocol('):
            self.assertNotIn(forbidden, workflow)
        self.assertIn('contents: read', workflow)
        self.assertIn('--require-hashes --only-binary=:all:', workflow)

    def test_numerical_collection_is_explicit_and_skips_are_rejected(self):
        workflow = (ROOT/'.github/workflows/reproducibility.yml').read_text()
        self.assertIn('scripts/reproducibility/upstream/tests scripts/reproducibility/tests', workflow)
        configuration = (ROOT/'scripts/reproducibility/conftest.py').read_text()
        self.assertIn("reporter.stats.get('skipped')", configuration)
        self.assertIn("session.exitstatus = 1", configuration)
        self.assertIn("socket, 'create_connection', forbidden", configuration)


if __name__ == '__main__':
    unittest.main()
