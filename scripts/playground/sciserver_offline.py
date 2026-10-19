"""Offline-only SciServer v0.2 entrypoint for sandbox exploration.

Source is pinned to upstream PR #111. No SciServer authentication, network
submission, arbitrary SQL execution, registry mutation or physical claim exists.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PORTS = Path(__file__).resolve().parent / "ports"


def load_policy():
    """Import the unmodified pinned policy from the isolated source snapshot."""
    if str(PORTS) not in sys.path:
        sys.path.insert(0, str(PORTS))
    from integrations.sciserver import query_policy
    return query_policy


def main(argv=None) -> int:
    """Inspect allowlisted SQL or explicitly create a local, private canary plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List fixed, validated DR18 SQL identities (no submission)")
    sub.add_parser("validate", help="Verify catalog fields and pinned SQL file bytes")
    prepare = sub.add_parser("prepare", help="Explicit opt-in LOCAL run plan (no submission)")
    prepare.add_argument("--query-id", required=True,
                         choices=("DR18-CANARY-10", "DR18-DETERMINISTIC-200K"))
    prepare.add_argument("--state-root", type=Path, default=None,
                         help="Private POSIX state root for local write-once receipts")
    options = parser.parse_args(argv)
    try:
        policy = load_policy()
        if options.command == "list":
            records = policy.list_approved_queries()
            result = {"scope": "sandbox-only", "execution": "disabled",
                      "catalog_queries": records}
        elif options.command == "validate":
            catalog = policy.load_catalog()
            result = {"scope": "sandbox-only", "execution": "disabled",
                      "remote_submission_enabled": False,
                      "catalog_sha256": catalog["catalog_sha256"],
                      "approved_query_ids": sorted(catalog["queries"])}
        else:
            from integrations.sciserver import receipts
            target = (options.state_root if options.state_root is not None
                      else receipts.DEFAULT_STATE_ROOT)
            result = policy.prepare_casjobs_run(options.query_id, state_root=target)
            if result["plan"]["remote_submission_enabled"] is not False:
                raise ValueError("Remote SciServer action forbidden in sandbox")
            result = {"scope": "sandbox-only", "execution": "disabled",
                      "local_plan_only": True, **result}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(f"SciServer offline sandbox refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
