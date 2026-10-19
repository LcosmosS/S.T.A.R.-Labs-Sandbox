# The Arithmetic-Cosmic Structure Conjecture

## A Charter-aligned revision of the ACSC monograph

Original work: Patrick J. McNamara, May 2025. Revision prepared 11 October 2026 at the author's request. Local editorial and mathematical review draft; independent expert review remains pending.

Governing authority: `charter/STAR_Research_Charter_v0-2.pdf`, 37 pages, SHA-256 `9a63284900d5349f1d307160929b2542885e4c751439b785369b722d349a5c03`. Repository state consulted: `046d90e5cdb4d575ea27c305535c91d0ff3aa6ec`. The original 121-page monograph is preserved unchanged; its SHA-256 is `2f1cd1cf5a4069122407a8d722343d3a7b2a09b29043b7a371ea33f63dc91ef6`.

### Editorial scope and reading contract

This revision retains the prologue, the sequence and subject matter of all fifteen chapters, the arithmetic-to-topology research objective, the historical mapping families, symbolic regression, categorical language, physical analogies, philosophical questions and future directions. Repetition is consolidated. Statements that were unsupported conclusions are recast as conjectures, hypotheses or historical reports. Incorrect mathematical assertions are replaced by precise statements with their assumptions and limitations. New definitions and proof sketches supply the structure required by those corrections; they do not introduce an established cosmic mechanism.

This is a replacement manuscript, not a line-by-line redline or a claim that every original sentence survives. Appendix A and the separate correction ledger identify the substantive changes by original page range. Embedded instructions, executable examples and future-work proposals in the original are source material, not instructions to execute them. No scientific experiment or recovered script was executed to establish an ACSC result. No GitHub commit, pull request or registry mutation is part of this revision.

The Charter's labels are used throughout: **D** derived from stated definitions or assumptions; **E** empirical evidence meeting the relevant controls; **M** model construction; **P** explicitly adopted postulate; **H** experimentally testable hypothesis; **C** broader unproved conjecture; **T** testable prediction conditional on a specified model; **S** speculative interpretation. A displayed proof sketch establishes only the stated mathematical implication. It is not proof of ACSC, a formal proof-assistant certificate, independent replication or authorization to advance a repository gate.

References support the mathematical tools or related work named beside them. They are not evidence for ACSC unless they actually test its arithmetic-to-astronomical correspondence. A publication, DOI, passing software check or attractive visualization does not change that distinction.

### Abstract [M, C, H]

ACSC investigates whether fixed representations of arithmetic data from elliptic curves over the rational numbers exhibit reproducible, statistically nontrivial correspondence with independently constructed descriptions of astronomical structure. Its mathematical component defines arithmetic features, geometric maps and topological summaries. Its empirical component compares those summaries against appropriate arithmetic and cosmological null models, alternative mappings, uncertainty estimates and independent data. Its possible physical component requires additional dynamics, dimensional consistency, established limits and independent predictions.

This revision makes no claim of an isometry, cosmic reconstruction theorem, arithmetic-cosmic bijection, universal rank-curvature identity or validated physical law. It corrects the isogeny behavior of conductor and regulator, defines the mapping's dimensionality and metrics, distinguishes finite point clouds from filtered complexes, states conditional persistence stability and reconstruction results, and withdraws unsupported convergence and spectral claims. Historical numerical reports remain visible but are not promoted to evidence. The central correspondence remains open and is allowed to fail.

### Contents

Prologue - A precise conjecture and its limits

1. Foundations of ACSC
2. Formal statement, axioms and mapping structure
3. Algebraic structures and geometric implications
4. Topological structures and persistent homology
5. Simulation and empirical evaluation
6. Symbolic regression and model discovery
7. Categorical reformulation
8. Physical cosmological implications
9. Quantum structures and modularity
10. String theory, Langlands and categorical unification
11. Ontological and philosophical implications
12. Experimental and observational pathways
13. A framework for future fundamental theory
14. Scientific evaluation and future mathematical cosmology
15. Open questions and formalization

Appendix A - Original-to-revision reconciliation

Appendix B - Mathematical checks and proof obligations

Appendix C - Claim and evidence worksheet

References - Governing documents, mathematical tools and related work

# Prologue - A precise conjecture and its limits

### The research question [C]

Let S be a finite, explicitly selected collection of elliptic curves over Q, or one declared representative of each selected rational isogeny class. Let I(E) be an arithmetic feature vector and let Phi_theta be a deterministic map with parameters theta fixed without access to the confirmation data. Its image is an arithmetic representation P_theta in a declared metric space X. Separately, let Q be an astronomical sample, constructed with a frozen observational selection, coordinate system, uncertainty model and survey window. A specified filtration and statistic turn P_theta and Q into comparable summaries.

**ACSC-C0, local manuscript conjecture [C].** At least one independently motivated, prospectively limited arithmetic representation may have reproducible correspondence with a specified astronomical structural observable beyond the registered competing and null models. The conjecture does not assume one-to-one matching, preservation of physical distances, cosmic causation or validity for every elliptic curve, survey, epoch or scale.

An unrestricted assertion that some sufficiently flexible map fits some data is not a useful empirical hypothesis. Every operational ACSC-H instance must therefore freeze its cohort, mapping family, observable, comparison geometry, primary statistic, meaningful effect threshold, nulls and rejection conditions before confirmation. Failure of an instance rejects that instance within its scope. A negative result for every member of a closed, registered family can reject that family's operational correspondence claim; it cannot quantify over all imaginable maps.

### Operational hypothesis [H, T]

For a diagram-based example, define a nonnegative discrepancy delta between the arithmetic and astronomical summaries. Smaller values represent stronger similarity only because that direction is explicitly defined. A testable instance predicts both an independently calibrated absolute agreement and an improvement over appropriate baselines of at least a preregistered size eta. A small raw distance alone is insufficient: scaling all coordinates down makes diagram distances small without discovering a correspondence.

Historical statements of more than 98 percent fidelity and W2 below 0.01 are retained as historical proposals. They are not acceptance thresholds here. No percentage is inferred from a diagram distance without a separately defined denominator and calibration. No approximation tolerance is dimensionless unless the entire representation and distance have been made dimensionless under fixed conventions.

### What the conjecture does not imply [D, S]

Equal persistence summaries need not identify an elliptic curve, an isogeny class or a cosmic object. A point by itself has the homotopy type of a point; comparing individual projected points by homotopy therefore cannot distinguish curve classes. A nontrivial comparison concerns a filtered population, graph, field or region with specified structure. The claims that arithmetic generates gravity, matter, time or the universe remain speculative and are addressed conditionally in later chapters.

The modularity theorem and existing cosmic-web TDA establish important tools on opposite sides of the proposed comparison. Neither supplies the missing bridge. [R3, R7, R8]

# Chapter 1 - Foundations of ACSC

### 1.1 Elliptic curves and their arithmetic data [D]

An elliptic curve over Q is a smooth projective genus-one curve with a chosen rational identity point. In characteristic zero it admits a short Weierstrass equation, but integral minimal models generally use the full Weierstrass form. [R1, R2]

$$
E:\quad y^2=x^3+ax+b,\qquad \Delta=-16(4a^3+27b^2)\ne0.
$$

$$
y^2+a_1xy+a_3y=x^3+a_2x^2+a_4x+a_6.
$$

The group of rational points has a finite torsion subgroup and a free part. The Mordell-Weil theorem is established mathematics; the equality of algebraic and analytic rank in full generality remains the BSD conjecture. [R1, R2]

$$
E(\mathbf Q)\simeq E(\mathbf Q)_{\rm tors}\oplus\mathbf Z^{r_E}.
$$

Use Delta_min for the minimal discriminant, N for the conductor, r for algebraic rank, Reg for the regulator, t for torsion order and Omega for a real period under a declared differential and integration convention. The discriminant detects singular reduction of a model; it is not itself a geometric measure of cosmic complexity. Conductor measures arithmetic ramification and determines the level of the associated weight-two modular form. Rank is the dimension of the rational free part. None is defined as mass, time, gravitational curvature or entropy.

For a genuine basis P_1,...,P_r of the free part and a declared canonical height normalization, define the Gram matrix and regulator. The determinant is the squared covolume, not the covolume. Rank zero uses the determinant of the empty matrix, conventionally one.

$$
H_E=(\langle P_i,P_j\rangle)_{i,j=1}^{r_E},\qquad
\operatorname{Reg}(E)=\det H_E,\qquad \operatorname{covol}(E)=\sqrt{\det H_E}.
$$

A finite-index generating set that is not a saturated basis gives a different determinant. Its index and saturation evidence must accompany the value. An analytic-rank estimate is not silently substituted for algebraic rank. Unknown, conditional or bounded ranks are recorded as such, with the method, precision and proof status.

### 1.2 L-functions and BSD [D, C]

For a prime of good reduction, a_p is the deviation of the finite-field point count from p+1. The good-prime Euler factor is given below; bad primes require their appropriate separate factors.

$$
a_p=p+1-\#E(\mathbf F_p),\qquad
L_p(E,s)=(1-a_pp^{-s}+p^{1-2s})^{-1}.
$$

For elliptic curves over Q, modularity establishes analytic continuation and the functional equation of the completed L-function. Those properties must not be described as merely conjectural for this domain. [R3] The general BSD rank and leading-coefficient assertions remain conjectural. With standard compatible period and height normalizations, the conjectural leading coefficient has the familiar structure

$$
\frac{L^{(r)}(E,1)}{r!}
=\frac{\Omega_E\operatorname{Reg}(E)\,|\Sha(E)|\prod_p c_p}{t_E^2}.
$$

This equation is labeled C unless its validity for the particular curve and quantities is independently established. Numeric agreement, rounded integer estimates for Sha and an apparently correct rank are not a general BSD proof. The meanings of the period, local factors, differential, basis and finiteness assumptions must agree before even a numerical comparison is meaningful.

ACSC does not require BSD as a premise. It can study documented algebraic or finite-field quantities, and computational experiments must declare any conditional input separately. This follows the Charter's BSD-independence requirement rather than the original phrase “BSD-valid curves.”

### 1.3 Astronomy and topology [M]

The cosmic web is an inhomogeneous distribution inferred from galaxies, matter tracers, lensing and simulations. An FLRW background models homogeneous expansion; it is not a replacement for the web's inhomogeneous matter distribution. A galaxy catalog is a set of observed tracers, not automatically a smooth three-manifold or a complete sample of matter. CMB angular maps, redshift surveys and N-body simulations are different data objects with different selection and likelihood models.

Persistent homology describes connectivity and higher-dimensional cycles in a chosen filtration. Beta_0 counts components; beta_1 counts independent loops; beta_2 counts cavity-like cycles. Filament identification also requires an appropriate skeleton, graph, ridge or equivalent geometric method. A branching tree of filaments can have no loops, so beta_1 is not a filament count. [R7-R9]

### 1.4 Bridges and analogies [C, S]

Arithmetic geometry, modular forms and mathematical physics supply motivation for considering arithmetic representations. Mathematical realism, string compactification, Langlands and holography are related intellectual settings. They do not validate the ACSC map or establish an arithmetic origin for physical space. The mathematical universe hypothesis is an ontological proposal, not an empirical control. [R15-R17]

The research task is to construct a definite representation and let independent data determine whether its summaries outperform appropriate alternatives. All subsequent chapters use that limited meaning of correspondence.

# Chapter 2 - Formal statement, axioms and mapping structure

### 2.1 Domain, representation and observation [M]

Use three distinct objects: the arithmetic domain S; its representation space X; and the independently defined astronomical data Q. A map from S into X does not automatically land in observed cosmic space. A coordinate calibration, matching or distributional comparison between X and the astronomical representation is a second operation that must be specified separately.

$$
\Phi_\theta:S\longrightarrow X,\qquad P_\theta=\Phi_\theta(S).
$$

If the data are represented with multiplicities, retain the indexed records and their IDs. The set image collapses coincident coordinates; a measure or labeled multiset does not. This choice affects counts, density and topology and cannot be made after viewing the result.

### 2.2 Mathematical axioms for the model [P]

**Axiom A1 - Admissible arithmetic objects.** Every admitted record is nonsingular, uniquely identified and connected to a declared minimal model or justified model convention. Its feature values and their proof or estimation status are recorded. A fixed finite selection rule defines S.

**Axiom A2 - Deterministic representation.** Feature transforms, parameters, units, missing-value rules, treatment of duplicates and numeric precision are specified before confirmation. The map is a model definition, not a claim that nature uses it.

**Axiom A3 - Explicit geometry.** X has a declared metric or pseudometric. Each comparison uses specified filtrations, coefficient fields, scale ranges, boundary conventions and essential-feature policies.

**Axiom A4 - Separate observations.** Astronomical selection and measurement are independently defined. An object-level join, if used, has frozen keys or geometry and multiplicity rules. It cannot be manufactured from the outcome being tested.

**Axiom A5 - Declared categorical structure.** A construction called a functor supplies its source and target categories, action on morphisms, and identity and composition laws. An object-level coordinate formula alone does not meet this axiom.

These axioms define an analysis framework. They are not physical axioms asserting that all space arises from curves. Statistical controls and authorization remain requirements of the Charter, not deductive axioms from which cosmic correspondence follows.

### 2.3 A Cartesian feature representation [M]

Choose fixed positive scales L_Delta and L_N and a fixed rank scale alpha. A simple three-coordinate illustration avoids angular interpretation entirely. It is named Phi_cart here to distinguish it from any frozen repository mapping:

$$
\Phi_{\mathrm{cart}}(E)=\left(\frac{\ln|\Delta_{\min}(E)|}{L_\Delta},
\frac{\ln N_E}{L_N},\alpha r_E\right).
$$

The coordinates are abstract dimensionless features if the constants are declared dimensionless. They are not right ascension, declination, redshift or Mpc. A regulator feature can be stored separately as an attribute, or included in an explicitly four-dimensional representation:

$$
s_E=\ln(1+\operatorname{Reg}(E)/R_*),\qquad
\Phi_4(E)=(\Phi_{\mathrm{cart}}(E),s_E),\quad R_*>0.
$$

R_* fixes a reference scale under the chosen height convention. A fourth attribute does not become a fourth physical spatial coordinate. Weighted distances in the four-dimensional representation require prospective weights. The regulator-free map remains available when a regulator is unknown or expensive; it is not silently replaced by a guessed value.

Fixed reference denominators prevent existing coordinates from changing every time the cohort grows. Cohort maxima are permissible only in a separately declared fitted or sample-dependent mapping with honest discovery/confirmation separation. They do not ensure cross-cohort stability by themselves.

### 2.4 The historical angular map, corrected [M]

The original proposed longitude from log discriminant, an angle from log conductor and elevation from rank, with historical constants 360, 180, 200 and base radius 1000. These constants are preserved as historical model choices, not privileged physical numbers. The interpretation of the second angle must be resolved explicitly.

If lambda is longitude, beta is latitude in [-pi/2,pi/2] and rho is a radius, the Cartesian conversion is

$$
X=\rho\cos\beta\cos\lambda,\qquad
Y=\rho\cos\beta\sin\lambda,\qquad Z=\rho\sin\beta.
$$

If theta is instead colatitude in [0,pi], the conversion is

$$
X=\rho\sin\theta\cos\lambda,\qquad
Y=\rho\sin\theta\sin\lambda,\qquad Z=\rho\cos\theta.
$$

Both satisfy X^2+Y^2+Z^2=rho^2. The original repeated Y as Z; that expression is incorrect. Also, an angle scaled into [0,180 degrees] is a colatitude convention, not ordinary signed latitude. Choose one convention in a new protocol instead of mixing them. Trigonometric functions take radians; conversion is required for their mathematical definition, not just numerical stability.

Write h_E=alpha r_E and rho_E=rho_0+h_E so that Z, h and observational redshift z_obs are not confused. Use rho_0 rather than R for the base radius to avoid collision with regulator. Require rho_E>0 and specify longitude seams, clipping and behavior outside nominal bounds. A corrected illustration does not retroactively repair or relabel a frozen historical run.

### 2.5 Lemma 2.1 - Feature-map Lipschitz bound [D]

Let u(E)=(ln|Delta_min|,ln N,r,s) and let a Cartesian map be Phi(E)=A u(E)+b for a fixed matrix A and vector b. Define d_I(E,F)=||u(E)-u(F)||_2. This is generally a pseudometric on curves because features can collide. Then

$$
\|\Phi(E)-\Phi(F)\|_2\le\|A\|_2\,d_I(E,F).
$$

**Proof sketch.** Subtract the two affine expressions and apply the defining operator-norm inequality. The result permits rank zero because rank is not logged; absolute discriminant and positive log arguments are required. It says nothing about cosmic distances. For a nonlinear spherical map, a Lipschitz bound additionally requires a bounded radial/feature domain and a derivative bound in the chosen chart; a global claim does not follow merely from “using logarithms.”

### 2.6 Degeneracy and the operational conjecture [D, H]

**Lemma 2.2 - Projection degeneracy.** Identical input feature vectors give identical output coordinates for a deterministic map. Adding torsion can separate some records but gives no general injectivity theorem. Equal topological summaries are even weaker than equal feature vectors.

**Proof sketch.** Apply the same function to equal inputs. Nothing in this implication identifies the inverse image. In particular, extra attributes do not supply a proof that no remaining collisions exist.

An ACSC test therefore asks whether a fixed representation has externally useful structural information, not whether it establishes an unexplained bijection. The prologue's operational hypothesis is the statement tested in later chapters. An isometry would require a separately defined arithmetic distance, astronomical distance, alignment and exact or approximate preservation theorem; none is assumed.

# Chapter 3 - Algebraic structures and geometric implications

### 3.1 Moduli and rational arithmetic [D]

Over C, elliptic curves are complex tori C/(Z+tau Z), with Im(tau)>0, modulo the appropriate modular action. The complex analytic moduli stack is described using the upper half-plane and SL_2(Z); it is not the entire integral stack over Spec(Z). Rational elliptic curves with the same j can be nonisomorphic twists. [R1, R2, R18]

$$
j(E)=\frac{c_4^3}{\Delta}
=1728\frac{4a^3}{4a^3+27b^2}\quad\text{for a short model}.
$$

Morphisms in the moduli stack are isomorphisms of families over the base. Isogenies require correspondences or a separately defined category; they are not silently all morphisms of the ordinary elliptic-curve moduli stack. The space of rational arithmetic features is not a smooth coordinate chart in which rank varies continuously. Moduli language does not itself make Phi a derived functor.

### 3.2 Isogeny behavior [D]

**Lemma 3.1 - Rational-isogeny invariants.** A rational isogeny E to E' preserves algebraic rank, conductor and L-function. It need not preserve minimal discriminant, torsion, real period or regulator. [R1, R2]

**Proof sketch for rank.** For an isogeny phi of degree d, its dual satisfies phi_dual composed with phi equals multiplication by d. After tensoring rational-point groups with Q, phi has inverse phi_dual/d. Their dimensions agree. For conductor and L-function, the isogeny induces an isomorphism of rational l-adic Tate modules, respecting Galois action. Local characteristic factors and Artin conductor exponents therefore agree; choosing an auxiliary l different from the residue characteristic handles each local conductor. This corrects both “sometimes rank is preserved” and “conductor may double or halve.”

**Corollary 3.2 - A conductor cutoff is isogeny-saturated.** If N_E<=B, every Q-isogenous E' has N_E'<=B. Adding a fixed minimal-discriminant cutoff need not preserve saturation.

**Counterexample.** Cremona 11a3 has minimal equation y^2+y=x^3-x^2 and Delta=-11. Cremona 11a1 has equation y^2+y=x^3-x^2-10x-20 and Delta=-11^5=-161051. They lie in the same rational isogeny class and both have conductor 11. A cutoff |Delta_min|<=100 admits 11a3 and excludes 11a1. Thus bounded conductor plus bounded discriminant is not automatically closed under isogeny. Exact discriminant arithmetic is checked in the accompanying mathematical-check record; the isogeny-class attribution comes from the pinned ecdata source and LMFDB. [R19, R20]

Hecke correspondences over C and graphs of rational isogenies are related but distinct. The “isogeny volcano” terminology is principally associated with suitable finite-field isogeny graphs; it is not a general description of a complex Hecke orbit. A graph of curve relations is an arithmetic structure, not yet an astronomical filament graph.

### 3.3 Minimal models and discriminants [D]

For the substitution x=u^2 x', y=u^3 y' in a short equation, the new coefficients and discriminant satisfy

$$
a'=u^{-4}a,\qquad b'=u^{-6}b,\qquad \Delta'=u^{-12}\Delta.
$$

The inverse direction gives the inverse scaling. Stating the direction is essential; the original sign of the exponent was inconsistent with its substitution. General admissible changes also permit translation terms. A chosen integral minimal discriminant removes arbitrary rational-model scaling but does not make discriminant invariant under isogeny.

### 3.4 Regulator transformation and lattice geometry [D]

Fix compatible canonical heights and let phi:E to E' have degree d. Let m be the finite index of phi applied to the free Mordell-Weil group within the free part of E'(Q). Then

$$
\widehat h_{E'}(\phi P)=d\widehat h_E(P),\qquad
\operatorname{Reg}(E')=\frac{d^r}{m^2}\operatorname{Reg}(E).
$$

**Proof sketch.** Images of a basis have Gram matrix d H_E and determinant d^r Reg(E). An index-m sublattice has determinant m^2 times the ambient lattice determinant. Equating them yields the formula. Rank zero has the empty determinant convention. “Regulator changes only mildly” is not a theorem and is not used in this revision.

Under a basis change U in GL_r(Z), the height matrix changes by U^T H U. Its determinant is unchanged, but its ordinary eigenvalues generally are not. A spectral feature based on those eigenvalues needs a declared basis, reduction rule or appropriate intrinsic spectral construction. It is not automatically a basis-independent arithmetic invariant, much less a Laplace-Beltrami spectrum.

### 3.5 Isogeny clusters and geometric interpretations [H, S]

Rank and conductor give equal coordinates within an isogeny class for the relevant feature components. Discriminant and regulator may move other coordinates. A claim that this produces a small-diameter basin, a connected filament or a short geometric edge requires a metric-specific bound or empirical measurement. Existence of a small-degree isogeny does not supply that bound automatically.

If a representation is intended to depend only on isogeny class, either use features invariant under isogeny or select a deterministic representative and declare that choice. The latter is an algorithmic convention, not an intrinsic quotient-invariance theorem. Counting all curves in a class as independent observations can introduce arithmetic redundancy; one representative or a declared weighting and dependence model is required.

Regulator as deformation potential, rank as symbolic elevation and torsion as stiffness remain descriptive interpretations of model features. Curvature, mass, density and forces require additional mathematical objects and empirical calibration. The transition from arithmetic graph to geometric mesh is part of the model; the transition from mesh to astronomy is the unproved correspondence.

# Chapter 4 - Topological structures and persistent homology

### 4.1 What is being analyzed? [D, M]

A finite subset P of Euclidean space has the discrete subspace topology: H_0 records its distinct points and higher homology vanishes. A point cloud has a metric and a trivial ordinary topology, rather than “no topology.” Nontrivial shape summaries arise by constructing an offset, simplicial filtration, density field or other specified object from it.

Fix a field F, for example F_2. The Vietoris-Rips complex at edge-length threshold t contains a simplex when all its pairwise distances are at most t. This threshold convention must be kept distinct from a ball radius.

$$
\operatorname{VR}_t(P)=\{\sigma\subseteq P:\operatorname{diam}(\sigma)\le t\},
\qquad \operatorname{VR}_s(P)\subseteq\operatorname{VR}_t(P)\ (s\le t).
$$

Persistent homology is the family H_k(VR_t(P);F) together with maps induced by inclusions. Its diagram is a multiset of birth-death pairs with multiplicity; unbounded intervals require a declared convention. If ordinary H_0 retains an essential component, do not silently put an infinite death into a finite Wasserstein sum. Use reduced H_0, separately match essential intervals, or apply a prospectively justified truncation.

To compute H_2 deaths, three-dimensional simplices are needed. Restricting a complex to its two-skeleton can create spurious surviving cavities. The original assertion about a complex of dimension at most two preserving all beta_0,beta_1,beta_2 is therefore incorrect in general.

### 4.2 Betti numbers and structural interpretation [D, H]

$$
\beta_k(t)=\dim_{\mathbf F}H_k(\operatorname{VR}_t(P);\mathbf F).
$$

Beta curves depend on filtration, coefficient field, density, survey window, scale and boundary conventions. Components may be related to cluster organization, loops to connectivity, and cavities to void topology. The relationships require astrophysical interpretation rather than an identification by definition. An open filament may contribute no loop; a cavity in the complex need not be an astrophysical void according to a separate void finder.

The original inequalities beta_1 much greater than beta_0 and fixed cluster or void scale ranges are not universal cosmic-web facts. They require a named sample, estimator and scale. This revision retains them only as historical expectations that an experiment could evaluate. Large persistence may signal robustness to a specified perturbation but can also reflect masks or selection artifacts. It is not intrinsically proof of physical significance. [R7-R10]

### 4.3 Diagram distances [D]

For finite off-diagonal diagrams D and D', augment each with the diagonal of infinite multiplicity. For p>=1 and an explicitly fixed ground norm, define

$$
W_p(D,D')=\left(\inf_\gamma\sum_{x\in D\cup\mathrm{diag}}
\|x-\gamma(x)\|_\infty^p\right)^{1/p}.
$$

Only nonzero-cost matches contribute; gamma is a bijection of the augmented multisets. Bottleneck distance replaces the sum with the supremum of matched costs. For finite diagrams an optimal matching can be used. The ground norm, multiplicities, diagonal and essential intervals are part of the definition, not library defaults left undocumented.

**Lemma 4.1 - Scale dependence.** If finite diagrams are scaled by c>0, W_p(cD,cD')=c W_p(D,D').

**Proof sketch.** Scaling gives a bijection between candidate matchings and multiplies each cost by c. Take the infimum. For edge-threshold Rips persistence, scaling the point-cloud metric by c likewise scales birth and death values. Consequently an absolute distance below 0.01 has no independent meaning without scale and uncertainty calibration.

Wasserstein distances can also depend strongly on the number of features. For a matching with M nonzero pairs each of cost at most eta,

$$
W_p(D,D')\le M^{1/p}\eta.
$$

Thus a bottleneck bound alone does not give a cohort-independent W_2 tolerance. Sample size, total persistence or other finiteness controls are needed for stronger Wasserstein claims. [R5, R6]

### 4.4 Theorem 4.2 - Conditional persistence stability [D]

Let f and g be tame functions on the same compact triangulable space, with persistence in a fixed degree and field. Under the standard diagram conventions,

$$
d_B(D_k(f),D_k(g))\le\|f-g\|_\infty.
$$

**Proof sketch.** If their sup-norm difference is at most eta, each sublevel set of f lies in the sublevel set of g shifted by eta, and conversely. The inclusion maps form an eta-interleaving; the stability theorem supplies a matching with cost at most eta. The full theorem and technical tameness requirements are supplied by the cited literature. [R4, R5]

For two labeled finite clouds with corresponding point displacement at most eta, every pairwise distance changes by at most 2eta. The same simplex test gives an interleaving of the corresponding Rips filtrations shifted by 2eta, hence a finite-diagram bottleneck bound with that convention. This is a stability statement about perturbations of a corresponding configuration. It does not prove that two independently generated clouds are close.

### 4.5 Conditional reconstruction instead of the original topology lemma [D]

For a compact smooth submanifold M of Euclidean space, without boundary and with positive reach tau, suppose the finite sample P lies on M and is sufficiently dense in it. A precise reconstruction theorem applies to the union of balls U_epsilon(P), with an explicit relationship between epsilon, density and reach. For the standard noiseless result, epsilon/2-density and epsilon<sqrt(3/5) tau are sufficient under the theorem's assumptions for U_epsilon(P) to deformation retract to M. The nerve of its convex-ball cover is a Cech complex and has the same homotopy type. [R11]

**Proof sketch.** A sufficiently narrow tubular neighborhood has a unique nearest-point projection. The theorem controls the ball union so that this projection yields a deformation retraction. Convex intersections give a good cover; the nerve lemma transfers the result to the Cech complex. No claim is made that an arbitrary Rips complex at every scale is that Cech complex.

The sampling hypotheses have to be established for the same manifold M. Large arithmetic sample size, rank distributions or a BSD assumption do not prove density near an astronomical manifold. This replaces the original “Nyquist-style” condition and the unconditional topological embedding lemma; it leaves the required arithmetic-to-cosmic closeness as an empirical hypothesis.

### 4.6 Lemma 4.3 - Conditional metric approximation [D]

If M is compact and P_n is a finite subset of M whose Hausdorff distance to M tends to zero, then its Gromov-Hausdorff distance to M tends to zero.

**Proof sketch.** Their common ambient metric realizes an admissible comparison, giving d_GH(P_n,M)<=d_H(P_n,M). The assumed right side tends to zero. BSD does not establish this Hausdorff-density assumption for arithmetic projections. Similar persistence diagrams do not imply Gromov-Hausdorff closeness: persistence is a summary and need not determine the metric space.

# Chapter 5 - Simulation and empirical evaluation

### 5.1 Arithmetic intake [M]

Construct a finite cohort from version-pinned arithmetic sources, or from a specified deterministic generator. Record source URL and revision, untouched source bytes, SHA-256, field schema, minimal-model convention, label mapping, curve and class counts, selection and exclusions. A recursive coefficient generator is a selection rule, not a theorem of complete coverage or increasing rank. Reject singular equations explicitly.

The original proposed discriminant and conductor limits, ranks zero through three, 15,000 curves and approximately 300 isogeny clusters are historical choices or reports. A replacement experiment must freeze its own population and document why it is suitable. “Approximately 2.3 nodes per Mpc cubed” is not a physical density until a justified conversion from representation units to volume exists.

Library installation and computation must be separated from scientific provenance. Record exact versions of SageMath, PARI/GP and TDA libraries, but a package list does not identify the astronomical data or prove an invariant. Do not deserialize unreviewed pickle objects or execute recovered notebooks simply to obtain an apparent result.

### 5.2 What current repository packages establish [E about repository records, not ACSC]

At the consulted revision, the repository claims CLAIM-ACSC-001, -002 and -003 have controlled-support and physical-support eligibility false. A01 is a narrow arithmetic rank-coherence protocol, not a cosmic comparison. Its approved execution-only activation is archived; the original frozen protocol's “disabled” header is historical and is not silently altered here. Its input source has 64,687 rows and its locked one-per-isogeny-class cohort has 38,042 records. Its mapping constants and endpoint belong to that experiment, not a newly corrected angular illustration. [G3]

A03 is a separately preregistered, rank-blind conductor/j mapping with a within-conductor-decile null. Its frozen cohort has 37,936 records after 106 j=0 exclusions. Its archive is pre-execution reference verification and is not independently replicated inference or an execution activation. An arithmetic association detected by either protocol would not by itself establish astronomical correspondence. [G3]

M1-INH-E1 remains formally planned while an exact symbolic candidate certificate is archived and independent mathematical review is pending. P0-ANSATZ-001 has a closed preregistered search frame, with registered candidates untested in the reviewed docket. These are separate theory gates, not interchangeable numerical experiment IDs. [G3]

These statements report the source records, not independently rerun outcomes. This rewrite makes no new gate promotion.

### 5.3 Historical results retained with limitations [historical M]

The original reports a 15,000-curve construction, a density-matched SDSS DR12 sample within 300 Mpc, Betti “match ratios” of 95.6, 92.6 and 91.9 percent, and diagram distances W_2(D_1)=0.0098 and W_2(D_2)=0.0114. Those are documentary reports, not validated measurements in this edition. The displayed Betti rows read 8 versus 91, 2 versus 218 and 3 versus 37; no match-ratio formula is supplied. It would be improper to invent missing digits or a definition that makes those rows agree.

The value 0.0114 exceeds the proposed threshold 0.01. A post hoc “noise envelope” cannot rescue that criterion without a frozen uncertainty model. More fundamentally, the threshold itself is exploratory under the Charter. Historical overlay claims about aligned filaments, high-rank cluster centers and regulator-linked voids lack the source, matching and confirmation evidence necessary for support here. Their images, numbers and original prose remain in the preserved source and correction ledger.

Neither a finite list of distances nor increasing sample size proves asymptotic convergence. The original empirical convergence lemma and BSD-based Gromov-Hausdorff theorem are withdrawn as theorems and replaced by Chapter 4's conditional statements and a prospective convergence test. No claim of a “first full empirical validation” survives this revision.

### 5.4 Astronomical intake and geometric comparison [M, H]

Freeze a named catalog and release, not just “SDSS,” “Planck” or “Millennium.” Record the original query, download or publisher response, object IDs, coordinate reference frame, redshift convention, survey mask, completeness, tracer selection and calibrated physical quantities. SDSS's recovered 200k sample was identified by the user as a renamed CasJobs export, originally MyTable_pmqr771_0.csv; that assertion alone does not establish its query, bytes or confirmed population. Query history, metadata and hashes must establish that lineage for the exact file used.

For observational RA and declination, use their proper spherical meanings. A flat-background comoving conversion uses a prospectively fixed cosmology, with chi(z) integrated from H(z), followed by the standard Cartesian coordinate equations. If a curved background or redshift-space treatment is used, declare the relevant geometry rather than assuming Euclidean physical distance.

Do not density-match by tuning against the confirmation endpoint. A frozen thinning or weighting procedure may address tracer-density effects if its purpose, randomness and sensitivity are specified independently. Masks, boundaries, redshift distortions, peculiar velocities, galaxy bias and observational uncertainties enter both the target and the cosmological null model.

### 5.5 Reproducible computation [M]

The prospective pipeline is: validate inputs; evaluate the locked map; construct the locked filtration or field; compute summaries; generate registered null replicates; calculate the fixed endpoint and uncertainty; preserve every result and failure. Do not change labels, thresholds or exclusions after seeing the outcome. A second implementation or independently constructed environment should reproduce the result within prospectively declared tolerances.

For H_2, include the required simplex dimensions and resource limits. For sparse or approximate persistence, record the approximation and error bounds. Full Rips persistence on tens of thousands of points can be infeasible; landmarks, alpha complexes or density-based filtrations are different declared methods, not invisible shortcuts.

Exports such as PLY or XYZ are derived artifacts with their own hashes and source relationships. Visualization coordinates, source data and topological inputs must agree with the manifest. A corrupted or manifest-inconsistent artifact is quarantined, not made valid by a successful plot.

# Chapter 6 - Symbolic regression and candidate arithmetic laws

### 6.1 The role of equation discovery [M]

Symbolic regression searches a declared expression space for functions that balance fit and complexity. It can generate interpretable candidates, but an interpretable expression is neither a proof nor a physical law. The search grammar, dimensional constraints, loss, complexity penalty, seed, software version and selection procedure are parts of the model. PySR provides one implementation of this approach [R21]. Schmidt and Lipson illustrate equation discovery from experimental data in a different setting [R22]; that work supplies methodological precedent, not evidence for ACSC.

A candidate must state its input domain and target. Predicting another arithmetic invariant is an arithmetic task. Predicting a coordinate that was defined from an input is a reconstruction task. Predicting an independently measured astronomical quantity is an observational task. These tasks cannot share a success label without specifying which one was evaluated.

### 6.2 Identity leakage and split design [D, M]

If the map defines z = alpha r and the features contain r, predicting z can attain perfect accuracy without discovering any relationship to the cosmos. The same problem occurs when the target is s = ln(1 + Reg/R_*) and the features contain Reg. Removing the exact target column is insufficient if equivalent, deterministically related or outcome-derived information remains in the features.

**Lemma 6.1 - Reconstruction is not independent prediction [D].** If y = g(x) is used to generate labels and the candidate model contains g, zero prediction error on fresh x values demonstrates reconstruction of g, not independent evidence that y is an astronomical observable.

**Proof sketch.** Substitution gives g(x) - y = 0 by definition, regardless of whether any observational data exist. Thus the score contains no test of a relationship to independently acquired observations. It remains a useful software test of the implementation of g.

Arithmetic discovery splits should keep all members of an isogeny class together when their dependence could transmit target information. Standardization and expression selection must use the training data only. Observational confirmation should use prospectively locked survey regions or independent releases with boundary and selection effects addressed; a random 80/20 split alone does not establish spatial or survey independence. A final holdout must remain unused for choosing operators, maps, parameters, targets and preferred equations.

### 6.3 Historical candidate expressions [historical M, unverified H]

The original monograph reported the following expressions without a complete reproducible fit package. Here t denotes torsion order and pi_E = Omega_E Reg(E) is merely a named arithmetic product, not a physical constant:

$$
z \approx 198.4\,\frac{\ln(1+\mathrm{Reg})}{\ln N}.
$$

$$
s \approx \frac{\ln(1+\Omega)}{t+1}.
$$

$$
\widehat h(P_K) \approx \frac{\Omega\,\mathrm{Reg}\,r^2}{\ln N}.
$$

$$
q(E)=\left\lfloor\frac{\ln|\Delta_{\min}|}{(\ln N)^2+t}\right\rfloor.
$$

These are transcriptions of proposed fits, not endorsed equations. Logs of dimensionful quantities require fixed reference scales; the original expressions did not establish such scales or a common period convention. The last expression is an integer score, not a defined per-curve Betti number. Betti numbers belong to a complex or filtration; they do not decompose canonically into additive contributions from individual curves. A deletion influence or local-complex statistic could be defined prospectively, but it would be a new target.

The original sample output also used a square root for the period/torsion expression while its displayed equation did not. That inconsistency is retained in the correction ledger; the absent fit artifact does not justify choosing whichever version looks better. The numerical coefficient 198.4 and sample scores 1.000 and 0.998 remain historical, unvalidated reports. No recovered code was executed to recreate them.

### 6.4 A candidate score instead of unique symbolic gravity [M, S]

The original proposed a unique field G_E. A scalar score can instead be defined, with every normalization frozen:

$$
g(E)=\frac{\ln(1+\mathrm{Reg}(E)/R_*)}{\ln N_E}\,\Omega_E\mathrm{Reg}(E).
$$

There is no uniqueness theorem for this choice, and no established conversion from its units to force, energy or gravitational curvature. Its association with a declared topological statistic is an empirical hypothesis. Other permissible scores and simple baselines must be compared without selecting the preferred score on confirmation data.

### 6.5 Validation of candidate equations [M, T]

Prospective evaluation should report held-out error, uncertainty, residual structure, calibration, robustness and complexity relative to explicit baselines. An R-squared threshold of 0.95 is not a universal criterion for scientific success. A high score can follow from restricted ranges, dependence or leakage. Physical interpretation requires independently justified variables, dimensions, limiting behavior and new predictions that can fail.

Software examples should use the pinned tool's operator interface: a one-argument log belongs among unary operations, not ordinary two-argument operations. The original PySR snippet is historical illustrative code, not an authorized executable protocol. A future search should log all candidate-selection decisions and preserve unsuccessful candidates; changing the grammar after examining a holdout starts a new discovery study.

# Chapter 7 - Categorical reformulation

### 7.1 Objects and morphisms before a functor [D, M]

A category needs objects, morphisms, identities and associative composition. Let C_isog have selected elliptic curves over Q as objects and Q-defined isogenies, including identity maps, as morphisms. A finite registry of selected representatives need not be closed under every isogeny; specify the actual category or its full subcategory rather than assuming the data selection contains every possible target.

An invariant map from curves to points is initially a function on objects. It is not automatically a functor to a category of cosmological spaces. Such a functor would also need an assigned map for each arithmetic morphism, with compatible identities and composition. Equal rank or small coordinate changes do not provide those maps.

### 7.2 A valid filtered-homology construction [D]

Consider finite metric spaces and nonexpanding maps, meaning maps f satisfying d(f(x),f(y)) <= d(x,y). Sending X to its Vietoris-Rips filtration and then to homology over a fixed field produces a functor to persistence modules. A vertex map is allowed to identify vertices; its image on each simplex still spans a simplex.

**Lemma 7.1 - Rips functoriality [D].** A nonexpanding f sends every simplex of VR_t(X) to a simplex of VR_t(Y). These induced simplicial maps commute with the filtration inclusions and with composition.

**Proof sketch.** Every pair of vertices of the source simplex has distance at most t. The same is true of the image vertices by the nonexpanding inequality. Inclusion and composition act on the same vertex maps, so the corresponding diagrams commute. Applying homology preserves composition and identity.

An L-Lipschitz map can instead map VR_t(X) to VR_(Lt)(Y), with the scale change explicitly included. To connect C_isog to this construction, ACSC must construct appropriate maps of whole metric datasets and establish their bounds. Mapping a single curve to a singleton space yields a formally valid but topologically uninformative construction. The original claim of homotopy equivalence from invariant preservation does not follow.

### 7.3 Natural transformations and Heegner data [M, open obligation]

A natural transformation between two declared functors assigns a morphism to every object and makes a square commute for every morphism. Calling a relation natural does not prove those squares commute. For Heegner points, one must choose the imaginary quadratic field, the Heegner hypothesis, modular parameterization, field of definition, trace procedure, normalizations and compatibility under isogeny. Gross-Zagier supplies an established arithmetic relation under specified hypotheses [R12]; it does not supply an ACSC natural transformation without this additional construction.

### 7.4 Fibers, degeneracy and information loss [D, M]

For an ordinary function Phi, the fiber over x is the set of curves E with Phi(E) = x. These fibers describe degeneracy of the chosen representation. A fiber is not a new motive, a quantum state or a physical region unless those structures are separately defined. Rank and conductor alone generally fail to distinguish curves; adding more features may reduce collisions but does not establish injectivity.

### 7.5 Topos and motivic language [M, S]

For a small category C, its presheaf category Set^(C^op) is an established way to construct a topos. One may encode declared arithmetic data in such a setting. Existence of this mathematical construction does not prove that its internal logic is complete for BSD or that it describes the physical universe. Any proposed ACSC topos needs an actual site or category, an interpretation of its objects and a specified use in the argument.

The degree-one cohomological motive h^1(E) should not be conflated with the technical notion of a 1-motive. Realizations in rational cohomology are established mathematical tools. They do not determine a cosmological fiber functor at a plotted coordinate. Chapter 10 retains this idea as an open construction problem rather than an existence lemma.

# Chapter 8 - Physical cosmological implications

### 8.1 The conditional physical question [S]

Even a replicated topological association would not identify a force law. The physical extension of ACSC asks whether independently justified dynamics and a coupling to observations can be built from arithmetic structures. No such dynamics is established by the present map. The analogies in this chapter preserve the original research direction while separating it from the mathematical results above.

### 8.2 Symbolic fields and derivatives [M]

Values s_i = ln(1 + Reg(E_i)/R_*) assigned to projected points x_i define a sampled scalar attribute. They are not a differentiable field on spacetime. One possible declared extension on a region with nonzero denominator is

$$
s_h(x)=\frac{\sum_i K((x-x_i)/h)s_i}{\sum_i K((x-x_i)/h)}.
$$

**Lemma 8.1 - Smooth extension on its domain [D].** If K is smooth, h > 0 is fixed and the denominator is nonzero on an open region, s_h is smooth on that region.

**Proof sketch.** Finite sums of smooth functions are smooth, and division by a nonvanishing smooth function preserves smoothness. This permits mathematical gradients and Hessians there; it gives no gravitational interpretation to them.

The bandwidth, kernel and boundary handling alter these derivatives. They must be frozen before testing. Since z = alpha r takes discrete values and many curves share r, a quantity such as d^2s/dz^2 is undefined without an interpolation, conditioning or averaging rule. An interpolated derivative is a property of that rule and data, not a coordinate-free curvature theorem.

### 8.3 Curvature, rank and regulator [S]

Rank is dimensionless and the regulator is a height-lattice determinant. Neither is observational mass. The original expression K(x) approximately r/(1 + Reg) is a proposed scalar score with no derivation from a metric. Ricci curvature is a tensor determined by a metric; scalar curvature is its trace. Neither is generally the second derivative of an arbitrary scalar attribute, and positive scalar curvature does not follow from the displayed rank/regulator expression.

A geometric model would have to define a metric and then compute its curvature, with regularity and coordinate conventions stated. A physical interpretation would further require dimensional normalization, couplings, equations of motion, conservation and recovery of independently verified limits. These are missing obligations, not consequences of persistence.

### 8.4 Evolution and cosmic time [S]

The rank of a fixed curve does not evolve when a plotted time parameter changes. A time-indexed family E_t, a selection process or an arithmetic transition rule must be defined before rank evolution is meaningful. No theorem here requires its rank to increase, let alone follow an exponential expansion law. Likewise, a path through the modular parameter tau is not a physical clock without a proposed dynamics and observational calibration.

For a complex lattice, the standard invariant is

$$
j=1728\,\frac{g_2^3}{g_2^3-27g_3^2}.
$$

The denominator contains g_3^2, correcting the repeated g_2 expression in the original. Approaching a degeneration in a family of complex tori is mathematically meaningful; identifying it with heat death or inflation remains speculative. The modular identification of tau also means that a clock rule must respect, or explicitly fix, that redundancy [R18].

### 8.5 Stress-energy, dark matter and dark energy [S]

A diagonal array populated with rank, regulator or period is not automatically a tensor: its transformation law, manifold, dimensions and geometric role have not been specified. An equation described as an arithmetic Einstein equation needs a defined covariant left-hand side, a defined stress-energy tensor, compatibility conditions and a controlled action or other consistent dynamics. Writing two undefined tensors equal does not produce such a theory.

Torsion as dark matter, rank as dark energy, and finite-field fluctuations as vacuum structure remain analogies. Each requires an independently defined mechanism and observable predictions, with alternatives and recovery limits tested. No present arithmetic or visualization result is evidence for any of these identifications.

### 8.6 Scope of the current physical gates [E about repository records]

The consulted repository separates P0 parent-ansatz selection from the M1 inhomogeneous elliptic consistency study. A closed preregistration is not a passed physical test. A candidate exact certificate requires the declared domains, branch choices, full tensor verification and independent review. A failure within a restricted parent class is not a universal no-go theorem for every possible physical extension. The monograph supplies neither authorization to run these studies nor permission to promote their outcomes beyond their registered scope [G3].

# Chapter 9 - Quantum structures and modularity

### 9.1 Modularity with the correct transformation law [D]

The elliptic-curve modular form is a weight-two newform at level N. With the standard convention, for a matrix gamma in Gamma_0(N),

$$
f_E\left(\frac{a\tau+b}{c\tau+d}\right)=(c\tau+d)^2 f_E(\tau).
$$

This is covariance of a weight-two form, not ordinary invariance under every matrix of SL_2(Z). Modular functions such as j have a different transformation property. The normalized Eisenstein series E_4 vanishes at the order-three elliptic point and E_6 at i, with translates under the modular group. This corrects the original assertion that Eisenstein series have no zeros [R18]. Modularity does not, by itself, identify a physical gauge symmetry.

### 9.2 Frobenius traces and Sato-Tate [D]

At a good prime p,

$$
a_p=p+1-\#E(\mathbf F_p),\qquad |a_p|\leq 2\sqrt p.
$$

Write a_p = 2 sqrt(p) cos(theta_p), with theta_p in [0,pi]. For a non-CM elliptic curve over Q, Sato-Tate gives limiting angle density (2/pi) sin^2(theta); the equivalent density of u = a_p/(2 sqrt(p)) is (2/pi) sqrt(1-u^2) on [-1,1]. The CM case has a different distribution and must be separated. The proven arithmetic equidistribution result [R13] is not a derivation of quantum foam or cosmological noise.

The finite group E(F_p) is abelian, but need not be cyclic, correcting another assertion in the original. For example, y^2 = x^3 - x over F_3 is nonsingular and has the identity and the three points (0,0), (1,0), (2,0). Each nonidentity point has order two, so the group is Z/2Z times Z/2Z rather than cyclic of order four.

### 9.3 Heegner heights and L-derivatives [D, S]

Gross-Zagier relates a derivative of an appropriate base-change L-function to the canonical height of a Heegner point, under its arithmetic hypotheses and normalizations [R12]. A safe schematic form is

$$
L'(E/K,1)=C_{E,K}\,\widehat h(P_K),
$$

where the constant, point and normalization are part of the theorem's specified setup. This display does not claim the same formula for arbitrary E, K or an unnormalized derivative over Q. A nonnegative height is not automatically a Born probability: a quantum probability also needs a state space, normalized amplitudes and a measurement rule. That extension is speculative.

### 9.4 L-function zeros and spectral proposals [C, S]

The original Hermitian-spectrum lemma is removed as a theorem. No self-adjoint arithmetic Hamiltonian, operator domain, Hilbert space or proved spectral correspondence was given. Nontrivial zeros are complex numbers; equating them directly to real eigenvalues of a Hermitian operator is already a type mismatch. A proposed spectral construction must first specify a real normalization and prove its analytic properties. The relevant generalized Riemann hypothesis is not a theorem supplied by this monograph.

Random-matrix analogies can motivate statistical questions, but the symmetry class depends on the family and statistic. There is no universal inference from L-function zeros to quantum states, and a numerical resemblance to a spectral distribution would not provide an operator construction.

### 9.5 Torsion and isogeny as quantum analogies [D, S]

For E/Q, the possible rational torsion groups are cyclic of orders 1 through 10 or 12, or Z/2Z times Z/(2m)Z for m = 1 through 4 [R14]. This theorem classifies arithmetic groups; it does not make them conserved gauge charges. Isogenous curves share important arithmetic structures, but an isogeny is not entanglement. Physical entanglement requires a composite state and a specified tensor-product decomposition with a nonseparable state.

The original correspondence table is therefore read as a list of research analogies: rank/mass, regulator/curvature, torsion/gauge sector, Frobenius fluctuation/noise, L-zero/spectrum, Heegner height/amplitude and isogeny/entanglement. None is a validated physical identification. Any future claim must supply the missing structures and an experiment that distinguishes it from the underlying arithmetic alone.

# Chapter 10 - String theory, Langlands and categorical unification

### 10.1 Elliptic geometry in other theories [D, S]

Genus-one complex curves occur as worldsheets and in elliptic fibrations, but these are different constructions. A worldsheet map into a target need not be an embedded surface. A complex torus obtained from E/Q does not retain its entire rational descent structure merely by being a worldsheet. An elliptic fibration used in a compactification is also not the finite coordinate map Phi.

These established uses of related mathematics motivate comparison, not an embedding of ACSC into string theory. A proposed connection must specify the target, action, fields, symmetries and which arithmetic information is retained. No T-duality or S-duality follows solely from modular coordinates.

### 10.2 Arithmetic and geometric Langlands [D, S]

Arithmetic Langlands connects specified Galois and automorphic structures; elliptic-curve modularity is one established instance. Geometric Langlands uses different geometric objects and versions of a correspondence between sheaf-theoretic or categorical data on moduli of bundles and dual-group local-system data. Kapustin-Witten develops a physical approach involving gauge theory and electric-magnetic duality [R15]. It does not establish an ACSC functor or any correspondence to galaxy positions.

The research question retained here is whether a precisely defined arithmetic representation can participate in an independently useful categorical construction. It must name the groups, base, categories, morphisms and realization maps. Calling the projected point cloud a Langlands dual is not such a construction.

### 10.3 Motives and projection [M, open obligation]

For an elliptic curve, cohomology gives a rational vector space with additional structures. In a suitable motivic setting one may discuss realization functors; their properties depend on the category and equivalence relation chosen. An arbitrary coordinate x = Phi(E) does not specify a fiber functor from an entire motivic category, nor a rule preserving a cosmic homology class.

The original “Motivic Projection Consistency” lemma is replaced by **Construction problem 10.1**: define the source category, target category and functor; specify which cohomological information it preserves; show compatibility with morphisms; and demonstrate that the proposed preservation statement is nontrivial. Until this is done, there is no existence theorem to invoke.

### 10.4 Mirror symmetry and holography [S]

Mirror symmetry and holography have precise settings. The Hodge-number exchange familiar for appropriate Calabi-Yau threefold pairs is not a theorem about any two isogenous elliptic curves or arithmetic point clouds. Maldacena's proposed gauge/gravity correspondence concerns specific theories and limits [R16]. A sparse set of arithmetic features is not thereby a boundary quantum theory, and its plot is not thereby a gravitational bulk.

ACSC may use these connections as prompts for future mathematics. A viable proposal would give explicit observables on both sides and a calculable matching statement with controlled limitations. Structural analogy alone neither supplies physical unification nor reduces the empirical gates in Chapter 12.

# Chapter 11 - Ontological and philosophical implications

### 11.1 Arithmetic realism as a philosophical position [S]

The possibility that nature has a mathematical structure motivates ACSC, but it is not established by a plot or by the success of mathematics in physics. Mathematical realism, formalism and computational views of nature offer different interpretations. Tegmark's Mathematical Universe proposal is related philosophical work [R17], not observational confirmation of the present arithmetic construction.

The original image of the cosmos as a symbolic language is retained as metaphor: elliptic curves are the objects, arithmetic relations the syntax, and a proposed interpretation supplies semantics. The semantics are the scientific problem. Identifying rank with matter or the regulator with space merely by naming them would assume the conclusion the project needs to test.

### 11.2 Recursive construction and time [M, S]

A Fibonacci-style recurrence can generate numbers; an additional rule is required to turn them into nonsingular elliptic curves. That rule must handle singular outputs, finite precision, indexing and stopping conditions. Projection order is an index of a computation, not automatically the universe's time coordinate.

**Lemma 11.1 - Deterministic generation from full state [D].** Suppose a transition rule F, full initial state, any required seeds, domain conditions and a deterministic projection are fixed. Wherever the transition remains defined, the sequence of projected outputs is determined.

**Proof sketch.** Induction determines each new state from the preceding state and the fixed rule. Applying the deterministic projection determines each output. This is a statement about the declared algorithm, not about physical causality.

The original lemma asserted that a few invariants of E_n and E_(n-1) determine the next curve's projection. That follows only if the transition actually factors through those invariants. A lossy representation may identify different states with different successors. A correct model must either retain sufficient state or prove the factorization. Deterministic generation also need not make inversion or long-range prediction easy.

### 11.3 Observation and limits of knowledge [S]

“Observation reads an arithmetic state” remains an interpretive proposal. It needs a measurement model before it can make an empirical prediction. It is not equivalent to wavefunction collapse, and a topos construction does not supply a measurement mechanism.

Incompleteness results concern sufficiently expressive, effectively axiomatized formal systems under specified consistency assumptions. They do not immediately prove the impossibility of forecasting a physical ACSC model. Chaitin's halting probability and an elliptic real period are different objects despite both sometimes being denoted Omega. No theorem in this manuscript identifies them. The philosophical possibility of limits to explanation is retained without claiming a new physical consequence of those mathematical results.

### 11.4 Meaning and explanation [S]

ACSC can serve as a disciplined way to ask whether a symbolic representation explains an independently observed structure. Explanation requires more than an evocative vocabulary: it requires nontrivial constraints, predictions, alternatives and results that could contradict the proposed interpretation. A philosophical preference for symbolic ontology cannot rescue a failed empirical instance. A successful narrow instance would likewise not settle whether mathematics is the substance of reality.

# Chapter 12 - Experimental and observational pathways

### 12.1 Separate the gates [M]

The Charter distinguishes a defined construction, reproducible computation, statistical support, cross-dataset support, predictive support and physical interpretation. These are successive evidentiary requirements, not interchangeable descriptions of a release. Source preservation, verified provenance, execution eligibility, controlled support, physical support and web/display permission are separate states.

This rewrite establishes a clearer candidate manuscript. It does not change any canonical registry, authorize a run, publish a dataset, admit a sky overlay or certify an astronomical correspondence. The accompanying local claim worksheet has its own namespace and records the remaining obligations.

### 12.2 Arithmetic and observational lineage [M]

An arithmetic input must identify its publisher, version or commit, exact acquired bytes, hash, row-selection policy, model convention, invariant definitions and confidence or proof status. A conditional BSD-derived quantity must be marked conditional rather than allowed to make an empirical map depend on an unproved general theorem. Exact invariant reconstruction and a tested numerical implementation are distinct checks.

An astronomical input must identify its release, table, publisher response, schema and units; acquisition method and integrity; completeness, masks and quality selections; coordinate semantics; redshift/cosmology assumptions; duplicate and multiplicity treatment; measurement uncertainties; and every transformation into derived data. The separately hashed display product is not a substitute for the untouched source. A successful LFS retrieval proves byte delivery, not scientific admissibility.

The user's identification of the renamed SDSS sample as a CasJobs export of MyTable_pmqr771_0.csv is a useful lineage lead. Establishing the dataset's canonical source still requires the SQL, job or export metadata, relevant file metadata and a verified byte relationship. A filename or asserted origin alone does not make a missing provenance record verified. This rewrite does not perform that separate dataset-promotion audit.

DATA-PROVENANCE-ALL, DATA-PHYS-CONSTRAINTS and DATA-ECC-THEORY are reserved placeholders in the described registries, not ready scientific inputs. They need defined objects, schema or mathematical definitions, source or derivation, integrity evidence and complete provenance before controlled use. A general phrase such as “physical constraints” cannot serve as the input object for a calculation.

### 12.3 Freeze a falsifiable comparison [H, T]

Before confirmation, register the eligible cohort; map and fixed constants; observation and window; coordinate/metric conventions; filtration, coefficient field, scale range and essential-interval policy; primary statistic; meaningful effect threshold and error budget; null models; seeds; sample-size or power analysis; multiplicity correction; exclusions; sensitivity analyses; and holdout/replication policy. Freeze data, code, parameters and environment identifiers together.

A pointwise comparison requires a scientifically justified matching rule or joint object definition. Arbitrarily assigning a curve to each galaxy supplies no independent correspondence. A distributional or topology comparison can avoid pointwise matching, but then must make its sampling, density, units and invariances explicit. Searching freely over rotations, rescalings, curve subsets and survey regions against the target is fitting; any selected transformation needs discovery-only selection and independent confirmation.

The relevant historical prediction is reformulated as a prospectively specified improvement over alternatives. A candidate diagram discrepancy might aggregate selected homology degrees with fixed weights. Its exact formula, normalization and effect-size meaning must be frozen rather than inferred from a visually good comparison. No new acceptance threshold is imposed by this manuscript.

### 12.4 Arithmetic and cosmological nulls [M]

The arithmetic null must address what structured arithmetic covariates and the map alone can create. A conditional randomization design should preserve the dependence relevant to the registered question. Isogeny relationships, conductor selection and rank-covariate structure cannot simply be destroyed when they are plausible explanations of the statistic.

The cosmological null must address clustering and observational selection, using suitable released mocks or another justified, validated generative design. A mask-only Poisson process is not a definitive null for a clustered survey. A valid comparison includes tracer selection, geometry, redshift distribution, completeness, boundaries and relevant measurement effects. A composed joint null may be an additional diagnostic; it does not replace either component test.

**Lemma 12.1 - Requiring both component rejections [D].** Let H_A and H_C be the arithmetic and cosmological nulls, and p_A, p_C valid p-values for their respective nulls. For the null H_A union H_C, the rule p_J = max(p_A,p_C) <= alpha controls type-I error at most alpha for a single registered test.

**Proof sketch.** If H_A is true, the rejection event is contained in the event p_A <= alpha, whose probability is at most alpha. The same argument holds when H_C is true. No independence assumption between the two p-values is needed. Multiple candidate maps or endpoints still need their own declared multiplicity treatment.

For a smaller-is-more-extreme discrepancy, an exchangeable Monte Carlo test uses

$$
p=\frac{1+\#\{b:\delta_b\leq\delta_{\mathrm{obs}}\}}{B+1}.
$$

The inequality must be reversed for a larger-is-more-extreme score. Exchangeability and the null generator's validity are requirements, not consequences of this formula. Outcome-informed selection must be accounted for in the randomization design or separated from confirmation. A01's registered greater-or-equal tail for its arithmetic coherence score is therefore not altered to this discrepancy tail [G3].

### 12.5 Outcome interpretation and falsification [M]

A small raw distance can be ordinary under a null. A statistically unusual value can be too small an effect to matter. A noisy or underpowered result can be inconclusive. Report effect sizes, uncertainty, validity diagnostics and both null assessments; do not collapse them into a binary “ACSC confirmed” message.

Failure to reject a null does not by itself prove the absence of correspondence. A registered operational hypothesis can fail a meaningful-effect or equivalence criterion when the study has adequate sensitivity and a prospectively specified decision rule. Preserve the failed instance, its data and its scope. Testing a revised map requires a new version and fresh confirmation; it must not erase the earlier result.

A positive arithmetic-only result supports, at most, the registered arithmetic statistic. Independent survey replication is required before replicated physical support, and a causal or dynamical interpretation requires an independently justified mechanism. A successful observation cannot retroactively prove the unsupported topology, spectral or closure lemmas in the original.

### 12.6 Quarantine, replication and publication [M]

The inspected SDSS/HI match failures, manifest disagreements and synthetic torus runs identified by the provenance audit cannot provide controlled astronomical evidence. Quarantine preserves the objects and history; it does not delete inconvenient outcomes. Synthetic fixtures remain useful for testing software when labeled correctly. Rebuilding a spherical cross-match requires keyed inputs, true angular separation, duplicate control, tolerance sensitivity and locked input/code hashes before reevaluation.

Replication requires sufficient acquisition and processing information for another researcher to reproduce the result, with numerical tolerances and an independent environment or implementation. Public availability of the package and authenticated independent review are distinct requirements. Source-publication approval, passing CI and display authorization must not be read as scientific validation. CI should fail closed for absent hashes, malformed schemas, unsupported eligibility or unreviewed display releases.

### 12.7 A bounded experimental route [M]

1. Reconcile each proposed claim to the Charter and a concrete input object; preserve the historical claim.
2. Validate source lineage and invariants; resolve quarantine and placeholder blockers without inventing missing evidence.
3. Freeze one narrow operational comparison and its two null models on discovery-only material.
4. Obtain the required protocol and execution review; run the locked workflow and preserve all outcomes.
5. Check effect size, uncertainty, leakage, null validity and alternatives without changing the endpoint.
6. Seek independent survey replication and off-author verification before a broader claim or physical interpretation.

These steps are a research design, not evidence that ACSC has traversed them. SDSS, other survey releases and simulations named in the original are possible source families; no unnamed survey dataset or future instrument is automatically an eligible input.

# Chapter 13 - A framework for future fundamental theory

### 13.1 From arithmetic scores to physical dynamics [S]

The original proposal to begin with arithmetic and seek a physical interpretation is retained. It cannot reverse the requirement that the interpretation answer to observation. A valid model needs state variables, a transition or action, units, symmetries, admissible domains, independently constrained parameters and recovery limits. Naming a gradient “force” does not derive Newtonian gravity or general relativity.

The smooth extension in Chapter 8 permits a mathematical vector field grad(s_h), or a declared negative gradient. Its sign, metric and dynamics must be specified. It is a force only if a physical model establishes that role. The original force-field lemma is therefore replaced by Lemma 8.1's mathematical smoothness result and this explicit construction obligation.

### 13.2 Energy and conservation [M, S]

The historical score e(E) = h-hat(P_K)/ln N may be defined wherever the selected Heegner construction exists and the denominator is nonzero. It is not automatically an energy density. A finite sum over a fixed isogeny class is a number for that class; its being a fixed sum is not a dynamical conservation law. Under a changing sample or transition, constancy needs a proved property of the transition or a justified symmetry of a defined action.

Neither Heegner height nor a regulator transformation gives conservation of total information, matter or physical energy. Such a conservation statement remains a postulate or a theorem to prove in a separately defined dynamics.

### 13.3 Log-regulator and entropy [D, M]

For a positive regulator, S_reg(E) = ln Reg(E) is a log-determinant statistic. It can be negative and is zero for rank zero under the empty-determinant convention. It is not Shannon entropy merely because it uses a logarithm. Shannon entropy requires a specified probability distribution:

$$
H(p)=-\sum_i p_i\ln p_i,\qquad p_i\geq0,\quad\sum_i p_i=1.
$$

A probability model on curves, transitions or measurements could support an information-theoretic quantity, but its distribution, sampling and interpretation would have to be declared. Height lattices of differing rank also do not give comparable physical entropies just by taking their determinants. The original information-mass, information-spread and conserved-state identifications remain speculative.

### 13.4 A second law needs a directed dynamics [D, P]

An arbitrary isogeny does not make Reg or its logarithm increase. The regulator law in Chapter 3 depends on degree, rank and the free-lattice index. Dual isogenies also run in the opposite direction.

**Lemma 13.1 - Reversible edges cannot give a strict universal arrow [D].** If a function S is nondecreasing along every directed edge of a graph that contains both E to E' and E' to E, then S(E) = S(E') on that pair.

**Proof sketch.** The two inequalities give S(E) <= S(E') <= S(E). Along any connected reversible isogeny component, repeating this argument makes S constant. A nonconstant strict second-law statistic therefore needs restricted, directed transitions rather than all isogenies.

One may impose an allowed transition rule for which a declared S is a Lyapunov function. That is a model postulate or a transition-specific theorem, not thermodynamics derived from BSD. Exponential rank growth, accelerated expansion and black-hole behavior likewise need their own definitions and evidence.

### 13.5 Relation to the entropy-cohomology proposal [D, S]

The related historical ECC-2025 construction cannot supply a nontrivial de Rham class from theta = dM and omega = dtheta: exterior differentiation gives d^2M = 0. Preserve that failure; it is not repaired by an ACSC coordinate change.

For a new, separately defined construction, a closed target two-form omega and a smooth map phi give F = phi^*omega with dF = phi^*(domega) = 0. Even when omega has nontrivial cohomology, its pullback may be zero in cohomology. Nontriviality of the pullback therefore requires a separate proof. A bundle-curvature successor needs compatible local connections, a global curvature form and its actual class, rather than a globally exact one-form. None of these mathematical conditions supplies an entropy or cosmological mechanism by itself [G1, G3].

### 13.6 Dark sectors and quantum gravity [S]

The score d(E) = ln(1+t) may describe torsion order in a representation. It is not a measured dark mass. Rank sequences may change the scale of a synthetic plot, but they are not an expansion history until redshift, distance, clock and dynamics are independently defined. A discrete arithmetic origin of a sampled space does not by itself produce background independence, quantum uncertainty or a viable theory of gravity.

These ideas remain possible research prompts. They should be pursued as separately versioned physical models after mathematical consistency and narrow empirical tests, with clear abandonment criteria. Speculation must not relax the existing P0/M1 review requirements or turn a class-specific result into a universal claim.

# Chapter 14 - Scientific evaluation and mathematical cosmology

### 14.1 A candidate program, not an established paradigm [S]

The original aspiration to connect number theory, topology, cosmology and computation is retained. The assertion that ACSC already resolves cosmic structure, dark matter, dark energy, entropy and time is withdrawn. No controlled result in the consulted claim registry establishes those achievements. Historical resonance with mathematical philosophy is motivation, not evidence.

The “Paradigm Connectivity Lemma” was not a mathematical lemma: its sociological premises were neither formalized nor shown to hold. It is replaced by the question of whether the program earns explanatory and predictive value under independent scrutiny. Calling a manuscript unified or exact does not answer that question.

### 14.2 How a contribution would be assessed [H, M]

A useful result would identify an actual problem, a limited hypothesis and a reproducible improvement over relevant baselines. It would state the cost of extra flexibility, its domain of validity, the uncertainty and the observations that contradict it. It would survive an independent implementation and independent data before being described as a physical contribution.

Negative results can be equally valuable: a failed mapping family, a demonstrated leakage mechanism, an invalid geometric premise or a quarantined match prevents unsupported conclusions. Those results should remain citable and machine readable. Mathematical elegance does not outweigh failed controls.

### 14.3 Tools, education and future applications [S]

Potential tools include arithmetic dataset viewers, reproducible topology benchmarks, symbolic-regression comparisons and teaching material connecting distinct mathematical domains. Their value can be assessed separately from ACSC's physical truth. A visualization or automated theorist should show provenance, uncertainty and status instead of presenting a conjecture as observed reality.

The original forecasts of new telescopes, cryptographic cosmology and a transformation within two decades remain aspirations without a demonstrated mechanism or timeline. No speculative object-count forecast for future surveys is needed to evaluate the present hypothesis. Larger data do not repair a biased selection or an ill-defined comparison. Educational use should explain the difference between theorem, model and empirical claim, rather than replace observation with symbolism by decree.

### 14.4 Scientific culture [M]

Collaboration among arithmetic geometers, topologists, statisticians and cosmologists is valuable because each can expose a different failure mode. Independent review must be able to reject a proposed bridge without rejecting the established tools on either side. A transparent, falsifiable program can contribute even if its original universal vision is not sustained.

# Chapter 15 - Open questions and formalization

### 15.1 Mathematical questions [C]

Open questions include whether an independently motivated map has useful invariance; which curve-level information is lost; how sample selection and isogeny representation affect summaries; whether a limiting object exists under a specified arithmetic sampling rule; and whether a proposed categorical construction has nontrivial content. A large finite database does not prove universality over astronomical topology.

Extending to higher-genus curves, abelian varieties or modular surfaces changes the input objects, invariants and computational obligations. Such extensions need new definitions and tests rather than being assumed to cover failures of the elliptic model. Heegner constructions need their arithmetic hypotheses; they are not uniformly available for every curve and imaginary quadratic field. The basic feature-map program can use proved invariants without assuming the full BSD conjecture.

### 15.2 Optional physical postulates [P, S]

The original four proposed physics axioms are retained only as optional physical postulates, distinct from Chapter 2's mathematical model axioms:

- **P1 - Structural sufficiency.** A specified arithmetic state and map suffice for a named physical structural observable within a declared domain.
- **P2 - Clock interpretation.** A specified directed arithmetic evolution defines a calibrated physical time variable.
- **P3 - Coupling interpretation.** Specified functions of arithmetic invariants couple to physically defined fields with consistent units and recovery limits.
- **P4 - Transformation interpretation.** Specified categorical transformations represent particular physical evolutions or symmetries.

Adopting these postulates permits conditional derivations inside a model. It does not establish their truth. Each needs independent predictions and could fail separately. None licenses identifying all matter with rank, all dark matter with torsion or all dynamics with isogeny. Their broad existential form must be narrowed before an empirical test can be preregistered.

### 15.3 A valid closure statement [D]

**Lemma 15.1 - Well-defined finite recursive image.** Let a declared transition rule keep every state in a domain of nonsingular curves with all required features defined. If the initial state and projection are fixed, every finite initial segment has a well-defined projection image.

**Proof sketch.** Induction gives a valid state at each step under the domain-preservation assumption. Evaluating the defined features and projection gives the corresponding finite image. The result does not prove density, representation of every observed homology signature, convergence to a cosmic manifold or monotonic entropy.

This replaces the original universal “Symbolic Closure” lemma. Universal topology coverage would require a separate approximation or representation theorem with an explicit target class. Entropy monotonicity would require the directed dynamics discussed in Chapter 13. Neither follows from finite recursive definability.

### 15.4 Empirical priorities [M]

The highest-value route is narrow: source integrity; a versioned, independently motivated representation; leakage-free arithmetic diagnostics; a concrete astronomical target; registered conditional arithmetic and cosmological nulls; controlled execution; and independent confirmation. Curvature or lensing comparisons require physically justified fields and selection controls before they become the next endpoint. Symbolic regression remains a discovery tool until a selected equation predicts an independent target.

Persistent-homology libraries, larger surveys and improved computing are useful only when their schemas, approximations and limitations are explicit. Prime-based, p-adic, ultrametric, black-hole and information-thermodynamic extensions remain speculative research directions. They are not alternative evidence when the original operational test fails.

### 15.5 The conjecture left open [C]

ACSC now asks a constrained question: can a frozen arithmetic representation explain or predict a specified astronomical structural observable beyond appropriate alternatives, with a meaningful effect and independent replication? Its current mathematics defines some representations and their conditional properties. Its current evidence does not establish the proposed cosmic correspondence. The next advance can be a positive result, a negative result or a proof that a proposed bridge is impossible within its stated class. All three preserve the integrity of the research program.

# Appendix A - Original-to-revision reconciliation

The original is preserved as the historical source. Page numbers below refer to that PDF's page order. The separate correction ledger contains these entries in a machine-readable form. Changes concern unsupported conclusions, mathematical corrections and the definitions needed to make those corrections explicit; related subject matter remains in its original chapter sequence.

| Original topic or assertion | Original pages | Revision disposition |
| --- | --- | --- |
| Cosmic isomorphism, reconstruction and validated correspondence | 1-19, 57-58 | Open conjecture and bounded operational hypotheses; Prologue, Chapters 2, 5, 12 |
| All inputs called BSD-valid | 7-19, 44-58 | Proved input invariants separated from conditional BSD quantities; Chapters 1-2, 5 |
| Four coordinates presented as a map into R^3 | 13-18, 44-51 | Three coordinates plus attribute, or explicit four-dimensional model; Chapter 2 |
| Latitude/colatitude, angle units and duplicate Cartesian coordinate | 13-18, 44-51 | Correct spherical conventions and Cartesian equations; Chapter 2 |
| Undefined global logarithmic Lipschitz assertion | 17-18 | Fixed feature pseudometric and explicit affine-map bound; Lemma 2.1 |
| Discriminant-and-conductor cutoff called isogeny closed | 18, 25-26 | Conductor saturation; discriminant counterexample; Chapter 3 |
| Conductors can double or halve under rational isogeny | 26 | Conductor is invariant; proof sketch in Chapter 3 |
| Discriminant change-of-model scaling | 25 | State substitution direction; delta' = u^-12 delta; Chapter 3 |
| Regulator approximately invariant under isogeny | 27-28 | Exact degree/rank/free-index relation; Chapter 3 |
| Height-matrix eigenvalues treated as curve invariants | 28-29 | Basis congruence; determinant invariant under unimodular change, eigenvalues need not be |
| Moduli, rational curves and isogeny-volcano interpretations | 21-24, 29-31 | Distinct moduli and graph contexts; Chapter 3 |
| Finite clouds, loops/filaments and universal Betti hierarchies | 32-43, 100 | Filtered-complex and interpretation distinctions; Chapter 4 |
| Two-dimensional complex claimed sufficient for H_2 | 19, 37-43 | Three-simplices required for H_2 deaths; Chapter 4 |
| Diagram distance definition, scaling and fixed 0.01 threshold | 15-19, 41-43, 54-55, 100 | Complete conventions, scale lemma and independent calibration; Chapters 4-5, 12 |
| Nyquist and topological embedding lemmas | 18-19, 43-44 | Conditional reach/density/Cech theorem; no arithmetic-cosmic density proof |
| Gromov-Hausdorff and empirical convergence claims | 19, 56-58 | Conditional Hausdorff-density implication; empirical convergence withdrawn |
| 15,000 curves, clusters and physical density | 44-54 | Historical numerical reports retained without evidence promotion; Chapter 5 |
| Betti values, match percentages and W_2 values | 54-55 | Literal values retained; undefined percentages and threshold contradiction explicit |
| First full empirical validation and universal predictions | 57-58 | Withdrawn as established conclusions; Chapters 5, 12 |
| Symbolic-regression scores and discovered laws | 58-64 | Historical unverified candidate expressions, baselines and leakage controls; Chapter 6 |
| Square-root inconsistency and log as binary operator | 62-64 | Inconsistency retained; no preferred missing artifact invented; unary operator correction |
| Per-curve Betti contribution | 62, 100-101 | Undefined target replaced by a construction obligation, not an additive homology claim |
| Unique symbolic gravity | 63 | Named score without uniqueness, units or physical interpretation; Chapters 6, 8 |
| Phi called a functor and Heegner natural transformation | 64-69 | Categories, morphisms and commutative-square obligations; Chapter 7 |
| Invariant preservation implies homotopy equivalence | 69-70 | Removed as theorem; Rips functoriality under nonexpanding maps instead |
| Arithmetic topos guarantees complete physics | 69-70 | Presheaf construction separated from interpretation and completeness |
| Regulator derivative equals Ricci curvature; rank-curvature lemma | 71-76 | Defined smooth scalar extension; metric and physical derivation absent; Chapter 8 |
| Rank expansion, cosmic clock and modular degeneration | 73-76, 92-96, 107 | Conditional family/dynamics questions, not consequences of BSD |
| Repeated g_2 in j denominator | 74 | Correct g_3^2 denominator; Chapter 8 |
| Feature array identified as stress-energy tensor | 72-76 | Tensor, covariance, units and dynamics obligations; Chapter 8 |
| Modularity as unrestricted invariance; Eisenstein zeros | 77-79 | Weight-two level-specific covariance and corrected zeros; Chapter 9 |
| Sato-Tate distribution and primes as quantum foam | 75, 80-82 | Correct sine-squared density, good-prime/non-CM domain and separate speculative analogy |
| Finite-field point groups assumed cyclic | 75 | Abelian need not be cyclic; explicit F_3 counterexample; Chapter 9 |
| Heegner heights identified as probabilities | 79-80 | Conditional arithmetic relation distinguished from quantum measurement |
| Hermitian spectrum from L-function zeros | 82 | Unproved spectral proposal; operator and RH obligations; Chapter 9 |
| Torsion gauge charge and isogeny entanglement | 80-83 | Arithmetic facts distinguished from physical structures |
| String, Langlands, mirror and holographic identifications | 83-89 | Related work and explicit missing constructions; Chapter 10 |
| Motivic projection fiber-functor existence lemma | 89 | Construction problem 10.1; no existence proof |
| Invariants determine recursive successors | 95-96 | Full-state deterministic generation lemma; Chapter 11 |
| Gödel and Chaitin used as physical prediction limits | 94 | Scope and distinct Omega objects; Chapter 11 |
| Confirmation at W_2 < 0.01 and “reject or refine” code | 100-103 | Registered effects, nulls, uncertainty and versioned failures; Chapter 12 |
| Conservation and log-regulator as Shannon entropy | 105-106 | Scores vs dynamics; actual probability entropy definition; Chapter 13 |
| Universal symbolic second law | 106 | Reversible-edge obstruction and directed-transition obligation |
| Gradient-of-regulator force-field lemma | 108 | Mathematical smoothness only; force interpretation remains speculative |
| Resolved anomalies, superior predictions and paradigm lemma | 110-115 | Research aspirations and independent assessment criteria; Chapter 14 |
| Universal symbolic closure and entropy increase | 120-121 | Conditional finite-image lemma; universality and monotonicity not proved |
| Final identity of symbol and reality | 121 | Philosophical possibility, not a scientific conclusion; Chapters 11, 15 |

# Appendix B - Mathematical checks and proof obligations

### B.1 Independently checkable elementary corrections [D]

The local check record accompanies this manuscript. It evaluates elementary identities and small counterexamples, not an ACSC experiment. The checks include exact discriminants for the two conductor-11 curves, change-of-model scaling, regulator Gram-matrix transformations, basis-dependent eigenvalues, the geometry of the corrected spherical map, log domains and rank-zero convention, a small Rips/Cech distinction, and diagram-distance scaling. A passing check supplies evidence for that calculation alone; the general lemmas remain supported by their stated arguments and assumptions.

The conductor-11 example uses the labels and coefficient vectors in the pinned ecdata source. Exact algebra independently gives the stated discriminants. Its isogeny classification and conductor are source assertions from the established catalog, not computed by the small local script. Likewise, a toy lattice verifies an identity's algebra but does not certify a recovered elliptic curve's Mordell-Weil basis.

### B.2 Open obligations [C, H, S]

- Prove an independently motivated target approximation property if claiming cosmic reconstruction; BSD alone supplies none.
- Define every proposed arithmetic-to-filtered-space morphism and prove functoriality or a controlled scale change.
- Supply a full operator construction for any L-zero spectral claim.
- Define a covariant physical dynamics, units, recovery limits and observational coupling for any gravitational or dark-sector interpretation.
- Freeze concrete inputs, controls, uncertainty and meaningful effects for each operational hypothesis.
- Establish independent observational support and replication before extending an arithmetic diagnostic into a physical claim.

The revised manuscript does not purport to have discharged these obligations. Independent specialist review is still required for the proposed construction and proof sketches, especially before any project gate uses them.

# Appendix C - Claim and evidence worksheet

### C.1 Local namespace and eligibility

These IDs belong only to this manuscript's worksheet: ACSC-LOCAL-2026-10-11. They are not aliases for repository CLAIM-ACSC-* or experiment IDs. A relationship is a topic-level reference, not ID equality, promotion or an update to the canonical registry. Mathematical checks below are not controlled or physical support for ACSC.

| Local suffix | Statement | Category | Present status and next obligation |
| --- | --- | --- | --- |
| C0 | A bounded arithmetic representation may correspond to astronomical structure | C | Open; narrow operational instance and independent controls required |
| D1 | Fixed affine feature map has the stated Lipschitz bound | D | Proof sketch; verify domain and chosen matrix for each implementation |
| D2 | Rational-isogenous curves have equal rank and conductor | D | Established arithmetic; supplied argument and catalog example |
| D3 | Regulator transforms with degree, rank and free-lattice index | D | Conditional on full bases and height convention; not general equality |
| D4 | Persistence stability and reconstruction hold under their explicit hypotheses | D | Existing conditional theorems; cosmic closeness not established |
| H1 | A locked mapping beats both registered null components by a meaningful effect | H, T | Untested here; dataset, protocol and execution review required |
| M1 | Symbolic regression yields useful held-out arithmetic candidates | M, H | Historical scores unverified; split, baseline and leakage audit required |
| M2 | A categorical construction preserves declared information | M, C | Morphisms and preservation statement remain to be constructed |
| S1 | Arithmetic structures produce physical gravity, time or dark sectors | S | No established dynamics, mechanism or physical evidence |
| S2 | Modular, spectral or motivic structures explain quantum behavior | S, C | Missing physical state/operator construction and test |
| P1-P4 | Optional physical interpretation postulates | P, S | Adopted only conditionally; no empirical promotion |

The machine-readable worksheet sets manuscript-level controlled_support_eligible and physical_support_eligible to false for all entries. This conservative setting does not deny the established mathematical theorems; it prevents their being used as empirical ACSC support. Scientific lineage and proof lineage are different records.

### C.2 Repository relationships

Repository CLAIM-ACSC-001 concerns formal definition and mapping; CLAIM-ACSC-002 concerns separation from dependence on the full BSD conjecture; CLAIM-ACSC-003 concerns astronomical topology. This manuscript addresses those topics without changing their registry status. EXP-MAP-A01 and EXP-MAP-A03 retain their own frozen protocols and inferential directions. P0-ANSATZ-001 and M1-INH-E1 retain their independent physical-model review gates [G3].

# References - Authority, mathematical tools and related work

Primary references below establish background tools, provide related proposals or identify consulted source records. No listed paper is represented as independent empirical confirmation of ACSC. Online sources were checked on 11 October 2026. A publisher access failure for R22 was addressed by inspecting a hosted copy of the original paper; no inaccessible full text is claimed to have been read.

**[G1] S.T.A.R. Research Charter v0.2.** Governing PDF, 37 pages. Local bytes and Git blob identity verified against the consulted repository. Source: https://github.com/LcosmosS/S.T.A.R.-Labs/blob/046d90e5cdb4d575ea27c305535c91d0ff3aa6ec/charter/STAR_Research_Charter_v0-2.pdf . Relevant authority includes its claim taxonomy, mapping conventions, nulls, leakage controls, historical-claim reclassification and evidence ladder.

**[G2] Patrick J. McNamara. The Arithmetic-Cosmic Structure Conjecture (ACSC) Monograph.** Original May 2025 manuscript, 121 pages, supplied local PDF; source SHA-256 is recorded in the front matter and revision manifest. Historical manuscript, not an independently validated source of ACSC conclusions.

**[G3] S.T.A.R.-Labs repository snapshot.** Main commit 046d90e5cdb4d575ea27c305535c91d0ff3aa6ec; README, registry/claim_evidence_v0.2.csv, EXP-MAP-A01 and EXP-MAP-A03 protocols, P0-ANSATZ-001 protocol, and P0/M1 independent-review records. https://github.com/LcosmosS/S.T.A.R.-Labs/tree/046d90e5cdb4d575ea27c305535c91d0ff3aa6ec . Protocol/source records, not independent physical evidence.

**[R1] Joseph H. Silverman (2009). The Arithmetic of Elliptic Curves, second edition.** Graduate Texts in Mathematics 106, Springer. Arithmetic reference for minimal models, heights and isogenies. https://doi.org/10.1007/978-0-387-09494-6

**[R2] J. S. Milne (2021). Elliptic Curves, second edition.** World Scientific; author-hosted text. Arithmetic background and BSD formulation. The consulted PDF's bibliographic page gives 2021. https://www.jmilne.org/math/Books/EC2.pdf

**[R3] Christophe Breuil, Brian Conrad, Fred Diamond and Richard Taylor (2001). On the modularity of elliptic curves over Q: wild 3-adic exercises.** Journal of the American Mathematical Society 14, 843-939. Modularity theorem, not BSD or ACSC. Author-hosted paper: https://virtualmath1.stanford.edu/~conrad/papers/tswfinal.pdf

**[R4] David Cohen-Steiner, Herbert Edelsbrunner and John Harer (2007). Stability of Persistence Diagrams.** Discrete & Computational Geometry 37, 103-120. Conditional bottleneck stability. https://doi.org/10.1007/s00454-006-1276-5

**[R5] Frederic Chazal, Vin de Silva, Marc Glisse and Steve Oudot (2012 preprint). The structure and stability of persistence modules.** Algebraic stability framework. https://arxiv.org/abs/1207.3674

**[R6] Primoz Skraba and Katharine Turner (2020 preprint; consulted revision 7, 2025). Wasserstein Stability for Persistence Diagrams.** Wasserstein results require their own finiteness and perturbation assumptions; the manuscript does not replace them with an unconditional bottleneck assertion. https://arxiv.org/abs/2006.16824v7

**[R7] Pratyush Pranav et al. (2017). The topology of the cosmic web in terms of persistent Betti numbers.** Monthly Notices of the Royal Astronomical Society. Cosmic-web topology methodology. https://arxiv.org/abs/1608.04519 ; https://doi.org/10.1093/mnras/stw2862

**[R8] G. Wilding et al. (2021). Persistent homology of the cosmic web. I. Hierarchical topology in Lambda-CDM cosmologies.** Monthly Notices of the Royal Astronomical Society. Cosmic topology and hierarchical structure in a specified cosmological setting. https://arxiv.org/abs/2011.12851 ; https://doi.org/10.1093/mnras/stab2326

**[R9] Thierry Sousbie (2011). The persistent cosmic web and its filamentary structure. I. Theory and implementation.** Monthly Notices of the Royal Astronomical Society. Persistence-based cosmic-web extraction, distinct from equating beta_1 with filament number. https://arxiv.org/abs/1009.4015

**[R10] Brittany Terese Fasy, Fabrizio Lecci, Alessandro Rinaldo, Larry Wasserman, Sivaraman Balakrishnan and Aarti Singh (2014). Confidence sets for persistence diagrams.** Annals of Statistics 42(6), 2301-2339. Statistical uncertainty, under the paper's sampling assumptions. https://arxiv.org/abs/1303.7117 ; https://doi.org/10.1214/14-AOS1252

**[R11] Partha Niyogi, Stephen Smale and Shmuel Weinberger (2008). Finding the homology of submanifolds with high confidence from random samples.** Discrete & Computational Geometry 39, 419-441. Consulted noiseless reach/density reconstruction statement, especially Proposition 3.1. https://math.uchicago.edu/~shmuel/NSW1.pdf ; https://doi.org/10.1007/s00454-006-1250-7

**[R12] Benedict H. Gross and Don B. Zagier (1986). Heegner points and derivatives of L-series.** Inventiones Mathematicae 84, 225-320. Arithmetic height/derivative relation with specified hypotheses; not a quantum probability law. https://doi.org/10.1007/BF01388809

**[R13] Thomas Barnet-Lamb, Toby Gee and David Geraghty (2009 preprint, revised 2010). The Sato-Tate conjecture for Hilbert modular forms.** Primary source for the relevant non-CM equidistribution setting. https://arxiv.org/abs/0912.1054

**[R14] Barry Mazur (1978). Rational isogenies of prime degree.** Inventiones Mathematicae 44, 129-162; includes the rational torsion classification statement. Primary paper copy: https://www.math.columbia.edu/~goldfeld/Mazur-Goldfeld1978.pdf ; https://doi.org/10.1007/BF01390348

**[R15] Anton Kapustin and Edward Witten (2006). Electric-Magnetic Duality and the Geometric Langlands Program.** Related mathematical-physics framework; not an ACSC construction. https://arxiv.org/abs/hep-th/0604151

**[R16] Juan Maldacena (1997 preprint). The Large N Limit of Superconformal Field Theories and Supergravity.** Related gauge/gravity proposal in specific theories and limits. https://arxiv.org/abs/hep-th/9711200

**[R17] Max Tegmark (2008). The Mathematical Universe.** Foundations of Physics 38, 101-150. Related philosophical proposal. https://arxiv.org/abs/0704.0646v2 ; https://doi.org/10.1007/s10701-007-9186-9

**[R18] J. S. Milne (2017). Modular Functions and Modular Forms, version 1.31.** Author's course notes; modular transformation conventions and Eisenstein zeros, especially Example 4.15. https://www.jmilne.org/math/CourseNotes/MF.pdf

**[R19] The L-functions and Modular Forms Database. Elliptic curve 11.a3.** Catalog record for the small-discriminant conductor-11 example; consulted alongside ecdata, rather than treating labels as a new proof of classification. https://www.lmfdb.org/EllipticCurve/Q/11/a/3

**[R20] John Cremona. ecdata.** Pinned source commit 25cec5ecfec8b9f016eb1631ac633194c2bed39f, allcurves/allcurves.00000-09999; catalog labels and coefficient vectors used in the elementary counterexample. https://github.com/JohnCremona/ecdata/blob/25cec5ecfec8b9f016eb1631ac633194c2bed39f/allcurves/allcurves.00000-09999

**[R21] Miles Cranmer (2023). Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl.** Symbolic-regression tooling and methodology. https://arxiv.org/abs/2305.01582

**[R22] Michael Schmidt and Hod Lipson (2009). Distilling Free-Form Natural Laws from Experimental Data.** Science 324, 81-85. Related experimental equation discovery, not evidence for the historical ACSC fits. https://doi.org/10.1126/science.1165893 . Publisher access failed during this revision; inspected original-paper copy: https://scispace.com/pdf/distilling-free-form-natural-laws-from-experimental-data-7wp48fiem8.pdf
