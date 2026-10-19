# Pinned upstream code snapshot — sandbox only

The Python files under `src/` are byte-for-byte snapshots from [S.T.A.R.-Labs](https://github.com/LcosmosS/S.T.A.R.-Labs) at commit [`51927a9b396cdfa880f3128440db4715acdec8dc`](https://github.com/LcosmosS/S.T.A.R.-Labs/commit/51927a9b396cdfa880f3128440db4715acdec8dc). The exact source Git blob hashes and paths are recorded in [MANIFEST.json](MANIFEST.json).

**This is a software convenience, not a scientific endorsement.** No upstream experiment registry, controlled-execution tool, preregistration, review gate, evidence record, release pipeline, data corpus or independent-review approval has been cloned.

Available: arithmetic projection, seeded Gaussian null generation, symbolic FLRW cosmology helper, persistence homology (Ripser/GUDHI optional), and survey column schema checks. These are *candidate utilities* subject to direct verification, unit tests and adversarial analysis. In particular, coordinate scaling choices are phenomenological, not derived laws.

To import from an optional environment at repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install numpy pandas scipy sympy
PYTHONPATH=scripts/playground/upstream_snapshot python3 -c "from src.acsc.projection import project; print(project([{'delta':-37,'conductor':37,'rank':1}]))"
```

For persistent homology also install `ripser` or `gudhi`. Never install packages or run research code merely to pass the sandbox integrity CI; sandbox CI uses only standard-library structural checks. Upstream source code may contain analytical assumptions or bugs; results must be separately tested and labeled exploratory.

The source modules remain untouched here. To experiment with modified algorithms, copy them into an `experiments/SBX-...` folder and document precisely what changed. Do not modify the pinned snapshot silently.

Original upstream and sandbox code: MIT licensed. See both repositories' `LICENSE` files.
