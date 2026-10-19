"""Verify historical bytes and segregate new work; never execute research code."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

BASELINE = "a48ee3c41d17305530d65616c16c158f04e502d8"
UPSTREAM_REPOSITORY = "LcosmosS/S.T.A.R.-Labs"
UPSTREAM_COMMIT = "51927a9b396cdfa880f3128440db4715acdec8dc"
ROOT = Path(__file__).resolve().parents[1]

# Frozen reference scope, independently of the proposal's mutable manifest.
EXPECTED_UPSTREAM_PATHS = frozenset({
    ".github/workflows/a01-activation-preflight.yml",
    ".github/workflows/a01_primary_evidence.yml",
    ".github/workflows/a01_release_package.yml",
    ".github/workflows/a03_preexecution_release_review.yml",
    ".github/workflows/a03_preexecution_verification.yml",
    ".github/workflows/build-image.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/independent_dataset_verification.yml",
    ".github/workflows/main.yml",
    ".github/workflows/notebooks.yml",
    ".github/workflows/observational_dataset_intake.yml",
    ".github/workflows/recovered-intake.yml",
    ".github/workflows/sciserver-approval-offline.yml",
    ".github/workflows/sciserver-v02-policy.yml",
    ".github/workflows/sky_surveys.yml",
    ".github/workflows/starmap.yml",
    ".github/workflows/test.yml",
    "README.md",
    "Contributing.md",
    "charter/RESEARCH_CHARTER_v0.2.md",
    "LICENSE",
    "SECURITY.md",
    "research/gates/ECC_RTCH_RECOVERY.md",
})

# Owner-reviewed, explicit path-only relocation authority. Source bytes and Git
# file modes remain pinned to BASELINE; no new content is authorized here.
HISTORICAL_ROOT_RELOCATIONS = frozenset({
    "Advancing the Global-to-Local Mapping Paradox Correction Theory_ An Analytical Framework.pdf",
    "analyze_coma.py",
    "analyze_phi.py",
    "Citations.pdf",
    "compute_virgo.py",
    "cosmo_scale.py",
    "entropy_cohomology.py",
    "fibonacci.py",
    "first_principals.py",
    "foundational_equivalence.py",
    "iterative_refinement.py",
    "lmfdb_crosscheck.py",
    "MyTable_Bigsby.csv",
    "normalization_validation2.py",
    "predict_coma.py",
    "recursive.py",
    "The Arithmetic–Cosmic Structure Conjecture (ACSC) (1).pdf",
    "The Entropy Cohomology Conjecture (ECC).pdf",
})


def require(condition, message):
    """Raise a descriptive validation error when a condition is false."""
    if not condition:
        raise ValueError(message)


def text(value):
    """Check that a value is nonempty textual input."""
    return isinstance(value, str) and bool(value.strip())


def safe_file(root, relative):
    """Resolve a repository-relative regular file without traversal or symlinks."""
    require(text(relative), "missing relative path")
    path = PurePosixPath(relative)
    require(
        not path.is_absolute() and ".." not in path.parts
        and str(path) == relative and "\\" not in relative,
        f"unsafe path: {relative}",
    )
    candidate = root.joinpath(*path.parts)
    require(candidate.resolve().is_relative_to(root.resolve()), f"escaped root: {relative}")
    require(
        all(not p.is_symlink() for p in [candidate, *candidate.parents] if p != root.parent),
        f"symlink not allowed: {relative}",
    )
    require(candidate.is_file(), f"missing file: {relative}")
    return candidate


def load(path):
    """Parse a JSON file while rejecting duplicate object keys."""
    def unique(pairs):
        """Build a mapping without permitting repeated JSON keys."""
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def git_tree(root, revision):
    """Read the tracked blob modes and object IDs from a Git revision."""
    output = subprocess.run(
        ["git", "ls-tree", "-r", "-z", revision], cwd=root,
        check=True, capture_output=True,
    ).stdout
    tree = {}
    for row in output.split(b"\0"):
        if not row:
            continue
        header, path = row.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        require(kind == "blob", "unexpected archival submodule/tree entry")
        tree[path.decode("utf-8")] = (mode, oid)
    return tree


def check_archive(root):
    """Match every preserved archive entry to baseline and proposed Git objects."""
    manifest = load(safe_file(root, "sandbox/archive-manifest.json"))
    require(manifest["baseline_commit"] == BASELINE, "archival baseline must not change")
    tree = git_tree(root, BASELINE)
    proposed_tree = git_tree(root, "HEAD")
    entries = manifest["files"]
    require(len(entries) == len(tree), "archive inventory count mismatch")
    seen = set()
    for entry in entries:
        path = entry["original_path"]
        require(path not in seen and path in tree, f"duplicate/unknown archival path: {path}")
        seen.add(path)
        mode, oid = tree[path]
        require((entry["git_mode"], entry["git_blob"]) == (mode, oid), f"Git binding changed: {path}")
        if path == "README.md":
            preserved = "archive/README.pre-sandbox.md"
        elif path in HISTORICAL_ROOT_RELOCATIONS:
            destination = f"historical/{path}"
            source_exists = path in proposed_tree
            destination_exists = destination in proposed_tree
            require(source_exists != destination_exists,
                    f"must preserve exactly one original or relocated path: {path}")
            preserved = destination if destination_exists else path
        else:
            preserved = path
        require(entry["preserved_path"] == preserved, f"unexpected relocation: {path}")
        # Original README is retained at archive/README.pre-sandbox.md;
        # the new README.md is intentionally allowed to change.
        require(preserved in proposed_tree, f"archival Git path missing in proposal: {preserved}")
        proposed_mode, proposed_oid = proposed_tree[preserved]
        require(proposed_mode == mode, f"archival Git mode changed: {preserved}")
        require(proposed_oid == oid, f"archival Git object changed: {preserved}")
        data = safe_file(root, preserved).read_bytes()
        require(len(data) == entry["size_bytes"], f"archival size mismatch: {path}")
        require(hashlib.sha256(data).hexdigest() == entry["sha256"], f"archival digest mismatch: {path}")
        git_blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        require(git_blob == oid, f"archival bytes differ from original Git blob: {path}")
    return len(entries)



def check_upstream_reference(root, upstream):
    """Verify each manifest binding against a checkout at a pinned upstream commit.

    The checkout is supplied by CI; no network operation or source execution
    occurs inside this validator.
    """
    manifest = load(safe_file(root, "sandbox/upstream-reference.json"))
    require(isinstance(manifest, dict), "invalid upstream reference manifest")
    require(type(manifest.get("schema_version")) is int
            and manifest["schema_version"] == 1, "upstream schema version changed")
    require(manifest.get("repository") == UPSTREAM_REPOSITORY, "upstream repository changed")
    require(manifest.get("commit") == UPSTREAM_COMMIT, "upstream pinned commit changed")
    require(manifest.get("authority") == "reference_only", "upstream authority is not reference_only")
    entries = manifest.get("files")
    require(isinstance(entries, list) and len(entries) == len(EXPECTED_UPSTREAM_PATHS),
            "upstream reference inventory count mismatch")
    actual_paths = {entry.get("path") for entry in entries if isinstance(entry, dict)}
    require(actual_paths == EXPECTED_UPSTREAM_PATHS,
            "upstream reference inventory missing or unexpected paths")
    require(upstream.is_dir() and not upstream.is_symlink(), "invalid upstream checkout")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=upstream, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    require(revision == UPSTREAM_COMMIT, "upstream checkout is not at pinned commit")
    seen = set()
    for entry in entries:
        require(isinstance(entry, dict)
                and set(entry) == {"path", "sha256", "url"},
                "invalid upstream reference entry fields")
        relative = entry["path"]
        require(text(relative) and relative not in seen,
                "duplicate or empty upstream reference path")
        seen.add(relative)
        claimed = entry["sha256"]
        require(isinstance(claimed, str) and len(claimed) == 64
                and all(c in "0123456789abcdef" for c in claimed),
                f"invalid upstream SHA-256: {relative}")
        expected_url = (
            f"https://github.com/{UPSTREAM_REPOSITORY}/blob/{UPSTREAM_COMMIT}/{relative}"
        )
        require(entry["url"] == expected_url, f"upstream URL mismatch: {relative}")
        contents = safe_file(upstream, relative).read_bytes()
        require(hashlib.sha256(contents).hexdigest() == claimed,
                f"upstream reference SHA-256 mismatch at pinned commit: {relative}")
    return len(entries)


ROOT_FILES = {"README.md", "DISCLAIMER.md", "CONTRIBUTING.md", "GOVERNANCE.md",
              "MODERATION.md", "SECURITY.md", "NOTICE.md", "SANDBOX_POLICY.md",
              "UPSTREAM.md", ".gitignore"}
AUDIT_FILES = {"archive-manifest.json", "upstream-reference.json", "SETTINGS.md", "SETUP_AUDIT.md",
               "admission-ruleset.proposed.json", "governance-ruleset.proposed.json"}

def check_layout(root):
    """Reject research files introduced outside the permitted intake layout."""
    original = git_tree(root, BASELINE)
    paths = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root, check=True, capture_output=True,
    ).stdout.decode("utf-8").split("\0")
    for path in filter(None, paths):
        if path in original:
            continue
        parts = PurePosixPath(path).parts
        allowed = (path in ROOT_FILES or parts[0] in {".github", "scripts", "tests", "schemas", "experiments"}
                   or path == "archive/README.pre-sandbox.md"
                   or path == "historical/README.md"
                   or (len(parts) == 2 and parts[0] == "historical"
                       and parts[1] in HISTORICAL_ROOT_RELOCATIONS)
                   or (len(parts) == 2 and parts[0] == "sandbox" and parts[1] in AUDIT_FILES))
        require(allowed, f"new artifact outside experiments/governance paths: {path}")
        safe_file(root, path)

def check_all(root, upstream):
    """Run ancestry, preservation, layout, and upstream-reference verification."""
    subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"],
                   cwd=root, check=True, capture_output=True)
    count = check_archive(root)
    check_layout(root)
    references = check_upstream_reference(root, upstream)
    return {"archive_files": count, "upstream_reference_files": references,
            "research_executed": False,
            "result": "archive_integrity_layout_and_upstream_reference_only"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--upstream", type=Path, required=True,
                        help="Read-only checkout of pinned upstream commit")
    args = parser.parse_args()
    try:
        print(json.dumps(check_all(args.root.resolve(), args.upstream.resolve()), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Archive check failed: {error}", file=sys.stderr)
        sys.exit(1)
