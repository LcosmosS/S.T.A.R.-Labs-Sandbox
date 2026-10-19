# SANDBOX / UNVERIFIED — SBX-2026-0003

**Status:** exploratory · **Field:** first-principles cochain algebra relevant to ECC and RTCH.

## Mathematical starting point

Let `M` be a single-valued real scalar on vertices. On an oriented edge
`e=(u,v)`, the discrete gradient is `(d0 M)(e) = M(v) - M(u)`.
Along a closed four-edge loop, summation telescopes:

```text
sum_boundary(d0 M)
 = [M1 - M0] + [M2 - M1] + [M3 - M2] + [M0 - M3]
 = 0.
```

This is the elementary discrete counterpart of `d(dM)=0` for sufficiently smooth globally defined `M`. It is **not a conjectural novel result**.

## Topology and critical distinction

- **Unfilled square graph (`S1`):** no 2-cells, so every graph 1-cochain is closed (`d1=0`); the assignment `[1,1,1,1]` has loop integral `4`, so it cannot be the gradient of a single-valued vertex scalar. This illustrates a nontrivial first cohomology class of the graph.
- **Filled square (disk):** adding the oriented face makes the same 1-cochain have `d1(theta)(face)=4`, so it is **not closed** there.
- **Exact gradient:** choose potentials `[0,1,4,9]`; edge values `[1,3,5,-9]` sum to zero, identically.

This control is relevant to ECC/RTCH **model construction**: if one defines an entropy 1-form as `theta=dM` with a smooth globally single-valued scalar `M`, then `omega=dtheta` must vanish. Nonzero flux or non-exact cohomology requires a different mathematical structure (e.g. a non-exact closed form, singularities, multivalued potentials, connections, or a specified nonstandard discretization), not merely a numerical claim.

## Reproduce

At repository root:

```bash
python3 -m scripts.playground.cochains
```

The stdout JSON includes the exact and candidate edge integrals, topology declarations and explicit nonpromotion flags. Only Python's standard library is needed; CI exercises the algebraic helper as a unit test but does not perform scientific inference.

## How this idea could fail

A nonzero loop sum from a purported discrete gradient would indicate inconsistent edge orientation, a non-single-valued potential, a modified cochain rule, or a bug. Misidentifying a filled face as an unfilled graph changes the chain complex. These controls do **not** show that spacetime entropy has a nontrivial cohomology class, that mass-energy changes, or that RTCH has a physical effect. There is no observational data and no independent review.

## Follow-on questions

For a concrete RTCH model: define the spacetime manifold, degree of the entropy form, regularity, boundary conditions, the exact cochain complex, and a gauge-invariant observable. Distinguish `H1`, `H2`, `H3` and derive a standard-physics recovery limit before matching measurements. Repeat cohomology checks on an explicit triangulation rather than inferring them from matrix ranks alone.
