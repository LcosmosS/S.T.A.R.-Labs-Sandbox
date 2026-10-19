# SANDBOX / UNVERIFIED — SBX-2026-0002

**Status:** exploratory · **Scope:** sandbox-only · **Scientific review:** not performed

## First-principles question

Can a simple dimensionless arithmetic candidate coordinate `x = log10(|Δ|)` exhibit an association with a mock numerical response that differs from a seeded *response-label permutation* null? This is a pipeline exercise, not a claim that `Φ(E)` maps actual elliptic curves to physical galaxies.

## Domain, assumptions and dimensional analysis

- The CSV data are **invented arithmetic-like rows**, not checked against a Weierstrass equation, a Cremona label, LMFDB, or observations. Every sample is retained; duplicates are reported and missing values cause a failure.
- `Δ` and `N` are treated as dimensionless integers, `rank` is a nonnegative integer, and `mock_signal` has arbitrary synthetic units. `log10(|Δ|)` only exists for nonzero Δ; introducing physical Mpc, m/s, SFR, entropy or curvature would require an independent dimensional map.
- The null permutes response labels across all rows. This assumes exchangeability, valid only by construction for this teaching example, **not** automatically for galaxy environments, sky masks, spatially correlated redshifts or arithmetic isogeny classes.

## Explicit hypothesis, rival and falsifier

**Exploratory hypothesis:** the selected arithmetic coordinate has nonzero linear association with the synthetic response.

**Rival:** the observed magnitude arises from exchangeable labels under a permutation null.

**Falsifier/criticism:** equal or stronger null correlations, mapping sensitivity, a counterexample, or failures of exchangeability or data selection assumptions undermine the interpretation. A small p-value from these invented rows would still **not** establish ACSC, ECC, RTCH, GLMPCT, a bijection or physical support.

## Reproducible execution (opt-in)

From the repository root, using Python 3.12+:

```bash
python3 -m scripts.playground.runner \
  --spec experiments/SBX-2026-0002-first-principles-workbench/study.json
```

The result is written to `runs/latest.json` locally (not auto-committed). It records the exact SHA-256 of input CSV and study.json, preserved row counts, mapping choice, seed, statistic, all null draws, plus-one two-sided empirical p-value, assumptions, and explicit nonclaims. To try another mapping, copy the experiment folder to a new SBX ID or document the changed study config in its experiment log. The supported axes are `log10_abs_delta`, `log10_conductor`, `rank`, `rank_saturation`; no physical calibration is implied.

For optional upstream-derived numerical utilities see [the workbench infrastructure](../../scripts/playground/README.md). Those source modules are pinned but **not executed** by this basic stdlib example or by sandbox CI.

## Outcome

**Not executed in GitHub CI by design.** This PR supplies the runnable instrument and negative regression tests, not an observational result or a scientific validation. Do not treat a green CI check as evidence for the hypothesis.

## Extension targets

ACSC/GLMPCT: compare alternate projections, class-preserving permutations and matched survey geometry. ECC/RTCH: derive exact differential identities and detect topology-dependent obstructions before interpreting entropy proxies. SFR: compare against mass and gas baselines, enforce train/test separation and independently verify any proxy features. Each requires new experiments with source and assumption audits; no upstream gate is crossed automatically.
