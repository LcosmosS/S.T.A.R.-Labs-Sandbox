# SANDBOX / UNVERIFIED — SBX-2026-0008: Resource-qualified arithmetic v3

**Exploratory, versioned, NOT EXECUTED.** This is a distinct prospective protocol, not a rewrite of failed SBX-2026-0006. The full v2 eligible set requires **1,068,501 unordered pairs**, above its frozen 300,000-pair cap; the v2 primary endpoint was never computed. The source-bound independent pre-inference receipt lives in [SBX-0006 on PR #25](../SBX-2026-0006-arithmetic-pilot-v2/cohort_resource_receipt.json).

This v3 protocol precommits to taking every **16th conductor** in the *sorted list of eligible conductor strata*, zero-based index beginning at 0, **retaining all curves inside selected strata**. Preliminary source-structure census (no endpoint measured) gives 208 conductors, 3,324 curves and 67,094 unordered within-conductor pairs. These are source-derived design quantities, not scientific findings. The selection is deterministic and systematically sampled; no generalization to the population of all conductors is authorized.

## Protocol and reproduction

Read [protocol_v3.json](protocol_v3.json) before running. The unchanged v2 analysis/preflight implementation is locked to exact Git blob SHA identifiers. The opt-in runner `v3_runner.py` checks both source identities, the real ecdata SHA-256 and census, v3 counts, and the exact inherited rank/conductor permutation code before creating any outputs.

```bash
python3 -I experiments/SBX-2026-0008-arithmetic-pilot-v3/v3_runner.py \
  --source /path/to/allcurves.00000-09999 \
  --out /new/empty/v3-run-directory
```

It computes the one frozen primary arithmetic statistic, 1,999 conditioned permutations and six strictly descriptive scale sensitivities; output is stored only in the new folder with source/protocol/analysis hashes and a null CSV. **This runner has not been executed.** Its dependency is the separately reviewed/merged PR #25 v2 core, pinned at exact code blobs; do not run before those source files are available.

## Interpretation boundary

This is an arithmetic-only diagnostic with no observed galaxies, no cosmological units, no physical correspondence, no independent mathematical verification, and no proof. A null rejection does not validate the ACSC, ECC or GLMPCT hypotheses. Non-rejection or a resource failure remains archived. Promotion is forbidden automatically.
