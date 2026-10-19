# Sandbox governance

## Two distinct records

**Sandbox:** quick, reversible, speculative, falsifiable R&D. A merge means *admitted to the playground*, not *established truth*.

**Upstream S.T.A.R.-Labs:** separate source of controlled execution, evidence provenance, independent-review obligations, and scientific-status decisions. No automatic sync, claim-status transfer, or bot-assisted promotion.

## Roles

- **Contributor:** suggests hypotheses, reproductions, refutations, and code through issues and PRs.
- **Maintainer:** can merge ordinary sandbox contributions and address metadata issues; that is **not** scientific endorsement.
- **Safety steward / owner:** handles security, rights, and moderation concerns; approves changes to the sandbox's epistemic boundary and public deployment surfaces.
- **Upstream reviewer:** follows upstream's independent governance, not sandbox permissions.

## Practical review policy

Target for ordinary experiments: **0 mandatory scientific approvals**, plus low-privilege metadata/safety-boundary checks. Target for governance, CI, license, security, README disclaimers, and validation scripts: **owner review**. Repository rulesets and CODEOWNERS must be configured to make those targets enforceable; a CODEOWNERS file by itself requests review but does not mandate it.

Prefer a PR before edits to canonical `main`; never force-push or delete `main`. Experiment branches may be rapidly revised or discarded. Preserve legacy R&D and do not force old material to conform retroactively.

## Configuration left to GitHub admins

Recommended default-branch ruleset for `main`: PR required, **0 general approvals**, prevent force pushes/deletion, require `sandbox-policy` check, and require CODEOWNERS approval for sensitive paths. Depending on account plan and ruleset capabilities, path-specific reviewer enforcement may need adjustment; do **not** enable a universal one-review minimum for all experiments. GitHub Actions token should be read-only by default, cannot create/approve PRs, and should receive no external secrets or upstream write credentials.

No production deployment or automatically published releases. Future previews, if any, should display prominent sandbox warnings and require a separate safety signoff.

A documented failure to enforce the ruleset is a deployment gap; policy prose must never be confused with technical enforcement.

The proposed owner-review rule is separate from admission/CI rules; see
[specific settings](sandbox/SETTINGS.md). GitHub cannot count self-approval.
Sole-owner governance changes need another qualified owner or an explicitly
recorded administrator bypass through a PR. That exception does not waive the
separate metadata check and must never be called independent review.
