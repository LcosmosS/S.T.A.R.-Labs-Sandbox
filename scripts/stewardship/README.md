# Sandbox stewardship check and GitHub App

This package separates engineering stewardship from numerical CI, \`sandbox-policy\`,
and scientific review. It contains a pure policy evaluator and a trusted, separately
deployed GitHub App publisher. Never run this service from a pull-request checkout.

## Decision contract

- Files are approval-free only when every changed path is under a valid
  \`experiments/SBX-YYYY-NNNN-slug/\` directory.
- Unknown paths, repository governance, CI, scripts, tests, schemas, archives,
  historical records, \`.gitmodules\`, experiment templates, and renames from or to
  any protected path require review.
- A protected PR requires one non-author \`APPROVED\` review from \`LcosmosS\` or
  \`LibertySquared\` on the exact current head SHA, while the reviewer has current
  Write, Maintain, or Admin repository permission.
- Dismissed approvals do not count. A latest effective \`CHANGES_REQUESTED\`
  review blocks until superseded by a later substantive review from that steward.
- Incomplete or unbounded API results, missing rename origins, permission lookup
  failures, and a head SHA that changes during evaluation fail closed.
- This is engineering-compliance enforcement only, not scientific review or
  approval to promote Sandbox findings to Legacy.

## Runtime and API permissions

Build from a reviewed, pinned commit and install the App only on
\`LcosmosS/S.T.A.R.-Labs-Sandbox\`. Required repository permissions:

| Permission | Access |
| --- | --- |
| Metadata | Read |
| Pull requests | Read |
| Checks | Write |

Subscribe to \`pull_request\` and \`pull_request_review\` webhooks. The service needs
HTTPS ingress to \`POST /webhook\`; \`GET /healthz\` is a health probe and
\`POST /reconcile\` repairs missed deliveries with a separate secret.

Required environment variables:

- \`GITHUB_APP_ID\`
- \`GITHUB_APP_INSTALLATION_ID\` (the installation ID after installing on Sandbox)
- \`GITHUB_APP_PRIVATE_KEY_PATH\` (mount the App PEM as a secret file; alternatively
  provide \`GITHUB_APP_PRIVATE_KEY\` as a protected secret environment variable)
- \`GITHUB_WEBHOOK_SECRET\` (must match the App configuration)
- \`STEWARDSHIP_RECONCILIATION_TOKEN\` (high-entropy secret, distinct from the webhook secret)

Optional variables: \`STEWARDSHIP_DELIVERY_DB\` (persistent writable SQLite path),
\`PORT\` (defaults to 8080). The container runs as a non-root user. Mount the SQLite
path on persistent storage; for a horizontally scaled deployment, replace the local
delivery store with a shared durable store and serialize check publication per SHA.

Example container build from the repository root:

\`\`\`sh
docker build -f scripts/stewardship/Dockerfile -t sandbox-stewardship:<reviewed-tag> .
\`\`\`

Configure the App's webhook URL to \`https://<your-host>/webhook\`, set its secret,
install only for the Sandbox repository, and store the App private key and other
secrets in the deployment platform's secret manager. Never commit credentials.
The service pins the repository ID and name and requests an installation token
restricted to that repository and the three permissions above.

## Security and same-SHA behavior

The service verifies the \`X-Hub-Signature-256\` HMAC over the exact request bytes,
pins the repository ID/name and installation ID, deduplicates delivery IDs, fetches
current PR data instead of trusting webhook review claims, follows API pagination,
and uses a separate constant-time authenticated manual reconciliation endpoint.
The SQLite database must be persistent so webhook replay protection survives
restarts. Only expose the service behind HTTPS.

A GitHub check run belongs to a commit SHA, not exclusively to one pull request.
Therefore the publisher re-evaluates every open PR, groups them by current head SHA,
and publishes success only when every open PR sharing that SHA passes. If any sibling
PR is protected without valid approval, the one SHA-scoped check fails for all of
them. This conservative rule avoids cross-PR approval leakage.

The publisher creates a new completed run per reconciliation (or updates an
in-progress run owned by this App); it never accepts a status from Actions as
authoritative. An API outage during a signed PR/review event triggers a best-effort
failure run for that event's reported head. Manual reconciliation can be requested
with:

\`\`\`sh
curl --fail-with-body -X POST \\
  -H "X-Reconciliation-Token: $STEWARDSHIP_RECONCILIATION_TOKEN" \\
  https://<your-host>/reconcile
\`\`\`

## Verification and activation

Run the pure evaluator and App-decision integration tests:

\`\`\`sh
python3 -I -m unittest discover -s tests -p 'test_stewardship*.py' -v
\`\`\`

The test suite proves that dismissed approvals fail protected PRs, valid current-head
approvals pass, and experiment-only PRs pass without making any review or permission
API reads. It also exercises stale approvals, permission lookup failures, and same-SHA
failure aggregation.

This repository PR does not create a GitHub App registration, generate or store
credentials, host the service, or alter repository rulesets. Those actions require an
authorized administrator. Deploy first in observational mode, test dismissal/re-push/
permission-loss and fork/same-SHA scenarios against GitHub, then set
\`sandbox-stewardship\` as a required check with the dedicated App as expected source.
Keep \`sandbox-policy\` and the computational checks required. Do not add a universal
human-review requirement for experiment-only changes.
