"""RF-01 · Fidelity *audit*, not an alternative modeling engine.

Two tracks are disjoint:
  PARITY: D2/C00 external choices, shared parameters, real OMC (engineering).
  NATIVE_METHOD: D rejected input, M original E1 enumeration, B offline mock.

Consumes unchanged original worker receipts, six actual scoped SQLite ledgers,
the prior F3 report OF four OpenModelica parity outputs and frozen F0 identity.\nRF-01 does NOT re-open or re-hash original solver CSV files.
Does not call solvers, providers, model generators or hidden DES.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from scripts.arena_cafe import f3_adjudicate as f3
from scripts.arena_cafe.native_handoff import validate_a1_visible, need
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-arena-method-fidelity/1.1"
REPORT="igc-arena-rf01-fidelity-classification/1.0"
ARMS=("D","B","M")
CONDITIONS=("O0","O1")
ALLOWED_STATES={
    "NOT_RUN","BLOCKED_BEFORE_RUN","ATTEMPTED_METHOD",
    "FAILED_TECHNICAL","METHOD_ABSTAINED","COMPLETED_METHOD",
    "ARENA_POLICY_SELECTED",
}
WORKER_STATES={
    "D":("BLOCKED_NOMINAL_PULSE_MISSING","BLOCKED_BEFORE_RUN"),
    "B":("ORIGINAL_ENGINE_OFFLINE_MOCK","BLOCKED_BEFORE_RUN"),
    "M":("ORIGINAL_E1_ENUMERATOR_ENGINEERING_ONLY","METHOD_ABSTAINED"),
}
SOURCE={
    "D":"scripts/arena_d_v01.py",
    "B":"scripts/arena_b_native_runner.mjs",
    "M":"scripts/arena_m_short_e1.py",
}
ENTRY={
    "D":"scripts.arena_d_v01.validate_case (rejected); generate NOT invoked",
    "B":"UB-IAD/sd-ai engines/quantitative/Engine.generate (mock; no live inferencing)",
    "M":"scripts.arena_m_short_e1.prepare -> original Short E1 enumerate_graphs",
}
VERSION={
    "D":"generic-conservative-chain-search/0.1",
    "B":"UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc",
    "M":"short-e1-molecular-composition-port/0.1",
}
FIELDS=("construction.pos_arrival_events","construction.observation_series")
PARITY_ID="PARITY_BENCHMARK_D2_EQUIVALENT_E1_C00"


def read_json(p):
    p=Path(p)
    need(p.is_file(),"RF01_MISSING_SOURCE_ARTIFACT:"+p.name)
    return json.loads(p.read_text(encoding="utf-8"))


def blob_hash(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()


def sha256_file(path):
    return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_original_sources(baseline):
    need(baseline["schema"]=="igc-arena-fidelity-baseline/1.0" and
         baseline["tracks"]["PARITY"]["method_complete"] is False and
         baseline["tracks"]["NATIVE_METHOD"]["method_complete"] is False and
         baseline["G4"]==baseline["G5"]=="NOT_RUN" and
         baseline["A3"]=="PARTIAL" and baseline["historic_live_is_ev01_live"] is False,
         "RF01_BASELINE_CLAIMS_INVALID")
    for filename,expected in baseline["original_source_git_blobs"].items():
        need(blob_hash(filename)==expected,"RF01_FROZEN_SOURCE_MUTATED:"+filename)
    need(baseline["original_buffalo_upstream_sha"] in VERSION["B"],
         "RF01_B_UPSTREAM_MISMATCH")
    # This is a historical snapshot. Never silently substitute current main.
    need(baseline["stacked_prs"][-1]["head_sha"]==baseline["source_head"],
         "RF01_F0_BASE_SHA_MISMATCH")
    return True


def verify_m_universe(receipt):
    from scripts.arena_m_short_e1 import E1, get_composer
    c=get_composer()
    cfg,classes,_=c.load_registry(E1/"registry.base.json")
    all_graphs=c.enumerate_graphs(cfg,classes)
    graphs=[{"canonical_sha256":key,"ast":graph} for key,graph in all_graphs]
    need(len(graphs)==6 and
         receipt.get("candidate_count")==len(graphs) and
         receipt.get("candidate_graphs_hash")==digest(graphs),
         "RF01_M_ENUMERATED_ORIGINAL_UNIVERSE_DRIFT")
    return graphs


def _fields(visible,condition,arm):
    """Observed instrument access is NOT original-engine cognitive use.

    These operations are source-attested STATIC CODE observations, not a runtime
    proof of inner-model reasoning. The original worker receipt + baseline SHA
    authenticates the particular path; status values cannot be freely edited.
    """
    fields=list(FIELDS)
    if condition=="O1":
        fields.append("construction.physical_observation")
    if arm=="D":
        adapter_read=["construction.observation_series"]
        native_read=[]  # validate_case rejects schema before native data use.
        routed=[]
        statuses={
            "construction.pos_arrival_events":
               ("ARENA_HANDOFF","POS_EVENT_VISIBLE_D_NATIVE_CONTRACT_REJECTED",
                "A1_HANDOFF_VALIDATED_NOT_D_GENERATOR_USED"),
            "construction.observation_series":
               ("ARENA_OBSERVATION_PORT","OBSERVATION_CONSTRAINT_CONSTRUCTED",
                "ADAPTER_READ_ONLY_NOT_D_NATIVE_READ"),
            "construction.physical_observation":
               ("ARENA_HANDOFF","VALIDATED_ONLY_NOT_MAPPED_TO_D_STOCKS",
                "NO_D_NATIVE_PHYSICAL_PORT"),
        }
        interface="UNSUPPORTED_DOCUMENTED"
    elif arm=="M":
        adapter_read=["construction.observation_series"]
        if condition=="O1":
            adapter_read.append("construction.physical_observation")
        native_read=[]  # E1 graph enumeration is registry-driven.
        routed=[]
        statuses={
            "construction.pos_arrival_events":
               ("ARENA_HANDOFF","POS_EVENT_VALIDATED_NOT_E1_GRAPH_GENERATOR_USED",
                "E1_NO_DATA_DEPENDENT_GRAPH_SELECTION"),
            "construction.observation_series":
               ("ARENA_OBSERVATION_PORT","TYPED_SOURCE_RECEIPT_OPERATOR_BUILT",
                "E1_GRAPH_ENUMERATOR_NOT_DATA_DRIVEN"),
            "construction.physical_observation":
               ("ARENA_OBSERVATION_PORT","PREPARATION_SERVICE_AGGREGATE_MAPPED",
                "NO_EQUIVALENT_E1_SERVICE_TIME_PARAMETER_PROVEN"),
        }
        interface="UNSUPPORTED_DOCUMENTED_FOR_OBSERVATION_DRIVEN_SELECTION"
    else:
        adapter_read=[]
        native_read=[] # Mock prompt was sent, no LLM cognitive-use proof.
        routed=fields[:]
        statuses={
            x:("BUFFALO_OFFLINE_TRANSPORT","MOCK_PROMPT_TRANSPORT_ONLY",
               "NO_LIVE_PROVIDER_OR_COGNITIVE_FIELD_USE_PROOF")
            for x in fields
        }
        interface="TRANSPORT_ONLY_LLM_COGNITIVE_USE_NOT_VERIFIED"
    operations=[{"field":x,"actor":statuses[x][0],
                 "operation":statuses[x][1],"status":statuses[x][2],
                 "evidence_level":"SOURCE_PATH_AND_RECEIPT_NOT_RUNTIME_COGNITIVE_TRACE"}
                for x in fields]
    return fields,adapter_read,native_read,routed,operations,interface


def classify_worker(visible,arm,condition,receipt,verified,baseline):
    need(arm in ARMS and condition in CONDITIONS,"RF01_BAD_LANE")
    validate_a1_visible(visible,condition)
    expected,state=WORKER_STATES[arm]
    # Both raw receipt and independent ledger reconstruction must agree.
    need(receipt.get("arm")==arm and receipt.get("condition")==condition
         and receipt.get("status")==expected
         and receipt.get("visible_input_hash")==digest(visible)
         and receipt.get("source_snapshot_hash")==visible["source_snapshot_hash"]
         and receipt.get("provider_calls")==0
         and receipt.get("scientific_use_proven") is False,
         "RF01_WORKER_PROVENANCE_MISMATCH")
    need(verified["status"]==expected and
         verified["memory"]["actual_SQLite_reconstruction"] is True,
         "RF01_UNVERIFIED_LEDGER_OR_WORKER")
    if arm=="M":
        graphs=verify_m_universe(receipt)
        native_ids=[x["canonical_sha256"] for x in graphs]
        universe={"count":6,"enumerable":True,
                  "source":"ORIGINAL_E1_BASE_REGISTRY_ENUMERATION",
                  "enumeration_only_not_evidence_selection":True}
        origins=[{"parameter":"E1_BASE_REGISTRY_FIXED",
                  "owner":"SOURCE_REGISTRY_NOT_SENSOR",
                  "origin":"EXPLICIT_STRUCTURAL_PRIOR"}]
        scope_in=["ORIGINAL_TYPED_GRAPH_ENUMERATION"]
        scope_out=["OBSERVATION_DRIVEN_CHOICE","PARAMETER_FITTING",
                   "G2_FOR_ALL_GRAPHS","G3_SELECTION"]
        abst="ARENA_M0_BRIDGE_UNRESOLVED_SELECTION"
    elif arm=="D":
        need(receipt.get("native_method_run") is False,
             "RF01_D_INVOKED_WITHOUT_CONTRACT")
        native_ids=[]
        universe={"count":None,"enumerable":False,
                  "original_max_candidates_if_valid_pulse":6,
                  "reason":"PUBLIC_POS_IS_NOT_AN_ORIGINAL_D_PULSE_AND_HAS_NO_NATIVE_NOMINAL"}
        origins=[]
        scope_in=["D_ORIGINAL_VALIDATE_CASE_REJECTED_EVENT_INPUT"]
        scope_out=["D_GENERATE_SIX_CANDIDATES","D_MODEL_SELECTION",
                   "D_PARAMETER_INFERENCE","D_NATIVE_G2_G3"]
        abst="NOT_APPLICABLE_BLOCKED_BEFORE_NATIVE_GENERATION"
    else:
        need(receipt.get("native_method_run") is True
             and len(receipt.get("user_prompt_hashes",[]))>=1,
             "RF01_B_OFFLINE_TRANSPORT_UNPROVEN")
        native_ids=[]
        universe={"count":None,"enumerable":False,
                  "reason":"MOCK_RESULT_NOT_REAL_GENERATED_MODEL"}
        origins=[]
        scope_in=["ORIGINAL_QUANTITATIVE_ENGINE_TRANSPORT_OFFLINE_FIXTURE"]
        scope_out=["REAL_CLOUDFLARE_INFERENCE","NATIVE_PROPOSAL",
                   "REAL_FEEDBACK_REVISION","G0_G3_EV01"]
        abst="NOT_APPLICABLE_NO_LIVE_METHOD_ATTEMPT"
    fields,adapter_read,native_read,routed,operations,interface=_fields(visible,condition,arm)
    return {
        "schema":SCHEMA,"track":"NATIVE_METHOD",
        "arm_id":arm,"condition_id":condition,
        "method_version":VERSION[arm],
        "original_entrypoint":ENTRY[arm],
        "original_source_sha":"gitblob:"+baseline["original_source_git_blobs"][SOURCE[arm]],
        "native_input_contract":"igc-arena-visible-input/0.1",
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "visible_input_sha":digest(visible),
        "input_fields_present":fields,
        "adapter_fields_read":adapter_read,
        "native_fields_read":native_read,
        "transport_fields_submitted":routed,
        "input_fields_used_or_rejected":operations,
        "interface_status":interface,
        "method_capabilities_in_scope":scope_in,
        "method_capabilities_out_of_scope":scope_out,
        "original_candidate_universe":universe,
        "native_candidate_ids":native_ids,
        "native_candidate_hashes":native_ids,
        "selection_decision_owner":"NONE",
        "selection_policy_sha":None,
        "parameters_origin":origins,
        "cross_arm_prior_imports":[],
        "calibration_policy":"NOT_RUN",
        "abstention_origin":abst,
        "execution_state":state,
        "native_component_execution_complete":arm=="M",
        "arena_task_complete":False,
        "method_route_complete":False,
        "method_complete":False,
        "provider_calls":0,"omc_invocations":0,
        "gates_by_candidate":[],
        "source_exposure":["SINGLE_PUBLIC_"+condition+"_VIEW",
                           "NO_EVALUATOR_DES_OR_FULL",
                           "APPLICATION_LEVEL_SCOPE_NOT_VERIFIED_OS_ACL"],
        "unsupported_observables":(
            ["O1_PREPARATION_WAIT_SERVICE_NOT_EQUIVALENT_TO_E1_OR_D_NATIVE"]
            if condition=="O1" else []),
        "ledger_case_id":verified["memory"]["case_id"],
        "worker_receipt_sha":digest(receipt),
        "worker_executed_component":expected,
        "method_use_proven":False,
        "historical_B_live_not_this_EV01":arm=="B",
        "g0":"NOT_RUN_NATIVE_METHOD",
        "g1":"NOT_RUN_NATIVE_METHOD",
        "g2":"NOT_RUN_NATIVE_METHOD",
        "g3":"NOT_RUN_NATIVE_METHOD",
        "g4":"NOT_RUN","g5":"NOT_RUN",
    }


def classify_parity(native,arm,condition,baseline):
    need(arm in ("D","M") and condition in CONDITIONS,
         "RF01_PARITY_BAD_LANE")
    need(native["G2"]=="PASS_REAL_OMC_MATERIAL_BALANCE_ENGINEERING"
         and native["G3"]=="CONSTRUCTION_DESCRIPTIVE_ONLY_NO_ADMISSIBILITY_THRESHOLD"
         and native["no_structure_selection"] is True
         and native["parameters_nominal_unfitted"] is True
         and native["independent_forecast"]=="NOT_RUN",
         "RF01_PARITY_NOT_G2_ENGINEERING_OR_FALSE_METHOD")
    metric=native["metrics"]
    need(metric["comparison_semantics"]=="SAME_PUBLIC_POS_DELIVERED_COUNTS_AND_HJ"
         and metric["delivery_rmse_orders"]>0,
         "RF01_PARITY_BAD_METRIC")
    return {
        "schema":SCHEMA,"track":"PARITY","classification":PARITY_ID,
        "arm_id":arm,"condition_id":condition,
        "native_model_sha256":native["native_model_sha256"],
        "trace_sha256":native["trace_sha256"],
        "source_f3_run_id":"41575917332",
        "source_f3_report_artifact_id":"13202639585",
        "source_native_csv_rehashed_this_rf01_run":False,
        "model_id":native["native_model"],
        "source_snapshot_hash":native["source_snapshot_hash"],
        "full_candidate_hash":native["full_candidate_hash"],
        "source_config_sha256":sha256_file("scripts/arena_cafe/native_pos_scenario.py"),
        "selection_decision_owner":"ARENA_POLICY",
        "selection_rule":"D_TOPOLOGY_2_NO_LOSS_OR_M_MIN_INSTANCES_C00",
        "parameters_origin":(
            ["E1_BASE_REGISTRY_PRIOR_IMPORTED_AS_D_NOMINAL"]
            if arm=="D" else ["E1_BASE_REGISTRY_FIXED_PRIOR"]),
        "cross_arm_prior_imports":(
            ["E1_PARAMETER_PRIOR_IN_D_PARITY"] if arm=="D" else []),
        "native_generation_component_executed":True,
        "real_omc_simulated":True,
        "native_component_execution_complete":True,
        "arena_task_complete":False,
        "method_route_complete":False,"method_complete":False,
        "calibration":"NOT_RUN","G0":"ENGINEERING_NATIVE_RENDER",
        "G1":"ENGINEERING_DECLARED_BALANCE",
        "G2":"PASS_REAL_OMC_ENGINEERING_ONLY",
        "G3":"DESCRIPTIVE_NOT_G3_ADMISSIBILITY",
        "G4":"NOT_RUN","G5":"NOT_RUN",
        "construction_metrics_descriptive_only":metric,
        "competitive_evidence":False,
        "independent_method_convergence":False,
        "input_reconstruction":"UNIFORM_MASS_PER_HALF_MINUTE_BIN_ASSUMPTION",
        "note":"Original components with ARENA-PREFIXED candidates and matched priors."
    }


# Closed, versioned manifest variants. A key missing from either track is an
# error even if the other flags happen to look sound. Schema v1.1 is append-only:
# any new semantic claim requires a new schema and fresh adversarial tests.
NATIVE_KEYS=frozenset("""
schema track arm_id condition_id method_version original_entrypoint
original_source_sha native_input_contract source_snapshot_hash visible_input_sha
input_fields_present adapter_fields_read native_fields_read
transport_fields_submitted input_fields_used_or_rejected interface_status
method_capabilities_in_scope method_capabilities_out_of_scope
original_candidate_universe native_candidate_ids native_candidate_hashes
selection_decision_owner selection_policy_sha parameters_origin
cross_arm_prior_imports calibration_policy abstention_origin execution_state
native_component_execution_complete arena_task_complete method_route_complete
method_complete provider_calls omc_invocations gates_by_candidate source_exposure
unsupported_observables ledger_case_id worker_receipt_sha
worker_executed_component method_use_proven historical_B_live_not_this_EV01
g0 g1 g2 g3 g4 g5
""".split())
PARITY_KEYS=frozenset("""
schema track classification arm_id condition_id native_model_sha256
trace_sha256 source_f3_run_id source_f3_report_artifact_id
source_native_csv_rehashed_this_rf01_run model_id source_snapshot_hash
full_candidate_hash source_config_sha256 selection_decision_owner
selection_rule parameters_origin cross_arm_prior_imports
native_generation_component_executed real_omc_simulated
native_component_execution_complete arena_task_complete method_route_complete
method_complete calibration G0 G1 G2 G3 G4 G5
construction_metrics_descriptive_only competitive_evidence
independent_method_convergence input_reconstruction note
""".split())


def _m_native_graph_ids():
    """Reference ASTs come only from original, pinned E1 grammar and base registry."""
    from scripts.arena_m_short_e1 import E1,get_composer
    c=get_composer()
    cfg,classes,_=c.load_registry(E1/"registry.base.json")
    return [key for key,_ in c.enumerate_graphs(cfg,classes)]


def _source_baseline():
    return read_json(Path(__file__).resolve().parents[2]/
                     "docs/arena_cafe/fidelity/F0_FIDELITY_BASELINE.json")


def _valid_sha(value):
    return isinstance(value,str) and re.fullmatch(
        r"sha256:[a-f0-9]{64}",value) is not None


def verify_manifest(m, *, baseline=None, receipt=None, worker=None,
                    visible=None, f3_native=None):
    """Fail closed on ALL fidelity assertions, including those not used for CI totals.

    Pure invocation validates against immutable catalogues/source paths and
    frozen metadata. The build path additionally binds row claims to actual
    original source receipts, scoped SQLite and earlier F3 report.
    Neither form is cryptographic signing or runtime cognitive-use tracing.
    """
    need(type(m) is dict and m.get("schema")==SCHEMA and
         m.get("track") in ("PARITY","NATIVE_METHOD") and
         m.get("arm_id") in ARMS and m.get("condition_id") in CONDITIONS,
         "RF01_MANIFEST_TYPE_OR_VERSION")
    variant=m["track"]
    need(set(m)==(NATIVE_KEYS if variant=="NATIVE_METHOD" else PARITY_KEYS),
         "RF01_MANIFEST_REQUIRED_FIELDS_OR_EXTRA")
    arm,condition=m["arm_id"],m["condition_id"]
    baseline=_source_baseline() if baseline is None else baseline
    need(baseline.get("schema")=="igc-arena-fidelity-baseline/1.0" and
         baseline["source_head"]=="589a4b8604753b8ab5d0adf3f0606f6c30ae6e45",
         "RF01_BASELINE_IDENTITY")
    need(m["method_complete"] is False and
         m["method_route_complete"] is False and
         m["arena_task_complete"] is False and
         m["g4" if variant=="NATIVE_METHOD" else "G4"]=="NOT_RUN" and
         m["g5" if variant=="NATIVE_METHOD" else "G5"]=="NOT_RUN",
         "RF01_FALSE_METHOD_COMPLETION")
    need(_valid_sha(m["source_snapshot_hash"]),
         "RF01_INVALID_EVIDENCE_SHA")

    if variant=="PARITY":
        need(arm in ("D","M") and
             m["classification"]==PARITY_ID and
             m["selection_decision_owner"]=="ARENA_POLICY" and
             m["competitive_evidence"] is False and
             m["independent_method_convergence"] is False and
             m["G3"]=="DESCRIPTIVE_NOT_G3_ADMISSIBILITY",
             "RF01_PARITY_LAUNDERED_AS_NATIVE_METHOD")
        need(m["cross_arm_prior_imports"]==(
              ["E1_PARAMETER_PRIOR_IN_D_PARITY"] if arm=="D" else []),
             "RF01_CROSS_ARM_PRIOR_HIDDEN")
        need(m["parameters_origin"]==(
              ["E1_BASE_REGISTRY_PRIOR_IMPORTED_AS_D_NOMINAL"]
              if arm=="D" else ["E1_BASE_REGISTRY_FIXED_PRIOR"])
             and m["selection_rule"]=="D_TOPOLOGY_2_NO_LOSS_OR_M_MIN_INSTANCES_C00"
             and m["source_config_sha256"]==
                sha256_file("scripts/arena_cafe/native_pos_scenario.py")
             and m["input_reconstruction"]==
                "UNIFORM_MASS_PER_HALF_MINUTE_BIN_ASSUMPTION"
             and m["calibration"]=="NOT_RUN"
             and m["native_generation_component_executed"] is True
             and m["real_omc_simulated"] is True
             and m["native_component_execution_complete"] is True
             and m["G0"]=="ENGINEERING_NATIVE_RENDER"
             and m["G1"]=="ENGINEERING_DECLARED_BALANCE"
             and m["G2"]=="PASS_REAL_OMC_ENGINEERING_ONLY"
             and m["G4"]==m["G5"]=="NOT_RUN"
             and m["source_f3_run_id"]=="41575917332"
             and m["source_f3_report_artifact_id"]=="13202639585"
             and m["source_native_csv_rehashed_this_rf01_run"] is False
             and m["note"]==
                "Original components with ARENA-PREFIXED candidates and matched priors.",
             "RF01_PARITY_ORIGIN_OR_PROVENANCE_DRIFT")
        need(all(_valid_sha(m[k]) for k in
                 ("native_model_sha256","trace_sha256","full_candidate_hash",
                  "source_config_sha256"))
             and type(m["model_id"]) is str and bool(m["model_id"])
             and type(m["construction_metrics_descriptive_only"]) is dict
             and m["construction_metrics_descriptive_only"].get("comparison_semantics")==
                 "SAME_PUBLIC_POS_DELIVERED_COUNTS_AND_HJ"
             and type(m["construction_metrics_descriptive_only"].get(
                 "delivery_rmse_orders")) in (float,int)
             and m["construction_metrics_descriptive_only"]["delivery_rmse_orders"]>0,
             "RF01_PARITY_IDENTITY_OR_METRICS_INVALID")
        if f3_native is not None:
            need(m["native_model_sha256"]==f3_native["native_model_sha256"] and
                 m["trace_sha256"]==f3_native["trace_sha256"] and
                 m["full_candidate_hash"]==f3_native["full_candidate_hash"] and
                 m["model_id"]==f3_native["native_model"] and
                 m["construction_metrics_descriptive_only"]==
                    f3_native["metrics"],
                 "RF01_PARITY_NOT_BOUND_TO_PRIOR_F3")
        if visible is not None:
            need(m["source_snapshot_hash"]==visible["source_snapshot_hash"],
                 "RF01_PARITY_NOT_BOUND_TO_PUBLIC_SOURCE")
        return True

    # NATIVE_METHOD: all informational fields are either (a) original source
    # identity/receipt, or (b) explicitly labeled STATIC source-path assessment.
    need(m["method_version"]==VERSION[arm] and
         m["original_entrypoint"]==ENTRY[arm] and
         m["original_source_sha"]==
            "gitblob:"+baseline["original_source_git_blobs"][SOURCE[arm]] and
         m["native_input_contract"]=="igc-arena-visible-input/0.1" and
         _valid_sha(m["visible_input_sha"]) and
         _valid_sha(m["worker_receipt_sha"]),
         "RF01_NATIVE_ENTRYPOINT_SOURCE_OR_CONTRACT_DRIFT")
    fields,adapter_read,native_read,routed,operations,interface=_fields(
        None,condition,arm)
    need(m["input_fields_present"]==fields and
         m["adapter_fields_read"]==adapter_read and
         m["native_fields_read"]==native_read and
         m["transport_fields_submitted"]==routed and
         m["input_fields_used_or_rejected"]==operations and
         m["interface_status"]==interface,
         "RF01_FIELD_ACTOR_OR_CONSUMPTION_FALSIFIED")
    need(m["execution_state"]==WORKER_STATES[arm][1] and
         m["worker_executed_component"]==WORKER_STATES[arm][0] and
         m["selection_decision_owner"]=="NONE" and
         m["selection_policy_sha"] is None and
         m["method_use_proven"] is False and
         m["provider_calls"]==m["omc_invocations"]==0 and
         m["cross_arm_prior_imports"]==[] and
         m["g0"]==m["g1"]==m["g2"]==m["g3"]==
           "NOT_RUN_NATIVE_METHOD" and
         m["gates_by_candidate"]==[] and
         m["calibration_policy"]=="NOT_RUN" and
         m["source_exposure"]==[
           "SINGLE_PUBLIC_"+condition+"_VIEW",
           "NO_EVALUATOR_DES_OR_FULL",
           "APPLICATION_LEVEL_SCOPE_NOT_VERIFIED_OS_ACL"] and
         m["unsupported_observables"]==(
           ["O1_PREPARATION_WAIT_SERVICE_NOT_EQUIVALENT_TO_E1_OR_D_NATIVE"]
           if condition=="O1" else []),
         "RF01_NATIVE_METHOD_FALSE_GATES_OR_SELECTION")
    need(isinstance(m["ledger_case_id"],str) and
         bool(m["ledger_case_id"]) and
         m["historical_B_live_not_this_EV01"] is (arm=="B") and
         m["native_component_execution_complete"] is (arm=="M"),
         "RF01_COMPONENT_OR_HISTORICAL_STATE_FALSE")

    if arm=="M":
        expected=_m_native_graph_ids()
        need(len(expected)==6 and len(set(expected))==6 and
             m["native_candidate_ids"]==expected and
             m["native_candidate_hashes"]==expected and
             len(set(m["native_candidate_ids"]))==6,
             "RF01_M_COMPLETE_CANDIDATE_IDENTITY_DRIFT")
        need(m["original_candidate_universe"]=={
               "count":6,"enumerable":True,
               "source":"ORIGINAL_E1_BASE_REGISTRY_ENUMERATION",
               "enumeration_only_not_evidence_selection":True}
             and m["parameters_origin"]==[
               {"parameter":"E1_BASE_REGISTRY_FIXED",
                "owner":"SOURCE_REGISTRY_NOT_SENSOR",
                "origin":"EXPLICIT_STRUCTURAL_PRIOR"}]
             and m["method_capabilities_in_scope"]==[
                 "ORIGINAL_TYPED_GRAPH_ENUMERATION"]
             and m["method_capabilities_out_of_scope"]==[
                 "OBSERVATION_DRIVEN_CHOICE","PARAMETER_FITTING",
                 "G2_FOR_ALL_GRAPHS","G3_SELECTION"]
             and m["abstention_origin"]==
                 "ARENA_M0_BRIDGE_UNRESOLVED_SELECTION",
             "RF01_M_PARTIAL_WRONGFUL_SELECTION")
    elif arm=="D":
        need(m["original_candidate_universe"]=={
              "count":None,"enumerable":False,
              "original_max_candidates_if_valid_pulse":6,
              "reason":"PUBLIC_POS_IS_NOT_AN_ORIGINAL_D_PULSE_AND_HAS_NO_NATIVE_NOMINAL"}
             and m["native_candidate_ids"]==m["native_candidate_hashes"]==[]
             and m["parameters_origin"]==[]
             and m["method_capabilities_in_scope"]==[
                  "D_ORIGINAL_VALIDATE_CASE_REJECTED_EVENT_INPUT"]
             and m["method_capabilities_out_of_scope"]==[
                  "D_GENERATE_SIX_CANDIDATES","D_MODEL_SELECTION",
                  "D_PARAMETER_INFERENCE","D_NATIVE_G2_G3"]
             and m["abstention_origin"]==
                  "NOT_APPLICABLE_BLOCKED_BEFORE_NATIVE_GENERATION",
             "RF01_D2_FIXED_LAUNDERED_AS_GENERATION")
    else:
        need(m["original_candidate_universe"]=={
                 "count":None,"enumerable":False,
                 "reason":"MOCK_RESULT_NOT_REAL_GENERATED_MODEL"}
             and m["native_candidate_ids"]==m["native_candidate_hashes"]==[]
             and m["parameters_origin"]==[]
             and m["method_capabilities_in_scope"]==[
                   "ORIGINAL_QUANTITATIVE_ENGINE_TRANSPORT_OFFLINE_FIXTURE"]
             and m["method_capabilities_out_of_scope"]==[
                   "REAL_CLOUDFLARE_INFERENCE","NATIVE_PROPOSAL",
                   "REAL_FEEDBACK_REVISION","G0_G3_EV01"]
             and m["abstention_origin"]==
                 "NOT_APPLICABLE_NO_LIVE_METHOD_ATTEMPT",
             "RF01_B_MOCK_AS_LIVE")
    if condition=="O0":
        need("construction.physical_observation" not in
             (m["input_fields_present"]+m["adapter_fields_read"]+
              m["native_fields_read"]+m["transport_fields_submitted"]),
             "RF01_O0_O1_EVIDENCE_LEAK")
    if receipt is not None:
        need(m["worker_receipt_sha"]==digest(receipt) and
             receipt.get("arm")==arm and receipt.get("condition")==condition and
             receipt.get("status")==m["worker_executed_component"] and
             receipt.get("visible_input_hash")==m["visible_input_sha"] and
             receipt.get("source_snapshot_hash")==m["source_snapshot_hash"] and
             receipt.get("provider_calls")==0,
             "RF01_NOT_BOUND_TO_ORIGINAL_RECEIPT")
    if worker is not None:
        need(m["ledger_case_id"]==worker["memory"]["case_id"] and
             worker["status"]==m["worker_executed_component"] and
             worker["memory"]["actual_SQLite_reconstruction"] is True,
             "RF01_NOT_BOUND_TO_SCOPED_SQLITE")
    if visible is not None:
        need(m["visible_input_sha"]==digest(visible) and
             m["source_snapshot_hash"]==visible["source_snapshot_hash"],
             "RF01_NOT_BOUND_TO_PUBLIC_EVIDENCE")
    return True

def build(visible, worker_roots, parity, baseline):
    verify_original_sources(baseline)
    need(set(visible)==set(CONDITIONS) and
         set(worker_roots)=={(c,a) for c in CONDITIONS for a in ARMS},
         "RF01_REQUIRED_SIX_LANES")
    need(parity["schema"]==f3.SCHEMA and parity["A3"]=="PARTIAL" and
         parity["G4"]==parity["G5"]=="NOT_RUN" and
         parity["no_genuine_buffalo_inference_in_this_EV01_run"] is True and
         parity["historical_B_cloudflare_capability"]["status"]==
           "REAL_INFERENCE_DEMONSTRATED_ON_OTHER_EXPERIMENTS_NOT_EV01",
         "RF01_UNAUTHORIZED_A3_PROMOTION")
    method_cases=[]
    parity_cases=[]
    for c in CONDITIONS:
        v=visible[c]
        validate_a1_visible(v,c)
        for a in ARMS:
            root=Path(worker_roots[(c,a)])
            raw=read_json(root/"worker-receipt.json")
            worker=f3._worker(root,v,a,c) # validates real SQLite and case scope
            own=parity["arms"][c][a]["worker"]
            need(own["worker_receipt_hash"]==digest(raw) and
                 own["memory"]["case_id"]==worker["memory"]["case_id"],
                 "RF01_A3_WORKER_LINEAGE_DRIFT")
            m=classify_worker(v,a,c,raw,worker,baseline)
            verify_manifest(m,baseline=baseline,receipt=raw,
                            worker=worker,visible=v)
            method_cases.append(m)
            if a in ("D","M"):
                n=parity["arms"][c][a]["native"]
                p=classify_parity(n,a,c,baseline)
                need(p["source_snapshot_hash"]==v["source_snapshot_hash"],
                     "RF01_PARITY_CONDITION_SOURCE_MISMATCH")
                verify_manifest(p,baseline=baseline,visible=v,f3_native=n)
                parity_cases.append(p)
    need(len(method_cases)==6 and len(parity_cases)==4 and
         len(set((m["arm_id"],m["condition_id"]) for m in method_cases))==6 and
         len(set(m["ledger_case_id"] for m in method_cases))==6,
         "RF01_LINEAGE_UNIQUENESS_FAIL")
    for c in CONDITIONS:
        d=next(p for p in parity_cases if p["condition_id"]==c and p["arm_id"]=="D")
        m=next(p for p in parity_cases if p["condition_id"]==c and p["arm_id"]=="M")
        need(d["selection_decision_owner"]==m["selection_decision_owner"]==
              "ARENA_POLICY" and d["cross_arm_prior_imports"] and
              not m["cross_arm_prior_imports"],
             "RF01_PARITY_CROSS_ARM_PRIOR_NOT_EXPLICIT")
    return {
        "schema":REPORT,"baseline_source_sha":baseline["source_head"],
        "current_git_sha":os.environ.get("GITHUB_SHA","LOCAL_NOT_ASSERTED"),
        "A3":"PARTIAL","R0":"TECHNICAL_CLASSIFICATION_READY_FOR_REVIEW",
        "R1":"SIX_METHOD_MANIFESTS_READY_FOR_REVIEW",
        "scientific_method_fidelity":"NOT_ESTABLISHED",
        "native_method_complete_count":0,
        "parity_case_count":4,"method_case_count":6,
        "public_evidence_synthetic":True,
        "no_new_provider_calls":True,"no_new_omc_invocations":True,
        "parity_classification":PARITY_ID,
        "parity_not_competitive":True,
        "method_manifest_cases":method_cases,
        "parity_cases":parity_cases,
        "historic_buffalo_real_but_not_EV01":{
            "original_model":"@cf/zai-org/glm-5.3-flash",
            "run_ids":baseline["historic_buffalo_live_runs"],
            "status":"HISTORIC_REAL_EXECUTIONS_UNSCORED_FOR_EV01",
        },
        "F0_original_source_blobs_verified":True,
        "G4":"NOT_RUN","G5":"NOT_RUN",
        "independent_review":"PENDING"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--public",type=Path,required=True)
    p.add_argument("--workers",type=Path,required=True)
    p.add_argument("--f3",type=Path,required=True)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),"RF01_REFUSE_OVERWRITE")
    views={c:read_json(a.public/(c+"_VISIBLE.json")) for c in CONDITIONS}
    worker_roots={(c,arm):a.workers/("a1-cafe-native-"+c+"-"+arm)
                  for c in CONDITIONS for arm in ARMS}
    report=build(views,worker_roots,read_json(a.f3),read_json(a.baseline))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "R0":report["R0"],"R1":report["R1"],
        "method_manifest_cases":report["method_case_count"],
        "parity_cases":report["parity_case_count"],
        "method_complete":report["native_method_complete_count"],
        "G4":report["G4"],"G5":report["G5"]}))


if __name__=="__main__":
    main()
