# S.T.A.R. Labs Sandbox

> [!CAUTION]
> **SANDBOX / UNVERIFIED**
>
> **EXPERIMENTAL SANDBOX — NOT A VERIFIED SCIENTIFIC OR PUBLICATION RECORD.**
>
> This repository preserves historical R&D and welcomes speculative hypotheses, deliberately false controls, counterexamples, incomplete derivations, negative results, and computational experiments. **A merge, passing CI check, or repository presence does not establish truth, reproducibility, independent review, or endorsement by [S.T.A.R.-Labs](https://github.com/LcosmosS/S.T.A.R.-Labs).**
>
> Synthetic data must be identified as synthetic; intentionally false statements must be marked as test objects. **Nothing is promoted upstream automatically.**

## Why this repository exists

The [main S.T.A.R.-Labs research repository](https://github.com/LcosmosS/S.T.A.R.-Labs) has controlled-execution, provenance, and review rules. The sandbox is a **different venue**, allowing rapid falsification attempts, adversarial constructions, and exploratory work without treating sandbox admission as evidence. Its purpose is to make error cheap to discover and impossible to mislabel as verification.

## Existing historical research is preserved

The existing research notes and [R&D/](R%26D/) archive predate this governance framework. The original root-level `.pdf`, `.py`, and `.csv` research files have been **moved without content or Git-mode changes** to [historical/](historical/), with original-path mappings and fixed digests preserved in the archive inventory. Other historical root files remain in place. These are **legacy historical materials, not retrospectively certified findings**. No new experiment metadata schema is imposed on them; historical uses of “proof” or “validation” do not establish scientific acceptance.

## Start a new experiment

1. Read [SANDBOX_POLICY.md](SANDBOX_POLICY.md), [DISCLAIMER.md](DISCLAIMER.md), and [CONTRIBUTING.md](CONTRIBUTING.md).
2. Copy [experiments/_template/](experiments/_template/) to `experiments/SBX-YYYY-NNNN-short-name/`. Reserve a distinct SBX ID; never reuse one.
3. Complete `metadata.json` and `README.md`, including a concrete falsifier or an explicit reason falsification is not yet formulated.
4. Submit a pull request. **Scientific approval is not required for ordinary sandbox contributions.** Repository permissions or branch settings may still require a PR, basic automated checks, or safety review.
5. Keep code, results, limitations, provenance, and refutations together. Do not convert exploratory output into upstream claims.

**Example:** [SBX-2026-0001 — deliberately false parity control](experiments/SBX-2026-0001-parity-control/README.md). CI validates experiment metadata and repository boundaries; it does not run untrusted experiment programs or judge scientific truth.

## Status and promotion

Permitted sandbox statuses: `speculative`, `intentionally-false-control`, `exploratory`, `inconclusive`, `refuted`, `archived`. **No `validated`, `proven`, `peer-reviewed`, or `supported` status exists here.**

Upstream promotion requires a **separate PR to [S.T.A.R.-Labs](https://github.com/LcosmosS/S.T.A.R.-Labs)** under the upstream repo's own requirements. See [UPSTREAM.md](UPSTREAM.md) and [GOVERNANCE.md](GOVERNANCE.md).

- [Contributions](CONTRIBUTING.md) · [Governance](GOVERNANCE.md) · [Moderation](MODERATION.md) · [Security](SECURITY.md)
- [Experiments](experiments/README.md) · [License](LICENSE) · [Notice](NOTICE.md)

**Scope:** experimental mathematical, computational, and physical hypotheses, including ACSC, ECC, GLMPCT, RTCH, and other S.T.A.R.-Labs-related sketches. None are established by appearing here.

[Setup audit](sandbox/SETUP_AUDIT.md) · [Live settings and owner exception](sandbox/SETTINGS.md) · [Historical byte inventory](sandbox/archive-manifest.json)
