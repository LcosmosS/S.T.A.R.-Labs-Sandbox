# SciServer MCP v0.2 — Controlled execution policy and protocol lock (PR 1)

**Status: POLICY ONLY / REVIEW REQUIRED. This PR does not activate asynchronous
CasJobs execution, enable database write tools, or change scientific eligibility.**

## 1. Authority and scope

This policy extends the independently reviewed read-only SciServer MCP v0.1.1
integration. The v0.1.1 tools remain unchanged: fixed DR18 inspection and
read-only MyDB table metadata. The new modules provide offline query validation,
one-time local plan creation, and integrity-evident provenance events; **no new
MCP network tools are registered**. All submissions remain prohibited.

Dataset_ID is `DATA-SDSS18-200K`. This is acquisition/source-verification
infrastructure, not a registered controlled experiment. There is no Claim_ID,
Parameter_Set_ID, Null_ID, statistical endpoint, inferential alpha, or experiment
activation in this PR. Do not fabricate them. A dataset-source verification
receipt cannot establish ACSC/ECC/GLMPCT support.

## 2. Approved SQL and immutable byte pins

The catalog at `integrations/sciserver/query_catalog.json` enumerates exactly
two queries. Before any run plan is written, both SQL files are opened with
`O_NOFOLLOW` and checked against SHA-256. Unknown query IDs, content changes,
symlinks, unsafe paths, other contexts and registry activation are rejected.

| ID | Existing SQL source | SHA-256 | Preparation | Submission |
| --- | --- | --- | --- | --- |
| DR18-CANARY-10 | `verification/datasets/casjobs/STAR_DR18_10_canary.sql` | `159b83a0d36c1d05dda6108591d1ea5756a66d1f4355c5304655cf48df655b3d` | permitted (local only) | disabled |
| DR18-DETERMINISTIC-200K | `verification/datasets/casjobs/DATA-SDSS18-200K_deterministic_probe.sql` | `163bf311ba274d4a7c7a4ceaa136cf691130687d17a456202f2e98d04fc415d4` | blocked | disabled |

Both use only context `DR18`, `PhotoObj` joined to `SpecObj`,
the original magnitude predicates, and explicit ordering. The new canary
returns up to 10 rows and casts `objid` and `specobjid` to decimal character
strings. It is not the original historical query and is not evidence of
historical row selection.

The historical CSV hash stays
`9dca2008683fde4b0f7a90af5de85ee846a30a47f6f6fae3968c83dea06fa5d2`.
The recovered unordered `TOP 200000` historical SQL is archival evidence
only. Neither the canary nor deterministic ordered sample may overwrite it.

## 3. Locked plan and destination naming

`query_policy.prepare_casjobs_run("DR18-CANARY-10")` prepares a **local**
record and performs no remote operation. Run_ID is 32 random lowercase hex
characters. The only permitted table-name form is
`STAR_SCISERVER_C10_<FIRST_16_UPPER_HEX_OF_RUN_ID>`, verified against
the generated Run_ID and the strict destination regex. For the disabled
large probe, the reserved future name is
`STAR_SCISERVER_D200K_<FIRST_16_UPPER_HEX_OF_RUN_ID>`.
No caller may supply a table name, SQL string, context or output path.

A locally unique name and create-only receipt are necessary but insufficient
to prove MyDB table nonexistence. The later live submission adapter MUST check
MyDB metadata immediately before submission, use create-only server behavior,
and fail closed on any collision or ambiguous response. It MUST NOT issue
DROP/DELETE/UPDATE/ALTER statements.

## 4. Human authorization and execution boundary

PR 1 ships **no** REST/SDK job-submission path, job-export path, or approval
command. The catalog has `remote_submission_enabled=false` and both entries
have `submission_enabled=false`. A called
`query_policy.require_submission_authorization` always raises PermissionError.

A `planned` event is not operator approval. A local event named
`operator_approved` is not sufficient to grant database permissions either.
For a later PR, require a separate, auditable human approval of an exact plan
digest binding query ID, source SQL SHA-256, verified source commit, DR18
context, destination name, run ID and one-time nonce. Store approval outside
the writable MCP/Codex sandbox, or use a human-run submit command with no
MCP write authority. Do not expose arbitrary SQL or a generic execution API.

PR 2 may implement the adapter **only after explicit human authorization**
and testing that the current SciServer REST service accepts `CreateTable` /
`TableName` without rewriting the pinned SQL. These historical API field
names are a compatibility hypothesis, not yet live-verified here.

## 5. Event lifecycle and recovery

Local chain state transitions are:

```
planned -> operator_approved -> submission_intent
  -> job_accepted -> job_finished -> exported -> verified
                   |                   |         |
                   +--> aborted        +-------> aborted
submission_intent -> submission_ambiguous -> reconciled
  -> job_accepted OR aborted
```

A submission with uncertain result becomes `submission_ambiguous`. Never
automatically submit it again. Future recovery requires operator-reviewed
CasJobs history plus exact table/job attribution; if still ambiguous, abort.
Do not interpret job status 5 (Finished) as a verified dataset. A failure
or aborted state is terminal and cannot be replayed.

The PR 1 tests inject mock future event types only; they do NOT perform real
approval, remote submission, status polling, reconciliation or export.

## 6. Output and provenance contract

By default local plans write into
`~/.local/state/star-sciserver/runs/<run_id>/`; no outputs are created
inside the Git checkout. For every run:

- `event_0000.json`: immutable local `planned` event including dataset,
  approved SQL SHA, catalog SHA, context, destination and nonclaim flags.
- `event_0001.json`, ...: future transitions only when explicitly called
  by later governed software. Each event has a UTC timestamp, monotonically
  increasing sequence, previous-event SHA-256 and own canonical-event digest.
- `.append.lock`: local POSIX exclusive lock serializing event writers.

Events are written via temporary same-directory files and atomic hard-link
create; existing event paths cannot be overwritten by the API. Each append
requires the exact prior digest and the permitted transition; reads verify the
full hash chain and ordering. A process with write access to the state
directory can still rewrite the entire chain. **These receipts are
tamper-evident, not tamper-proof or signatures.** Independent post-execution
archival/hash attestation is a separate gate.

The source commit is not presented as independently pinned at preparation
time; the future approved submission bundle must bind its exact reviewed
Git SHA alongside the catalog and query hashes.

## 7. Scientific nonclaims and activation gate

There are zero new SCIENTIFIC controlled experiments, results, physical
correspondences, theorem assertions, or promotion of source provenance in
this PR. Do not modify `registry/`, historical source files, frozen
`DATA-SDSS18-200K` bytes, `Evidence_Status`,
`Provenance_Status` or support/eligibility flags.

The later approved, deterministic 200k export must reuse
`scripts/independent_dataset_verification.py` with an independent frozen
CSV comparison; ordering does not reproduce the historical unordered
selection. It remains blocked until an approved canary and subsequent review.

## 8. Offline verification

Run from repository root:

```bash
python -m pytest -q tests/integrations/test_sciserver_policy.py
python -m pytest -q tests/integrations/test_sciserver_identifier.py
git diff --check
```

No live credentials, SDK connection, or MyDB modification are necessary.
This document and hashes are a proposed, reviewable lock; only an approved
PR and verified unchanged source pins make it a governed baseline.
