# Sandbox setup audit — 2026-10-19

This is a setup and preservation audit, not scientific review, independent
replication or evidence authentication. The user supplied the completed design
“Designing a Permissive S.T.A.R. Labs Playground Without Turning Speculation Into
Claims”. The referenced conversation was read; its cached research replies were
content-reference placeholders. Implementation uses the complete supplied text,
not an assertion that inaccessible citations were authenticated.

## Pinned repositories and preservation

| Repository | Inspected default revision | Role |
| --- | --- | --- |
| [Sandbox](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox) | `a48ee3c41d17305530d65616c16c158f04e502d8` | Existing independent public repository; not archived or a fork |
| [Upstream](https://github.com/LcosmosS/S.T.A.R.-Labs) | `51927a9b396cdfa880f3128440db4715acdec8dc` | Read-only reference; no mutations made |

The 221 baseline files are inventoried by original path, Git blob, mode, size and
SHA-256. All research files remain at their original paths. The baseline README
is one newline; it is preserved verbatim in `archive/README.pre-sandbox.md` and a
new landing page replaces it. The blank one-byte README is not a scientific disclaimer. The earlier README remains at commit
`27ddc11605756dbf8072de35be4206ed60d185aa`. Baseline ancestry is checked. No archived-history
rewrite, research-script execution, data import or upstream code copy is involved.
An older unfinished local setup draft was inspected and left untouched; this PR
was prepared in a fresh checkout at the current remote baseline.

The pinned [upstream reference manifest](upstream-reference.json) binds 24 files:
all 18 currently tracked workflow definitions plus README, contribution guide,
Charter text, license, security guidance and ECC/RTCH recovery gate. Upstream
scientific-status flags and record IDs are references only; none are imported
as sandbox authority. Their source bytes and hashes were read and checked during
setup. **Current routine CI also checks all 24 reference files against a
separate read-only checkout at the exact pinned upstream commit**, as well as
checking local archive integrity and sandbox metadata; it does not contact
mutable upstream `main`. The reference manifest is steward-owned. Original
sandbox licensing is unchanged.

## Live baseline inspection

| Control | Sandbox before setup | Upstream at inspection |
| --- | --- | --- |
| Default branch | `main`, unprotected | `main`, protected by ruleset |
| Classic protection API | HTTP 404: branch not protected | HTTP 404: no classic branch protection |
| Rulesets including parent rules | None; effective branch rules empty | Active [Non-negotiable #15259335](https://github.com/LcosmosS/S.T.A.R.-Labs/rules/15259335), all branches |
| PR review | None required | One approval, last-push approval, stale approvals dismissed |
| Other branch requirements | None | Signed commits, linear history, CodeQL and code quality |
| Bypasses | No rules to bypass | Maintain/admin roles and several integrations have always-bypass authority |
| Actions default token | Read; PR approvals disabled | Write; Actions PR approvals enabled |
| Workflows | 0 registered, 0 tracked | 25 registered including dynamic/previous entries; 18 tracked at pinned head |
| Pages | `has_pages=false`, Pages API 404 | Pages API 404 |
| Environments | None | `copilot`, `Preview`, `Production`, `SageMath/Python`; no protection rules listed |

Upstream's protected flag does not imply classic branch protection or that every
actor needs independent approval: the ruleset has explicit bypasses. In the
sandbox, Actions is enabled with all actions allowed; the workflow itself pins
checkout. No repository Actions secrets were listed (count zero); this does not
prove the absence of every possible user/integration credential. Secret scanning
and push protection are disabled at baseline and are not asserted as controls.
Wiki is disabled; Issues and Discussions are enabled. There were no tags.

Upstream CI includes registry/controlled-readiness and runner tests, Sage smoke
execution, source-package integrity, CodeQL and image building/publishing.
`build-image.yml` has a package-write publishing job; CodeQL has security-event
write permission. Those privileges, the broader repository token default, and deployment settings
are not copied or changed. All 18 tracked upstream workflows declare top-level
read permissions, but selected jobs grant additional permissions.
No privileged `pull_request_target` workflow is introduced here.

## Concurrent setup and reconciliation

While this work was being prepared, [PR #1](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/pull/1)
landed at `22e74794bec8116a019f25bae51ec3f25f62dc6f`. It already provides the
permissive governance, root `experiments/` layout, JSON schema, a parity-control
example and the `sandbox-policy` workflow. The follow-up
[PR #2](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/pull/2) is reconciled on
that revision; the new scaffold is retained, not replaced with a competing
experiment format. Only the new unmerged PR branch is rebased; archived history
is not rewritten. The original R&D and the landed parity-control program are
not executed by this follow-up.

## Live rules changed during setup

At **00:15:30 America/New_York on 2026-10-19**, an active
[Sandbox Rules #25371960](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/rules/25371960)
was created and then updated at 00:15:53. Readback shows all-branches coverage,
deletion/force-push prevention, linear history, CodeQL high/errors thresholds,
code-quality severity `all`, Copilot review on pushes/drafts, and a status rule
with an **empty required-check list**. It has **no PR or CODEOWNERS rule**.
DeployKey, admin-role and three integration entries may always bypass it.

`main` is now `protected=true` even though classic branch protection still returns
404. The proposal branch is also covered. The guarded, leased replacement of our
new PR branch was permitted using the existing administrator bypass and reported
force-push and pending CodeQL violations. No archived branch or upstream ref was
rewritten; this is not an independent approval.

These live settings are preserved. The concrete minimal replacement JSON files
and two-rule rationale are in [SETTINGS.md](SETTINGS.md). Until applied, zero
required reviews does not imply PR-based admission, governance approval is not
technically enforced, and a green `sandbox-policy` is not a required merge check.
The PR can remain blocked on the configured scanning/quality conditions despite
its own workflow passing. No actual zero-review merge, direct-write denial,
CODEOWNERS gate or hostile-fork isolation has been demonstrated.

## Minimal additions in PR #2

- A Git-bound inventory of all 221 pre-policy files, historical ancestry check,
  and placement check prevent silently editing the archive or adding research
  outside `experiments/`. The one-byte pre-policy README is preserved separately.
- The existing JSON validator now rejects unknown/nested metadata keys, duplicate
  JSON keys, boolean schema versions, malformed source lists, short/unpinned
  upstream revisions, unlabeled false controls, unclassified files and symlinks.
  The schema and validator retain one canonical experiment format.
- The existing workflow is pinned to a verified checkout commit, reads the PR
  base validator, uses no retained checkout credentials and fetches history for
  byte verification. Candidate policy checks and regression tests also run;
  experiment programs, scientific dependencies and archived tests do not.
- CODEOWNERS extends stewardship to the archive checker/inventory and template
  paths while leaving ordinary experiment folders unowned. Sole-owner policy PRs
  require another owner or a documented governance-rule bypass; that exception
  does not waive the separate admission CI rule.
- The supplied completed design is adapted to the now-existing `main` layout.
  Upstream references are pinned, no authoritative records are copied, and no
  releases, automatic promotion or deployments are introduced.

## Validation and activation status

Local archive validation, metadata validation, **15 guardrail tests** and
**actionlint 1.7.12** passed before publication. The first reconciled head
`ac0b5e3cf1c091467cfd260efec0fc56551b7a51` passed the
[Actions run](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/actions/runs/39198642877).
 Exact-head Actions results and live rule readback
are recorded with PR #2. The archive checker is a one-time bootstrap because it
does not exist in PR #2's base; the older base metadata validator still runs.
Post-merge routing of extended CODEOWNERS paths, a real outsider merge with zero
reviews, hostile-fork isolation and tag blocking have not been live-tested. No
tag rules are installed by the files in this PR; GitHub administrators remain
able to edit rules. Configuration readback is not an end-to-end merge test. The proposed admission
rule requires an up-to-date branch so an earlier successful check cannot remain
valid after the base policy changes; this is an explicit departure from the
supplied design's loose-check recommendation.

Activation follows [SETTINGS.md](SETTINGS.md). The setup PR does not merge itself.

## Post-review ruleset readback and reference-check extension (2026-10-19)

The earlier sections document historical setup snapshots. The owner's
subsequent change to [Sandbox Rules #25371960](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/rules/25371960)
now targets **`~DEFAULT_BRANCH` only**, requires PRs with zero general
approvals, **explicitly requires `sandbox-policy`** from GitHub Actions
(integration `15368`) with strict up-to-date checks, and has **no bypass
actors**. This fixes the earlier all-branches admission blocker and the
missing required-check setting. Other live constraints remain (CODEOWNERS,
conversation resolution, stale-review dismissal, CodeQL/code quality,
linear history). A real zero-review merge and independent writer direct-push
rejection have **not** been demonstrated and are not claimed.

The improved validator in this PR verifies all **24 upstream reference files**
against a separate, sparse, read-only checkout of
`LcosmosS/S.T.A.R.-Labs` at pinned commit
`51927a9b396cdfa880f3128440db4715acdec8dc`.
It checks the commit identity, paths, canonical URLs and SHA-256 digests,
rejecting missing files, altered bytes and incorrect revisions without
executing upstream code. [CI run 39200818602](https://github.com/LcosmosS/S.T.A.R.-Labs-Sandbox/actions/runs/39200818602)
passed all 221 historical archive bindings, all 24 upstream reference bindings
and 17 regression tests, including negative hash and revision cases.

## Review remediation: immutable bootstrap and archive-mode protections

PR #2's bootstrap base `22e74794bec8116a019f25bae51ec3f25f62dc6f`
does not itself contain `scripts/verify_archive.py`. Its workflow now
loads the verifier from immutable commit
`6b4e234f49e7881eaa1e03943165ab50c39550e4` in a separate
read-only checkout when, and only when, the PR base is that bootstrap commit.
The proposal branch's checker is **not** the trusted verifier during bootstrap.
For later PRs, the workflow uses the verifier from the trusted base branch.
The required workflow is CODEOWNERS-owned; changes require the configured
governance review rather than becoming a self-authorized trust bypass.

That pinned verifier compares preserved file modes and Git object IDs in the
proposed tree to the baseline tree, including the **relocated historical
README** while permitting the sandbox's new landing README. It also binds
the upstream reference list to a fixed inventory of **exactly 24 paths**,
rejecting missing, duplicate or unexpected entries before hash comparison.

Security and moderation guidance now points to a dedicated **public contact
request form** if GitHub private vulnerability reporting is unavailable. The
form is only for requesting a confidential route; it is not itself a private
reporting channel and must contain no sensitive report content. No contact
address was invented.

## Root research-file organization (2026-10-19; staged PR)

The initial setup snapshot above accurately describes the original root paths
**at the time of setup**. A subsequent, explicitly authorized organization
change relocates exactly **18** root-level files (4 PDFs, 13 Python, 1 CSV) into
`historical/`. The original repository snapshot remains reachable through
Git history; `sandbox/archive-manifest.json` retains every `original_path`
and binds each moved item's `preserved_path` to `historical/<filename>`.

A separate owner-reviewed verifier change must merge first. It pins the exact
18 relocation names in its own code, verifies **exactly one** of old/new paths
for each, compares Git blob IDs and modes with the original baseline, and
retains the SHA-256, byte count and 24-file upstream-reference checks.
No research bytes, executable modes, upstream artifacts, or scientific status
records are changed as part of the folder reorganization.

## Subsequent root organization: 29 additional historical files (2026-10-19)

After the first 18 root artifacts were relocated, the user requested that **every
other root-level file** except Markdown (`.md`), `.gitignore`, and `LICENSE` be
placed in `historical/`. This move covers exactly 29 additional original
baseline research files, making 47 relocations in total. The root `.gitignore`
remains where Git can apply its patterns globally. Markdown governance and
landing-page documentation plus `LICENSE` are also preserved at the root.

The immutable baseline's `original_path`, Git object IDs, Git modes, SHA-256
hashes, byte lengths, and entry count (221) remain unchanged. Only the 29
approved `preserved_path` values were rebound from their old root path to
`historical/<original_filename>`. The separate trusted-verifier PR explicitly
pins all 29 names before the actual path-only move; runtime integrity checks
require exactly one original or historical path per file and reject changed
content, modes, unapproved paths, and missing or duplicate objects.

Other nested files and upstream S.T.A.R.-Labs evidence remain unchanged.
