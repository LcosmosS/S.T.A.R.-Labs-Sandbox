# ALFALFA100 provenance evidence — issue #34

This provenance-only Sandbox investigation compares the preserved frozen and publisher-refetched VOTables. It assigns no scientific status. The original publisher-refetch run 39368709247 remains FAIL. Raw SHA256 identity remains FAIL: the two original 10,981,088-byte files have different hashes.

Hypothesis: the complete responses differ only in two request timestamps. Test: authenticate both inputs, compare every table cell and XML metadata node, then independently replace exactly two byte strings in memory and demand whole-file equality. Observation: all 31,502 rows and 25 fields agree, including unique nonempty AGC keys, AGC order, FIELD descriptions, null conventions, typed values and lexical cells. Two XML metadata nodes differ. Interpretation: these particular authenticated responses have equivalent table content; any additional byte or scientific-cell difference falsifies this reconciliation.

The live DESCRIPTION has `Date: 2026-10-20T04:16:54 [V7.6.1]` versus frozen `Date: 2026-10-09T07:47:29 [V7.6.1]`. The live `<INFO name="request_date" value="2026-10-20T04:16:55">` has frozen value `2026-10-09T07:47:29`. Replacing precisely these two full strings in an in-memory copy produces exact frozen bytes. Neither original is rewritten or normalized on disk.

Frozen SHA256: `654217f9b3414856c1a8b09071c81eb834a0b0fbc6ec3aea9777e01fdaea1079`.
Refetched SHA256: `008502caa196f15883f199dfdb8979cfb91f20b087fb63235cd5d26fecc5a4f2`.
Typed digest (STAR-VOTABLE-TABLEDATA-TYPED-V1): `4019ecb6dbe8dc8378388837fa26c4dc8d804bd3738955da6b6287636adbcdcf`.
Lexical-cell digest: `bb40a7227805c7a5bb4896cfcbb4a23e13497e2606da6112bdfd18f7bf1c82d3`.

The comparator hashes JSON-encoded typed rows prefixed with the method identifier and complete FIELD descriptions. Integers and Decimal numeric values are canonicalized; declared nulls and empty cells have distinct tags. The lexical digest encodes parsed TD text in row order (it is not an XML serialization digest). Metadata comparison strips surrounding text whitespace and excludes TABLEDATA. The separate whole-file byte proof covers all serialization and whitespace differences omitted by these semantic comparisons.

## Reproduce

From the repository root, hydrate only these two LFS paths, then verify the hydrated file checksums. Use Python 3 with venv/pip support; the recorded comparator runtime and exact executable versions are in reproducibility.json. The byte test uses only the standard library and does not import the comparator. Do not run Python with `-O`, which disables assertions.

```bash
git lfs pull --include='experiments/SBX-2026-0009-alfalfa100-provenance/*.vot' --exclude=''
cd experiments/SBX-2026-0009-alfalfa100-provenance
sha256sum -c SHA256SUMS.txt
python3 -m venv /tmp/alfalfa-review-venv
/tmp/alfalfa-review-venv/bin/python -m pip install -r requirements.txt
/tmp/alfalfa-review-venv/bin/python -I alfalfa_votable_compare.py frozen.vot refetched.vot > /tmp/alfalfa-review-comparison.json
python3 -I verify_report.py /tmp/alfalfa-review-comparison.json
python3 -I byte_reconciliation_test.py
cd ../..
python3 -I scripts/validate_sandbox.py
```

The initial directory name failed the mandatory `SBX-YYYY-NNNN-short-slug` convention; the unchanged `sandbox_policy.log` preserves that historical failure. The directory now uses the previously unclaimed SBX-2026-0009 identifier and includes sandbox-only exploratory metadata. `policy_revalidation.log` records the current validator result separately. No policy exception or gate change is included.

## Evidence and limits

`frozen.vot` and `refetched.vot` are unchanged LFS originals. `frozen-pointer.txt` exactly matched the Legacy Git blob at commit `51927a9b396cdfa880f3128440db4715acdec8dc`, checked read-only before copying. The comparator and three supplied JSON reports are unchanged source evidence; `comparison_rerun.json` is a fresh execution against the original inputs. Logs preserve byte-test, comparator, LFS and policy outcomes. GitHub API snapshots record the repository ruleset, original failed run and artifact identity. `reproducibility.json` records commands and runtime; `evidence_manifest.json` hashes all other evidence artifacts; `SHA256SUMS.txt` additionally covers the manifest, excluding itself to avoid a cycle.

The artifact digest recorded by GitHub is `ece9228018e53ca5cb2e2d296657ca38c3d8e48903c3b6ee5fe176e8b2530585`; this investigation authenticates the supplied extracted binary by its expected SHA and does not independently download or authenticate the original artifact ZIP. The source comparator was supplied for this task; rerunning it and the separate byte proof is not external independent scientific review. A reviewer must inspect the methods and original source chain, hydrate the remote LFS originals and rerun the checks. No source registry, eligibility, scientific support, review or promotion gate changes are made. No claim of future publisher stability, scientific correctness, dataset admission, upstream acceptance or physical support follows. Issue #34 remains open; arithmetic v3 PR #32 is outside scope.

Current revalidation commands and outcomes, including the repository unittest suite, are recorded in `reproducibility.json` and separate revalidation logs. Original reports, scientific-check scripts and historical logs remain unchanged.

Policy revalidation: PASS. All 141 repository tests passed outside the sandbox after the initial loopback socket restriction (both logs retained). Archive revalidation remains FAIL because the read-only local Legacy reference lacks `.github/workflows/a01-activation-preflight.yml`; a reviewer must rerun against a complete checkout of the pinned upstream commit.
