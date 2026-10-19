# EXP-ECC-B01 — Proposed blinded comparison of three ECC foundational candidates

**Status: DRAFT / REVIEW ONLY — NOT AN ACTIVATED OR EXECUTED PROTOCOL**

**Experiment reference:** `REPO-CSV-v0.2:EXP-ECC-B01` (verify canonical registry revision before activation).  
**Governing gate:** [ECC_RTCH_RECOVERY.md](../ECC_RTCH_RECOVERY.md).  
**Purpose:** Assess three mathematically distinct candidate replacements for the invalid inference `theta=dS => [dtheta] != 0`. No theorem, physical, or arithmetic-cosmological support is asserted.

## 1. Scope and boundary

For a globally defined smooth entropy scalar S, `d(dS)=0` and `[dS]=0`. The topology of the ambient space alone cannot make `[dS]` nonzero. This PR **does not choose a replacement theory** and **does not amend dependent ECC theorems**. It proposes mathematical controls, independent implementations, and a blinded adjudication procedure.

All experiment activation, registry transitions, claim-support flags, and physical interpretations remain blocked. This document is a **protocol proposal**, not a frozen preregistration. Formal activation requires the gate's independent signatures, versioned canonical parameter/null/dataset records, and a locked primary endpoint.

## 2. Candidate definitions (not interchangeable)

**A — Closed non-exact 1-form:** on smooth M, specify a global one-form eta with `d eta=0`, `[eta] != 0 in H^1_dR(M;R)`. Measure integrals of eta over independently specified closed 1-cycles. An entropy coupling must be explicit and must not equate eta with the exact differential dS.

**B — Nontrivial U(1) bundle connection:** specify a principal U(1)-bundle P over M, local connection potentials A_i, transition maps, curvature F agreeing on overlaps, and integer Chern flux `(1/2pi) integral_Sigma F in Z`. A topologically nontrivial torsion bundle need not have nonzero real de Rham curvature class. Gauge covariance, transition cocycles and orientation are mandatory.

**C — Separate entropy-coupled closed 2-form:** on an oriented closed Riemannian 2-manifold, fix a closed form F0 and globally defined entropy scalar S, and set `F_S = F0 + d(*dS)`. It follows that `dF_S=0` and `[F_S]=[F0]`. This tests **local entropy-dependent redistribution**, NOT entropy-generated topology. On a 2-manifold every 2-form is closed by degree; include a separate 3D closure counterexample.

## 3. Exact mathematical controls

Specify orientations, coordinates, units, cycle bases, and metric before execution.

| ID | Space / fixture | Expected exact result | Detects |
|---|---|---|---|
| A01 | T²; eta=dS, S globally smooth | all cycle periods 0 | exactness |
| A02 | T²; eta=dphi | periods (2pi,0) | H¹ generator |
| A03 | T²; eta=dpsi | periods (0,2pi) | second generator |
| A04 | T²; eta=dphi+2dpsi+dS | periods (2pi,4pi) | exact perturbation invariance |
| A05 | S²; globally smooth closed eta | all periods 0 | H¹ negative control |
| A06 | T²; eta=sin(phi)dpsi | d eta=cos(phi)dphi wedge dpsi != 0 | reject nonclosed candidate |
| B01 | S²; charge n=0 | normalized flux 0 | trivial bundle |
| B02 | S²; n=1 | normalized flux 1 | Chern flux |
| B03 | S²; n=-1 | normalized flux -1 | orientation |
| B04 | S²; n=2 | normalized flux 2 | integrality |
| B05 | S²; n=1/2 with proposed transition exp(i n phi) | reject as not single-valued | gluing |
| B06 | S²; n=1, legitimate gauge change | unchanged F and flux | gauge invariance |
| C01 | Flat T²; q=0, S constant | F_S=0 | zero baseline |
| C02 | Flat T²; q=0, nonconstant S | integral F_S=0; local density may vary | exact response |
| C03 | Flat T²; q=1, S constant | integral F_S=4pi² | baseline class |
| C04 | Flat T²; q=1, nonconstant S | integral F_S=4pi² | class rigidity |
| C05 | Flat T²; S -> S+c | F_S unchanged | shift invariance |
| C06 | Flat T²; S -> lambda S | exact perturbation scales, class fixed | local vs global |
| C07 | T³; F=sin(z)dx wedge dy | dF=cos(z)dz wedge dx wedge dy != 0 | 3D nonclosure negative control |
| T01 | B³ | H¹=H²=0 | contractible topology |
| T02 | T² | b1=2, b2=1 | torus topology |
| T03 | S² | b1=0, b2=1 | sphere topology |

For B on S² use northern/southern potentials `A_N=n/2(1-cos(theta))dphi`, `A_S=-n/2(1+cos(theta))dphi`. The overlap difference is `n dphi`. Check single-valued transition function, not just numerical flux.

For C on flat T², `F0=q dphi wedge dpsi`, `S=A cos(k phi)+B sin(l psi)` with integer k,l; fix Hodge-star convention and orientation in the signed protocol. The local density must be checked independently of the global integral.

**Important distinction:** GUDHI Betti numbers measure the *space*, not the class represented by eta or F. Gmsh/GUDHI topology checks cannot substitute for cycle/flux cochain integration.

## 4. Independent implementation design

- **Investigator A:** Python/SymPy/NumPy/SciPy; symbolic exterior differentiation and independent quadrature.
- **Investigator B:** Python/SymPy/Gmsh/GUDHI; independent derivations, meshes, simplicial/cochain checks and numerical integration. SageMath and PARI/GP may be optional cross-checks, not mandatory dependencies.
- Shared inputs: only this signed fixture specification and independently published reference identities. Do not share helper source code, intermediate results, or fitted tolerances.
- Each investigator commits a source revision and output SHA-256 manifest to a separate submission location, without inspecting the other's results.
- **Blinding caveat:** Known exact expected values are not hidden; this is blinded *implementation/output comparison*, not blinded ground-truth evaluation. Release outputs for comparison only after both manifests are locked.
- Before running: record dependency versions, operating system, mesh algorithms, seed, resolutions, numerical quadrature methods, precision, cycle representatives, orientation and acceptance tolerances. No post-hoc tuning.

## 5. Verification and numerical acceptance

1. **Exact identity gate:** symbolic derivations of d²=0, closedness/nonclosedness, period/flux values, gauge overlap and cohomological invariance.
2. **Discrete topology gate:** GUDHI homology of Gmsh-generated spaces must match the declared spaces, with documented treatment of boundary and periodic identification. A geometrically drawn torus is not automatically a topologically periodic mesh.
3. **Cochain gate:** discrete coboundary squared is exactly zero on oriented simplicial cochains; independently integrate forms on fixed cycles and surfaces.
4. **Resolution gate:** at least four preregistered resolutions, report error vs exact values, convergence order and failure diagnostics; mesh-dependent tolerances must be justified and locked before data inspection.
5. **Adversarial gate:** A06, B05 and C07 must be rejected for their respective reasons. A successful script exit is not sufficient.
6. **Independence gate:** compare exact identities and all numerical endpoints only after two separate immutable submissions.

Suggested engineering targets pending independent approval: period/normalized-flux absolute error <=1e-6 at final resolution, gauge comparison <=1e-8 where meaningful. These numbers are **not preregistered thresholds** until reviewers approve their suitability for the selected algorithms.

## 6. Null and sensitivity controls (must be frozen before activation)

- Exact perturbation null: vary S while fixing the A-period coefficients or B-bundle class; predicted cohomology remains unchanged.
- Entropy null for C: smooth phase shifts or amplitude changes of S; track both local density and invariant global flux.
- Discretization null: reverse orientation (signed periods/flux reverse), refine meshes, and independently change triangulations without changing underlying topology.
- Reject topology-only leakage: distinguish preselected H¹/H² generators from data-derived cohomology; do not infer entropy dependence from known Betti numbers.
- No galaxy, cosmology, arithmetic, or physical data are involved in this phase.

## 7. Required immutable submissions

Each investigator independently supplies:

```text
investigator_<A|B>/
  proof_notes.md
  counterexamples.md
  fixture_results.csv
  convergence.csv
  implementation_manifest.json
  nonclaims.md
  SHA256SUMS
```

Each manifest records source revision, source hash, environment lock/hash, fixture version, mesh generator/version, random seeds (if any), numerical conventions and commands. Include full failures and exceptions. Missing fixtures count as incomplete, not passing.

Comparison outputs, created only after both submissions are locked:

```text
comparison/
  paired_results.csv
  discrepancy_register.md
  independent_review_signoffs.md
  foundation_selection_decision.md
```

## 8. Decision rule and non-claims

**Mathematical verification** requires all exact controls and adversarial fixtures to behave as specified, numerical convergence within locked bounds, and agreement of the two independent implementations. If any required item is missing or fails, record INCONCLUSIVE/FAIL, not a pass.

Passing controls demonstrates that the *specified constructions* behave correctly on test spaces. It does **not** establish entropy-generated topology, physical entropy conservation, astrophysical torque/vorticity, BSD correspondence, cosmological structure, or uniqueness of a preferred ECC foundation.

Even if all candidates pass, foundation selection remains a separate decision based on what each invariant measures and whether it contains information beyond topology/geometry baselines. No dependent theorem is revised automatically.

## 9. Draft PR hold conditions

- [ ] Two independent reviewers approve exact definitions, counterexamples, and candidate separation.
- [ ] Resolve canonical experiment namespace and protocol location against registries.
- [ ] Freeze cochain degree, domain, coefficient group, null model, primary endpoint, tolerances, environment and mesh resolutions.
- [ ] Investigator A immutable submission received.
- [ ] Investigator B immutable submission received.
- [ ] Blinded comparison executed and discrepancies adjudicated.
- [ ] Reviewers approve an explicit selection / non-selection report.
- [ ] Separate authorization for any later registry or theorem edits.

**Do not merge this PR as a research result. Do not activate EXP-ECC-B01 or change support flags on the basis of this draft.**
