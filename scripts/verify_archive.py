"""Verify historical bytes and segregate new work; never execute research code."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

BASELINE = "a48ee3c41d17305530d65616c16c158f04e502d8"
ROOT = Path(__file__).resolve().parents[1]

def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def safe_file(root, relative):
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
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def git_tree(root, revision):
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
    manifest = load(safe_file(root, "sandbox/archive-manifest.json"))
    require(manifest["baseline_commit"] == BASELINE, "archival baseline must not change")
    tree = git_tree(root, BASELINE)
    entries = manifest["files"]
    require(len(entries) == len(tree), "archive inventory count mismatch")
    seen = set()
    for entry in entries:
        path = entry["original_path"]
        require(path not in seen and path in tree, f"duplicate/unknown archival path: {path}")
        seen.add(path)
        mode, oid = tree[path]
        require((entry["git_mode"], entry["git_blob"]) == (mode, oid), f"Git binding changed: {path}")
        preserved = "archive/README.pre-sandbox.md" if path == "README.md" else path
        require(entry["preserved_path"] == preserved, f"unexpected relocation: {path}")
        data = safe_file(root, preserved).read_bytes()
        require(len(data) == entry["size_bytes"], f"archival size mismatch: {path}")
        require(hashlib.sha256(data).hexdigest() == entry["sha256"], f"archival digest mismatch: {path}")
        git_blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        require(git_blob == oid, f"archival bytes differ from original Git blob: {path}")
    return len(entries)


ROOT_FILES = {"README.md", "DISCLAIMER.md", "CONTRIBUTING.md", "GOVERNANCE.md",
              "MODERATION.md", "SECURITY.md", "NOTICE.md", "SANDBOX_POLICY.md",
              "UPSTREAM.md", ".gitignore"}
AUDIT_FILES = {"archive-manifest.json", "upstream-reference.json", "SETTINGS.md", "SETUP_AUDIT.md",
               "admission-ruleset.proposed.json", "governance-ruleset.proposed.json"}

def check_layout(root):
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
                   or (len(parts) == 2 and parts[0] == "sandbox" and parts[1] in AUDIT_FILES))
        require(allowed, f"new artifact outside experiments/governance paths: {path}")
        safe_file(root, path)

def check_all(root):
    subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"],
                   cwd=root, check=True, capture_output=True)
    count = check_archive(root)
    check_layout(root)
    return {"archive_files": count, "research_executed": False,
            "result": "archive_integrity_and_layout_only"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(check_all(args.root.resolve()), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Archive check failed: {error}", file=sys.stderr)
        sys.exit(1)
