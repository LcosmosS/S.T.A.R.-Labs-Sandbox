# P2 observational protocol — DESIGN ONLY / BLOCKED

## Required distinction

This protocol does not assert that elliptic curves over Q determine the positions, masses, star-formation rates or topology of physical galaxies. The projected arithmetic point cloud and galaxy survey point cloud are **not samples from the same coordinate system** unless a separate physical model supplies a testable, dimensionally valid correspondence. A matched persistence diagram alone cannot supply that model or establish causation.

## Nonnegotiable entry gates

All seven gates in [stage_gate.json](stage_gate.json) must have authenticated, immutable evidence. No P2 execution may start from this PR. An unverified claim cannot be promoted by changing the JSON booleans; the authoritative science gate remains in Legacy.

## Physical hypothesis that must be specified before observing an endpoint

Propose an explicit operator C taking arithmetic curve invariants with canonical model/isogeny treatment to an observable-space prediction. State its codomain, metric, units, causal assumptions, parameter-identification strategy, and dependence on cosmological data. Derive or explicitly hypothesize each relation from independent premises. Include the null hypothesis that there is **no coupling**. If C does not exist, report the endpoint as NOT_IDENTIFIED; do not optimize C post hoc against the survey.

## Candidate data sources, not yet frozen

- SDSS DR18 parent source with exact CasJobs/VizieR SQL bytes and deterministic ordering/membership backcheck.
- MaNGA Pipe3D spectroscopy and SFR/stellar-mass products when field IDs, release and line-flux calibration are frozen.
- GAMA stellar mass/environment material only where exact CATAID/SDSS cross-survey linkage can be audited.

For each separately: publisher URL, download UTC, release, content SHA-256, byte size, source rows, key uniqueness, schema, units, missingness, duplicates and licensing; no unqualified hash or row count is filled in here. Galaxy Zoo morphology is an optional covariate, not a source of SFR unless calibrated independently.

## Selection and join tests

Record the exact flux/magnitude/redshift selection, angular completeness and geometry/mask, radial n(z), quality cuts, fiber collisions, out-of-volume effects and censoring. Freeze RA/Dec epoch and distance cosmology. Preserve raw NaNs/duplicates; report one-to-many matches and angular separations. Do not silently choose the first source in a KDTree match or treat an overlapping survey pair as independent. Fail instead of guessing object identity.

## Confirmatory design that must be locked later

One candidate primary endpoint is held-out H1 persistence-diagram 2-Wasserstein distance under a **specified common dimensionless metric/filtration**, comparing C's physical prediction against survey topology. This remains a **candidate** (not a locked endpoint) until the map C, cohort, physical controls, uncertainty and stratified permutation scheme are fully specified. If a meaningful H1 comparison cannot be defined, the study stops or creates a **new protocol version before seeing outcome**. Fix one-sided inferential rule, alpha, random seed, draws, tie convention, bootstrap uncertainty and sensitivity grid prospectively.

Required rival models include a survey-geometry-only spatial null (sky mask/redshift/selection matched), randomized arithmetic labels within appropriate isogeny/conductor/rank constraints, standard cosmological clustering baselines, and available mass/gas/redshift/environment predictors. Use field/sky-region and redshift-block holdouts to prevent spatial/duplicate leakage; report untouched validation metrics and negative results. Never use a shuffled galaxy sky-coordinate null that violates survey exchangeability.

## Immutable output contract (once execution is authorized)

`source_manifest.json`, `query_receipts/`, `cohort_manifest.json`, `crossmatch_audit.json`, `selection_function.json`, `physical_operator.md`, `preanalysis_lock.json`, `environment_manifest.json`, `null_distribution.csv`, `primary_endpoint.json`, `sensitivity.json`, `failures.json`, `run_manifest.json`, `negative_results.md`. Each result binds input/output SHA-256 and exact commit/run IDs. Missing artifacts produce FAIL; a blocked study produces no fabricated zeros/p-values.

## Interpretation constraints

A negative result is retained. A small p-value alone is not ACSC proof, physical prediction, causation, GLMPCT geometry or ECC cohomology. No release or upstream support status is set from this Sandbox. Exact source and consent boundaries from the legacy registries still govern data acquisition.
