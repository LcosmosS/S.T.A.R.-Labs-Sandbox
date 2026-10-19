# Sandbox stewardship check

This package implements the deterministic policy evaluator for the dedicated
`sandbox-stewardship` GitHub App check. It is deliberately separate from
computational CI, `sandbox-policy`, and scientific review.

## Policy

- Only files below a well-formed `experiments/SBX-YYYY-NNNN-slug/` path are
  approval-free. `experiments/README.md`, templates, root files, unknown paths,
  and all non-experiment paths are protected.
- Renames inspect both the old and new paths.
- Protected changes require one `APPROVED` review from `LcosmosS` or
  `LibertySquared`, not the PR author, on the exact current head SHA.
- The reviewer must currently have Write, Maintain, or Admin permission.
- A latest effective `CHANGES_REQUESTED` review blocks until that steward
  submits a later substantive review. Dismissed reviews never count.
- Incomplete changed-file, review, or permission results fail closed.
- This is an engineering-compliance decision only; it makes no scientific
  validity claim and never promotes experiment content.

## Architecture and trust boundary

`evaluate.py` is pure policy logic and has no network or credential access.
The `stewardship-tests` workflow tests it only; **that workflow is not the
stewardship status and must not be configured as the required check**.

The production publisher must be a separately deployed GitHub App using this
reviewed code (not code checked out from the pull request being evaluated).
The service must verify HMAC webhook signatures, pin the repository ID,
deduplicate delivery IDs, fetch all pages of changed files and reviews, re-fetch
current PR head data on every event, verify live steward permissions, and publish
a Check Run named `sandbox-stewardship` against the PR's current head. Subscribe
to `pull_request` (opened, reopened, synchronize) and
`pull_request_review` (submitted, edited, dismissed). Provide an authenticated
manual reconciliation path for missed deliveries.

The App requires Metadata: read, Pull requests: read, Checks: write. It does not
need Contents, Actions, Secrets, or Deployments permissions. App ID, private key,
webhook secret, and installation token handling belong in the deployment
environment, never this repository.

### Activation is an administrator operation

This PR does not deploy an App or alter rulesets. After deployment, run in
observational mode and test stale/dismissed approvals, lost permissions, renames,
incomplete API pagination, forks, and two open PRs sharing one head SHA. Verify
PR-specific check association prevents cross-PR approval leakage. Only then make
`sandbox-stewardship` required with the dedicated App as expected source, while
retaining `sandbox-policy` and computational checks. Do not add a universal
approval requirement for experiment-only changes.

## Local tests

```sh
python3 -I -m unittest discover -s tests -p 'test_stewardship.py' -v
```
