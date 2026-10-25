"""Private evaluator-side custody store with atomic one-use holdout consumption.

For genuine independence run this code with SQLite/db/holdout under a different
principal/permission boundary than model constructors. Never upload DB, nonce,
reserve or scoring report into public GitHub Actions artifacts.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import sqlite3
from typing import Any

from .arena_round import (RoundError, hash_obj, canonical, verify_lock,
                          score_locked, numbers)


SCHEMA = "igc-arena-custodian/0.1"


class CustodyError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _open(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db), timeout=15, isolation_level=None)
    c.execute("PRAGMA busy_timeout=15000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=FULL")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS registered_reserve(
          reserve_id TEXT PRIMARY KEY,
          round_id TEXT NOT NULL UNIQUE,
          private_salt TEXT NOT NULL,
          sealed_hash TEXT NOT NULL,
          commitment TEXT NOT NULL UNIQUE,
          registered_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS consumed_reserve(
          reserve_id TEXT PRIMARY KEY REFERENCES registered_reserve(reserve_id),
          round_id TEXT NOT NULL,
          lock_hash TEXT NOT NULL,
          report_hash TEXT NOT NULL,
          report_json TEXT NOT NULL,
          consumed_at TEXT NOT NULL
        );
    """)
    return c


def _validate_reserve(reserve: dict) -> None:
    for key in ("reserve_id", "round_id", "observable_id", "unit"):
        if not isinstance(reserve.get(key), str) or not reserve[key]:
            raise CustodyError(f"reserved {key} missing")
    times = numbers(reserve.get("times"))
    values = numbers(reserve.get("values"))
    if len(times) != len(values) or any(y <= x for x, y in zip(times,times[1:])):
        raise CustodyError("invalid reserved time series")


def _commit(reserve: dict, salt: str) -> str:
    return hash_obj({"domain":"ARENA_PRIVATE_RESERVE_V1",
                     "nonce":salt, "reserve":reserve})


def register(db: Path, reserve: dict, *, salt: str | None = None) -> dict:
    """Register before producer execution. Only commitment leaves custodian."""
    _validate_reserve(reserve)
    # Explicit salt is for deterministically testing only.
    salt = salt if salt is not None else secrets.token_hex(32)
    if not isinstance(salt,str) or len(salt) != 64 or any(ch not in "0123456789abcdef" for ch in salt):
        raise CustodyError("salt must be 32 private random bytes as hex")
    commitment = _commit(reserve,salt)
    with _open(db) as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO registered_reserve"
                " (reserve_id,round_id,private_salt,sealed_hash,commitment,registered_at)"
                " VALUES (?,?,?,?,?,?)",
                (reserve["reserve_id"],reserve["round_id"],salt,hash_obj(reserve),
                 commitment,_now()))
            conn.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            conn.execute("ROLLBACK")
            raise CustodyError("RESERVE_ALREADY_REGISTERED") from exc
    return {"schema":SCHEMA, "status":"PREREGISTERED_PRIVATE_COMMITMENT",
            "round_id":reserve["round_id"],"reserve_id":reserve["reserve_id"],
            "commitment":commitment,
            "blindness":"REQUIRES_EXTERNAL_ACCESS_CONTROL",
            "no_gold_in_public_commitment":True,
            "timing_attestation":"LOCAL_CLOCK_ONLY_NOT_INDEPENDENT"}


def consume(db: Path, lock: dict, reserve: dict, *, custodian_ref: str) -> dict:
    """One atomic commit across evaluators sharing a private SQLite database."""
    verify_lock(lock)
    _validate_reserve(reserve)
    if not isinstance(custodian_ref,str) or not custodian_ref:
        raise CustodyError("custodian identifier required")
    conn = _open(db)
    try:
        conn.execute("BEGIN IMMEDIATE")
        record = conn.execute(
            "SELECT round_id,private_salt,sealed_hash,commitment "
            "FROM registered_reserve WHERE reserve_id=?",
            (reserve["reserve_id"],)).fetchone()
        if record is None:
            raise CustodyError("RESERVE_NOT_PREREGISTERED")
        round_id, private_salt, sealed_hash, commitment = record
        if (round_id != lock["round_id"] or round_id != reserve["round_id"]
            or sealed_hash != hash_obj(reserve)
            or commitment != _commit(reserve,private_salt)):
            raise CustodyError("RESERVE_TAMPERED_OR_WRONG_ROUND")
        existing = conn.execute(
            "SELECT 1 FROM consumed_reserve WHERE reserve_id=?",
            (reserve["reserve_id"],)).fetchone()
        if existing:
            raise CustodyError("RESERVE_ALREADY_CONSUMED")
        report = score_locked(lock,reserve,custodian_ref=custodian_ref)
        conn.execute(
            "INSERT INTO consumed_reserve"
            " (reserve_id,round_id,lock_hash,report_hash,report_json,consumed_at)"
            " VALUES (?,?,?,?,?,?)",
            (reserve["reserve_id"],round_id,lock["lock_hash"],
             report["report_hash"],canonical(report).decode(),_now()))
        conn.execute("COMMIT")
        return report
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def read_receipt(db: Path, reserve_id: str) -> dict:
    """Private-only receipt. Do not serve this from a public workflow."""
    with _open(db) as conn:
        record = conn.execute(
            "SELECT round_id,lock_hash,report_hash,consumed_at "
            "FROM consumed_reserve WHERE reserve_id=?",(reserve_id,)).fetchone()
    if not record:
        raise CustodyError("UNKNOWN_OR_UNCONSUMED_RESERVE")
    return {"schema":SCHEMA, "status":"HOLDOUT_CONSUMED",
            "reserve_id":reserve_id, "round_id":record[0],
            "lock_hash":record[1], "report_hash":record[2],
            "consumed_at":record[3]}


def main() -> int:
    p=argparse.ArgumentParser(description="Private Arena evaluator, do not run in public CI")
    sub=p.add_subparsers(dest="action",required=True)
    init=sub.add_parser("register")
    init.add_argument("--db",type=Path,required=True)
    init.add_argument("--reserve",type=Path,required=True)
    init.add_argument("--out",type=Path,required=True)
    ev=sub.add_parser("consume")
    ev.add_argument("--db",type=Path,required=True)
    ev.add_argument("--reserve",type=Path,required=True)
    ev.add_argument("--lock",type=Path,required=True)
    ev.add_argument("--custodian-ref",required=True)
    ev.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    read=lambda x:json.loads(x.read_text(encoding="utf-8"))
    if args.action=="register":
        output=register(args.db,read(args.reserve))
    else:
        output=consume(args.db,read(args.lock),read(args.reserve),
                       custodian_ref=args.custodian_ref)
    from .arena_round import exclusive_json
    exclusive_json(args.out,output)
    print(json.dumps({"status":output["status"],"round_id":output["round_id"]}))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
