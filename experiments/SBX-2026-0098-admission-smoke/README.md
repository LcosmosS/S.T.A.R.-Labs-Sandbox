# SBX-2026-0098 — Sandbox admission smoke (NOT SCIENCE)

Status: speculative. Scope: sandbox-only. No scientific claim, physical correspondence, reviewer certification, or automatic promotion.

## Testable operational hypothesis
A PR restricted to this valid new `experiments/SBX-YYYY-NNNN-*` directory should be eligible to merge with **zero independent scientific approvals**, provided the required GitHub engineering checks pass. No files under protected repository paths are changed by this PR.

## Required independent observation
1. Record PR URL, exact head and base SHAs, live ruleset revision, and all required check contexts.
2. Observe `sandbox-policy`, `sandbox-stewardship` and `saved-reference-integrity-only` as reported for this PR head. Distinguish pending/skipped from pass.
3. Record mergeability and any demanded approval. Do not interpret an unrelated bot comment as GitHub review approval.
4. Enumerate **all submitted reviews on the exact observed head**, including unsolicited scientific approvals. Confirm that zero independent scientific approvals were actually present when mergeability and the stewardship check were observed; otherwise record INCONCLUSIVE.
5. Compare with the protected-path PR in the linked remediation series; confirm an eligible non-author engineering steward is required for protected changes.
6. Record conclusion in a permanent receipt before closing this smoke PR; this README by itself is **not** a receipt.

Falsifier: an unowned experiment-only change requires a scientific reviewer, or a protected change is admitted without required engineering stewardship. Closing without a green end-to-end mergeability readback means **INCONCLUSIVE**, not PASS.

**Do not automatically merge or promote this engineering-only synthetic control.**
