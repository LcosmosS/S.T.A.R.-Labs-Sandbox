# Repository settings and activation

Policy files do not configure GitHub. The [setup audit](SETUP_AUDIT.md) records
live settings; this document defines the intended minimum. Keep `main` as the
existing default branch and leave experimental branches unrestricted.

## Current live rule: differs from this proposal

[Sandbox Rules #25371960](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/rules/25371960)
appeared during setup, created at **00:15:30 America/New_York on 2026-10-19**.
It targets all branches, blocks force pushes/deletion, requires linear history,
CodeQL and code quality (`all`), and enables Copilot review. It has **no PR rule,
no code-owner rule, and an empty named status-check list**. Deploy keys, the
administrator role and three integrations have always-bypass entries.

This PR does not overwrite that newly changed live configuration. The following
is a concrete **proposed replacement**, not active protection: replace that rule
with [admission-ruleset.proposed.json](admission-ruleset.proposed.json) and add
[governance-ruleset.proposed.json](governance-ruleset.proposed.json). The required
status source is GitHub Actions app `15368`, verified from an actual check run.
Do not merely add these alongside the all-branches scanning rule and assume the
extra scanning requirements disappeared: applicable rules combine.

## Admission ruleset: default branch only

- Active branch ruleset; include `~DEFAULT_BRANCH`, exclude nothing.
- Require a PR with **0** approving reviews; no code-owner or last-push approval
  in this ruleset, no stale-review dismissal, no conversation-resolution gate.
- Require `sandbox-policy`, from GitHub Actions, against an up-to-date branch. No release, controlled-runner, signing or scientific-review check.
- Block deletion and force pushes. No bypass actors in this ruleset.
- Leave existing merge-method settings, repository visibility, default branch,
  archived history and contributor access unchanged. Auto-merge remains off.

## Governance ruleset: default branch only

- Separate active ruleset with PR + **0** general approvals and code-owner review.
- CODEOWNERS owns governance/CI paths only, not experiment folders.
- Repository administrators may bypass **this governance rule only via a PR**
  when handling sole-owner policy changes. Admission/CI rules still apply.
- Explicitly record a bypass decision. It is stewardship, not independent review.

Separating the two rulesets prevents an owner-review exception from also skipping
metadata checks or permitting direct writes to the default branch. An administrator
can still edit rules: the boundary is accountable process, not tamper-proofing.
This deliberately tightens the supplied design's loose-check suggestion: a policy
change on the base branch must invalidate an older experiment check, rather than
letting metadata merge under a superseded validator. The required check is small
and grants no scientific status. A future incompatible schema/policy migration
needs a documented steward plan; do not silently bypass the trusted-base check.

CODEOWNERS is already present on `main` from PR #1; this PR extends it. Its actual
behavior for ordinary versus owned-path PRs needs testing after setup is merged;
configuration readback is not an end-to-end merge test.

## Actions and public surfaces

- Default workflow permissions: read; Actions PR approval: disabled.
- Workflow: `pull_request`, default-branch `push`, manual dispatch; `contents: read`.
- Checkout is pinned by commit, credentials are not retained, submodules/LFS off.
- The PR base validator checks submitted metadata; the archive checker binds the historical bytes.
  The archive checker is new in this PR; its one-time bootstrap requires maintainer inspection.
- No scientific dependency install, archived test discovery, experiment execution,
  secrets reference, write token, upstream API write, release or deployment job.
- No Pages site or production environment is created. Wiki remains disabled;
  existing Issues/Discussions settings are retained.

Recommended future controls if publication is introduced: a separately reviewed
`sandbox-preview` environment, permanent warning in the rendered UI, isolated
credentials and maintainer publication approval. No publishing automation is
part of this setup. Reserving release-like tags is a future option; no tag rule
or GitHub Release prohibition should be inferred from the branch rules.

References: [GitHub rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets),
[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
[PR trust boundary](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).
