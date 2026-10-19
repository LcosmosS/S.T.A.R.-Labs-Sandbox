# Independent first-principles research workbench

This directory contains a **reusable exploratory infrastructure layer** modeled after the computational portions of the upstream S.T.A.R.-Labs project. It has **no scientific admission gate**: no preregistration, no registry status, no independent research reviewer, no predeclared alpha required to investigate hypotheses, and no automatic promotion. Repository CI, integrity, security and code-owner controls remain in effect for code that changes those safeguards.

| Upstream component | Pinned sandbox snapshot | Scientific boundary |
| --- | --- | --- |
| `src/acsc/projection.py` | `upstream_snapshot/src/acsc/projection.py` | Coordinates are candidate arithmetic embeddings, not astronomical correspondences |
| `src/acsc/null_models.py` | `upstream_snapshot/src/acsc/null_models.py` | Gaussian draws are synthetic benchmark controls |
| `src/physics/cosmology.py` | `upstream_snapshot/src/physics/cosmology.py` | A model prediction is not a fitted observation |
| `src/tda/persistence.py` | `upstream_snapshot/src/tda/persistence.py` | Requires Ripser/GUDHI, no fictitious persistence diagrams |
| `src/data/sky_survey_schema.py` | `upstream_snapshot/src/data/sky_survey_schema.py` | Schema is not dataset identity or scientific provenance |

Uncopied by design: `src/control/`, `src/experiments/exp_map_a*.py` as controlled-gate workflows, `controlled_execution/`, `preregistrations/`, `registry/`, `release_packages/`, upstream GitHub Actions, proprietary or large astronomy data, and any assertion of independent certification. ECC/RTCH exploratory numerical tests can be implemented **as new sandbox experiments**, but the upstream entropy/cohomology prototypes were not copied because some methods are explicitly placeholders rather than proofs of non-exactness. A later port may follow with individual tests and source attribution.

## Starting an experiment

Copy the normal `experiments/_template/`; use a fresh SBX identifier. Write the axioms, domain, dimensional assumptions, a mathematical consequence, an observable and its units, competing interpretations, data provenance, and how the idea might fail.

For two runnable **synthetic examples**, see [SBX-2026-0002](../../experiments/SBX-2026-0002-first-principles-workbench/README.md) (arithmetic mapping and seeded null) and [SBX-2026-0003](../../experiments/SBX-2026-0003-exact-form-controls/README.md) (exact versus closed cochains, ECC/RTCH). A separate stdlib cochain runner prints the latter demonstration with `python3 -m scripts.playground.cochains`. Its standard-library runner is `scripts/playground/runner.py`; it computes an exploratory Pearson statistic and a reproducible seeded permutation diagnostic without claiming scientific acceptance.

```bash
python3 -m scripts.playground.runner \
  --spec experiments/SBX-2026-0002-first-principles-workbench/study.json
```

The output defaults to `runs/latest.json` inside that experiment, clearly identifies synthetic input and returns no verified/proven/supported status. GitHub CI does not run arbitrary experiment code, infer physical support, fetch live datasets, or invoke the upstream controlled runner.

## First-principles reasoning contract

1. **Axioms and units.** Specify objects and a domain first; separate dimensionless invariants from physical distances/times. A phenomenological factor such as rank-to-distance scaling is an adjustable assumption until independently derived or measured.
2. **Derivation.** Show each implication with conditions. A numerical example is not a theorem and a small p-value is not a mechanism.
3. **Adversarial tests.** Construct counterexamples, trivial/permutation controls, alternative mappings, rank/normalization ablations, and sensitivity to missing rows, duplicates and selection.
4. **Provenance and reproducibility.** Declare dataset origin, explicit input digest, code commit, parameters, seed, statistic, null mechanism, and all exclusions before interpretation. No silent row drops.
5. **Interpretation.** A sandbox outcome is exploratory even if the toy data yields an extreme statistic. Any physical ACSC/GLMPCT/ECC/RTCH claim belongs to a separate upstream submission under its own rules.

The demo's exchangeability assumption is intentionally narrow. A simple permutation is inappropriate for spatially clustered galaxies, grouped isogeny classes or survey-selection effects without a defensible blocked/conditional null. Such studies must implement and justify a different null model.

## Optional environments

Core runner and regression tests require Python 3.12+ standard library only. The upstream source snapshot is **not imported** by CI and requires optional scientific dependencies (`numpy`, `pandas`, `scipy`, `sympy` and, for TDA, `ripser` or `gudhi`). Pin versions in each experiment's environment lock when using them. Never auto-download private data or install packages in a PR job merely to execute untrusted hypotheses.
