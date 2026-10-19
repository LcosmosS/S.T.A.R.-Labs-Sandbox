# SBX-2026-0004 — arithmetic isogeny geometry (SANDBOX / UNVERIFIED)

**Status:** exploratory; **scientific review:** none; **observational stage:** NOT STARTED.

## First-principles scope and protocol

[study_protocol.json](study_protocol.json) freezes 38 **actual** E/Q records selected by 1-based line number from John Cremona's immutable [`ecdata` allcurves source](https://github.com/JohnCremona/ecdata/blob/25cec5ecfec8b9f016eb1631ac633194c2bed39f/allcurves/allcurves.00000-09999) (SHA-256 `259f3846329395b371e8079c77a6f1097adaebc98a054974573e241416efa968`, 64,687 source lines). `curves.csv` contains original Weierstrass integers, conductor, rank, torsion, label, and source line. No observations and no synthetic elliptic curves are substituted.

We compute discriminant and j using the general Weierstrass invariant formulas, then compare two explicitly **dimensionless** embeddings:

* ACSC-like: `(ln |Delta| / ln 10^30, ln N / ln 10^9, r)`; the original 200 m rank-altitude is divided by 200 m before taking Euclidean distances. The metric is an imposed arithmetic diagnostic, **not** a cosmological metric.
* Modified MCJ-inspired, BSD-free: `(ln N / ln 10^9, asinh(j/1728)/40, ln(1+T)/ln 13)`. This deliberately **differs** from the original complex-log MCJ candidate; for E/Q, rational j has zero/constant phase, making the original imaginary axis degenerate and `log 0` undefined.

Both are actual arithmetic maps, not reconstructed 3D galaxy positions. The primary endpoint is the **difference** between maps' equal-conductor averaged `(mean between-isogeny-class distance - mean within-class distance)`. Condition the 999 permutation draws on `(conductor, algebraic rank)` while shuffling only the class labels; this preserves an isogeny-rank invariant already encoded in ACSC and prevents a tautological rank advantage. The p-value is one-sided, empirical, plus-one corrected, and **exploratory**, not preregistered before this result. No selection adjustment or inferential generalization is claimed.

## Frozen computation and negative finding

Run from the root on Python 3.12+ with no external dependencies or network:

```bash
python3 -I scripts/reproducibility/arithmetic_pilot.py --check
# Strong source identity audit, with 2.1 MB ecdata source already downloaded by existing CI:
python3 -I scripts/reproducibility/arithmetic_pilot.py --check --source /path/to/allcurves.00000-09999
```

All 38 source lines are checked against the **full-file** authenticated SHA when `--source` is given. CI uses its existing pinned ecdata download and verifies byte-identical `result.json`. Input and output digests, sizes, and schema are independently checked by `reproducibility.json`; no experiment-supplied executable is auto-run.

An earlier **unconditioned, methodologically inappropriate** permutation gave **p = 0.005**; the conditional null was chosen after inspecting that result to address trivial rank leakage, so it is **not preregistered**. That historical exploratory result is retained in `result.json`, not hidden or claimed as support.

The frozen conditional result is **T = 0.355925264911**, with conditional empirical **p = 0.344** (343 of 999 shuffles at least this large), MC standard error reported in `result.json`. The diagnostic **does not reject** the stated conditional null at descriptive alpha 0.05. Its initial apparent association is sensitive to control of direct rank information; an unrestricted class-label permutation would be methodologically unsound. This is negative/inconclusive arithmetic evidence, not a cosmological falsification of ACSC.

## Limits and separate observational stage

The sample is purposive, small and biased; MCJ is intentionally modified; scales are not physically derived; no curve-to-galaxy correspondence, held-out galaxy data, or causal mechanism is tested. Coordinate and cohort sensitivity, independent invariant computation and survey-selection nulls remain unresolved and recorded in the protocol. **Observational stage is separately `not_started`.** Nothing here establishes or refutes physical ACSC, BSD, ECC, GLMPCT or RTCH, and nothing is automatically eligible for Legacy.
