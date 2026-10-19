# Security policy — Sandbox

This repository contains experimental code, much of which is not independently verified or safety-reviewed. Do **not** treat it as production-ready software or execute unfamiliar scripts with secrets, privileged permissions, or network credentials.

Please do **not** disclose exploitable vulnerabilities, tokens, private keys, or personal information in public issues or PRs. Use GitHub's private vulnerability reporting when the Security tab offers it. Otherwise use GitHub private security/support reporting channels. No project-specific private maintainer inbox has been verified. Report the affected file/commit, reproduction conditions, and risk without publishing sensitive exploitation details.

Sandbox CI must use the minimum required read-only token. No sandbox workflow should have write access to the main S.T.A.R.-Labs repository, access to upstream data stores, signing/deployment keys, or privileged publication credentials.

Issues in theoretical correctness should generally be reported as sandbox refutations, not security vulnerabilities. Security reports are handled separately from scientific review.
