# Sandbox reproducibility CI, independent of scientific review

The sandbox reuses **the mathematical, dataset and software-verification
mechanics**, not the legacy program's independent-review or activation
authority. This is a two-direction workflow:

1. **Pinned upstream baseline**: run the unchanged relevant legacy tests and
   integrity validators on immutable upstream commit
   `51927a9b396cdfa880f3128440db4715acdec8dc`.
   These prove those *legacy source checks* remain reproducible; they do not
   test every sandbox experiment.
2. **Candidate precheck**: optionally add `reproducibility.json` inside a
   sandbox `experiments/SBX-YYYY-NNNN-description/` folder. The checker
   validates declared CSV, JSON, SQL and other file hashes/sizes and all CSV
   rows without dropping NaNs or duplicates. It does **not** run experiment
   programs or approve SQL. A reviewable JSON diagnostic is created in CI.
   The candidate remains sandbox-only and unverified scientifically.

## Automatic jobs

`.github/workflows/sandbox-reproducibility.yml` runs on sandbox PRs, pushes
to main and manual dispatch, with read-only GitHub permissions:

- `candidate-input-contracts`: new sandbox SHA/CSV/SQL source validator
  plus negative tests. Reports **zero contracts checked** if no SBX candidate
  has opted in. A green run is not a claim that nonexistent candidates passed.
- `upstream-dataset-sql`: exact, unchanged legacy dataset census, provenance,
  VizieR specification and CasJobs SQL tests, plus audit lifecycle and
  provenance-capture negative tests from the pinned source checkout. These
  include distinct historical unordered SQL, deterministic ordered SQL and
  membership backcheck contracts.
- `upstream-sciserver-offline`: original SQL allowlist, local hash-chained
  receipts, synthetic signature verification, identifier fidelity, and mocked
  MCP runtime tests. No credentials, actual operator approval or remote query.
- `upstream-deterministic-numerics`: pinned seeded arithmetic null/robustness,
  MCMC reproducibility and failure-path unit tests.
- `pinned-arithmetic-source`: real ecdata source from immutable external Git
  commit `25cec5ecfec8b9f016eb1631ac633194c2bed39f`, with exact
  `259f3846...916a968` SHA-256 and 64,687-record census.
- `upstream-saved-packages`: compare existing A01 saved output/manifest to
  the saved verification receipt and check A03 pre-execution archive bytes
  and their original Git sources. This is **not rerunning registered science**.
- Existing sandbox `sandbox-policy` (221 archive files, 24 upstream references)
  and CodeQL security checks remain independent and mandatory.

**Output contract:** JSON and JUnit reports are job artifacts, retained for
30 days. Immutable source revisions are shown in the workflow and manifest.
Passing CI is software/data reproducibility **only**, never observational
support, a theorem, independent replication or a prerequisite-waiver upstream.

## Reproducibility contract in an experiment

An investigator who wants their experiment considered for a *future separate*
upstream submission can opt in by committing `reproducibility.json`.
An example skeleton (hashes are placeholders and will FAIL until replaced):

```json
{
  "schema_version": 1,
  "experiment_id": "SBX-2026-0004",
  "scope": "sandbox-only",
  "status": "exploratory",
  "source_kind": "synthetic",
  "scientific_claim": false,
  "independently_reviewed": false,
  "automatic_promotion": false,
  "artifacts": [
    {
      "path": "sample.csv",
      "sha256": "64-lowercase-hex-character-hash-of-exact-file",
      "size_bytes": 100,
      "format": "csv",
      "columns": ["objid", "ra", "dec", "sfr"],
      "rows": 3,
      "source": "Synthetic teaching fixture, not an observational catalogue",
      "source_commit": null
    }
  ]
}
```

Every artifact path is relative to its own SBX folder. Exact hashes, byte
sizes, CSV headers/row counts, missing values and duplicate counts are
checked. CSV rows are **retained**, not filtered or imputed. Additional
artifact formats `sql`, `json`, `binary` are supported. The conservative
SELECT-TOP-only SQL lint is **not a SQL parser, SQL security proof, or
execution authorization**; only separate source-pinned legacy query policy
governs real SciServer preparation (remote submission remains disabled).
No `reproducibility.json` is required for speculative contributions.

Run locally without imports from the legacy review system:

```bash
python3 -B scripts/reproducibility/candidates.py --root .
python3 -B -m unittest discover -s tests -p test_sandbox_reproducibility.py -v
```

## Heavy, live and extended checks

See [`coverage.json`](coverage.json) for **all 18 legacy workflow files**,
their automated/optional mapping and exact exclusions. An `on_demand_suite`
value names an explicitly dispatched, potentially expensive job. Optional
checks are **not inferred PASS** from an automatic green CI run.

- Hydrated observational FITS/VOTable/SDSS data, recovered source LFS,
  publisher re-fetches and CasJobs export comparison may require large
  downloads, external service access and independently supplied inputs.
  They never silently replace canonical data or promote provenance.
- Sage notebooks, survey/Parquet tools, JavaScript browser builds and image
  builds can be used as software smoke tests, **not scientific admissions**.
- Google Docs acquisition is not cloned as an unattended scraping job: the
  source documents can be private and mutable. The hash-manifest validation
  logic and negative tests are still covered. A user-supplied capture can
  be separately verified.
- Independent reviewers, blinded adjudication, controlled study admission,
  upstream eligibility flags, GHCR publication, MyDB writes and production
  deployment are **explicitly excluded**, not assumed to have run.

Once a sandbox candidate has reproducible inputs, its protocol, assumptions,
falsifiers, selection effects, null model and output contract can be
**considered** in a future upstream PR. Review eligibility and whether to
adopt it remain independent decisions by the upstream project.
