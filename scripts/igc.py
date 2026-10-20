"""Small F1a journal CLI used by GitHub Actions synthetic fixtures."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from scripts.ledger import Ledger, LedgerError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATION = ROOT / "migrations" / "0001_ledger.sql"


def _ledger(args: argparse.Namespace) -> Ledger:
    return Ledger(args.database, args.migration)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="igc")
    commands = parser.add_subparsers(dest="command", required=True)
    ledger_parser = commands.add_parser("ledger", help="append and query the local journal")
    actions = ledger_parser.add_subparsers(dest="ledger_action", required=True)

    append = actions.add_parser("append", help="append one immutable entity revision")
    append.add_argument("--database", required=True)
    append.add_argument("--migration", type=Path, default=DEFAULT_MIGRATION)
    append.add_argument("--entity-id", required=True)
    append.add_argument("--entity-type", required=True)
    append.add_argument("--case-id", required=True)
    append.add_argument("--actor-id", required=True)
    append.add_argument("--idempotency-key", required=True)
    append.add_argument("--payload-file", required=True, type=Path)
    append.add_argument("--recorded-at", required=True)
    append.add_argument("--created-at", required=True)
    append.add_argument("--valid-from")
    append.add_argument("--valid-to")
    append.add_argument("--occurred-at")
    append.add_argument("--schema-version", default="0.1.0")
    append.add_argument("--access-policy", default="case-private")

    show = actions.add_parser("show", help="query the latest known revisions at a system-time cut")
    show.add_argument("--database", required=True)
    show.add_argument("--migration", type=Path, default=DEFAULT_MIGRATION)
    show.add_argument("--case-id", required=True)
    show.add_argument("--as-known-at", required=True)
    show.add_argument("--valid-start")
    show.add_argument("--valid-end")

    verify = actions.add_parser("verify", help="verify one revision digest")
    verify.add_argument("--database", required=True)
    verify.add_argument("--migration", type=Path, default=DEFAULT_MIGRATION)
    verify.add_argument("--entity-id", required=True)
    verify.add_argument("--revision", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        ledger = _ledger(args)
        if args.ledger_action == "append":
            payload = json.loads(args.payload_file.read_text(encoding="utf-8"))
            revision = ledger.append_revision(
                entity_id=args.entity_id,
                entity_type=args.entity_type,
                case_id=args.case_id,
                actor_id=args.actor_id,
                idempotency_key=args.idempotency_key,
                payload=payload,
                recorded_at=args.recorded_at,
                created_at=args.created_at,
                valid_from=args.valid_from,
                valid_to=args.valid_to,
                occurred_at=args.occurred_at,
                schema_version=args.schema_version,
                access_policy=args.access_policy,
            )
            print(json.dumps(asdict(revision), ensure_ascii=False, sort_keys=True))
            return 0
        if args.ledger_action == "show":
            if bool(args.valid_start) != bool(args.valid_end):
                raise LedgerError("--valid-start and --valid-end must be supplied together")
            valid_during = (args.valid_start, args.valid_end) if args.valid_start else None
            revisions = ledger.snapshot(
                case_id=args.case_id,
                as_known_at=args.as_known_at,
                valid_during=valid_during,
            )
            print(json.dumps([asdict(item) for item in revisions], ensure_ascii=False, sort_keys=True))
            return 0
        if args.ledger_action == "verify":
            valid = ledger.verify_integrity(entity_id=args.entity_id, revision=args.revision)
            print(json.dumps({"entity_id": args.entity_id, "revision": args.revision, "integrity_valid": valid}))
            return 0 if valid else 1
    except (LedgerError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 2
    parser.error("unsupported ledger action")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
