# ECC-B01 non-claim and governance gates

**As of 2026-10-17**, reviewed #103 head `c33916a35009674ab5abd5e74c717cc0289b1cbd` and #108 head `79296815837985d25f4f1a732d89811814cac4ad`. This is an evidence-packaging checkpoint, not approval of a mathematical foundation or controlled experiment. Recheck changed heads before any signoff. [Evidence index](submissions/investigator_b/README.md) · [integrity receipt](verification/2026-10-17_cross_pr_integrity.json).

## Packaging checks completed at the reviewed heads

- [x] Both PRs observed open, draft and unmerged.
- [x] Separate A/control and B independent-submission ownership identified; #108 submitted by `LibertySquared`, attestation names Shaughn McNamara.
- [x] Current #108 package inventory: 26/26 referenced files matched SHA-256/bytes and Git blob hashes.
- [x] Two retrospective run inventories: 10/10 references matched, including repeated historical-context references.
- [x] Historical manifest: 14/14 entries matched the preserved #103 original timestamped directory; recovered-result path remapping in #108 is explicit.
- [x] All 22 imported evidence files mapped: 13 identical #108 counterparts, nine changed versions retained by immutable #103 history links.
- [x] Investigator A source/result SHA-256 values match the preliminary-submission README: source `68108885ff5349f53d4b692a6d3b1937cae7924e0c7954584794b5bd70b031f2`; result `e5ac9a776caafd527c90508b9d164e372fad8ffde0ba59189dbb320ea5a06673`.

The #103 current-tree cleanup is an ordinary child commit of the reviewed #103 head. The cleanup must preserve the original source/results, protocol, registry/support files, and all prior commits. A checked packaging item does not close any scientific or execution gate below.

## Unmet gates — keep both PRs draft/unmerged

- [ ] **A assertion correction:** fix C-03's unconditional `True` in a separately versioned source/run, add a negative case demonstrating failure for a wrong residual, retain original source and preliminary report. The existing 15/15 report remains a smoke test.
- [ ] **Gauge consistency:** independently exercise smooth gauge transformation on overlapping connection patches and document gluing/transition consistency. Integer-normalized flux alone does not close this gate. #108 explicitly lists it as unmet in [claim_boundary.md](https://github.com/LcosmosS/S.T.A.R.-Labs/blob/79296815837985d25f4f1a732d89811814cac4ad/ECC_B01_Full_Independent_Reproduction/claim_boundary.md).
- [ ] **Revised B execution:** execute the revised source and expanded unit suite in a recorded environment using a new output directory; preserve exact commands, exit codes, logs, package versions, source digest, `run_receipt.json`, all hashed outputs and a new dated package manifest. Independently verify receipt hashes. The preserved eight-test log and 92-check outputs belong to the historical source, not this revised implementation.
- [ ] **Gmsh runtime/auto semantics:** review and document runtime-failure behavior. At the reviewed head, `auto` selects Gmsh after import succeeds; initialization/meshing exceptions record `MESH_* FAIL` without switching to fallback. Treat this as fail-closed behavior unless B explicitly implements and tests an honestly labelled fallback. Do not infer that `auto` guarantees recovery from runtime failures. Any B change belongs to B's own follow-up.
- [ ] **Receipt retention wording:** B's protocol describes receipt creation, but the literal Required artifact retention list omits the filename `run_receipt.json`. B should add it explicitly. Historical retrospective manifests must remain labelled retrospective, not contemporaneous receipts.
- [ ] **Independent toolchain verification:** independently reproduce the required Gmsh/GUDHI path and negative/missing-dependency cases; verify per-shape backend/homology records, required-backend nonzero exits and output-collision/manifest-overwrite refusal. Source inspection and generic CI do not substitute for this execution.
- [ ] **Evidence/attestation freeze:** obtain investigator-approved immutable source/output manifests and explicit scope of each attestation. Record prior access and the order of freezing, consultation and comparison. A typed attestation and matching hashes do not certify identity, creation time or blindness. Public historical exposure remains after cleanup.
- [ ] **Protocol/preregistration:** independently review exact definitions, cochain degree/domain/coefficient group, orientations, exactness criteria, endpoint/null, meshes, environment, positive/negative controls, noise null, resolution stability, tolerances and selection/non-selection rule. Reconcile canonical protocol with PAR-ECC-001/NULL-ECC-001 through separately authorized governance; this packaging commit makes no such changes.
- [ ] **Paired comparison:** freeze an explicit A/B fixture/coverage mapping before adjudication, document discrepancies, exclusions and unequal suite coverage. A's 15 and B's 92 checks are different suites, not a paired success statistic.
- [ ] **Independent theory review:** obtain named reviewer signoffs on proofs, counterexamples, gauge/mesh controls, reproducibility and discrepancy disposition; record an explicit selection or non-selection decision and unresolved limitations.
- [ ] **Final governance review:** revalidate both latest heads, all linked evidence/manifests and gate dispositions. Maintain the draft/unmerged hold until the governing requirements are fulfilled and a separately authorized release decision exists.

## Non-claims and protected state

No computational fixture pass or packaging check establishes empirical physical/cosmological support, an arithmetic correspondence, entropy-created cohomology/topology, a new ECC theorem, or a chosen ECC foundation. Closedness alone does not establish non-exactness; topology of a manifold alone does not establish a nontrivial class for a specified entropy form.

This checkpoint does not activate EXP-ECC-B01, modify registries/PAR/NULL or support/eligibility flags, select a foundational definition, revise dependent ECC theorems, merge either PR, or certify a blinded comparison. [ECC_RTCH_RECOVERY.md](../research/gates/ECC_RTCH_RECOVERY.md) and the [draft comparison proposal](../research/gates/EXP-ECC-B01_FOUNDATION_COMPARISON_PROPOSAL.md) remain governing references. Registry/support status must be adjudicated through its own authorized process, never inferred from this checklist.
