"""Execute actual native method boundaries D/M; stage B without pretending inference."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.arena_v0_contract import (
    INPUT_SCHEMA, SUBMISSION_SCHEMA, assert_same_evidence, arm_view, canonical,
    digest, trace_event, validate_submission, validate_visible_input
)
from scripts.arena_d_v01 import topology, lint_structure
from scripts.arena_m_short_e1 import prepare as short_e1_prepare
from scripts.arena_atms import ATMS, Rule
from scripts.ledger import Ledger
from experiments.cafeteria.l001.reference import execute as reference_execute, read_metrics, HERE
from experiments.cafeteria.l001.observation_operator import native_projection_gate

ROOT = Path(__file__).resolve().parents[3]

def common(reference, metrics):
    evidence={
        "case":"CAF-L001",
        "kind":"two_receptacle_observed_transfer_constraints",
        "metrics_source_sha256":reference["source_sha256"],
        "metrics":[{"id":k,**v} for k,v in sorted(metrics.items())],
        "observation_limits":reference["nonclaims"],
        "legacy_status":"UNRECONCILED_NONOVERLAPPING_BOUNDS",
    }
    payload={
        "schema":INPUT_SCHEMA, "investigation_id":"CAF_L001",
        "round_id":"L001_F01_F09_R0",
        "question":"What independent native mechanism can represent two distinct receipts under observational temporal bounds?",
        "construction":evidence,
        "observability":{
            "time_unit":"video_second_unverified",
            "material_unit":"two_visible_receptacles_in_one_lot",
            "accepted_orders_measured":False,
            "receipt_times_are_bounds_not_points":True,
        },
        "source_snapshot_hash":digest(evidence),
        "iteration_limit":1,
        "resources":{"buffalo_calls":0,"openmodelica_runs":0,"max_native_grammar_probes":2}
    }
    validate_visible_input(payload)
    views=[arm_view(payload,a) for a in ("D","B","M")]
    assert_same_evidence(views)
    return payload,{v["arm_id"]:v for v in views}

def own_submission(view,native,method,status,unknowns):
    sub={
        "schema":SUBMISSION_SCHEMA, "arm_id":view["arm_id"],
        "round_id":view["input"]["round_id"],"iteration":0,
        "parent_revision_id":None, "native_artifact_sha256":digest(native),
        "method_version":method, "hypothesis_ids":[], "status":status,
        "unknowns":unknowns, "assumption_ids":[],
        "evidence_refs":[view["input"]["source_snapshot_hash"]],
        "notes":"NATIVE_BOUNDARY_ONLY: no observed service time, no OpenModelica, no calibrated prediction",
    }
    validate_submission(view,sub)
    event=trace_event(
        arm_id=view["arm_id"],round_id=view["input"]["round_id"],
        event_type="ABSTENTION_RECORDED",iteration=0,
        source_hash=view["input_hash"],payload_hash=digest(sub))
    return sub,event

def perform():
    reference=reference_execute()
    metrics=read_metrics()
    evidence,views=common(reference,metrics)
    d_structures=[{"native":topology(n,False),"lint":lint_structure(topology(n,False))} for n in (1,2)]
    d_native={
        "method":"D_GENERIC_CONSERVATIVE_CHAIN_NATIVE",
        "structures":d_structures,
        "status":"NO_EVIDENCE_TO_PULSE_OR_SERVICE_PARAMETER_MAPPING",
        "candidate_models_for_L001":0,
        "modelica_runs":0,
    }
    ds,de=own_submission(
        views["D"],d_native,"generic-conservative-chain-search/0.1","PARTIAL",
        ["ARRIVAL_PULSE_NOT_OBSERVED","SERVICE_PARAMETERS_NOT_OBSERVED",
         "RECEPTACLE_COUNTS_NOT_EQUIVALENT_TO_DELIVERED_ORDERS"])
    b_native={
        "method":"B_BUFFALO_ORIGINAL",
        "state":"STAGED_NOT_SENT",
        "request_id":"CAF_L001_BUFFALO_NATIVE_REQUEST",
        "source_input_hash":views["B"]["input_hash"],
        "visible_constraints":evidence["construction"]["metrics"],
        "task":"Independent native hypothesis or explicit abstention for a bounded two-receptacle transfer, without D/M outputs",
        "other_arm_results_supplied":False,
        "provider_calls":0,
        "candidate_models_for_L001":0,
    }
    bs,be=own_submission(
        views["B"],b_native,"buffalo-native-request-staged/0.1","BLOCKED",
        ["PROVIDER_NOT_CALLED","NATIVE_HYPOTHESIS_NOT_AVAILABLE"])
    m_native,ms,me=short_e1_prepare(evidence,ROOT/"experiments/e1/registry.base.json")
    if ms["status"]!="PARTIAL" or ms["hypothesis_ids"] or m_native["candidate_origin"]!="PORT_ENUMERATION_NOT_OBSERVATIONAL_INFERENCE":
        raise ValueError("M_NATIVE_CANDIDATES_MISREPRESENTED")
    outputs={"D":{"native":d_native,"submission":ds,"event":de},
             "B":{"native":b_native,"submission":bs,"event":be},
             "M":{"native":m_native,"submission":ms,"event":me}}
    if set(outputs)!={"D","B","M"} or len({views[x]["input_hash"] for x in outputs})!=1:
        raise ValueError("THREE_INDEPENDENT_ARMS_REQUIRED")
    atms=ATMS(
        assumptions={"A_ASSOCIATION_OF_TWO_RECEPTACLES_WITH_ONE_LOT"},
        facts={"F04_NONZERO_RECEIPT_GAP","F07_FIRST_RECEIPT_BOUND","F08_SECOND_RECEIPT_BOUND"},
        justifications=[
            Rule("R_SEPARATED",("F04_NONZERO_RECEIPT_GAP",),"RECEIPTS_SEPARATED_IN_VIDEO"),
            Rule("R_AREA_DEPENDENT",("F07_FIRST_RECEIPT_BOUND","F08_SECOND_RECEIPT_BOUND",
                                     "A_ASSOCIATION_OF_TWO_RECEPTACLES_WITH_ONE_LOT"),
                 "F09_AREA_CONDITIONALLY_DERIVED"),
        ],
        nogoods=set())
    support={"separate_receipts":atms.explain("RECEIPTS_SEPARATED_IN_VIDEO"),
             "area_conditional":atms.explain("F09_AREA_CONDITIONALLY_DERIVED"),
             "truth_status":"NOT_DETERMINED_BY_ATMS"}
    report={
        "schema":"igc-caf-l001-three-arms-native-gate/0.1",
        "status":"NATIVE_BOUNDARIES_EXECUTED_NO_COMPETITIVE_SIMULATIONS",
        "common_input_hash":digest(evidence),
        "source_hash":reference["source_sha256"],
        "arm_status":{a:outputs[a]["submission"]["status"] for a in outputs},
        "D_native_structures_linted":len(d_structures),
        "M_short_E1_engineering_graphs_enumerated":m_native["candidate_count"],
        "B_provider_calls":0,"OpenModelica_runs":0,
        "selected_hypotheses":0, "comparison_with_physical_reference":"NOT_YET_POSSIBLE",
        "reference_case":"L001; two-receptacle bounded transfer, not café-level demand",
        "legacy_warning":"UNRECONCILED_NONOVERLAPPING_BOUNDS",
        "observation_operator_gate":"ALL_THREE_NOT_SCORABLE_UNTIL_NATIVES_PROJECT_INDIVIDUAL_RECEIPTS",
    }
    return report,reference,evidence,outputs,support

def write_artifacts(out:Path):
    if out.exists():
        raise ValueError("OUTPUT_DIRECTORY_EXISTS")
    report,ref,evidence,outputs,support=perform()
    operator_gates=native_projection_gate(outputs,evidence)
    out.mkdir(parents=True)
    for name,data in (
        ("00_reference.json",ref),("01_common_evidence.json",evidence),
        ("03_ATMS.json",support),
        ("05_observation_operator_gates.json",operator_gates),
    ):
        (out/name).write_bytes(canonical(data)+b"\n")
    ledger=Ledger(out/"L001_ledger.sqlite",ROOT/"migrations/0001_ledger.sql")
    stamp=datetime.now(timezone.utc).isoformat()
    for arm,payload in outputs.items():
        (out/f"02_{arm}_native.json").write_bytes(canonical(payload)+b"\n")
        ledger.append_revision(
            entity_id=f"L001-{arm}-native-0",entity_type="ArenaArmSubmission",
            case_id="CAF_L001", actor_id="arena-l001-native-gate",
            idempotency_key="CAF_L001-"+arm+"-"+digest(payload["submission"]),
            payload={"submission":payload["submission"],"event":payload["event"]},
            recorded_at=stamp,created_at=stamp,access_policy="lane:"+arm)
    report["ledger_revisions"]=3
    (out/"04_report.json").write_bytes(canonical(report)+b"\n")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(write_artifacts(args.out),sort_keys=True,ensure_ascii=False))
