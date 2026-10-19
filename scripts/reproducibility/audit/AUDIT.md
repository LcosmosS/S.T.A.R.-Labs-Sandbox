# Legacy reproducibility audit and Sandbox equivalents

Audit date: 2026-10-19. Upstream: `LcosmosS/S.T.A.R.-Labs` at
`51927a9b396cdfa880f3128440db4715acdec8dc`; Sandbox base:
`a2baf738d5aa0ed29841f85ca0f2c64c939e55bd`. The open workbench PR #4 is a separate
change, not a dependency or a source of claims in this port.

While this audit was being published, main advanced to
`3ec4793823a3a257b646abb5bc54012a49912e35` with a parallel legacy baseline,
candidate-contract checker and eight explicit extended dispatch suites. Those
changes are preserved. The decisions below describe this port's curated,
hash-locked checks. The pre-existing `coverage.json` separately maps the baseline
and extended suites; an optional job definition is not a successful run.
In particular, the inherited Sage/container/full legacy suites still use
partly unpinned environments and are not certified reproducible by this PR.
They must be environment-locked and qualified before treating their outputs as
reproducibility evidence. No such resource-heavy suite was dispatched here.

The [machine inventory](legacy-inventory.json) records original Git blob IDs,
all workflow job commands, and active check/build source paths. It is an audit
of what exists, not a declaration that all legacy checks are scientifically
sound or executable in this repository. Historical research files are inventoried
by the existing immutable archive manifest and are never executed here.

## Workflow coverage (all 18 definitions)

1. **`ci.yml`**: unit tests and arithmetic smoke become the allowlisted synthetic
   numerical suite; wheel/sdist building becomes a disposable, hash-locked build,
   byte-identical wheel rebuild and clean installed-package regression. CI
   artifacts contain JUnit, pinned-source receipts, environment and artifact
   digests. Registry referential integrity is replaced by Sandbox metadata,
   non-promotion, source manifests and trusted archive checks. Controlled
   readiness/transaction/admission and preregistration activation jobs are
   deliberately excluded. Their arithmetic source/schema and synthetic algorithm
   components are retained separately, without copying execution eligibility.
2. **`test.yml`**: duplicates the upstream full pytest invocation; covered by the
   curated suite, not a second unbounded invocation over archived sources.
3. **`a01-activation-preflight.yml`**: preserve exact ecdata Gitlink/hash/schema,
   64,687 records and 38,042 number-1 representatives. Existing submodule tests
   retain all three exact Gitlinks and remote URLs. No approval, readiness or
   controlled-runner preflight is introduced.
4. **`a01_primary_evidence.yml`**: execute the pinned read-only saved-package
   inspector in a separate legacy reference checkout; compare its JSON with the
   preserved receipt. This checks all eight declared run files, including empty
   logs, source/config/environment bindings, saved null rows and saved formulas.
   No inference, null regeneration, primary-run authentication or replication.
5. **`a01_release_package.yml`**: source identity is covered by the ecdata check;
   saved-byte integrity by the preceding inspector; generic package tamper
   rejection by local tests. GitHub scientific-approval verification and
   experiment activation are excluded. A Sandbox receipt is never an upstream
   reproducibility-package approval.
6. **`a03_preexecution_verification.yml`**: port the pure symbolic discriminant,
   independent PRNG/rejection sampling, tie/duplicate graph, strata and
   three-draw null reference tests on 40-row synthetic fixtures. The independent
   computation is retained; human scientific approval is not required. Real
   cohort graph, registered endpoint/null, eligibility and preflight functions
   are omitted from the extracted modules. Oversized reference graphs fail.
7. **`a03_preexecution_release_review.yml`**: retain immutable archive-origin
   verification and its three byte/false-status tamper controls in a separate
   pinned reference checkout. Inspection of historical false activation flags
   preserves the artifact's meaning; it does not require a reviewer or approve
   a new experiment. No release/admission operation or privileged publication.
8. **`independent_dataset_verification.yml`**: retain source hashes, sizes, exact
   CSV schema/keys, FITS table/row/field contracts and hardened ALFALFA VOTable
   metadata/identity/missingness/quality checks. Public re-fetch is opt-in. No
   independent-review census or review requirement is imported as a Sandbox
   admission gate. The historical unordered CasJobs limitation stays explicit.
9. **`observational_dataset_intake.yml`**: six local-source contracts plus explicit
   public re-fetch for four publisher objects. FITS/VOTable parser functions
   preserve exact upstream source slices with provenance. Unhydrated pointers
   fail. Synthetic crossmatch and leakage checks are executable; actual survey
   matching/SFR and web display admission are not enabled. Full historical
   Zone.Identifier and selection-lineage bundles are not fabricated.
10. **`recovered-intake.yml`**: port fixture-only `recovery_intake` regressions:
    real-byte/LFS checks, large identifiers, malformed rows, path escapes,
    non-overwrite rules, qualified lineage and prohibition of support promotion.
    Do not run corpus-wide processing over historical code or hydrate arbitrary
    quarantine patterns. The current Sandbox archive remains byte-protected.
11. **`sciserver-v02-policy.yml`**: run all 16 original offline SQL/catalog/replay/
    receipt policy tests, not just a syntax check. Preserve exact canary and
    deterministic-probe SQL hashes; reject path escapes, symlinks, catalog/hash
    drift, remote activation and unapproved queries. No authenticated requests.
12. **`sciserver-approval-offline.yml`**: operator-signature/trusted-approver
    machinery is not copied. No live submission capability exists to authorize;
    remote disable flags and local receipt integrity remain enforced. This is
    not a bypass of operator authorization for an enabled service.
13. **`main.yml`**: port the portable provenance-capture validator and its isolated
    fixture regression. Do not schedule mutable Google Docs exports or claim
    authenticated source capture without the actual exported documents and
    authorized access. No messages or document updates are performed.
14. **`notebooks.yml`**: no canonical active notebook set exists in the Sandbox.
    Equivalent synthetic APIs, seeded nulls, numerical invariants and
    preprocessing/builders run as allowlisted tests. Historical notebooks and
    their stored output are not executed or relabeled as new evidence.
15. **`sky_surveys.yml`**: retain strict missing-source/schema failures, synthetic
    downsampling and union behavior, exact Parquet round-trip with pinned
    PyArrow, plus the original finite/positive cosmology diagnostics. Duplicate
    rows survive a union; no positional crossmatch is implied. Full production
    survey inputs are not substituted with synthetic observational claims.
16. **`build-image.yml`**: upstream Sage/GHCR publishing is inapplicable to this
    repository's isolated Python check package. Build/install/rebuild validation
    is implemented; no registry login, package-write permission, mutable
    `latest` image, container publication or deployment is added. A future
    Sage-native/eclib build needs its own reviewed digest-pinned toolchain.
17. **`starmap.yml`**: no `web_tool` application exists in this Sandbox. Web build,
    typecheck, browser, registry-sync, release receipt and display-admission
    checks are therefore inapplicable. Do not copy an upstream evidence website
    or grant sky-overlay admission as a substitute.
18. **`codeql.yml`**: retain the existing Python/Actions security analysis and
    its security-events permission, and pin its two action uses to the resolved
    v4 commit. New reproducibility workflows have read-only contents permission,
    immutable action revisions, no persistent credentials and no recursive
    submodule/LFS initialization. Existing trusted-base archive policy is intact.

## Additional software checks

The source manifest lists each ported test and exact source origin. Coverage
includes finite projection bounds, corrected empirical p-values, effect-size
direction, real GUDHI persistence/Wasserstein and missing-backend failure,
bootstrap/witness reproducibility, seeded synthetic MCMC, strict redshift and
positive-Hubble evaluation, Fisher-Rao invariants, symbolic-regression seeds and
input rejection, target-proxy/group leakage, spherical distance/oracle and
ambiguity checks, Planck chain metadata/weights/nonfinite rejection, recovery
and ZIP auditing, provenance-capture portability, and synthetic data builders.
No fallback fake persistence diagrams or successful skipped backends are allowed.

The pinned ECC PR #103 v3 source runs its two original software regressions,
including 16 analytic/quadrature fixtures and the C-03 wrong-comparator control.
The exact M1 E1a algebra certificate and saved E1b source/hash/normalization
regressions run in the pinned read-only reference checkout. Neither is a claim
of independent mathematical review, physical support, or a completed theory.

## Known defect preserved as negative evidence

The legacy `tests/test_entropy_geodesics.py` asserts only shape and passes while
`EntropyGeodesics.geodesic([1,2,3], [.1,-.1,.05], steps=10)` overflows. The exact
original test is preserved as text in `quarantined-checks/`, with its original
Git blob retained in the inventory. It is replaced in the executable suite by
an explicit invalid-arithmetic rejection control; numerical RuntimeWarnings now
fail. The original implementation remains unchanged and **is not certified as
a valid integrator**. Separate finite Fisher-Rao invariant tests are retained.
This is a known failure, not a repaired upstream numerical method.

`tests/test_quantile.py` defines another transformer implementation but contains
no tests. It is not counted as regression coverage. No test mirroring that
definition is invented to claim otherwise.

## Blocked, unavailable and intentionally inapplicable work

- **Live SciServer/CasJobs**: no authenticated operator session, actual job IDs,
  database snapshot or freshly exported results are supplied to Sandbox CI.
  SQL identity/policy can pass offline; server schema/execution/export checks
  cannot. The old unordered TOP selection cannot be recreated exactly even
  with new credentials. No token input or submission step is introduced.
- **Three placeholder datasets**: `DATA-PROVENANCE-ALL`,
  `DATA-PHYS-CONSTRAINTS`, and `DATA-ECC-THEORY` lack complete construction/
  freeze packages. They have no fabricated source contracts or passing checks.
- **Full historical lineage/recovery processing**: original quarantine payloads,
  binding sidecars and construction/selection protocols are not Sandbox inputs.
  Some are available in the legacy repo; this is an intentional scope/security
  boundary, not a claim they are globally unavailable. Fixture regressions and
  available-source byte/schema checks do not reproduce the full historical
  transformation or establish authenticity.
- **Google Docs capture**: no immutable authorized export bundle is supplied.
  Public-source endpoint access is not presumed; private exports may require
  separately authorized access. Artifact validation is portable; scheduled
  acquisition is not enabled.
- **Cosmology builders/full inference**: the legacy builder extracts input ZIPs
  and overwrites likelihood modules; it is not a safe generic CI build step.
  Planck/BAO/CC/Pantheon scientific input contracts and calibration are not
  established by this port. Synthetic loader/MCMC/math tests remain distinct
  from running observational cosmology or replacing placeholder likelihoods.
- **Sage/eclib/LMFDB execution, notebook and web publication**: source pins remain
  intact, but native builds and applications are not present as active Sandbox
  products. This port does not pretend package tests validate native Sage/PARI
  behavior, arbitrary historical notebooks, a website or a deployment.
- **Independent scientific review/approval**: deliberately excluded, rather than
  marked unavailable or passed. CODEOWNERS, repository/security review and
  archive protection remain applicable. There is no claim promotion authority.

## Validation interpretation

During this audit, the six preserved governed inputs passed byte/schema checks.
Fresh public downloads of HI-MaNGA, Pipe3D and GEMA also matched their locks.
The fresh VizieR response had the same 10,981,088 bytes and matching declared
schema/row/quality/missingness invariants, but SHA-256
`a5c75e3df8128d690d773effc3478a872d46aabc53c5a8fe4ed7165b3ddfb437`
instead of frozen
`654217f9b3414856c1a8b09071c81eb834a0b0fbc6ec3aea9777e01fdaea1079`.
Its receipt is **FAIL** and the differing response is preserved locally. The
frozen pin was not changed. Semantic agreement does not establish byte identity.

Run-specific local and exact-head GitHub validation are reported in the PR and
artifact receipts. A green software job means the described software contracts
passed on the tested commit; it is neither independent replication nor a
scientific result. Optional public-source acquisition is skipped unless explicitly
requested through its workflow input, and is never reported as a completed
fresh publisher re-fetch merely because local preserved bytes passed.
