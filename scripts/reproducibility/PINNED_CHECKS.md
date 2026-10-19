# Sandbox reproducibility checks

These are software, source-byte and artifact checks. Passing them grants no
scientific status, independent review, execution eligibility, display admission,
or automatic promotion. The existing trusted-base archive/policy workflow and
CodeQL protections remain required. No historical program is executed.

The [audit](audit/AUDIT.md) maps all 18 upstream workflows
and records exclusions, unavailable dependencies, and the known overflow failure.

## Reproduce locally

Use CPython 3.12 on Linux x86_64 (WSL is supported). CI pins Python 3.12.12 on
ubuntu-24.04. The lock accepts only the exact binary wheels for this platform;
other platforms must not silently re-resolve or build dependencies from source.

```bash
python3.12 -m venv /tmp/star-sandbox-checks
/tmp/star-sandbox-checks/bin/python -m pip install --require-hashes --only-binary=:all: -r scripts/reproducibility/requirements-linux-py312.lock
/tmp/star-sandbox-checks/bin/python -I scripts/reproducibility/integrity.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/star-sandbox-checks/bin/python -m pytest -q -c scripts/reproducibility/pytest.ini scripts/reproducibility/upstream/tests scripts/reproducibility/tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=scripts/playground/ports /tmp/star-sandbox-checks/bin/python -m pytest -q scripts/playground/ports/tests/integrations/test_sciserver_policy.py
/tmp/star-sandbox-checks/bin/python scripts/reproducibility/build_check.py --output /tmp/star-sandbox-build-new
```

Always specify the two test directories explicitly. Broad repository discovery
would include historical/reference files that are not executable test inputs.
The build check creates a new output directory, builds in disposable copies,
requires two byte-identical wheels, installs into a fresh virtual environment,
and reruns the software suite outside the checkout. It checks the sdist member
safety and exact artifact inventory, including hashes and sizes. The receipt
records the source commit, Sandbox commit, environment and lock digests. A local
receipt made before committing identifies the prior HEAD and is not exact-head
CI evidence; CI artifacts bind the tested proposed commit.

## Inputs and offline boundaries

`SOURCE_MANIFEST.json` binds byte-identical upstream copies to Git blobs and
SHA-256 at `51927a9b396cdfa880f3128440db4715acdec8dc`. Empty package initializers
are explicitly local adapters. A03 kernel/reference functions are extracted
with function-level provenance; they expose only synthetic tests, with no
cohort loader, controlled runner, preflight, registry or approval entrypoint.
`FORMAT_PROVENANCE.json` identifies the extracted FITS/VOTable parser functions.
The copied MIT license is included in source distributions and wheels.
Source copies retain original bytes, including two upstream trailing-space
lines; the whitespace check applies to locally authored changes.

`DATA_CONTRACTS.json` contains six non-authoritative source contracts. It is not
a scientific-status registry. Check a preserved local input explicitly:

```bash
python scripts/reproducibility/datasets.py --dataset DATA-SDSS18-200K --file /path/to/frozen.csv
python scripts/reproducibility/datasets.py --dataset DATA-ARITHMETIC --download /tmp/new-allcurves
```

The first mode never downloads. The second is an explicit HTTPS public-source
fetch to a **new** path. Wrong hashes, sizes, schemas, missing artifacts and LFS
pointers fail. The optional `public_sources` workflow input checks publisher
FITS/VOTable bytes and declared schema invariants; a serialization/hash mismatch
remains a failure. It never replaces a frozen source or promotes a registry.
Offline numerical tests deny outbound socket connections and reject skips or
runtime warnings. SciServer SDKs, tokens, live queries, arbitrary SQL,
deployments and recursive submodule initialization are absent.

The pinned ECC v3 regression runs two tests over 16 analytic/quadrature fixtures,
including the deliberately wrong C-03 comparator. This is draft-software testing,
not independent adjudication. Neither ECC v1/v2 nor historical research scripts
are executed. `src` functions keep upstream names inside an isolated test package;
the package must not be installed into an upstream production environment.

Saved A01/A03 packages and M1 algebra/certificate checks use a separate sparse,
read-only checkout of the immutable legacy revision. Package inspection checks
saved bytes and formulas; it does not rerun experiments or authenticate execution.
The symbolic certificate tests do not constitute external mathematical review.
