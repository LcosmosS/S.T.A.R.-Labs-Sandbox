# New sandbox experiments

This directory contains **new-format experiments only**. The existing root files and `R&D/` archive are outside this schema and remain untouched.

For a new experiment, copy `_template/` to `SBX-YYYY-NNNN-short-name/`; choose an **unused ID**. Edit `metadata.json` and `README.md`, and keep code/results in that folder. The ID is stable; a refuted result does not get a new ID merely to make the old result disappear.

The JSON schema is at `../schemas/experiment-metadata.schema.json`. The CI validator deliberately checks identity, status, scope, minimum evidence metadata and boundary flags **but does not certify the truth of a claim**. Its checks do not run submitted experiment code.

Useful trajectories: deliberate false control → counterexample; novel map → null distribution; hypothesis → adversarial test; proposed proof → explicit failed lemma. Promotion is a distinct **upstream** transaction, never a status update here.

For a runnable first-principles example, see [SBX-2026-0002](SBX-2026-0002-first-principles-workbench/README.md) and the [independent workbench](../scripts/playground/README.md). Its local runner outputs only exploratory diagnostics from labeled synthetic inputs. The [SBX-2026-0003 discrete cochain controls](SBX-2026-0003-exact-form-controls/README.md) examine the exact-versus-closed distinction relevant to ECC/RTCH from elementary algebra, without asserting physical cohomology. The five optional numerical kernels are pinned source snapshots, not validated scientific conclusions.
