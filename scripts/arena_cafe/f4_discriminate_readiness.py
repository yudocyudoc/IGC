"""DISCRIMINATE-01: exact evidence obligations, not a second model search.

A fixed, retrospective F4 pair is compatible with known O0 and excluded
under *exact deterministic* O1 operators. The thresholds computed here are
NECESSARY sizes of a hypothetical absolute discrepancy allowance to avoid
excluding a given pair member, NOT observed sensor errors, confidence
intervals, statistical fit, model selection, or approval to start F5.

This module consumes ONLY the already published O0/O1 envelopes, original
F4 development witness and F4 O1 operator report. It neither runs a DES
nor calls Buffalo, PM4Py, OpenModelica or any provider.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import json
from pathlib import Path

from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_cafe import f4_rival_bottleneck_witness as f4
from scripts.arena_cafe import f4_o1_preparation_operator as h
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-arena-discriminate01-evidence-readiness/0.1"
COMPONENTS=("completed_preparation_count",
            "mean_completed_preparation_service_minutes")


def required_absolute_allowance(predicted,observed):
    """Coordinatewise necessary absolute-discrepancy allowance; no grid."""
    need(type(predicted) is tuple and type(observed) is tuple and
         len(predicted)==len(observed)==2 and
         all(type(x) in (int,str,Q) for x in predicted+observed),
         "DISC01_BAD_OBSERVABLES")
    a=Q(predicted[0]);b=Q(observed[0])
    t=Q(predicted[1]);s=Q(observed[1])
    need(all(x>=0 for x in (a,b,t,s)) and
         all(x.denominator==1 for x in (a,b)),
         "DISC01_BAD_COUNT_OR_SERVICE")
    return abs(a-b),abs(t-s)


def sufficient_to_not_exclude_given_allowances(
        requirement, count_allowance, mean_service_allowance):
    """Only within the two **fixed** deterministic hypotheses.

    An inequality pass is NOT physical compatibility or evidence of truth.
    This pure helper supports reasoning about bounded errors *if supplied*
    by a separately validated, empirical pilot.
    """
    need(type(requirement) is tuple and len(requirement)==2 and
         type(count_allowance) in (str,int,Q) and
         type(mean_service_allowance) in (str,int,Q),
         "DISC01_BAD_ALLOWANCE_SHAPE")
    c,t=Q(count_allowance),Q(mean_service_allowance)
    need(c>=0 and t>=0 and
         all(type(x) is Q and x>=0 for x in requirement),
         "DISC01_NEGATIVE_OR_UNGROUNDED_ALLOWANCE")
    return requirement[0]<=c and requirement[1]<=t


def build(o0,o1,witness,o1_result):
    validate_a1_visible(o0,"O0")
    validate_a1_visible(o1,"O1")
    need(witness.get("schema")==f4.SCHEMA and
         witness.get("source_snapshot_hash")==o0["source_snapshot_hash"] and
         witness.get("source_visible_sha256")==digest(o0) and
         witness.get("phase")=="F4_DEVELOPMENT_CONSTRUCTIVE_WITNESS_NOT_F5" and
         witness.get("F5_new_independent_worlds")=="NOT_CREATED" and
         witness.get("G4")==witness.get("G5")=="NOT_RUN" and
         witness.get("no_new_DES_or_parameter_grid_or_provider_or_PM") is True,
         "DISC01_F4_WITNESS_NOT_BOUND_TO_ORIGINAL_O0")
    need(o0["observability"]["world_public_id"]==
         o1["observability"]["world_public_id"] and
         o0["observability"]["cutoff_minutes_exact"]==
         o1["observability"]["cutoff_minutes_exact"]=="10" and
         o0["construction"]["pos_arrival_events"]==
         o1["construction"]["pos_arrival_events"] and
         o0["construction"]["observation_series"]==
         o1["construction"]["observation_series"] and
         "physical_observation" not in o0["construction"],
         "DISC01_S0_S1_NOT_SAME_WORLD_OR_CROSS_CONDITION_LEAK")
    need(o1_result.get("schema")==h.SCHEMA and
         o1_result.get("source_o0_snapshot_hash")==
            o0["source_snapshot_hash"] and
         o1_result.get("source_o1_snapshot_hash")==
            o1["source_snapshot_hash"] and
         o1_result.get("witness_sha256")==digest(witness) and
         o1_result.get("operation")==
            "POST_HOC_EVALUATOR_SENSITIVITY_NOT_NATIVE_INFERENCE" and
         o1_result.get("status")==
           "BOTH_KNOWN_F4_RIVALS_EXCLUDED_BY_EXACT_O1_PREPARATION_OPERATOR" and
         o1_result.get("exact_matches_under_S1")==[] and
         o1_result.get("real_sensor_error_model_estimated") is False and
         o1_result.get("G4")==o1_result.get("G5")=="NOT_RUN",
         "DISC01_O1_RESULT_NOT_BOUND_OR_NOT_EXACT_REJECTION")
    p=o1["construction"]["physical_observation"]
    observed=(p["n_completed_stage_services"],p["mean_service_minutes_exact"])
    need(observed==(9,"15/17") and
         o1_result["S1_o1_has_n_completed_preparation_services"]==observed[0] and
         o1_result["S1_o1_mean_preparation_service_minutes_exact"]==observed[1] and
         len(o1_result["S1_two_hypothesis_measurement_comparisons"])==2,
         "DISC01_ORIGINAL_O1_OBSERVABLES_DRIFT")
    requirements={}
    for item in o1_result["S1_two_hypothesis_measurement_comparisons"]:
        name=item["candidate_id"]
        need(name in dict(h.HYPOTHESES) and name not in requirements,
             "DISC01_DUPLICATE_OR_NEW_HYPOTHESIS")
        original=witness["S0_model_baselines"][name]
        need(item["model_prep_mean_service_minutes_exact"]==
             original["service_minutes_exact"]["preparacion"] and
             item["model_prep_mean_service_minutes_exact"]==
             dict(h.HYPOTHESES)[name][0] and
             original["delivered_cumulative"]==
             witness["S0_observed_delivered_cumulative"] and
             item["observed_prep_completed_services_before_cutoff"]==
                 observed[0] and
             item["observed_prep_mean_service_minutes_exact"]==
                 observed[1],
             "DISC01_F4_HJ_NOT_SAME_MODEL_OR_OBSERVATION")
        predicted=(
            item["model_prep_completed_services_before_cutoff"],
            item["model_prep_mean_service_minutes_exact"])
        req=required_absolute_allowance(predicted,observed)
        need(item["mean_service_residual_minutes_exact"]==
             str(Q(predicted[1])-Q(observed[1])) and
             item["count_matches_exactly"]==(req[0]==0) and
             item["mean_service_matches_exactly"]==(req[1]==0) and
             item["both_preparation_observables_match_exactly"] is False,
             "DISC01_INCONSISTENT_ORIGINAL_F4_HJ_RESIDUAL")
        requirements[name]=req
    need(set(requirements)=={"PREP_SLOW_A","DISPATCH_SLOW_B"} and
         requirements["PREP_SLOW_A"]==(Q(0),Q(2,17)) and
         requirements["DISPATCH_SLOW_B"]==(Q(6),Q(24,85)),
         "DISC01_FIXED_F4_EVIDENCE_THRESHOLD_DRIFT")
    # This is the least coordinatewise allowance permitting BOTH
    # fixed witnesses *not to be excluded* by these two metrics,
    # not their joint likelihood, nor confidence coverage.
    req_both=tuple(max(req[i] for req in requirements.values()) for i in (0,1))
    req_any=tuple(requirements["PREP_SLOW_A"])
    need(req_both==(Q(6),Q(24,85)) and req_any==(Q(0),Q(2,17)),
         "DISC01_REQUIRED_ALLOWANCE_CONTRADICTION")
    rows=[{
        "candidate_id":name,
        "count_error_required_to_avoid_exclusion_orders_exact":str(req[0]),
        "mean_service_discrepancy_required_minutes_exact":str(req[1]),
        "count_observation_is_completed_services_pre_cutoff":True,
        "mean_observation_is_conditional_on_completed_services":True,
        "these_are_observed_residuals_NOT_empirical_sensor_error_bounds":True,
        "not_a_true_mechanism_or_statistical_admission":True,
    } for name,req in sorted(requirements.items())]
    blockers=[
        {"id":"F3_THREE_AUTHENTIC_METHODS","state":"BLOCKED",
         "basis":"A3_PARTIAL_BUFFALO_EV01_LIVE_NOT_AUTHORIZED"},
        {"id":"OBSERVATIONAL_ERROR_BUDGET","state":"NOT_VERIFIED",
         "basis":"NO_EMPIRICAL_SENSOR_PRECISION_CLOCK_SYNC_DROPOUT"},
        {"id":"PROCESS_VARIATION_PILOT","state":"NOT_RUN",
         "basis":"NO_SEPARATE_PILOT_FOR_HETEROGENEITY_CENSORING_REPLICATION"},
        {"id":"ACTION_OPERATIONAL_FEASIBILITY","state":"NOT_ASSESSED",
         "basis":"SPACE_PERSONNEL_EQUIPMENT_INVENTORY_COST_NOT_ASSESSED"},
        {"id":"NEW_F5_RESERVE_AND_ACCESS_ISOLATION","state":"NOT_CREATED",
         "basis":"KNOWN_F4_DEV_WORLD_CANNOT_BE_HOLDOUT;CONDITION_ACL_NOT_CERTIFIED"},
        {"id":"G4_PREDICTIONS_AND_ABSTENTIONS","state":"NOT_RUN",
         "basis":"NO_THREE_NATIVE_FROZEN_PREDICTIONS_FOR_NEW_RESERVED_WORLDS"},
    ]
    return {
        "schema":SCHEMA,
        "scope":"KNOWN_EV01_RETROSPECTIVE_F4_ONLY",
        "o0_public_source_hash":o0["source_snapshot_hash"],
        "o1_public_source_hash":o1["source_snapshot_hash"],
        "original_F4_witness_digest":digest(witness),
        "original_F4_O1_operator_digest":digest(o1_result),
        "same_public_world":True,
        "question_type":"PREDICTIVE_DIFFERENCE_UNDER_SAME_ACTION_NOT_BUSINESS_UTILITY",
        "question":"Can two mechanisms compatible under S0 produce different observable outcomes under one feasible intervention, and does S1 narrow the compatible class without false uniqueness?",
        "hypothetical_action":"ONE_ADDITIONAL_PREPARATION_SERVER_FROM_T0",
        "development_only_counterfactual_gap_orders":witness[
             "absolute_counterfactual_divergence_orders"],
        "two_observable_components":list(COMPONENTS),
        "S1_observed_count":observed[0],
        "S1_observed_mean_service_minutes_exact":observed[1],
        "necessary_allowances_for_each_FIXED_hypothesis":rows,
        "necessary_allowance_to_avoid_excluding_at_least_one_FIXED_hypothesis":{
            "count_orders_exact":str(req_any[0]),
            "mean_service_minutes_exact":str(req_any[1]),
            "only_the_weakest_discrepancy_hypothesis_in_this_pair":True,
        },
        "coordinatewise_allowance_needed_to_avoid_excluding_BOTH_FIXED_hypotheses":{
            "count_orders_exact":str(req_both[0]),
            "mean_service_minutes_exact":str(req_both[1]),
        },
        "no_empirical_allowance_chosen":True,
        "no_inferred_sensor_error_from_deterministic_residuals":True,
        "no_inferred_model_variability_from_a_single_15_order_trace":True,
        "exact_condition_has_no_survivors":True,
        "finite_two_hypothesis_model_gap_not_universal_infeasibility":True,
        "not_yet_a_pre_registered_test":True,
        "F5_readiness_blockers":blockers,
        "F5_readiness":"NOT_READY",
        "required_pilot_evidence":[
            "INSTRUMENT_CLOCK_SYNC_AND_TIMESTAMP_RESOLUTION",
            "DIRECT_SERVICE_INTERVAL_VALIDATION_PER_STAGE",
            "MISSING_EVENT_AND_CENSORING_PROTOCOL",
            "SERVICE_TIME_HETEROGENEITY_AND_INDEPENDENT_REPLICAS",
            "PHYSICAL_ACTION_CAPACITY_SPACE_STAFF_INVENTORY_COST",
            "TRUE_CONDITION_ISOLATION_AND_NEW_UNSEEN_RESERVE",
            "NATIVE_D_B_M_OUTPUT_AND_ABSTENTION_CONTRACTS",
        ],
        "PM_test":"CONDITIONAL_ONLY_IF_OBSERVED_VARIATION_NOT_RECOVERED_BY_B1_B2",
        "PM_comparison":"SAME_RAW_LOGS_AND_SENSORS_WITH_WITHOUT_P_PER_ARM",
        "PM_prior_EV01":"ONE_ROUTE_NO_INCREMENT_OVER_B1",
        "PM_attribution_or_ablation":"NOT_RUN",
        "no_model_selection_no_parameter_grid_no_new_world":True,
        "no_DES_PM4Py_OMC_or_provider_calls":True,
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--o0",type=Path,required=True)
    parser.add_argument("--o1",type=Path,required=True)
    parser.add_argument("--witness",type=Path,required=True)
    parser.add_argument("--o1-operator",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    need(not args.out.exists(),"DISC01_REFUSE_OVERWRITE")
    load=lambda p:json.loads(p.read_text(encoding="utf-8"))
    result=build(load(args.o0),load(args.o1),load(args.witness),
                 load(args.o1_operator))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({
        "status":result["F5_readiness"],
        "blocking_evidence":len(result["F5_readiness_blockers"]),
        "exact_S1_survivors":0,
        "A3":result["A3"],"G4":result["G4"],"G5":result["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
