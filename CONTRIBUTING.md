# Contributing to S.T.A.R. Labs Sandbox

**You may be wrong here. You may not misrepresent what was done.** Negative results, deliberately false controls, adversarial counterexamples, and incomplete mathematics are welcome when clearly identified.

## Fast path

1. Propose an idea with a GitHub issue or create `experiments/SBX-YYYY-NNNN-short-name/` from `experiments/_template/`.
2. Use a unique SBX ID and keep its identifier stable across refutations or revisions.
3. Fill out `metadata.json` (JSON, standard-library parseable) and `README.md`, including explicit limitations and falsification conditions.
4. Keep code and outputs in your experiment directory, or link reproducibly to external inputs. **Never present invented data as observations.**
5. Open a PR. Ordinary contributions do **not** need an independent scientific reviewer. Maintainers may merge when basic integrity CI passes, subject to actual GitHub repository settings.

The optional Python command `python3 -I scripts/validate_sandbox.py` runs structural checks; `python3 -I -m unittest discover -s tests` tests the validator. CI does not execute submitted experiment code by default.

## Submission contract

Identify proposition, domain/assumptions, why the idea is being explored, counterexample or prospective falsifier, input provenance, meaningful parameters, results or non-results, and epistemic status. If you are reversing an implication, distinguish converse, inverse, and contrapositive; the truth of one does not automatically establish another.

No external independent-review packet is necessary to *experiment*. Independent review is required only where upstream decides it is necessary for **upstream** status.

## Sensitive reports

Do not place secrets, personal data, or exploitable vulnerability details in public issues/PRs; use private vulnerability reporting. Follow [MODERATION.md](MODERATION.md).

## Boundaries

Changes to `README.md`, policy, license, `.github/`, validation code, and schemas are **governance/security boundary changes**; submit them separately and request owner review. The technical enforcement of owner approval depends on repository rulesets being configured by an administrator. An experiment PR must not simultaneously weaken the policy checker.

Historical `R&D/` and original root documents are preserved in place and are not retroactively converted.

To run the complete archive and pinned-upstream verification locally, obtain
the public upstream repository at the **exact pinned commit** (the code is
inspected as data, not executed):

```bash
git clone --filter=blob:none --sparse --no-checkout \
  https://github.com/LcosmosS/S.T.A.R.-Labs.git ../star-labs-reference
git -C ../star-labs-reference sparse-checkout set --no-cone \
  .github/workflows/ README.md Contributing.md LICENSE SECURITY.md \
  charter/RESEARCH_CHARTER_v0.2.md research/gates/ECC_RTCH_RECOVERY.md
git -C ../star-labs-reference checkout --detach \
  51927a9b396cdfa880f3128440db4715acdec8dc
python3 -I scripts/verify_archive.py --root . \
  --upstream ../star-labs-reference
```

Run the command from the sandbox repository root. `--upstream` is required;
the script checks the upstream Git commit identity, the complete 24-file
reference inventory, SHA-256 values, and all 221 historical sandbox files and
Git modes. Keep derivatives in new experiments, cite exact source commits and
hashes, and put corrections in companion notes rather than editing archived
bytes.
