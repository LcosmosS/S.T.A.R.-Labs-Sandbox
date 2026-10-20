# SBX-2026-0005 — First-principles contradiction register

**Exploratory analysis; not a proof, independent review, or a new evidence claim.** The ledger lists historical manuscript assertions and necessary mathematical repairs; it does not edit archived manuscripts or rewrite their original meaning. A contradiction with a necessary mathematical identity is not an empirical falsification of every possible corrected physical theory.

Status fields must remain OPEN until a cited mathematical derivation or counterexample has been checked independently; external review status exists only upstream. A proposed repair is not accepted as the repair.

| Framework | Critical entries | High entries | Primary boundary |
|---|---:|---:|---|
| ACSC | 2 | 3 | Arithmetic map ≠ observed cosmological correspondence |
| ECC | 2 | 3 | Exact forms ≠ nontrivial de Rham class |
| GLMPCT | 3 | 1 | Coordinate rescaling ≠ physical metric invariance |

## Proof-obligation contract
For each `OPEN` item, record (1) manuscript section and assumptions; (2) well-typed domains and units; (3) an exact theorem, counterexample or explicit unknown; (4) a finite software regression when appropriate; (5) a separately cited independent crosscheck; (6) whether the proposition is repaired, narrowed or refuted. No `proven` or `validated` state is assigned by this Sandbox.

The full machine-readable list is in [contradictions.json](contradictions.json). It is intended for first-principles falsification experiments, not retroactive evidence promotion. A future ECC revision must explicitly distinguish non-exact H1 forms, U(1) H2 curvature, and entropy-dependent exact perturbations (v3 candidate); they are not interchangeable.

## Registered entry summary
- **ACSC-01** (Critical) — Conductor may double/halve along Q-isogenies. **Obstruction:** The manuscript's conductor-change examples contradict the Q-isogeny invariant used by Phi. **Proof/test:** For a specified Q-isogeny, compute conductors with two engines and exhibit equality.
- **ACSC-02** (High) — Discriminant-bounded cohort closed under isogeny. **Obstruction:** A member can have an isogenous partner with different minimal discriminant outside the bound. **Proof/test:** Construct exact partner pairs straddling the predeclared discriminant cutoff.
- **ACSC-03** (Critical) — Singleton homology equals cosmic manifold homology. **Obstruction:** An equality H*(Phi(E))=H*(M) cannot hold if M has nonzero H1 or H2. **Proof/test:** Check H1 and H2 of a point explicitly and compare with a circle/sphere target.
- **ACSC-04** (High) — Bijection of isogeny classes and cosmic homotopy classes. **Obstruction:** The two source statements are in tension without a restricted domain and equivalence relation. **Proof/test:** Find collisions or indistinguishable image signatures on pinned ecdata; do not interpret class clustering as a bijection.
- **ACSC-05** (High) — Universal numerical W2<0.01 correspondence. **Obstruction:** Coordinate rescaling or a changed sample can change Wasserstein distances without changing physical observations. **Proof/test:** Demonstrate rescaling sensitivity and no advantage against spatial/sampling-matched nulls.
- **ECC-01** (Critical) — Nonzero non-exact omega=d(dM). **Obstruction:** The claimed 2-form omega=d(dM) is identically zero and exact, not a nonzero H2 class. **Proof/test:** Exact edge coboundary and circle/torus counterexamples; derive the correct cohomology class.
- **ECC-02** (Critical) — Global potential theta yields nontrivial flux. **Obstruction:** Nonzero holonomy or flux requires topology, patchwise potentials, connection data or singularities not supplied by theta=dM. **Proof/test:** Integrate dM around a closed loop; independently verify any patchwise transition cocycle.
- **ECC-03** (High) — Hessian trace is Ricci and gradient flow is geodesic. **Obstruction:** A nonlinear coordinate change changes an ordinary Hessian; geodesic equation is an additional condition. **Proof/test:** Compute a coordinate-change counterexample and residual of geodesic equation for a chosen M.
- **ECC-04** (High) — Entropy probability weights from signed symbolic features. **Obstruction:** log(Reg), L_cosmo(1) and rank do not guarantee nonnegative weights or nonzero total. **Proof/test:** Exhibit a negative logarithmic regulator value or zero denominator and require explicit failure.
- **ECC-05** (High) — Unique nonexact class assigned to each curve. **Obstruction:** A point alone cannot select a global H2 class without a specified global construction and normalization. **Proof/test:** Use isogenous pairs and distinct curves with same proposed local coordinates.
- **GLMPCT-01** (Critical) — Conformal mapping preserves exact angle and area. **Obstruction:** Simultaneous arbitrary area and angle preservation requires an isometry locally, not merely conformality. **Proof/test:** Check sphere dilation with conformal factor k and area scaling k².
- **GLMPCT-02** (Critical) — Radius scaling flattens while preserving all original distances. **Obstruction:** Restoring original lengths by compensating metric change restores the original intrinsic curvature; cannot claim both for same intrinsic metric. **Proof/test:** For k>1 calculate Gaussian curvature and geodesic distance under both metrics.
- **GLMPCT-03** (High) — Closed 3-sphere is observationally established. **Obstruction:** Choosing k=+1 is not itself an observational validation of global spatial topology. **Proof/test:** Fit or cite independent curvature constraints; report results without assuming closure.
- **GLMPCT-04** (Critical) — Comoving volume and light travel distance invariant solely from comoving coordinates. **Obstruction:** A uniform coordinate remapping cannot certify both volumetric and null-geodesic invariance for a changed geometry. **Proof/test:** Construct a simple FLRW expansion example and compare light-travel versus comoving distance.
