"""Independent sandbox-only first-principles permutation workbench.

This stdlib-only module is intentionally *not* the controlled experiment runner.
It makes no claims about proof, physical correspondence, or upstream approval.
Never run it automatically on arbitrary submitted experiment code in CI.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import random
import sys

AXES = {"log10_abs_delta", "log10_conductor", "rank", "rank_saturation"}
STUDY_FIELDS = {
    "schema_version", "id", "scope", "status", "study_type",
    "scientific_question", "axioms", "hypothesis", "rival", "falsifier",
    "input", "mapping", "response", "null", "limitations",
}
INPUT_FIELDS = {"kind", "path", "origin"}
MAPPING_FIELDS = {"axis", "scale", "coordinate_unit"}
NULL_FIELDS = {"method", "n_permutations", "seed"}


def require(condition: bool, message: str) -> None:
    """Raise a descriptive error rather than silently repairing invalid data."""
    if not condition:
        raise ValueError(message)


def unique_pairs(pairs):
    """Reject duplicate JSON keys so no study parameter has two interpretations."""
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path):
    """Read a UTF-8 JSON file while disallowing duplicate object keys."""
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def declared_text(value, label: str) -> str:
    """Require meaningful, explicit scientific descriptions."""
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value.strip()


def regular_local_file(root: Path, relative: str) -> Path:
    """Resolve only nonsymlink files inside the experiment's own directory."""
    declared_text(relative, "input.path")
    rel = PurePosixPath(relative)
    require(not rel.is_absolute() and ".." not in rel.parts and
            str(rel) == relative and "\\" not in relative,
            "input.path must be a safe relative path")
    candidate = root.joinpath(*rel.parts)
    require(candidate.resolve().is_relative_to(root.resolve()),
            "input.path escapes the experiment directory")
    require(candidate.is_file() and not candidate.is_symlink(),
            "input.path must name an existing nonsymlink file")
    require(not any(p.is_symlink() for p in candidate.parents
                    if p == root or p.is_relative_to(root)),
            "input.path cannot traverse a symlink")
    return candidate


def finite_number(raw, field: str) -> float:
    """Reject missing, infinite, NaN and nonnumeric measurements."""
    try:
        number = float(raw)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{field} is not numeric: {raw!r}") from error
    require(math.isfinite(number), f"{field} must be finite (no silent row drops)")
    return number


def axis_value(row: dict, name: str, scale: float) -> float:
    """Evaluate one declared dimensionless mapping coordinate on a full row."""
    delta = finite_number(row["delta"], "delta")
    conductor = finite_number(row["conductor"], "conductor")
    rank = finite_number(row["rank"], "rank")
    require(delta != 0, "delta must not be zero")
    require(conductor > 0, "conductor must be positive")
    require(rank >= 0 and rank.is_integer(), "rank must be a nonnegative integer")
    if name == "log10_abs_delta":
        return math.log10(abs(delta))
    if name == "log10_conductor":
        return math.log10(conductor)
    if name == "rank":
        return rank
    return 2.0 * math.atan(rank / scale) / math.pi


def pearson(x, y) -> float:
    """Compute Pearson r with nonzero finite variances and no imputation."""
    require(len(x) == len(y) and len(x) >= 4, "need at least four paired rows")
    mx = math.fsum(x) / len(x)
    my = math.fsum(y) / len(y)
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    denx = math.fsum(a * a for a in dx)
    deny = math.fsum(b * b for b in dy)
    require(denx > 0 and deny > 0, "Pearson correlation undefined for constant values")
    r = math.fsum(a * b for a, b in zip(dx, dy)) / math.sqrt(denx * deny)
    require(math.isfinite(r), "Pearson correlation is not finite")
    return max(-1.0, min(1.0, r))


def check_study(spec: dict) -> None:
    """Validate schema, scientific nonclaims, and the exact permutation contract."""
    require(isinstance(spec, dict) and set(spec) == STUDY_FIELDS,
            "study.json must contain exactly the documented fields")
    require(type(spec["schema_version"]) is int and spec["schema_version"] == 1,
            "unsupported study schema")
    require(isinstance(spec["id"], str) and
            spec["id"].startswith("SBX-") and len(spec["id"]) == 13,
            "study id must have the form SBX-YYYY-NNNN")
    require(spec["scope"] == "sandbox-only" and spec["status"] == "exploratory",
            "study cannot claim upstream status or scientific verification")
    require(spec["study_type"] == "mapping_null", "unknown study type")
    for key in ("scientific_question", "hypothesis", "rival", "falsifier"):
        declared_text(spec[key], key)
    for key in ("axioms", "limitations"):
        require(isinstance(spec[key], list) and len(spec[key]) >= 1 and
                all(isinstance(x, str) and x.strip() for x in spec[key]),
                f"{key} must contain at least one nonempty statement")
    inp = spec["input"]
    require(isinstance(inp, dict) and set(inp) == INPUT_FIELDS, "invalid input contract")
    require(inp["kind"] in {"synthetic", "observed"}, "input.kind invalid")
    declared_text(inp["path"], "input.path")
    declared_text(inp["origin"], "input.origin")
    require("source unknown" not in inp["origin"].lower(),
            "input origin must be specified")
    mapping = spec["mapping"]
    require(isinstance(mapping, dict) and set(mapping) == MAPPING_FIELDS,
            "invalid mapping contract")
    require(mapping["axis"] in AXES, "unsupported arithmetic coordinate")
    scale = finite_number(mapping["scale"], "mapping.scale")
    require(scale > 0, "mapping.scale must be positive")
    require(mapping["coordinate_unit"] == "dimensionless",
            "the supplied arithmetic coordinates are dimensionless, not physical distance")
    response = spec["response"]
    require(isinstance(response, dict) and set(response) == {"column", "unit"},
            "invalid response contract")
    declared_text(response["column"], "response.column")
    declared_text(response["unit"], "response.unit")
    null = spec["null"]
    require(isinstance(null, dict) and set(null) == NULL_FIELDS, "invalid null contract")
    require(null["method"] == "permute_response", "unsupported null method")
    require(type(null["n_permutations"]) is int and
            1 <= null["n_permutations"] <= 5000,
            "n_permutations must be an integer between 1 and 5000")
    require(type(null["seed"]) is int and 0 <= null["seed"] < 2**64,
            "seed must be a nonnegative 64-bit integer")


def read_records(spec: dict, root: Path):
    """Load an unchanged local CSV, rejecting missing or malformed rows."""
    path = regular_local_file(root, spec["input"]["path"])
    data = path.read_bytes()
    require(len(data) <= 16 * 1024 * 1024, "input exceeds 16 MiB local workbench cap")
    try:
        source = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("input CSV must be UTF-8") from error
    reader = csv.DictReader(io.StringIO(source, newline=""), strict=True)
    fields = reader.fieldnames
    needed = {"delta", "conductor", "rank", spec["response"]["column"]}
    require(fields is not None and len(fields) == len(set(fields)) and
            needed.issubset(fields), "input CSV has missing or duplicated required headers")
    require(None not in fields and all(f and f.strip() for f in fields),
            "CSV header names must be nonempty")
    records = []
    for line, row in enumerate(reader, start=2):
        require(None not in row and all(value is not None for value in row.values()),
                f"malformed/missing CSV fields at line {line}")
        records.append(row)
        require(len(records) <= 10000, "local workbench row cap exceeded")
    require(len(records) >= 4, "input must contain at least four rows")
    return records, hashlib.sha256(data).hexdigest()


def run_study(spec_path: Path) -> dict:
    """Run an exploratory seeded permutation diagnostic with explicit nonclaims."""
    require(spec_path.is_file() and not spec_path.is_symlink(), "study spec not a regular file")
    spec_bytes = spec_path.read_bytes()
    spec = json.loads(spec_bytes.decode("utf-8"), object_pairs_hook=unique_pairs)
    check_study(spec)
    records, data_digest = read_records(spec, spec_path.parent)
    scale = float(spec["mapping"]["scale"])
    axis = spec["mapping"]["axis"]
    column = spec["response"]["column"]
    x = [axis_value(row, axis, scale) for row in records]
    y = [finite_number(row[column], column) for row in records]
    observed = pearson(x, y)
    seed = spec["null"]["seed"]
    n_permutations = spec["null"]["n_permutations"]
    rng = random.Random(seed)
    permutation_statistics = []
    count = 0
    for _ in range(n_permutations):
        shuffled = y.copy()
        rng.shuffle(shuffled)
        statistic = pearson(x, shuffled)
        permutation_statistics.append(statistic)
        if abs(statistic) >= abs(observed) - 1e-14:
            count += 1
    p = (count + 1) / (n_permutations + 1)
    duplicate_rows = len(records) - len({tuple(sorted(row.items())) for row in records})
    return {
        "schema_version": 1,
        "id": spec["id"],
        "scope": "sandbox-only",
        "status": "exploratory",
        "scientific_claim": False,
        "independent_review": False,
        "eligible_for_automatic_promotion": False,
        "input": {
            "kind": spec["input"]["kind"],
            "origin": spec["input"]["origin"],
            "sha256": data_digest,
            "rows_retained": len(records),
            "duplicate_rows_retained": duplicate_rows,
            "missing_data_policy": "fail_closed_no_silent_exclusion",
        },
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "mapping": spec["mapping"],
        "response": spec["response"],
        "statistic": {"name": "pearson_r", "observed": observed},
        "null": {
            "method": "unrestricted_response_permutation",
            "tail": "two-sided_absolute_pearson",
            "seed": seed,
            "n_permutations": n_permutations,
            "statistics": permutation_statistics,
            "count_as_or_more_extreme": count,
            "empirical_p_plus_one": p,
        },
        "reasoning": {
            "scientific_question": spec["scientific_question"],
            "axioms": spec["axioms"],
            "hypothesis": spec["hypothesis"],
            "rival": spec["rival"],
            "falsifier": spec["falsifier"],
            "limitations": spec["limitations"],
        },
        "interpretation": (
            "EXPLORATORY ONLY: synthetic fixtures and their permutation p-values "
            "cannot establish cosmological, arithmetic, cohomological or physical "
            "correspondence. A label-permutation null requires exchangeability "
            "and is not automatically appropriate for observational surveys."
        ),
    }


def output_path(spec_path: Path, name: str) -> Path:
    """Confine output to the experiment's runs/ directory; never modify inputs."""
    rel = PurePosixPath(name)
    require(not rel.is_absolute() and ".." not in rel.parts and
            "\\" not in name and len(rel.parts) == 2 and
            rel.parts[0] == "runs" and rel.suffix == ".json",
            "output must be a runs/<name>.json relative path")
    parent = spec_path.parent / "runs"
    require(not parent.is_symlink(), "runs directory cannot be a symlink")
    parent.mkdir(exist_ok=True)
    target = parent / rel.name
    require(not target.is_symlink(), "output must not overwrite a symlink")
    require(target.resolve().is_relative_to(spec_path.parent.resolve()),
            "output escapes experiment folder")
    return target


def main(argv=None) -> int:
    """Provide an opt-in local CLI; avoid running any code automatically in CI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path,
                        help="Path to study.json inside an SBX experiment")
    parser.add_argument("--output", default="runs/latest.json",
                        help="Relative output path runs/<name>.json")
    args = parser.parse_args(argv)
    try:
        result = run_study(args.spec.resolve())
        target = output_path(args.spec.resolve(), args.output)
        target.write_text(json.dumps(result, indent=2, sort_keys=True,
                                     allow_nan=False) + "\n", encoding="utf-8")
        print(f"SANDBOX / EXPLORATORY: wrote {target}")
        print("No research claim, theorem, independent review or upstream status inferred.")
        return 0
    except (ValueError, OSError, KeyError, TypeError, csv.Error,
            UnicodeDecodeError) as error:
        print(f"Sandbox study failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
