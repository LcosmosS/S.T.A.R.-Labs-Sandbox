# Computational CI boundary: required fast checks, without scientific reviewers

**Proposed GitHub administration action, NOT applied by this document.** The source branch and current GitHub ruleset are separate mutable objects. A PR cannot configure the live ruleset without an authorized settings change; never represent an unmodified ruleset as enforced. Live reference: [Rules #25371960](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/rules/25371960).

## Required green checks on applicable PRs to `main`

Keep the already-required `sandbox-policy` from GitHub Actions with strict up-to-date checking. In the existing ruleset, **add** these existing exact job names as required GitHub Actions statuses (verify names against current PR check UI before applying):

- `candidate-input-contracts` — optional SBX artifact claims are checked; zero opted-in contracts is NOT evidence of reproducibility.
- `upstream-dataset-sql` — pinned dataset, provenance, CasJobs SQL source and negative regressions.
- `upstream-sciserver-offline` — bounded SQL policy and offline receipt tests; no live SciServer authority.
- `upstream-deterministic-numerics` — arithmetic/null/MCMC deterministic software regressions.
- `pinned-arithmetic-source` — external gitlink/data bytes and full arithmetic census.
- `pinned-software-and-build` — pinned source byte audit, allowlisted ECC/mathematical software, reproducible wheel/sdist rebuild and clean package tests (includes `SBX-2026-0004` reference computation).

Preserve `sandbox-policy` always. Consider also `upstream-saved-packages` and `saved-reference-integrity-only` when upstream evidence-byte changes are in scope; they inspect frozen artifacts and do **not** authenticate experiment execution. Do not require optional manually dispatched, expensive or unqualified suites, the non-gating `promotion-readiness-report-only`, peer reviews, independent adjudication, activation gates, or upstream registry changes.

**Limitation:** the original six checks are logically separate workflows/jobs. Before enforcing check names, confirm their true status contexts on a sacrificial PR; never add a status that does not get reported or is always skipped. If GitHub path-specific required checks are not supportable, use these checks repository-wide (they currently run on PRs) rather than pretending conditional enforcement.

## Test the two admission paths independently

**Ordinary experiment:** open a PR containing *only* `experiments/SBX-.../` new-format documentation/data/metadata files (no code under `/scripts/`, no workflow/schema/CI or protected archive changes). It should pass the mandatory checks and remain mergeable with **zero human approvals**; code-owner review should not be demanded for an unowned path. Capture ruleset and PR mergeability readbacks. Do not merge an intentionally false research claim as truth; admission is sandbox-only.

**Steward-owned change:** open a separate PR modifying e.g. `schemas/` or `.github/workflows/` with an innocuous comment. The CODEOWNERS path must require stewardship, while green CI alone cannot bypass it. Current sole owner **cannot self-approve**; appoint an additional qualified steward or use a recorded administrator bypass limited to stewardship **through a PR**. Never bypass `sandbox-policy` or source-hash protection, and never call the steward approval independent scientific review.

The active single ruleset currently also requires conversation resolution, code-quality and Copilot review. Ensure those settings do not accidentally impose approvals on ordinary unowned experiment changes. GitHub rules readback is not equivalent to an end-to-end test: record actual test PR URLs and outcomes here after authorized activation.

## CI epistemic contract

A passing job validates its *named* software/data contracts only. No numerical or report job can produce `supported`, `validated`, `peer-reviewed`, `approved`, or `eligible_for_promotion` scientific status. Upstream admission remains a separate PR under Legacy rules.
