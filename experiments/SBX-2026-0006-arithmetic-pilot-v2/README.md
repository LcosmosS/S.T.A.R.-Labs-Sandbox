# SBX-2026-0006 — Prospective arithmetic pilot v2 (NOT EXECUTED)

This is a deliberately stronger successor to the 38-curve exploratory [SBX-2026-0004](../SBX-2026-0004-arithmetic-isogeny-geometry/README.md). It does **not** reinterpret its post-hoc null choice as confirmation.

The complete [preanalysis protocol](preanalysis_protocol.json) is frozen **before evaluating a new v2 primary endpoint** and fixes the full public ecdata source (64,687 rows), an algorithmic cohort rule, one primary statistic, both mappings, rank-and-conductor conditioned permutations, 1,999 draws, seed, one-sided tail and descriptive alpha. It retains every source row before the explicitly defined analysis eligibility selection. No survey or galaxy observation is involved.

## Audit-ready preflight

Run `python3 -I experiments/SBX-2026-0006-arithmetic-pilot-v2/preflight.py /path/to/allcurves.00000-09999`. This computes exact arithmetic identities and prospective cohort census only. It **does not compute a test statistic or p-value**. It fails on wrong SHA, source size, row count, malformed entries, singular curves, or conflicting invariant formulas.

The coordinate ablation grid is predeclared and cannot be used to alter the primary metric based on outcome. Full primary inferential implementation and execution, independent Sage/eclib crosscheck, optional heavy-runtime qualification and external replication remain explicit blockers. Do not claim v2 statistical significance or pass until exact-run receipts exist.

## Evidence boundary

- This is a new prospective design, not a retroactive preregistration of SBX-0004.
- Source records are genuine arithmetic catalogue entries, **not measured cosmological observations**.
- Test pipeline and acceptance conditions can be developed in Sandbox without independent scientific approval; moving to Legacy requires a separate complete submission and independent scrutiny.

## Optional v2 inferential runner — not a result

After reviewing the frozen protocol, the opt-in `analysis.py` implements the stated 1,999 seeded shuffles within conductor-and-rank blocks, seven paired statistic variants (primary plus six one-factor sensitivity checks), and a hard 300,000-pair computational limit (abort, never downsample). It writes `result.json`, `null_distribution.csv`, and SHA-256-bound `run_manifest.json` into a **new** output directory. It has **not** been run in this PR or CI; outputs do not exist and no inferential PASS is claimed. The Sage/eclib and independent-null reproductions remain NOT_RUN.
