# Draft candidate packet for possible independent Legacy review

**Template only — no upstream PR can be opened as evidence from this blocked experiment.** The purpose is to prevent a future successful-looking CI job from becoming a support claim without prerequisites.

## Required sections in any future, separate Legacy PR

1. **Exact claim and non-claims:** source SBX ID, full Git commit SHA, candidate Legacy Experiment_ID/Claim_ID proposal, what is not being asserted; historical claims not silently upgraded.
2. **Mathematical foundation:** precise hypotheses, theorem statements, dependencies, failed lemmas, P1 contradiction disposition, complete derivation and counterexample log.
3. **Provenance and source lock:** canonical data archive locations, acquisition query/UTC, immutable source SHA-256/byte count/row count/schema, LFS object IDs, licenses, individual join and selection decisions.
4. **Executable package:** exact source manifest, immutable dependency/container image digest, command line, seeds, output contract, full raw logs, failure/skip status and verification entrypoints.
5. **Prospective statistical lock:** cohort/field/sky mask, physical operator C, one primary endpoint, null algorithm, conditioning/exchangeability, draws, alpha, precommitted sensitivity grid, negative controls, multiplicity policy.
6. **Results:** expected vs observed, uncertainty, FAIL/NOT_RUN and negative evidence intact, ablation and holdout performance, limits of extrapolation.
7. **Independent replication invitation:** a separate implementation of arithmetic invariants, geometry/topology and statistic; trusted verifier checksum and reviewer steps not dependent on original investigator interpretation.
8. **Upstream governance:** new Legacy PR, off-author/independent review as required by Legacy, registry references established only there. No Sandbox code may write Legacy registers; a reviewer explicitly determines status and eligibility.

## Handoff invariant

`proposed_source_commit`, `source_dataset_sha256`, `cohort_sha256`, `protocol_sha256`, `analysis_code_sha256`, `environment_digest`, `run_manifest_sha256`, `negative_result_inventory`, `independent_verifier_digest`, and `nonclaims` must each be present or explicitly BLOCKED. No guessed placeholders may be rendered as matching hashes.

### Explicit present status

`P2 physical operator: NOT_DEFINED` · `observational data: UNFROZEN` · `P2 primary endpoint: NOT_LOCKED` · `confirmatory results: NOT_RUN` · `independent review: NOT_REQUESTED` · `Legacy submission: NOT_OPENED`.
