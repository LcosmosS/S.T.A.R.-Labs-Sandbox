# Integrated first-principles source port: SciServer, ACSC, ECC, P0 and submodules

This is an **independent scientific sandbox**, not an upstream preregistered
experiment or review certificate. Every source copy is byte-identical to an
identified upstream Git commit; see [the manifest](ports/MANIFEST.json) and
[the source and epistemic boundaries](ports/README.md). No historical archive
entries or upstream support flags are changed.

## 1. SciServer DR18 SQL (PR #111, offline mode)

Run from sandbox repository root with Python 3.12+ on **POSIX/WSL2**:

\`\`\`bash
python3 -m scripts.playground.sciserver_offline list
python3 -m scripts.playground.sciserver_offline validate
# Explicit opt-in: creates a private local plan/receipt only, NO remote request
python3 -m scripts.playground.sciserver_offline prepare \
  --query-id DR18-CANARY-10
\`\`\`

Use \`--state-root /private/user-owned/path\` if you prefer an alternative local
0700 receipt root. The unmodified pinned source uses a default
\`~/.local/state/star-sciserver/runs/\`; receipts are local hash-chained files,
not authenticated operator approvals. The only permitted local preparation
is the fixed TOP 10 DR18 canary. \`DR18-DETERMINISTIC-200K\` is **blocked**.
Both queries have \`submission_enabled=false\`. No SciServer account,
API key, MyDB write, remote SQL execution, login or MCP tool is activated.
Review the prepared SQL and provenance manually before proposing a distinct
authorized live-acquisition experiment.

The code and catalog are stored, with original relative paths, under
\`scripts/playground/ports/integrations/sciserver/\` and
\`scripts/playground/ports/verification/datasets/casjobs/\`.
Use the pinned tests under \`ports/tests/integrations/\` as source references;
the sandbox CI uses independent stdlib regression tests instead of invoking
the upstream's pytest suite or creating local receipt state.

## 2. ACSC manuscript revision (the requested "v2")

Read the exact [ACSC Charter-Aligned Rewrite](ports/docs/monographs/acsc/2026-10-11/ACSC_Charter_Aligned_Rewrite.md),
its correction ledger, assumptions and local claim worksheet.

**Source discrepancy:** the upstream does **not** contain a clearly titled or
released package "ACSC v2". This integration records the latest identifiable
2026-10-11 revision instead. If "ACSC v2" refers to another file or model
implementation, provide its exact path or commit; this port must not pretend
an editorial revision is a released scientific v2 result.

A first-principles ACSC experiment must define a fixed map \`Phi\` from actual
elliptic invariants, dimensionless arithmetic coordinates, a separately
specified physical correspondence hypothesis, survey sampling, units,
alternative mappings, arithmetic/cosmological nulls and falsifiers.
Mathematical embeddings alone are **not** observed cosmic positions.

## 3. ECC foundation comparison (unmerged upstream PR #103)

Read [ECC-B01 protocol](ports/ecc_b01/protocol.md), the
[foundation-comparison proposal](ports/research/gates/EXP-ECC-B01_FOUNDATION_COMPARISON_PROPOSAL.md)
and [governance notes](ports/ecc_b01/GOVERNANCE_GATES.md).

- Foundation A: periods of closed non-exact 1-forms in H1;
- B: U(1) connection curvature and quantized flux in H2;
- C: entropy-dependent locally changed **exact** 2-form contribution that
  leaves its global cohomology class unchanged.

These are **distinct models**; they cannot be conflated into one established
entropy-gravity coupling. The versioned Investigator A fixture implementations
are copied unchanged (original, v2 and corrected v3). Upstream PR #103 is
**open and unmerged**, with independent Investigator B comparison outstanding.

Optional local numerical fixture check, only after installing and verifying
\`numpy\`, \`scipy\`, \`sympy\` in a private virtual environment:

\`\`\`bash
python3 scripts/playground/ports/ecc_b01/investigator_a_v3.py \
  /tmp/ecc_b01_sandbox_v3.json
\`\`\`

This produces an analytic fixture report, not mathematical certification,
cosmological evidence, or independent replication. No ECC fixture scripts
run in sandbox CI.

## 4. Parent-theory ansatz

[P0-ANSATZ-001](ports/preregistrations/P0-ANSATZ-001/protocol.md) is a
**read-only original** preregistration with five historical candidates:
GR+irrotational dust; Einstein–Vlasov; canonical exponential quintessence;
Brans–Dicke–Lambda; Einstein–Abelian–Higgs defects.

Sandbox alternatives are allowed, but they do not change the upstream
\`P0-SF-v0.1\` cutoff, candidate definitions or negative/positive results.
Do not select a purported independent parent physical theory by fitting a
desired ACSC observable in reverse.

## 5. Real pinned arithmetic dependencies

The three **true git submodules** are under \`scripts/playground/external/\`
at the exact upstream gitlink commits. They are **not initialized by CI**,
do not auto-install packages or supply verified scientific evidence.

From repository root, initialize only those you actually need:

\`\`\`bash
git submodule update --init scripts/playground/external/ecdata
git submodule update --init scripts/playground/external/eclib
git submodule update --init scripts/playground/external/lmfdb
\`\`\`

Inspect each external repository's license, security and disk footprint before
cloning. \`lmfdb\` can be large. The root \`.gitmodules\` file is necessary Git
configuration and is a deliberate exception to the otherwise Markdown-only
top-level organization.

## Scientific reasoning and integrity

Each proposed SBX experiment should describe domain, first-principles
derivation, dimensional consistency, no-go arguments, rival theories, explicit
observables, data provenance, controlled nulls, sources, bootstrap/ablation
sensitivity, reproducible seeds, and failed counterexamples. Passing CI means
only that repository boundaries and data-source bindings survived their tests.
No source-port, software test or numerical fixture can promote claims or
alter upstream registries.
