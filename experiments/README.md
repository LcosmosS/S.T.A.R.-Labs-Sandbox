# New sandbox experiments

This directory contains **new-format experiments only**. The existing root files and `R&D/` archive are outside this schema and remain untouched.

For a new experiment, copy `_template/` to `SBX-YYYY-NNNN-short-name/`; choose an **unused ID**. Edit `metadata.json` and `README.md`, and keep code/results in that folder. The ID is stable; a refuted result does not get a new ID merely to make the old result disappear.

The JSON schema is at `../schemas/experiment-metadata.schema.json`. The CI validator deliberately checks identity, status, scope, minimum evidence metadata and boundary flags **but does not certify the truth of a claim**. Its checks do not run submitted experiment code.

Useful trajectories: deliberate false control → counterexample; novel map → null distribution; hypothesis → adversarial test; proposed proof → explicit failed lemma. Promotion is a distinct **upstream** transaction, never a status update here.
