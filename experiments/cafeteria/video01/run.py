"""Arena Café CV-01: observation-to-three-arms, no invented operational time.
Uses the existing D grammar, native Short E1 M enumerator, Buffalo request boundary,
V0 common evidence contract, ATMS and F1a ledger. No provider/solver call.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_v0_contract import (
    INPUT_SCHEMA, SUBMISSION_SCHEMA, arm_view, assert_same_evidence,
    canonical, digest, trace_event, validate_submission, validate_visible_input
)
from scripts.arena_d_v01 import topology, lint_structure
from scripts.arena_m_short_e1 import prepare as prepare_m
from scripts.arena_atms import ATMS, Rule
from scripts.ledger import Ledger

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/arena/video_barista_v0_1"
CASE = "CAF_VIDEO_01"
VIDEO_SHA = "cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5"
SOURCES = (
    "revisiones/r4_p031_estados_visuales.csv",
    "revisiones/r3_p045_lecturas_2s.csv",
)

def check(ok, code):
    if not ok:
        raise ValueError(code)

def read_csv(root, name):
    path = root / name
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    return rows, sha256(raw).hexdigest()

def construction(root=DATA):
    p031, h031 = read_csv(root, SOURCES[0])
    p045, h045 = read_csv(root, SOURCES[1])
    at = lambda rows, field, t: next((r for r in rows if int(r[field]) == t), None)
    three = at(p031, "video_s", 2888)
    three_at_end = at(p031, "video_s", 2893)
    clear = at(p031, "video_s", 2894)
    pitcher = at(p045, "video_second", 4118)
    two_cups = at(p045, "video_second", 4144)
    check(three and int(three["minimum_visible_containers_with_contents"]) == 3
          and three_at_end and int(three_at_end["minimum_visible_containers_with_contents"]) == 3,
          "P031_THREE_VISIBLE_NOT_SUPPORTED")
    check(clear and int(clear["minimum_visible_containers_with_contents"]) == 0
          and "local" in clear["level"], "P031_LOCAL_REGION_CLEAR_NOT_SUPPORTED")
    check(pitcher and pitcher["pitcher_at_wand_visible"] == "si"
          and int(pitcher["visually_mounted_cups_minimum"]) >= 1
          and pitcher["can_claim_machine_on"] == "NO",
          "P045_COPRESENCE_NOT_SUPPORTED")
    check(two_cups and int(two_cups["visually_mounted_cups_minimum"]) >= 2
          and two_cups["can_claim_machine_on"] == "NO",
          "P045_TWO_CUPS_NOT_SUPPORTED")
    check(len(p031) == 15 and len(p045) == 68, "SOURCE_ROWS_CHANGED")
    observed = [
        {"id": "F_P031_VISIBLE_CONTAINERS_3", "time_video_s": 2888,
         "observable": "minimum_visible_containers_with_contents", "lower_bound": 3,
         "unit": "containers_visible_in_local_region", "evidence": SOURCES[0] + "#video_s=2888"},
        {"id": "F_P031_REGION_CLEAR", "time_video_s": 2894,
         "observable": "local_region_visible_container_count", "value": 0,
         "unit": "containers_in_local_region_only", "evidence": SOURCES[0] + "#video_s=2894"},
        {"id": "F_P045_JAR_AND_CUP", "time_video_s": 4118,
         "observable": "pitcher_near_wand_and_mounted_cup_both_visible",
         "value": True, "unit": "visual_copresence", "evidence": SOURCES[1] + "#video_second=4118"},
        {"id": "F_P045_TWO_MOUNTED_CUPS", "time_video_s": 4144,
         "observable": "minimum_visually_mounted_cups", "lower_bound": 2,
         "unit": "visually_mounted_cups", "evidence": SOURCES[1] + "#video_second=4144"},
    ]
    evidence = {
        "case_type": "observational_physical_constraints_not_order_flow",
        "video_sha256_declared_not_rehashed": VIDEO_SHA,
        "source_csv_sha256": {SOURCES[0]: h031, SOURCES[1]: h045},
        "facts": observed,
        "non_claims": [
            "physical_clock_verified", "recording_continuity_verified",
            "pos_arrivals_known", "delivered_orders_known", "capacity_max_known",
            "steam_on_verified", "per_order_wip_identified", "employee_utilization_known",
        ]
    }
    payload = {
        "schema": INPUT_SCHEMA, "investigation_id": CASE, "round_id": "CV01_R0",
        "question": "Representar coexistencia de recipientes y recursos sin inventar flujos de pedidos",
        "construction": evidence,
        "observability": {"clock": "video_presentation_time_s",
                          "physical_clock_verified": False,
                          "recording_continuity_verified": False,
                          "observed_units": "visual_containers_and_equipment_proximity",
                          "not_equivalent_to": "accepted_order_equivalents_or_deliveries"},
        "source_snapshot_hash": digest(evidence), "iteration_limit": 1,
        "resources": {"buffalo_provider_calls_allowed": 0,
                      "modelica_runs_allowed": 0, "allowed_outputs": "native_preflight_only"},
    }
    validate_visible_input(payload)
    views = [arm_view(payload, arm) for arm in ("D", "B", "M")]
    assert_same_evidence(views)
    return payload, views

def submission(view, native, *, version, status, unknowns):
    s = {"schema": SUBMISSION_SCHEMA, "arm_id": view["arm_id"],
         "round_id": view["input"]["round_id"], "iteration": 0,
         "parent_revision_id": None, "native_artifact_sha256": digest(native),
         "method_version": version, "hypothesis_ids": [],
         "status": status, "unknowns": unknowns, "assumption_ids": [],
         "evidence_refs": [view["input"]["source_snapshot_hash"]],
         "notes": "Sin ajuste, predicción, validación física ni propuesta atribuida a otra rama"}
    validate_submission(view, s)
    event = trace_event(
        arm_id=view["arm_id"], round_id=view["input"]["round_id"],
        event_type="ABSTENTION_RECORDED", iteration=0,
        source_hash=view["input_hash"], payload_hash=digest(s))
    return s, event

def shared_atms():
    facts = {f["id"] for f in construction()[0]["construction"]["facts"]}
    assumption = "A_REGION_REPRESENTS_COMPLETE_SERVICE_BUFFER"
    a = ATMS(
        assumptions={assumption}, facts=facts,
        justifications=[
            Rule("R_ROI_FLOOR", ("F_P031_VISIBLE_CONTAINERS_3",),
                 "LOCAL_REGION_ACCOMMODATES_AT_LEAST_3"),
            Rule("R_BUFFER_HYPOTHESIS", ("LOCAL_REGION_ACCOMMODATES_AT_LEAST_3", assumption),
                 "SERVICE_BUFFER_ACCOMMODATES_AT_LEAST_3_CONDITIONAL"),
            Rule("R_COPRESENCE", ("F_P045_JAR_AND_CUP",),
                 "CUP_VISIBLE_WHILE_PITCHER_NEAR_WAND"),
        ], nogoods=set())
    return {
        "engine": a.to_report(),
        "observed_local_lower_bound": a.explain("LOCAL_REGION_ACCOMMODATES_AT_LEAST_3"),
        "conditional_buffer_claim": a.explain("SERVICE_BUFFER_ACCOMMODATES_AT_LEAST_3_CONDITIONAL"),
        "note": "ATMS tracks logical support of annotated observations, not empirical truth; "
                "the service-buffer hypothesis is conditional on an unverified assumption.",
    }

def execute(root=DATA, *, out=None):
    common, views = construction(root)
    v = {q["arm_id"]: q for q in views}

    d_structures = []
    for count in (1, 2):
        t = topology(count, False)  # Actual native D grammar, NOT a video-fitted model.
        d_structures.append({"topology": t, "lint": lint_structure(t)})
    d_native = {
        "kind": "D_NATIVE_GRAMMAR_COMPATIBILITY_ONLY", "grammars": d_structures,
        "not_a_candidate_for_video": True,
        "reason": "D accepted/delivered order unit cannot be bound to visually counted containers",
        "simulation": "NOT_RUN"}
    d_submission, d_event = submission(v["D"], d_native,
        version="generic-conservative-chain-search/0.1",
        status="PARTIAL",
        unknowns=["OBSERVATION_TO_ORDER_FLOW_MAPPING", "ARRIVALS", "DELIVERIES", "RATE_PARAMETERS"])

    b_native = {
        "kind": "B_BUFFALO_NATIVE_REQUEST_STAGED_NOT_SENT",
        "shared_evidence_hash": v["B"]["input_hash"],
        "question": common["question"],
        "data": common["construction"]["facts"],
        "requested_output": "Buffalo native mechanism or explicit abstention with identification limits",
        "other_arm_outputs_included": False,
        "provider_calls_consumed": 0,
        "provider_result": None, "simulation": "NOT_RUN"}
    b_submission, b_event = submission(v["B"], b_native,
        version="buffalo-sd-ai-native-not-invoked/0.1", status="BLOCKED",
        unknowns=["NATIVE_BUFFALO_PROPOSAL_NOT_REQUESTED", "ARRIVALS", "DELIVERIES"])

    m_native, m_submission, m_event = prepare_m(
        common, ROOT / "experiments/e1/registry.base.json")
    check(m_submission["status"] == "PARTIAL" and not m_submission["hypothesis_ids"]
          and m_native["candidate_origin"] == "PORT_ENUMERATION_NOT_OBSERVATIONAL_INFERENCE",
          "M_NATIVE_STATUS_CHANGED")
    check(m_native["common_stimulus_translation"] == "NOT_IMPLEMENTED",
          "M_VISUAL_ADAPTER_SILENTLY_AVAILABLE")
    outputs = {
        "D": {"native": d_native, "submission": d_submission, "event": d_event},
        "B": {"native": b_native, "submission": b_submission, "event": b_event},
        "M": {"native": m_native, "submission": m_submission, "event": m_event},
    }
    check(all(q["submission"]["hypothesis_ids"] == [] for q in outputs.values()),
          "UNSUPPORTED_HYPOTHESIS_CLAIM")
    check(all(q["submission"]["status"] in ("PARTIAL", "BLOCKED")
              for q in outputs.values()), "UNEXPECTED_SUCCESS")
    memory = shared_atms()
    report = {
        "schema": "igc-arena-cafe-video-observational-3arm/0.1", "case": CASE,
        "common_input_hash": digest(common), "construction_source_hash": common["source_snapshot_hash"],
        "arm_statuses": {k: v["submission"]["status"] for k, v in outputs.items()},
        "three_native_paths": {"D": "arena_d_v01.topology/lint_structure",
                               "B": "request staged only, provider not called",
                               "M": "arena_m_short_e1.prepare/Short E1 native composer"},
        "D_native_structures_examined": len(d_structures),
        "M_native_engineering_graphs_enumerated": m_native["candidate_count"],
        "native_hypotheses_selected": 0,
        "modelica_runs": 0, "provider_calls": 0,
        "physical_results": [
            "At t_video=2888 at least three visible content-containing vessels in specified ROI.",
            "At t_video=4118 a pitcher near wand and one mounted cup are jointly visible.",
            "At t_video=4144 at least two mounted cups are jointly visible.",
            "ROI appears cleared at 2894; NOT shop inventory=0 or customer delivery.",
        ],
        "identifiability": "NOT_IDENTIFIABLE_FROM_VISUAL_CONTAINERS",
        "physical_clock_verified": False, "independent_review": False,
        "memory_projection": "ATMS_LOGICAL_SUPPORT_INCLUDED; F1A_LOCAL_LEDGER_IF_OUT_ENABLED",
        "interpretation": "Three real native boundaries exercised; no three competing quantitative predictions.",
    }
    if out is not None:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=False)
        (out / "common_input.json").write_bytes(canonical(common) + b"\n")
        for arm, item in outputs.items():
            (out / (arm + "_native_and_submission.json")).write_bytes(canonical(item) + b"\n")
        (out / "atms_support.json").write_bytes(canonical(memory) + b"\n")
        db = Ledger(out / "case_ledger.sqlite", ROOT / "migrations/0001_ledger.sql")
        stamp = datetime.now(timezone.utc).isoformat()
        for arm, item in outputs.items():
            db.append_revision(
                entity_id=f"CV01-{arm}-submission", entity_type="ArenaArmSubmission",
                case_id=CASE, actor_id="arena-cv01-runner",
                idempotency_key=f"{CASE}-{arm}-" + digest(item["submission"]),
                payload={"submission": item["submission"], "event": item["event"]},
                recorded_at=stamp, created_at=stamp,
                access_policy="lane:" + arm)
        report["local_ledger_revisions"] = 3
        (out / "report.json").write_bytes(canonical(report) + b"\n")
    return report, common, outputs, memory

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    summary, _, _, _ = execute(out=Path(args.out))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
