"""CT-03 evaluator-only preflight; NO HELD-OUT TRUTH REVEAL OR SCORE.

The archive signature is checked BEFORE any private world file is opened.
Private world is required outside the producer workspace. Checks public
commitment, private world manifest and exact prepared Modelica/command bytes,
but DOES NOT certify runner independence, OS ACLs, empirical G2 or forecasts.
There is deliberately no function or CLI option to read reserved t6/t8 values.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.ct03_public import PUBLIC_INPUT
from scripts.arena_cafe.ct03_world_custody import SCHEMA as PRIVATE_SCHEMA
from scripts.arena_cafe.ct03_execution_boundary import (
    disjoint, verify_archive, sha_bytes,
)
from scripts.arena_cafe.ct_feedback_bridge import require

SCHEMA = "igc-ct03-evaluator-private-preflight/1.0"


def preflight(*, lock, archive_witness, trust_registry, archive_public_key,
              producer_root, evaluator_private_dir):
    """Fail closed; do not read any private file before detached archive check."""
    archive = verify_archive(
        lock=lock, witness=archive_witness,
        trust_registry=trust_registry, public_key=archive_public_key,
        producer_root=producer_root)
    require(archive["reserved_truth_opened"] is False,
            "CT03_EVALUATOR_ARCHIVE_MUST_NOT_OPEN_TRUTH")
    private = Path(evaluator_private_dir)
    disjoint(producer_root, private, trust_registry, archive_public_key)
    require(private.is_dir(), "CT03_EVALUATOR_PRIVATE_WORKSPACE_REQUIRED")
    manifest = json.loads((private / "private-manifest.json").read_text(encoding="utf-8"))
    require(type(manifest) is dict and
            manifest.get("schema") == PRIVATE_SCHEMA and
            manifest.get("status") == "PRIVATE_SOURCE_PREPARED_NOT_SIMULATED" and
            manifest.get("actual_omc_executions") == 0 and
            manifest.get("provider_calls") == 0 and
            manifest.get("source_definition_sha256") == digest(PUBLIC_INPUT),
            "CT03_EVALUATOR_PRIVATE_WORLD_MANIFEST_UNRECOGNIZED")
    # The two public/private commitments must refer to the exact same sealed
    # manifest. No public stage-count or parameter values are returned.
    require(digest(manifest) == lock["world_commitment_sha256"] and
            manifest["world_private_config"]["world_public_id"] == lock["world_public_id"] and
            manifest["world_private_config"]["protocol_sha256"] ==
                lock["protocol_sha256"] and
            manifest["modelica_sha256"] ==
                sha_bytes((private / "private_world.mo").read_bytes()) and
            manifest["script_sha256"] ==
                sha_bytes((private / "simulate.mos").read_bytes()),
            "CT03_EVALUATOR_WORLD_OR_PROTOCOL_BYTES_DIVERGED")
    return {
        "schema": SCHEMA,
        "status": "ARCHIVED_LOCK_AND_PRIVATE_SOURCE_BOUND_NOT_READY_FOR_TRUTH_REVEAL",
        "world_public_id": lock["world_public_id"],
        "protocol_sha256": lock["protocol_sha256"],
        "lock_sha256": lock["lock_sha256"],
        "world_commitment_sha256": lock["world_commitment_sha256"],
        "archive_authority": archive["archive_authority"],
        "private_world_source_verified": True,
        "actual_world_solver_execution_verified": False,
        "independent_signer_custody_verified": False,
        "reserved_truth_opened": False,
        "score_computed": False,
        "provider_calls": 0,
        "new_omc": 0,
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("lock", "archive-witness", "trust-registry",
                 "archive-public-key", "producer-root", "evaluator-private-dir", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    require(not args.out.exists(), "CT03_EVALUATOR_REFUSE_OVERWRITE")
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    witness = json.loads(args.archive_witness.read_text(encoding="utf-8"))
    report = preflight(
        lock=lock, archive_witness=witness,
        trust_registry=args.trust_registry,
        archive_public_key=args.archive_public_key,
        producer_root=args.producer_root,
        evaluator_private_dir=args.evaluator_private_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as out:
        out.write(canonical(report).decode("utf-8") + "\n")
    print(json.dumps({"status": report["status"], "reserved_truth_opened": False,
                      "provider_calls": 0, "new_omc": 0}))


if __name__ == "__main__":
    main()
