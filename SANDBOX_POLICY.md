# Sandbox policy and epistemic boundaries

## Admission is not validation

We encourage unconventional proposals and attempts to refute assumptions, including **explicitly false propositions used as controls**. The scientific merits of an idea do **not** require independent approval before ordinary sandbox admission. Repo maintainers still retain responsibility for security, rights, moderation, and changes to these safeguards.

The sandbox deliberately has **no scientific promotion authority**. No SBX label, issue, merged PR, CI green check, or readme statement can change an upstream registry, evidence gate, theorem status, or display admission.

## Classify the work accurately

Each **new** experiment in `experiments/SBX-YYYY-NNNN-description/` requires `metadata.json` with a unique immutable ID, one status, `scope: sandbox-only`, and explicit `eligible_for_automatic_promotion: false`. See [the schema](schemas/experiment-metadata.schema.json).

Allowed statuses:
- `speculative`: proposed but not yet tested;
- `intentionally-false-control`: deliberately incorrect construct used to test a method;
- `exploratory`: investigation without confirmatory claims;
- `inconclusive`: tested, with no interpretable conclusion;
- `refuted`: contradicted within the stated domain and test limits;
- `archived`: retained historical record.

**No `verified`, `validated`, `proven`, `peer-reviewed`, or `physical-support` status is assignable here.** A passing numerical test is not a proof; rejecting a selected null does not verify an entire physical correspondence.

## Required distinctions

- State **hypothesis**, **logical consequence**, **test**, **observation**, and **interpretation** separately.
- State what would falsify or undermine the proposal; if not yet known, say so.
- Label synthetic datasets, mock L-functions, generated numerical examples, and deliberately false logic.
- Identify sources, dataset versions, important parameters, code commits, and limitations when relevant.
- Record failures, negative results, and refutations rather than silently deleting them.
- Preserve the original historical archive. Existing root-level and `R&D/` files are not required to retroactively meet the new format.

## Reserved authoritative namespaces

Do not add root-level `controlled_execution/`, `preregistrations/`, `release_packages/`, `verified_evidence/`, or `registry/` as sandbox scientific-status mirrors. Discussion of those subjects is permitted inside experiment notes. An experiment may link to authoritative upstream artifacts, but cannot impersonate them.

## Promotion boundary (one way, never automatic)

To propose an experiment for controlled treatment:
1. Record the **SBX ID**, precise **sandbox commit SHA**, and provenance.
2. Open a **new, separate PR in S.T.A.R.-Labs**; do not merge histories or open cross-repo auto-sync automation.
3. Re-establish, under the **upstream** rules, precise dataset provenance, preregistration when required, null model, inference threshold, independent verification, and claim limits.
4. If upstream accepts the contribution, its upstream-native identifier and status live **only** upstream. Historical SBX metadata remains sandbox-only.

Promotion rejection does not erase the experiment, and sandbox acceptance grants no presumption of upstream acceptance.

## Unsafe and misleading material

No knowingly false factual allegations against actual individuals, privacy-invasive content, fabricated observations passed off as measured, malicious code, or dangerous misinformation. See [MODERATION.md](MODERATION.md) and [SECURITY.md](SECURITY.md).

## Preservation check

The archive inventory binds the pre-policy baseline at
`a48ee3c41d17305530d65616c16c158f04e502d8`. CI checks those bytes and ancestry,
without assigning scientific merit to historical language. New research belongs
under `experiments/`; root governance, CI, schemas and tests are steward-owned.
