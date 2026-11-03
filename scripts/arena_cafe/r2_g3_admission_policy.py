"""RF-02P: deterministic pre-G3 admission/abstention and prereg protocol.

Real G2 engineering traces and H_j are inputs; they are NOT G3 certificates.
No solver, provider, fitting, scoring, automated selection, or hidden holdout.
A syntactically conformant future evidence manifest is still NOT independent
adjudication, a secure enclave, or authorization to compute G3.

Existing O0 output was seen during engineering: it cannot later be called a
blind holdout. Future test input may be provided in full only for explicitly
CONDITIONAL REPLAY; that is not a real-time forecast.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scripts.arena_v0_contract import canonical,digest,ArenaContractError
from scripts.arena_cafe.native_handoff import need,validate_a1_visible
from scripts.arena_cafe import r2_hj_parameter_gate as hj

SCHEMA="igc-arena-rf02-prospective-g3-admission/0.1"
FUTURE_SCHEMA="igc-arena-g3-prospective-evidence-metadata/0.1"
CANDIDATE_PROTOCOL_SCHEMA="igc-arena-g3-conditional-replay-protocol/0.1"
SCOPE="PRE_G3_DETERMINISTIC_EVIDENCE_GATE"
SCIENTIFIC_STATUS="NOT_ESTABLISHED"
NO_G3="NOT_RUN"
ABSENT="ABSTAIN_NO_AUTHORIZED_G3_INPUTS"
D_REASON="D_ONLY_NONEMPIRICAL_G2_NOMINALS_NO_EV01_ESTIMATION"
M_REASON="M_E1_NATIVE_FIXED_PRIORS_VALID_AS_PRIORS_NOT_CALIBRATED"
B_REASON="B_NO_REAL_EV01_NATIVE_PROVIDER_RUN"
H_REASON="H_J_SCIENTIFIC_MEASUREMENT_EQUIVALENCE_UNESTABLISHED"
P_REASON="NO_PRE_REGISTERED_SEALED_INDEPENDENT_EVALUATION_WORLD"
E_REASON="G3_CANDIDATE_REGISTERED_BEFORE_EVALUATION_NOT_EVIDENCED"
METHODOLOGICAL_ACTIONS={
    "SCORE_G3","SELECT_WINNER","UNSEAL_EVALUATION_OUTCOMES",
    "CALIBRATE_FROM_RESERVED_DATA","RUN_NATIVE_B_PROVIDER",
    "PROMOTE_TO_G4","PROMOTE_TO_G5",
}
HEX=re.compile(r"^sha256:[0-9a-f]{64}$")
ID=re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,100}$")
ALLOWED_KIND={
    "construction":"NON_RESERVED_PUBLIC_OPERATIONAL_INPUTS",
    "evaluation":"PROSPECTIVE_SEALED_INDEPENDENT_WORLD",
}
SCORING_TIMES=("2","4","6","8","10")


def _valid_hash(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _valid_id(value):
    return type(value) is str and ID.fullmatch(value) is not None


def _assert_hj(h,visible):
    """Bind the report to the exact original public evidence and known runs."""
    validate_a1_visible(visible,"O0")
    need(type(h) is dict and h.get("schema")==hj.SCHEMA and
         h.get("scope")==hj.SCOPE and
         h.get("condition_id")=="O0" and
         h.get("public_source_snapshot_hash")==visible["source_snapshot_hash"] and
         h.get("public_view_sha256")==digest(visible),
         "RF02P_HJ_SOURCE_NOT_AUTHENTIC")
    rows=h.get("candidates")
    need(type(rows) is list and len(rows)==12,
         "RF02P_CANDIDATE_UNIVERSE_NOT_TWELVE")
    need(h.get("artifact_sources")=={
        "A1_public_run_id":hj.A1_ORIGIN_RUN,
        "D_G2_engineering_run_id":hj.D_ORIGIN_RUN,
        "M_G2_engineering_run_id":hj.M_ORIGIN_RUN,
    } and h.get("G2_source_audits_recomputed") is True and
         h.get("candidate_count")==12 and
         h.get("common_signal_sha256")==rows[0].get(
             "input_signal_sha256") and
         _valid_hash(h.get("common_signal_sha256")),
         "RF02P_HJ_NOT_FROZEN_G2_12")
    p=h.get("parameters",{})
    o=h.get("observables",{})
    gates=h.get("gates",{})
    need(p.get("schema")==hj.PARAM_SCHEMA and
         o.get("schema")==hj.OBS_SCHEMA and
         p.get("D",{}).get("eligible_for_G3") is False and
         p.get("M",{}).get("eligible_for_G3") is False and
         p.get("B",{}).get("eligible_for_G3") is False and
         p.get("D",{}).get("admissible_as_empirical_parameters") is False and
         p.get("M",{}).get("admissible_as_empirical_parameters") is False and
         p.get("M",{}).get("source")==
            "ORIGINAL_E1_FIXED_PRIORS_NOT_OBSERVATION_ESTIMATES" and
         o.get("delivery_cumulative",{}).get("G3_ADMISSIBLE") is False and
         o.get("delivery_cumulative",{}).get("operator_shape")==
            "PASS_D_M_DIRECT_NATIVE_STOCKS" and
         gates.get("G3")==gates.get("G4")==gates.get("G5")==NO_G3 and
         gates.get("A3")=="PARTIAL" and
         gates.get("Hj_scientific_semantic_equivalence")==SCIENTIFIC_STATUS and
         h.get("decision")==hj.DECISION and
         h.get("no_fit_to_observed_deliveries") is True and
         h.get("no_native_model_selection") is True,
         "RF02P_HJ_G3_OR_PARAMETERS_FALSELY_PROMOTED")
    candidates=h["candidates"]
    need(type(candidates) is list and len(candidates)==12,
         "RF02P_CANDIDATE_UNIVERSE_NOT_TWELVE")
    ids=set()
    for item in candidates:
        need(type(item) is dict and item.get("arm_id") in ("D","M") and
             _valid_hash(item.get("native_structure_sha256")) and
             _valid_hash(item.get("input_signal_sha256")) and
             item.get("input_signal_sha256")==h["common_signal_sha256"] and
             item.get("G2")=="ENGINEERING_PASS_ORIGINAL_FROZEN_TRACE" and
             item.get("G3")==NO_G3 and
             item.get("H_j",{}).get("engineering_operator")=="PASS" and
             item.get("H_j",{}).get("scientific_measurement_equivalence")==
                SCIENTIFIC_STATUS and
             item.get("H_j",{}).get("scoring_against_observations")==NO_G3 and
             item.get("H_j",{}).get("trajectory_values_exported") is False,
             "RF02P_FAKE_CANDIDATE_EVIDENCE")
        key=(item["arm_id"],item.get("candidate_id"))
        need(type(key[1]) is str and key not in ids,
             "RF02P_DUPLICATE_CANDIDATE")
        ids.add(key)
    need(sum(x[0]=="D" for x in ids)==6 and
         sum(x[0]=="M" for x in ids)==6,
         "RF02P_ASYMMETRIC_CANDIDATE_UNIVERSE")
    return h


def _dataset(meta,part):
    need(type(meta) is dict and set(meta)=={
        "dataset_id","world_id","snapshot_sha256","source_kind",
        "observed_outcomes_access","role","data_availability",
        "source_independence_attested_by",
    },"RF02P_FUTURE_DATASET_FIELDS")
    need(_valid_id(meta["dataset_id"]) and _valid_id(meta["world_id"]) and
         _valid_hash(meta["snapshot_sha256"]) and
         meta["source_kind"]==ALLOWED_KIND[part] and
         meta["role"]==part.upper() and
         meta["source_independence_attested_by"] in (
             "PENDING_EXTERNAL_AUDIT","EXTERNAL_AUDIT_REFERENCE") and
         _valid_id(meta["data_availability"]),
         "RF02P_FUTURE_DATASET_SOURCE_PROVENANCE")
    if part=="construction":
        need(meta["observed_outcomes_access"]=="VISIBLE_TO_METHOD_FOR_CONSTRUCTION",
             "RF02P_CONSTRUCTION_OUTCOME_POLICY")
    else:
        need(meta["observed_outcomes_access"]==
             "SEALED_NOT_ACCESSIBLE_TO_ARMS_OR_CALIBRATOR",
             "RF02P_EVALUATION_OUTCOMES_NOT_SEALED")


def validate_prospective_metadata(spec,existing_hj,existing_world_id):
    """Strict *metadata* sanity gate; never certifies scientific eligibility.

    This function does not contact source systems, authenticate independent
    evidence, or grant permissions. Self-declared SHA and audit references
    are not signatures. It cannot turn G3 on, even for valid metadata.
    """
    need(type(spec) is dict and set(spec)=={
        "schema","construction","evaluation","registration",
        "task","evaluation_outcomes_became_visible_before_registration",
        "any_candidate_or_parameter_selected_from_evaluation_outcomes",
    } and spec["schema"]==FUTURE_SCHEMA and
         spec["task"]==
           "OFFLINE_CONDITIONAL_REPLAY_WITH_EXOGENOUS_ARRIVALS_KNOWN" and
         spec["evaluation_outcomes_became_visible_before_registration"] is False and
         spec["any_candidate_or_parameter_selected_from_evaluation_outcomes"] is False,
         "RF02P_PROSPECTIVE_METADATA_SCOPE_INVALID")
    need(_valid_id(existing_world_id),"RF02P_CURRENT_WORLD_ID_INVALID")
    construction=spec["construction"]; evaluation=spec["evaluation"]
    _dataset(construction,"construction")
    _dataset(evaluation,"evaluation")
    need(construction["world_id"]!=evaluation["world_id"] and
         construction["dataset_id"]!=evaluation["dataset_id"] and
         construction["snapshot_sha256"]!=evaluation["snapshot_sha256"] and
         evaluation["snapshot_sha256"]!=existing_hj["public_source_snapshot_hash"] and
         evaluation["snapshot_sha256"]!=existing_hj["public_view_sha256"] and
         construction["snapshot_sha256"]!=evaluation["snapshot_sha256"] and
         evaluation["world_id"]!=existing_world_id,
         "RF02P_EVALUATION_IS_NOT_INDEPENDENT_WORLD")
    registration=spec["registration"]
    need(type(registration) is dict and set(registration)=={
        "protocol_sha256","candidate_register_sha256",
        "declared_prior_to_evaluation_outcomes",
        "measurement_equivalence_review",
        "access_isolation_review",
        "cost_authorization_state",
        "external_review_reference",
    } and _valid_hash(registration["protocol_sha256"]) and
         _valid_hash(registration["candidate_register_sha256"]) and
         registration["declared_prior_to_evaluation_outcomes"] is True and
         registration["measurement_equivalence_review"] in (
             "NOT_RUN","EXTERNAL_REVIEW_RECORDED") and
         registration["access_isolation_review"] in (
             "NOT_RUN","EXTERNAL_REVIEW_RECORDED") and
         registration["cost_authorization_state"] in (
             "NOT_AUTHORIZED","EXPLICIT_SEPARATE_AUTHORIZATION_RECORDED") and
         _valid_id(registration["external_review_reference"]),
         "RF02P_REGISTRATION_MISSING_OR_NOT_PROSPECTIVE")
    return {
        "schema":FUTURE_SCHEMA,
        "metadata_shape":"PASS_ONLY_UNVERIFIED_SELF_ATTESTATION",
        "independent_provenance":"NOT_EXTERNALLY_AUTHENTICATED",
        "sealing_isolation":"NOT_OS_OR_PROCESS_VERIFIED",
        "science_semantics":"NOT_INDEPENDENTLY_ADJUDICATED",
        "predeclared":True,
        "future_metadata_sha256":digest(spec),
        "G3":NO_G3,
        "execution_authorized":False,
    }


def prereg_template(h):
    """Prospective conditional REPLAY only; never a forecaster's backtest."""
    return {
        "schema":CANDIDATE_PROTOCOL_SCHEMA,
        "task":"OFFLINE_CONDITIONAL_REPLAY_WITH_EXOGENOUS_ARRIVALS_KNOWN",
        "warning":"FULL_ARRIVAL_SEQUENCE_KNOWN_IS_NOT_REAL_TIME_FORECAST",
        "development_O0_source_snapshot_sha256":
             h["public_source_snapshot_hash"],
        "development_O0_is_a_blind_holdout":False,
        "development_O0_status":"ALREADY_EXAMINED_FOR_ENGINEERING_DO_NOT_REUSE_AS_SEALED_EVALUATION",
        "construction_input_policy":{
            "given":"PUBLIC_POS_ORDER_CREATION_EVENTS_WITH_EXACT_TIMESTAMPS",
            "rate_instrument_measured":False,
            "causal_kernel":"CAUSAL_RIGHT_RECTANGULAR_EVENT_KERNEL/0.1",
            "kernel_width_minutes_exact":"1/2",
            "kernel_is_an_engineering_choice":True,
            "kernel_scientifically_authorized":False,
            "kernel_selected_after_outcome_review":False,
            "arrival_exposure":"EXOGENOUS_FULL_WINDOW_OFFLINE_INPUT_ONLY",
            "deferred_mass_at_cutoff":"PRESERVE_AS_DEFERRED_NOT_FORCE_TO_15",
        },
        "proposed_primary_observable":{
            "name":"delivered_cumulative",
            "times_minutes_exact":list(SCORING_TIMES),
            "candidate_statistic":"MAE_CUMULATIVE_DELIVERY_COUNTS",
            "formula":"mean(abs(predicted_delivered(t)-heldout_delivered(t)))",
            "scientific_approval":"NOT_GRANTED",
            "evaluation_data_is_already_available_to_this_task":False,
            "pre_registered_new_independent_world_required":True,
            "weighting":"EQUAL_TIMEPOINT_WEIGHTS_NOT_INDEPENDENT_REPLICATES",
            "do_not_treat_timepoints_as_independent_worlds":True,
        },
        "training_and_evaluation":{
            "development_source_use":"ENGINEERING_ONLY",
            "construction_and_evaluation_must_be_distinct_worlds":True,
            "evaluation_outcomes_sealed_before_candidate_freeze":True,
            "parameter_fit_on_evaluation_outcomes":"FORBIDDEN",
            "selection_using_evaluation_outcomes":"FORBIDDEN",
            "no_holdout_outcomes_in_arm_containers":"REQUIRES_R6_SEPARATE_ATTESTATION",
        },
        "per_arm_method_obligations":{
            "D":"DECLARE_INDEPENDENT_NOMINALS_OR_ABSTAIN;NO_NATIVE_D_POS_FIT_CLAIM",
            "M":"KEEP_SIX_NATIVE_AST_AND_FIXED_E1_PRIORS;NO_FORCE_ESTIMATION",
            "B":"REAL_NATIVE_EV01_MODEL_WITH_SEPARATE_COST_AUTHORIZATION_OR_ABSTAIN",
        },
        "preserve_all_native_candidate_universes":True,
        "selected_winner_before_evaluation":"NONE",
        "metric_application":"NOT_RUN",
        "G3":"NOT_RUN",
        "G4":"NOT_RUN",
        "G5":"NOT_RUN",
    }


def deny_privileged_action(action,report):
    """Application-level fail-closed gate. Not an OS/ACL protection boundary."""
    need(type(action) is str and action in METHODOLOGICAL_ACTIONS,
         "RF02P_UNKNOWN_PRIVILEGED_ACTION")
    need(type(report) is dict and report.get("schema")==SCHEMA,
         "RF02P_ADMISSION_REPORT_REQUIRED")
    raise ArenaContractError("RF02P_ACTION_DENIED_G3_NOT_AUTHORIZED:"+action)


def build(h,visible,prospective=None):
    h=_assert_hj(h,visible)
    # The full POS-delivery series is only read through source authentication.
    # We deliberately DO NOT use any delivered_cumulative values below.
    protocol=prereg_template(h)
    future=(validate_prospective_metadata(
                prospective,h,visible["observability"]["world_public_id"])
            if prospective is not None else None)
    arm_ids={"D":[],"M":[]}
    for entry in h["candidates"]:
        arm_ids[entry["arm_id"]].append({
            "candidate_id":entry["candidate_id"],
            "structure_sha256":entry["native_structure_sha256"],
            "native_G2_trace_sha256":entry["H_j"]["trace_sha256"],
            "scored":False,
        })
    need(all(len(v)==6 for v in arm_ids.values()),
         "RF02P_WRONG_NATIVE_UNIVERSE")
    arms={
        "D":{
            "native_component_state":"ORIGINAL_GRAMMAR_SIX_ENUMERATED",
            "G2":"PASS_REAL_OMC_ENGINEERING_ONLY",
            "parameter_state":"NON_EMPIRICAL_CONFORMANCE_FIXTURE_NOT_EV01_MEASUREMENT",
            "method_native_parameter_fit":"DOES_NOT_EXIST_IN_ORIGINAL_D",
            "calibration_option":"FUTURE_INDEPENDENT_PARAMETER_PROTOCOL_NOT_EXECUTED",
            "admission":ABSENT,
            "reasons":[D_REASON,H_REASON,P_REASON],
            "selection_actor":"NONE",
            "candidate_count":6,"candidates":arm_ids["D"],
        },
        "M":{
            "native_component_state":"ORIGINAL_E1_BASE_SIX_FULL_AST_ENUMERATED",
            "G2":"PASS_REAL_OMC_ENGINEERING_ONLY",
            "parameter_state":"E1_NATIVE_FIXED_PRIORS_NOT_ESTIMATED_FROM_EV01",
            "method_native_parameter_fit":"NOT_REQUIRED_BY_SHORT_E1_ENUMERATOR",
            "calibration_option":"NO_CALIBRATION_IMPOSED_ON_ORIGINAL_METHOD",
            "admission":"ABSTAIN_G3_BUT_NATIVE_ENUMERATOR_COMPLETE",
            "reasons":[M_REASON,H_REASON,P_REASON],
            "selection_actor":"NONE",
            "candidate_count":6,"candidates":arm_ids["M"],
        },
        "B":{
            "native_component_state":"LIVE_EV01_NATIVE_INFERENCE_NOT_RUN",
            "G2":"NOT_RUN",
            "parameter_state":"UNKNOWN_NO_LIVE_EV01_CANDIDATE",
            "method_native_parameter_fit":"NOT_OBSERVED",
            "calibration_option":"NOT_AUTHORIZED_TO_CALL_PROVIDER",
            "admission":ABSENT,
            "reasons":[B_REASON,H_REASON,P_REASON],
            "selection_actor":"NONE",
            "candidate_count":0,"candidates":[],
        },
    }
    return {
        "schema":SCHEMA,
        "scope":SCOPE,
        "public_view_sha256":h["public_view_sha256"],
        "public_source_snapshot_hash":h["public_source_snapshot_hash"],
        "source_hj_report_sha256":digest(h),
        "source_hj_schema":hj.SCHEMA,
        "source_artifact_runs":h["artifact_sources"],
        "independent_os_acl_or_holdout_protection":"NOT_ESTABLISHED",
        "arms":arms,
        "preregistration_candidate":protocol,
        "prospective_evidence_metadata":future,
        "proposed_G3_new_world_available":False,
        "syntactically_valid_future_metadata_is_G3_authorization":False,
        "scientific_measurement_equivalence":"NOT_ESTABLISHED",
        "scientific_parameter_admission":"NOT_ESTABLISHED",
        "evaluation_is_conditioned_on_future_arrivals":"OFFLINE_REPLAY_NOT_ONLINE_PREDICTION",
        "unregistered_g3_actions_permitted":[],
        "next_actions":[
            "SCIENTIFIC_REVIEW_H_J_AND_CONDITIONAL_REPLAY_DEFINITION",
            "D_SELECT_EXTERNAL_NOMINAL_MEASUREMENT_PROTOCOL_OR_ABSTAIN",
            "M_RETAIN_FIXED_E1_PRIORS_AND_NO_FORCED_ESTIMATOR",
            "B_REQUEST_SEPARATE_EXPLICIT_NATIVE_CALL_AUTHORIZATION_IF_NEEDED",
            "R6_ISOLATE_FUTURE_EVALUATION_OUTCOMES_FROM_ARMS",
            "REGISTER_INDEPENDENT_FUTURE_WORLD_AND_FREEZE_CANDIDATES_BEFORE_UNSEAL",
        ],
        "result":"ABSTAIN_G3_WITH_ARM_SPECIFIC_REASONS",
        "G3":NO_G3,"G4":NO_G3,"G5":NO_G3,
        "A3":"PARTIAL",
        "R2":"PARTIAL_CONTRACTS_ENGINEERING_ONLY",
        "no_scores":True,"no_parameter_fits":True,
        "no_native_model_selection":True,"no_private_data_access":True,
        "omc_invocations":0,
        "provider_calls":0,
        "independent_scientific_adjudication":"PENDING",
    }


def main():
    p=argparse.ArgumentParser(description="RF-02 P: no G3 without science")
    p.add_argument("--visible",required=True,type=Path)
    p.add_argument("--hj-report",required=True,type=Path)
    p.add_argument("--prospective-metadata",type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    need(not args.out.exists(),"RF02P_REFUSE_OVERWRITE")
    visible=json.loads(args.visible.read_text(encoding="utf-8"))
    report=json.loads(args.hj_report.read_text(encoding="utf-8"))
    spec=(json.loads(args.prospective_metadata.read_text(encoding="utf-8"))
          if args.prospective_metadata else None)
    result=build(report,visible,spec)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(result)+bytes([10]))
    print(json.dumps({"result":result["result"],"D":result["arms"]["D"]["admission"],
                      "M":result["arms"]["M"]["admission"],
                      "B":result["arms"]["B"]["admission"],
                      "G3":result["G3"]},sort_keys=True))


if __name__=="__main__":
    main()
