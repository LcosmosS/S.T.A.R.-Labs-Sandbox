# Independent partner handoff — ECC-B01

Use SageMath for your independent differential-form/topology checks, with PARI/GP for exact arithmetic checks where helpful. Do not port or inspect Investigator A's implementation before committing your own results. The shared source of truth is `protocol.md`, not Investigator A's code or output.

Implement three separate modules:
1. `a_periods`: eta=dphi+2dpsi+dS on flat T2, check closedness, periods 2pi and 4pi, exact-form negative control, and nonclosed rejection sin(phi)dpsi.
2. `b_bundle`: patch potentials A_N, A_S on S2, compute curvature, patch overlap, integral Q=n for n=-1,0,1,2, reject half-integer transition. Do not claim bundle consistency from curvature integration alone.
3. `c_entropy`: F0=q dphi^dpsi and F_S=F0+d(*dS); check local density, flux 4pi^2q, invariance under S->S+c and entropy amplitude changes, and 3D rejection of z dx^dy as nonclosed.

For each module provide symbolic derivation, a numerical check with separate quadrature code, negative controls, and any counterexample. Commit a source SHA-256 and environment manifest before looking at Investigator A's output.

**Caution:** These are exact mathematics fixtures, not empirical ECC validation. The existence of a nonzero class does not imply entropy generated it. Mathematical success cannot change the repository's evidence flags.
