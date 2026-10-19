# S.T.A.R.-Labs upstream sources — isolated sandbox ports

**SANDBOX / UNVERIFIED.** This directory stores **24 exact source-file
snapshots** at the Git commit and Git blob identities in [MANIFEST.json](MANIFEST.json).
These are reference materials and optionally runnable *local-only* tools,
not a cloned independent-review gate, a controlled run, a scientific result,
or a claim of physical correspondence.

## Sources and their epistemic boundaries

| Source | Frozen commit | Sandboxed role |
| --- | --- | --- |
| [SciServer PR #111](https://github.com/LcosmosS/S.T.A.R.-Labs/pull/111) | `222a550b357bcbde8d6d5a0c7d0cbc9f05fa3bef` | Offline DR18 SQL validation, one allowed TOP10 local plan and hash-chained receipts. **Remote submission disabled.** |
| [ECC PR #103](https://github.com/LcosmosS/S.T.A.R.-Labs/pull/103) | `264faed10173d0e8db6822692d50333eee0af547` | Draft A/B/C foundation comparison, Investigator A v1/v2/v3 scripts, controls and reviewer handoff. **Unmerged and not independently adjudicated.** |
| ACSC revision (requested "v2") | `51927a9b396cdfa880f3128440db4715acdec8dc` | The **2026-10-11 charter-aligned manuscript revision** with correction ledger, mathematical checks and local worksheet. There is no distinct upstream release identified as "ACSC v2." |
| [P0-ANSATZ-001](https://github.com/LcosmosS/S.T.A.R.-Labs/blob/51927a9b396cdfa880f3128440db4715acdec8dc/preregistrations/P0-ANSATZ-001/protocol.md) | `51927a9b396cdfa880f3128440db4715acdec8dc` | Preregistered **five-candidate** parent-theory search frame copied as read-only source. No canonical registry mutation or controlled activation. |

**SciServer:** `integrations/sciserver/query_policy.py`, `receipts.py`, its exact
catalog and SQL files live under this directory with original relative paths
so that the upstream code can run from a sandboxed PYTHONPATH. The 200,000-row
SQL is a **disabled** reference; the TOP10 canary permits **local preparation**
only. There is **no remote CasJobs/MCP submission tool** imported.

**ECC:** A is H1 periods of closed non-exact 1-forms; B is integral U(1)
connection curvature and gauge-patch consistency; C is an entropy-coupled
**exact** local 2-form perturbation with unchanged global H2 class. The v3
fixture script needs NumPy, SciPy and SymPy; it is never executed by CI.
It is not independent Investigator B replication.

**ACSC:** The monograph’s math corrections are not observational evidence,
a proof of unique mapping, or a physical theory. The revision is an editorial
draft. Treat "ACSC v2" as a user-requested label requiring an explicit source
identification if a *different* version is intended.

**P0-ANSATZ:** Five original parent theories are GR+dust, Einstein-Vlasov,
exponential quintessence, Brans–Dicke–Lambda and Einstein–Abelian–Higgs
defects. Sandbox work may try other ideas, but cannot represent them as
members of the original frozen P0 search frame or reverse-select a parent
theory from a favorable observable.

## Real submodules (opt-in)

The separate `scripts/playground/external/` directories are **true Git
submodule gitlinks**, pinned to the external commits in the manifest. CI
does not fetch, install, execute or treat their content as evidence. Run
`git submodule update --init scripts/playground/external/ecdata` (or
`eclib` / `lmfdb`) **only after** reviewing the third-party code, license
and storage needs. The root `.gitmodules` is required Git infrastructure
and therefore an explicit exception to the otherwise tidy Markdown-only root.

For the offline CLI and experiment design guidance, see
[`../INTEGRATIONS.md`](../INTEGRATIONS.md).
