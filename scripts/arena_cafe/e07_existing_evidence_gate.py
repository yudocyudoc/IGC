"""E07 conditional entry: bind the EXISTING F3 PM result to E02's exact public inputs.

No PM4Py, DES, OMC, provider, new data or model inference. The result is a
conditional decision for known synthetic EV-01, NOT a new PM experiment.
The F3 evaluator-only packet is not exposed as producer evidence.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from scripts.arena_v0_contract import canonical

SCHEMA = "igc-arena-e07-existing-evidence-entry/0.1"
# Byte identity of the actual historical CI #41730131596 artifact member.
F3_PIN_SHA256 = "a18116ae25ea8b3c38ec355f7108fd98c6b8fe1a34417e372fe1c7262bb38467"
F3_ORIGINAL_RUN = 41730131596
E02_NATIVE_CLOSURE_RUN = 42336183589


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _source_from_frozen_ledger(db: Path, arm: str, condition: str) -> dict:
    """Read-only access to the original evidence artifact for each D/M arm."""
    ident = f"E02-{arm}-{condition}:ARTIFACT:SOURCE"
    connection = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT payload_json FROM entity_revisions WHERE entity_id = ? "
            "AND case_id = ? ORDER BY revision DESC LIMIT 2",
            (ident, f"E02-{arm}-{condition}"),
        ).fetchall()
    finally:
        connection.close()
    _require(len(rows) == 1, "E07_FROZEN_E02_SOURCE_NOT_UNIQUE:" + ident)
    payload = json.loads(rows[0][0])
    _require(payload.get("schema") == "igc-e02-evidence-artifact/0.1"
             and payload.get("artifact_role") == "source",
             "E07_E02_PROVENANCE_NOT_SOURCE:" + ident)
    return payload["data"]


def adjudicate(original_f3_bytes: bytes, frozen_ledger: Path, b_closure: dict) -> dict:
    """Adjudicate an entry precondition, not new mining or a prediction."""
    _require(sha256(original_f3_bytes).hexdigest() == F3_PIN_SHA256,
             "E07_ORIGINAL_F3_BYTES_CHANGED")
    f3 = json.loads(original_f3_bytes)
    _require(f3.get("schema") == "igc-arena-f3-process-information-increment/0.1"
             and f3.get("scope") == "EVALUATOR_ONLY_KNOWN_SYNTHETIC_EV01"
             and f3.get("original_pm_engine") == "PM4Py.discover_dfg"
             and f3.get("same_world") is True
             and f3.get("n_cases") == 15,
             "E07_F3_NOT_THE_ORIGINAL_CONTROL")
    _require(b_closure.get("schema") == "igc-e02-b-genuine-native-g1-temporal-adjudication/0.1"
             and b_closure.get("source_live_workflow_run_id") == 42331388032
             and b_closure.get("total_e02_b_provider_attempts") == 4
             and b_closure.get("original_b_native_revision_decisions") == 0
             and b_closure.get("G2") == b_closure.get("G3") == "NOT_RUN"
             and b_closure.get("new_provider_calls") == b_closure.get("new_omc_runs") == 0,
             "E07_E02_B_CURRENT_STATUS_NOT_FROZEN")
    joins = {}
    for condition in ("O0", "O1"):
        sources = {arm: _source_from_frozen_ledger(frozen_ledger, arm, condition)
                   for arm in ("D", "M")}
        d, m = sources["D"], sources["M"]
        expected_visible = f3["public_" + condition + "_sha256"]
        b = b_closure["conditions"][condition]
        _require(d.get("condition") == m.get("condition") == condition
                 and d.get("visible_sha256") == m.get("visible_sha256") == expected_visible
                 and d.get("source_snapshot_hash") == m.get("source_snapshot_hash")
                 == b["source"].get("source_snapshot_hash")
                 and d.get("public_cutoff_minutes_exact") == m.get("public_cutoff_minutes_exact") == "10",
                 "E07_NOT_THE_SAME_O0_O1_EVENTS:" + condition)
        _require(b["source"].get("native_produced") is True
                 and b["source"].get("G2") == "NOT_RUN"
                 and b["memory"].get("status") == "REAL_NATIVE_RETURNED_G1_V02_BLOCKED_NO_SECOND_DECISION"
                 and b["memory"]["snapshots"][-1]["g2_blocked_current_native"] is True,
                 "E07_B_STATUS_INCORRECT:" + condition)
        joins[condition] = {"public_visible_sha256": expected_visible,
                            "source_snapshot_hash": d["source_snapshot_hash"],
                            "same_D_M_B_source": True}
    _require(joins["O0"]["public_visible_sha256"] != joins["O1"]["public_visible_sha256"]
             and joins["O0"]["source_snapshot_hash"] != joins["O1"]["source_snapshot_hash"],
             "E07_O0_O1_ISOLATION_FAILED")
    # Already completed by F3 over exactly these events. This is not a new DFG run.
    _require(f3["full_case_route_variants"] == 1
             and f3["repeated_stage_cases"] == 0
             and f3["full_case_route_counts"][0]["cases"] == 15
             and f3["full_dfg_14_edges_count_15_each"] is True
             and f3["B1_already_observes_order_and_per_stage_physics"] is True
             and f3["B2_already_observes_per_resource_service_periods"] is True
             and f3["PM_reveals_additional_structural_requirement_over_B1"] == "NOT_OBSERVED_IN_THIS_EV01"
             and f3["incremental_process_information_verdict"] ==
                 "NO_INCREMENTAL_ROUTE_VARIATION_OVER_B1_IN_KNOWN_EV01"
             and f3["PM_14"] == "NOT_TRIGGERED_FOR_THIS_KNOWN_CONTROL"
             and f3["same_evidence_P_ablation_per_D_B_M"] == "NOT_RUN",
             "E07_F3_NO_VARIATION_CONCLUSION_CHANGED_OR_REQUIRES_NEW_PROTOCOL")
    # Historical F3 A3=PARTIAL is a timestamped fact, not a current Buffalo status.
    _require(f3["A3"] == "PARTIAL" and f3["global_F6"] == "NOT_ADJUDICATED",
             "E07_HISTORICAL_SOURCE_STATUS_CHANGED")
    return {
        "schema": SCHEMA,
        "status": "E07_NOT_ACTIVATED_NO_INCREMENTAL_VARIATION_IN_EXISTING_EV01",
        "question": "OBSERVED_PROCESS_VARIATION_ADDS_STRUCTURAL_INFORMATION_OVER_B1_B2_SAME_EVENTS",
        "source_scope": "KNOWN_SYNTHETIC_EV01_ONLY_NOT_A_NEW_EXPERIMENT",
        "f3_original_run_id": F3_ORIGINAL_RUN,
        "f3_exact_member_sha256": "sha256:" + F3_PIN_SHA256,
        "original_f3_b1_b2_report_sha256": f3["original_f2_b1_b2_report_sha256"],
        "original_f3_pm4py_report_sha256": f3["original_pm4py_report_sha256"],
        "e02_current_b_native_closure_run_id": E02_NATIVE_CLOSURE_RUN,
        "same_public_events_verified_for_all_three_arms": joins,
        "n_cases": 15, "observed_route_variants": 1, "observed_rework_cases": 0,
        "known_B1_direct_stage_order": True,
        "known_B2_resource_periods": True,
        "new_incremental_requirement": "NOT_OBSERVED_IN_THIS_EV01",
        "pm_new_execution": False, "new_B_provider_calls": 0,
        "new_omc_or_des_runs": 0, "new_observation_events": 0,
        "e07_same_evidence_ablation": "NOT_AUTHORIZED_WITHOUT_NEW_OBSERVED_PROCESS_VARIATION",
        "e06_real_video2_source_fitness": "NOT_EVALUATED_NO_VIDEO2_WINDOWS_IN_THIS_EVIDENCE_PACKAGE",
        "e05_new_intervention": "BLOCKED_NO_ADMISSIBLE_LOCAL_ACTION_PREDICTION",
        "historical_f3_a3_is_not_current_b_status": True,
        "conclusions_not_supported": [
            "PM_HAS_NO_VALUE_IN_OTHER_PROCESS_CLASSES",
            "D_M_B_INFERRED_FULL_STAGE_ROUTE_FROM_PUBLIC_POS",
            "F4_E04_PHYSICAL_INTERVENTION_BECOMES_REPRESENTABLE",
            "E06_REAL_VIDEO2_LACKS_ROUTE_VARIATION",
        ],
        "next_plan_bound_action":
            "E06_ONLY_IF_EXISTING_VIDEO2_ANNOTATIONS_SUPPORT_A_SPECIFIC_SAME_UNIT_PROCESS_OBSERVABLE; "
            "E07_ONLY_IF_VARIATION_OBSERVED_NOT_PRESENT_IN_B1_B2_WITH_SAME_EVENTS",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--f3", required=True, type=Path)
    p.add_argument("--ledger", required=True, type=Path)
    p.add_argument("--b-report", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    _require(not a.out.exists(), "E07_REFUSE_OVERWRITE")
    output = adjudicate(a.f3.read_bytes(), a.ledger,
                        json.loads(a.b_report.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(canonical(output) + b"\n")
    print(json.dumps({"status": output["status"], "cases": output["n_cases"],
                      "new_PM": False, "new_provider_calls": 0}))


if __name__ == "__main__":
    main()