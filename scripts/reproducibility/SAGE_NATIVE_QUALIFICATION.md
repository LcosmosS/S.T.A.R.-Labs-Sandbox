# Optional native Sage arithmetic smoke — status NOT_RUN

This is a **manual opt-in**, non-publishing, read-only cross-engine control for the pinned Cremona ecdata catalogue, not a rerun of ACSC/ECC/GLMPCT and not an independent researcher review.

## Immutable runtime design

The image `sagemath/sagemath@sha256:310dfe23fc786f3a5a06a7b0387c60201ec79b32c0db941b7624505ee5edb565` is the Docker Hub published **manifest-index digest** (Sage 10.10 lineage; linux/amd64 manifest `sha256:4562582e9da21605ce1507932effb548d44888ed9e35ec768616049e6776391d`), observed from Docker Hub on 2026-10-19. See https://hub.docker.com/layers/sagemath/sagemath/latest/images/sha256-4562582e9da21605ce1507932effb548d44888ed9e35ec768616049e6776391d . The SHA-qualified reference, not the mutable `latest` tag, is used for every actual run.

Workflow `.github/workflows/sage-native-arithmetic.yml` must be deliberately dispatched by an authorized repo operator; it does **not** run on pull requests. It downloads an immutable Git SHA source over TLS and fails on wrong source SHA-256, length or row count. The container has no network access, no mutable `pip install`, read-only source mounts and fixed CPU/memory limits. Selected controls run Sage's independently implemented `EllipticCurve(QQ,...).discriminant()`, `.conductor()`, and `.j_invariant()` on two canonically selected catalogue curves for each conductor in [11,26,37,38,50,54,57,58]. This tests **16 native curves**, not all 64,687.

## Receipt and interpretation

The receipt states PASS or FAIL, image digest, runner commit, source SHA, sample labels and exact arithmetic values. Image pull/acquisition errors fail the job and leave an explicit incomplete/failure artifact where feasible. `sage-native-arithmetic` remains **NOT_RUN** until a real completed workflow run ID and artifact link are recorded; a green PR check means only the workflow syntax, security scanner or repo policy succeeded.

This one narrow digest-qualified smoke **does not qualify** the inherited `sage-notebooks` suite, legacy requirements.txt, native `eclib` compilation, or all analytic-rank calculations. The full P0 resource and environment discrepancies remain registered in issue #27.
