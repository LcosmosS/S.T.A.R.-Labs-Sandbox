# SciServer MCP v0.2 — policy-only installation

Read `protocol.md` for frozen SQL identities, security boundary, event state
machine, provenance schema, governance nonclaims and future execution gates.

The existing v0.1.1 `server.py` remains the only MCP entrypoint, with only
two read-only tools. This PR does not register `submit_approved_job`, allow
arbitrary SQL, or perform a live canary.

Offline policy check:

```bash
python -m pytest tests/integrations/test_sciserver_policy.py -q
```

Optional local-only plan creation (never submits to SciServer):

```bash
python - <<'PY'
from integrations.sciserver.query_policy import prepare_casjobs_run
result = prepare_casjobs_run("DR18-CANARY-10")
print(result["plan"]["run_id"])
print(result["plan"]["mydb_destination"])
print(result["receipt_sha256"])
PY
```

Before creating local plans, review the WSL2 state-root permissions:
`~/.local/state/star-sciserver/runs/` is expected to be user-owned and
private (mode 0700), and receipts are published with mode 0600. A local plan
is not an authorization, remote job, or scientific evidence.

**Local working tree warning:** an untracked preexisting
`integrations/sciserver/query_catalog.json` may conflict with the tracked
catalog when checking out this PR. Back up or rename that local draft first;
do not overwrite it blindly.
