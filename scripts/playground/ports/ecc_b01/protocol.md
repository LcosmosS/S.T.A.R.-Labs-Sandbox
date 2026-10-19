# EXP-ECC-B01 — Proposed mathematical-control protocol (DRAFT; not activated)

**Scientific status:** Fixture verification only. No empirical, physical, or arithmetic-cosmological support. This document does not change registry state.

## Scope and separation
A: non-exact closed one-form measured by periods in H1. B: U(1) connection measured by Chern flux and patch compatibility in H2. C: entropy-dependent exact curvature perturbation measured locally while the H2 class remains fixed. These are different theories, not equivalent repairs.

## Frozen mathematical conventions for fixture phase
- Manifolds: flat oriented T2 = R2/(2pi Z)2, round unit S2, contractible B3, and R3 adversarial local test. Coordinates phi,psi have 2pi period. T2 orientation dphi wedge dpsi; S2 orientation sin(theta)dtheta wedge dvarphi.
- T2 metric dphi^2+dpsi^2; Hodge star *dphi=dpsi and *dpsi=-dphi.
- Differential forms are real; B uses U(1) connection with real curvature normalized Q=(1/2pi) integral F. The complex connection convention is i times the real potential.
- S(phi,psi)=A cos(phi)+B sin(psi), with A=1 and B=2 for numerical checks; symbolic checks leave A,B free.
- A fixture eta=dphi+2dpsi+dS. Periods on standard positively oriented phi and psi cycles are (2pi,4pi). Negative exact control dS has zero periods. Nonclosed rejection: sin(phi)dpsi.
- B northern and southern potentials A_N=n/2(1-cos theta)dvarphi and A_S=-n/2(1+cos theta)dvarphi. Curvature n/2 sin(theta)dtheta wedge dvarphi; Q=n. Transition exp(i n varphi) must be single-valued. Charges n in {-1,0,1,2}; reject n=1/2.
- C F0=q dphi wedge dpsi; beta=*dS; F_S=F0+d beta=[q+Delta S]dphi wedge dpsi with Delta S=S_phiphi+S_psipsi. Total flux 4pi^2 q. For numerical checks q in {0,1}; local density changes for nonconstant S, but class does not. On 3D, F=z dx wedge dy is not closed and must be rejected.
- Contractible B3 has H1=H2=0; S2 H1=0 and H2=R; T2 H1=R2 and H2=R. These are *space* properties, not certificates that an arbitrary assigned form has nonzero class.

## Investigator assignments
Investigator A: Python SymPy/SciPy symbolic and numerical fixture suite, then independent discrete cochain/mesh implementation. Investigator B: independent SageMath implementation; PARI/GP may check exact constants/arithmetic but must not be presented as a full differential-geometric implementation. Contingency: SymPy + NumPy/SciPy, or Gmsh + FEniCSx for numerical differential forms; GUDHI for topology of complexes, not a direct substitute for gauge connections.

## Phase 1 — exact fixtures
Independently derive all formulae and run all analytic positive/negative fixtures. No code sharing. Exact failures block advancement. The **original** Investigator A kit (`investigator_a.py`) contains 15 symbolic/numerical checks; its preliminary 15/15 submission is historical smoke-test evidence only. The separately versioned `investigator_a_v2.py` and `investigator_a_v3.py` each contain 16 fixtures, including a C-03 negative control. The v2 WSL receipt and v3 CI evidence are distinct submissions. Neither version is an independent partner reproduction or substitutes for Phase 2/3.

## Phase 2 — numerical discretization (not yet implemented)
Each investigator independently chooses a documented discretization. Record mesh construction, incidence matrices, integration rules, coordinate charts, and orientation. Require cochain d_h^2=0 algebraically; evaluate periods and fluxes at four increasing resolutions, report observed convergence rates, gauge invariance and errors. Proposed final absolute tolerance 1e-6 for periods and normalized flux; justify and lock before execution. For exact-zero targets report absolute errors; for nonzero targets both absolute and relative errors. Distinguish integration of differential forms from Betti-number estimation. Check 3D closure with a genuine 3-form test, not a vacuous 2D dF=0.

## Phase 3 — independent comparison
Both parties record code commit SHA, source SHA256, dependency versions, platform, commands, data hashes (if any), expected and observed outputs, tolerances and failures. Commit reports before exchanging results. Compare exact values and numerical errors. Any discrepancy blocks PASS until independently explained. Report negative controls and failed cases, not only successes.

## Phase 4 — information-content study (separate preregistration)
Before using astronomical or elliptic-curve datasets, freeze the data cohort, projection, parameter rules, baselines, null randomization, primary endpoint, alpha and multiple-testing treatment. For C, global [F_S]=[F0] by construction, so only predeclared local descriptors can carry entropy-specific information; do not present global flux as entropy-derived evidence. For B, integral Chern charge on a fixed bundle cannot change continuously with S. For A, dS contributes no periods. A pass on mathematical fixtures does not authorize physical-support flags.

## Required artifacts
**Original-kit-only:** `protocol.md`, `investigator_a.py`, and the preserved historical output `submissions/investigator_a/preliminary_2026-10-17/results.json`. The name `investigator_a_results.json` refers to an original-kit transient output, not to a corrected-run receipt.

**Versioned corrections:** `investigator_a_v2.py` and its immutable output under `submissions/investigator_a/c03_correction_v2/executions/a-v2-20261017T234633Z-jqJdPZpa/`, including `investigator_a_v2_results.json`, `run_manifest.json`, dependency inventory, exit codes and logs. `investigator_a_v3.py` adds a negative test through the actual C-03 record construction; its dedicated CI workflow records a separate `ecc-b01-a-v3-ci-evidence` artifact with NumPy in the repository's declared range, not an Investigator A attestation. Preserve the prior evidence unchanged.

**Later stages:** independent partner implementation and manifest, `fixture_comparison.csv`, `convergence_a.csv`, `convergence_b.csv`, `counterexamples.md`, `claim_boundary.md`. Keep this work outside the controlled runner until approved and registries locked.

## Decision gates
G0 independent review of definitions; G1 analytic fixtures; G2 topological positive/negative controls; G3 independent numerical convergence; G4 independent replication; G5 separate information-content protocol. All gates are blocking; do not combine into one score. A mathematical PASS means only that the specified objects behave as expected on the fixtures.
