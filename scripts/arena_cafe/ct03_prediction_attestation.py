"""CT-03: signed runner evidence -> exact locked OWN M prediction (NO truth).

This binding does not accept unsigned 'verification reports' from a producer.
Each bundle is reverified from its detached signature, externally pinned key,
original native command, candidate/receipt and byte-exact CSV/log files.
D and B require their own future original-runner attestors; they never get a
false PASS through this M-only adapter. M revisions require a distinct signed
revision execution contract (not yet available): fail closed, no topology hack.

Success means byte correspondence to an independently *claimed* runner record.
It does not certify external key custody, physical solver authenticity, G2, an
actual forecast or permission to read withheld t6/t8.
"""
from __future__ import annotations

from scripts.arena_cafe.ct_feedback_bridge import require
from scripts.arena_cafe.ct03_prospective_lock import verify_locked
from scripts.arena_cafe.ct03_execution_boundary import verify_runner, sha, exact

SCHEMA = "igc-ct03-signed-m-prediction-links/1.0"

FIELDS = ("witness", "trust_registry", "public_key", "producer_root",
          "manifest", "parent", "receipt", "modelica_file", "script_file",
          "csv_file", "solver_log")


def bind_signed_m_initial(lock, bundles):
    """No signed links, all-failure fixture, or untrusted output is a release."""
    verify_locked(lock)
    require(type(bundles) is list, "CT03_PROOF_BUNDLES_LIST_REQUIRED")
    require(len(bundles) <= 21, "CT03_PROOF_EXCEEDS_PRESCRIBED_CEILING")
    expected = {}
    for row in lock["rows"]:
        for phase in ("initial", "final"):
            state = row[phase]
            if state["status"] != "PREDICTED":
                continue
            require(row["arm"] == "M",
                    "CT03_PROOF_D_OR_B_NEEDS_SEPARATE_ORIGINAL_ATTESTOR")
            # A ratified M model reuses exactly its initial file and
            # independent witness; no new physical run is counted.
            if phase == "final" and state == row["initial"]:
                continue
            require(phase == "initial",
                    "CT03_PROOF_REVISED_M_NEEDS_DISTINCT_SIGNED_REVISION_RUNNER")
            key = (row["arm"], row["candidate_id"], row["parent_hash"])
            require(key not in expected, "CT03_PROOF_AMBIGUOUS_PREDICTION_SLOT")
            expected[key] = state
    require(expected, "CT03_PROOF_NO_PREDICTIONS_TO_LINK")
    require(len(bundles) == len(expected),
            "CT03_PROOF_MISSING_OR_EXTRA_SIGNED_EXECUTION")
    accepted = {}
    for package in bundles:
        exact(package, FIELDS, "CT03_PROOF_BUNDLE_MISSING_INPUTS")
        report = verify_runner(
            witness=package["witness"],
            trust_registry=package["trust_registry"],
            public_key=package["public_key"],
            producer_root=package["producer_root"],
            manifest=package["manifest"], parent=package["parent"],
            receipt=package["receipt"], modelica_file=package["modelica_file"],
            script_file=package["script_file"], csv_file=package["csv_file"],
            solver_log=package["solver_log"])
        key = ("M", report["candidate_id"], report["parent_hash"])
        require(key in expected and key not in accepted,
                "CT03_PROOF_WRONG_OR_DUPLICATE_CANDIDATE")
        state = expected[key]
        require(report["world_public_id"] == lock["world_public_id"] and
                report["round_kind"] == "initial" and
                state["native_sha256"] == report["native_sha256"] and
                state["trace_sha256"] == report["trace_sha256"] and
                state["receipt_sha256"] == report["receipt_sha256"],
                "CT03_PROOF_SIGNED_TRACE_PARENT_OR_WORLD_DIFFERS_FROM_LOCK")
        accepted[key] = {
            "candidate_id": report["candidate_id"],
            "parent_hash": report["parent_hash"],
            "signed_statement_sha256": report["signed_statement_sha256"],
            "authority_id": report["authority_id"],
            "native_sha256": report["native_sha256"],
            "trace_sha256": report["trace_sha256"],
            "receipt_sha256": report["receipt_sha256"],
        }
    require(set(accepted) == set(expected),
            "CT03_PROOF_MISSING_OR_EXTRA_SIGNED_EXECUTION")
    return {
        "schema": SCHEMA,
        "status": "M_INITIAL_PREDICTIONS_SIGNED_BYTE_LINKS_MATCH_NOT_G2",
        "lock_sha256": lock["lock_sha256"],
        "linked_original_m_initial_count": len(accepted),
        "links": sorted(accepted.values(), key=lambda x: x["candidate_id"]),
        "cryptographic_byte_match": True,
        "independent_runner_operator_verified": False,
        "authentic_solver_execution_proven": False,
        "scientific_g2_granted": False,
        "reserved_truth_opened": False,
        "evaluator_reveal_authorized": False,
        "provider_calls": 0, "new_omc": 0,
    }
