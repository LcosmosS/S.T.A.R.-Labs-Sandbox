# Implementation erratum before arithmetic v3 execution

- The v3 protocol `protocol_v3.json` and all cohort/parameter/null/endpoint definitions are **unchanged**.
- The committed pre-execution Python runner referenced `core.ORIGIN_SHA256` in two places, but the frozen v2 preflight exports source SHA-256 as `core.SHA`. It would have raised `AttributeError` after calculating the 1,999 null draws and before writing any result. This is a provenance-symbol programming error, **not** a scientific observation or outcome.
- Repair: use the already locked `core.SHA`. Exact inherited v2 `analysis.py` and `preflight.py` Git blob SHAs remain immutable; all inferential methods unchanged.
- Add static core/source contract and an independent standard-library rebuild of all seven observed statistics, 1,999 conditioned Fisher–Yates label permutations, and exact tail classifications using the *same frozen Python MT seed*. Independent code does not import either analysis runner. Audit tolerance 5e-12 compares floating-point implementations; prespecified one-sided tail uses 1e-14 unchanged.
- The new workflow is `workflow_dispatch` for science execution and runs only static tests on pull requests. It never changes Legacy flags. **No arithmetic v3 result has been computed by this PR; execution is NOT_RUN until a real manual run ID and artifact are recorded.**
- Record failures without treating partial output as proof. The full 64,687-row source is verified by SHA-256/length and 208/3,324/67,094 cohort counts in both implementations.
