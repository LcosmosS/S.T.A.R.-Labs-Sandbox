# SBX-2026-0007 — Physical correspondence and promotion, held at P2

**Status:** speculative. **Stage:** BLOCKED / NOT STARTED. **Evidence:** none. **Automatic promotion:** forbidden.

This is the research-contract placeholder for the final two priorities of the remediation sequence, not their execution. A physical connection cannot be inferred from an arithmetic point cloud or from passing numerical CI, and Legacy review must never be bypassed.

- [Stage gate](stage_gate.json): prerequisites P0/P1/P2 all incomplete until independently evidenced.
- [Observational protocol](OBSERVATIONAL_PROTOCOL.md): candidate SDSS DR18/MaNGA/GAMA selection, identities, spatial nulls and held-out design. **No pinned source bytes or primary endpoint yet.**
- [Legacy packet template](UPSTREAM_PACKET_TEMPLATE.md): exact provenance, negative evidence, reproducible environment, independent reimplementation invitation and non-claims.

This experiment is permitted to document future test design while remaining non-executable. No cross-repo promotion PR is opened without an actual complete scientific package, and no prior Sandbox result is promoted retroactively.

## Executable packet preflight (blocked by design)

`python3 -I experiments/SBX-2026-0007-physical-correspondence/validate_packet.py --self-test` should confirm the incomplete stage gate rejects the template. When a real candidate exists, `--packet /path/to/candidate.json --root /path/to/immutable/artifacts` checks required SHA-256 inputs and all 13 output files. Even a structurally complete candidate is **not** Legacy review or scientific approval, and the default gate remains BLOCKED. No remote GitHub mutation occurs.
