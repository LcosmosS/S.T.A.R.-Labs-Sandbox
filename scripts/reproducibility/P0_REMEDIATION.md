# P0 verification: admission and numerical-qualification contract

This is an engineering remediation document, **not** certification of ACSC, ECC, GLMPCT, or any physical claim.

## Live rule readback (2026-10-19)

At the initial inspection of ruleset [#25371960](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/rules/25371960), `sandbox-policy` (GitHub Actions integration 15368), `sandbox-stewardship` (GitHub App integration 5379340), and `saved-reference-integrity-only` (Actions 15368) were required, strictly up to date. Approval count was zero, but CODEOWNERS, last-push approval and conversation resolution were enabled. No bypass actors. **This is a mutable observation, not evidence of end-to-end admission.**

The six proposed fast computational contexts in `scripts/reproducibility/COMPUTATIONAL_BOUNDARY_ACTIONS.md` are *not* all active required contexts. Only an authorized repository settings actor can change that. Do not edit ruleset blindly: verify actual job names and integration IDs in a test PR, then preserve existing required contexts while adding the intended checks.

## Required operational receipts

1. [Experiment-only smoke PR #23](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/pull/23): snapshot exact head/base, required check runs with conclusion and run ID, exact live rules, review count, GitHub `mergeable`/`mergeable_state`, and whether the branch could merge without scientific approval. Do not merge synthetic control as science.
2. **This protected-path PR**: `scripts/`, `tests/` and `.github/workflows/` must require a current-head approval from an authorized non-author steward; check that failing/pending stewardship is not represented as success. An ordinary bot comment does not count.
3. Repeat with a stale-head review, a revoked steward permission, and an unresolved change request if operational testing permits. Keep proofs as append-only URLs/JSON with checked SHA; no secrets.

The eligible steward `LibertySquared` had GitHub `write` permission at the time of initial inspection; permissions must be rechecked at the decision time. Required checks and branch settings cannot be changed by this PR alone.

## On-demand suites

Run `python3 -I scripts/reproducibility/qualification_inventory.py --out /tmp/sbx-qualification.json` and inspect the emitted machine-readable **NOT_RUN** statuses. Each of the eight optional suites requires an exact source/container/dependency lock and a **separate successful dispatched job with a saved receipt** before its scientific/engineering evidence can be described as executed. `image: sagemath/sagemath:latest`, untethered `pip install -r requirements.txt` and minor-only Python pins are identified as environment-qualification blockers rather than silently resolved.

The workflows in `.github/workflows/sandbox-extended-reproducibility.yml` can be dispatched only by an authorized Actions operator; manual dispatch is **not** effected by a pull request. Record `workflow_run_id`, commit SHA, runner image, container image **digest**, interpreter/native-library versions, exact dependency hashes, output SHA-256, failure logs and `PASS | FAIL | BLOCKED | NOT_RUN`. A run that used a mutable image cannot be declared independently environment-qualified even if the code succeeded.

## Evidence boundary

- Routine green CI is software-quality evidence for the exact tested source, not full historical reproducibility.
- No actual SciServer submit, private Google Docs access, observational cosmology, GHCR publication, independent science review, or legacy support flag is enabled here.
- **Do not remove existing provenance failures.** The preserved VizieR fresh-response SHA mismatch and entropy-geodesic overflow remain explicit unresolved defects in `scripts/reproducibility/audit/AUDIT.md`.
