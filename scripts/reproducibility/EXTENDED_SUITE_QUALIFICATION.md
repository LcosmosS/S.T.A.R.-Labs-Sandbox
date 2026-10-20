# Extended reproducibility suites — qualification boundary (2026-10-19)

**Current state: DESIGN IMPROVED / NONE OF THE EIGHT EXECUTED OR QUALIFIED BY THIS PR.**

This workflow has eight mutually exclusive `workflow_dispatch` suites and a new fail-closed `qualification-receipt` job. Each manual run records the selected suite's actual GitHub result; `SMOKE_PASS_ENVIRONMENT_UNQUALIFIED` means it executed successfully but not in a fully locked software environment. The receipt pins the legacy source commit `51927a9b396cdfa880f3128440db4715acdec8dc`, the current Sandbox workflow commit, Sage image digest, run ID, skipped sibling jobs and explicit non-claims. The receipt's SHA256SUMS is an integrity check, **not** a scientific independent-review signature.

The two prior mutable Sage container tags `sagemath/sagemath:latest` are replaced with immutable image index digest `sagemath/sagemath@sha256:310dfe23fc786f3a5a06a7b0387c60201ec79b32c0db941b7624505ee5edb565` (Sage 10.10). Python setup actions are pinned by action commit; interpreter requested version is `3.12.12`, but hosted OS updates still vary. **This does not lock transitive pip/apt/conda/browser dependencies.** Do not claim fully reproducible environment qualification until audited wheelhouse/package hashes, image/build/OS identities, and pinned result receipts exist.

| Suite | Source locked | Primary remaining limitations | Status |
| --- | --- | --- | --- |
| observational-lfs | Legacy Git SHA, declared LFS OIDs | LFS object hydration, runtime tools / schema test actual receipts | NOT_RUN |
| publisher-refetch | Legacy Git SHA, previous publisher hash | Live publisher response can change; parser pip install lacks wheel hash; retain known VizieR mismatch | NOT_RUN |
| recovered-lfs | Legacy Git SHA and LFS refs | Recovery quarantine integrity/corpus provenance, actual access/runs | NOT_RUN |
| sage-notebooks | Legacy SHA and Sage image digest | `apt-get` Git + un-hashed pip requirements and notebook/kernel additions | NOT_RUN |
| sage-sky | Legacy SHA and Sage image digest | Un-hashed pip and pyarrow wheel chain, runtime deployment | NOT_RUN |
| starmap-browser | Legacy SHA and npm package-lock | Node `24` floating patch, `npx playwright install --with-deps` system packages | NOT_RUN |
| build-image | Legacy SHA and Docker base index digest | `apt-get`, conda solver and pip installation resolve mutable deps in Dockerfile | NOT_RUN |
| legacy-unit-suite | Legacy SHA, direct pins in requirements.txt | PyYAML/corner version ranges and un-hashed transitive wheels | NOT_RUN |

The optional workflow must remain non-blocking with respect to independent scientific review. All scientific support flags remain false. A suite run's success is a *software smoke result*, not controlled-experiment admission.

## Execution order

Run one opt-in suite at a time using Actions **sandbox-extended-reproducibility** on `main`. Preserve each run ID, complete logs, the original suite output artifacts, and the new `sandbox-extended-receipt` artifact; any FAILED/SKIPPED status must remain faithfully recorded. Suggested first execution: `recovered-lfs` (isolated quarantined-source verification), then `observational-lfs`, `legacy-unit-suite`, browser and build; leave `publisher-refetch` for a separately audited known-hash drift case. The Sage suites still need external Python wheel/transitive lock qualification in addition to the pinned image. This ordering is operational, not an evidence ranking.
