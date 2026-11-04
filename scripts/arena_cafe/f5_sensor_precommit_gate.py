"""F5 candidate measurement policy and epistemic abstention gate.

This is a frozen *prospective-use specification*, selected POST-HOC from the
already disclosed F4 two-world pair. It is NOT a blind G4/G5 preregistration,
a newly authorized A1 O2 arm input, independent physical data, a measured
sensor accuracy, or evidence that D/B/M can infer the mechanism.

The policy is generated without reading any physical-event file. Probe takes
only a strictly pre-cutoff pilot CSV via the existing F5 ingest contract and
reports a descriptive two-hypothesis consistency result. The scorer imports
neither evaluator DES/EV01 nor a private truth/configuration module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.arena_cafe import pilot_event_capture as pilot
from scripts.arena_v0_contract import canonical, digest

POLICY_SCHEMA="igc-cafe-f5-precommitted-candidate-sensor/0.1"
PROBE_SCHEMA="igc-cafe-f5-declared-pilot-probe-gate/0.1"
A="REFERENCE_EV01_WORLD_A"
B="SWAPPED_DOWNSTREAM_WORLD_B"
STAGE="despacho"
CUTOFF="6"
KNOWN_COUNTS={A:4,B:5}


def need(ok,tag):
    if not ok:
        raise ValueError(tag)


def policy():
    """Predeclare the same selection *before future data*, not before PR158."""
    body={
        "schema":POLICY_SCHEMA,
        "candidate_id":"DISPATCH_COMPLETIONS_PRE_T6_KNOWN_F4_PAIR",
        "selection_origin":
            "POSTHOC_PR158_KNOWN_EV01_PAIR_NO_BLIND_DISCOVERY",
        "selection_is_prospective_for_existing_EV01":False,
        "future_evaluation_rule_frozen_before_new_data":True,
        "requires_independent_new_data_not_supplied_here":True,
        "stage":STAGE,
        "event_type":"servicio_fin",
        "count_window":"[0,6)",
        "cutoff_minutes_exact":CUTOFF,
        "time_rule":"EVENT_TIMESTAMPS_STRICTLY_LESS_THAN_CUTOFF",
        "counter_semantics":"ONE_COMPLETED_SERVICE_VISIT_PER_PHYSICAL_CASE",
        "physical_source_required":"instrumentacion_fisica",
        "clock_alignment_required":"SINGLE_DECLARED_CLOCK_FOR_POS_AND_STAGE",
        "clock_calibration_independently_established":False,
        "event_capture_completeness_independently_established":False,
        "requirements_before_scientific_interpretation":[
            "INDEPENDENT_SENSOR_COVERAGE_AUDIT_FOR_DISPATCH_COMPLETIONS",
            "CLOCK_RESOLUTION_ALIGNMENT_AND_ERROR_CALIBRATION",
            "CORRECT_STAGE_EVENT_RESOURCE_AND_VISIT_LABELS",
            "SEPARATE_UNSTRESSED_BASELINE_OBSERVATION_BEFORE_ACTION",
            "EVALUATOR_TRUTH_HIDDEN_FROM_SELECTION_AND_ARM_PREDICTION",
            "PREDECLARED_INDEPENDENT_WORLD_AND_HOLDOUT_GATES",
            "D_B_M_NATIVE_COMPARISON_IF_CLAIMING_METHOD_VALUE",
        ],
        "closed_reference_hypotheses_only":{
            A:4,B:5,
        },
        "unexpected_count_policy":"ABSTAIN_DO_NOT_INVENT_THIRD_MECHANISM",
        "matching_one_of_two_is_not_general_identification":True,
        "sensor_cost_and_operational_feasibility":"NOT_MEASURED",
        "does_not_modify_A1_O0_O1_or_authorize_O2":True,
        "stage_selection_fixed_not_reselected_after_probe":True,
        "experiment_blind_reserve":"NOT_CREATED",
        "G4":"NOT_RUN","G5":"NOT_RUN",
    }
    return {**body,"policy_sha256":digest(body)}


def validate_policy(p):
    need(type(p) is dict and p==policy(),
         "F5_SENSOR_POLICY_NOT_EXACT_FROZEN_CANDIDATE")
    need(p["policy_sha256"]==digest({
        k:v for k,v in p.items() if k!="policy_sha256"}),
         "F5_SENSOR_POLICY_SHA256_MISMATCH")
    return p["policy_sha256"]


def probe(frozen_policy,events,*,source_context,event_file_sha256=None):
    """Read only a pre-t6 pilot view; no independent-sensor certification.

    Returns a two-candidate DESCRIPTIVE consistency result or an abstention.
    The absence of a recorded service_finish cannot prove sensor drop-out:
    it might equally be a service still in progress at the cutoff.
    """
    policy_hash=validate_policy(frozen_policy)
    need(source_context in ("synthetic_fixture","real_pilot_declared"),
         "F5_SENSOR_PROBE_SOURCE_CONTEXT_INVALID")
    report=pilot.build(events,cutoff_minutes_exact=CUTOFF,
                       source_context=source_context)
    need(report["cutoff_minutes_exact"]==CUTOFF and
         report["time_window"]=="[0,cutoff)" and
         report["instrumental_error_calibrated"] is False and
         report["physical_clock_accuracy_known"] is False,
         "F5_SENSOR_PROBE_UNAUTHORIZED_PILOT_ASSERTION")
    count=None
    baseline_status=report["stage_aggregates_status"]
    if baseline_status=="DESCRIPTIVE_SAME_DECLARED_CLOCK_ONLY":
        record=report["stage_completed_only_descriptives"].get(STAGE)
        if record is not None:
            count=record["completed_services_pre_cutoff"]
            need(type(count) is int and count>=0,
                 "F5_SENSOR_PROBE_BAD_PHYSICAL_COUNT")

    matches=[name for name in (A,B) if count is not None and
             count==KNOWN_COUNTS[name]]
    if count is None:
        outcome="ABSTAIN_NO_USABLE_DISPATCH_COUNT_OR_SHARED_CLOCK"
    elif len(matches)==1:
        outcome="CONDITIONAL_CONSISTENCY_WITH_ONE_KNOWN_PAIR_HYPOTHESIS"
    elif len(matches)==0:
        outcome="ABSTAIN_NEITHER_KNOWN_HYPOTHESIS_MATCHES"
    else:
        need(False,"F5_SENSOR_PROBE_PAIR_COUNTS_NOT_SEPARATED")
    need(type(event_file_sha256) in (str,type(None)) and
         (event_file_sha256 is None or
          (len(event_file_sha256)==71 and
           event_file_sha256.startswith("sha256:"))),
         "F5_SENSOR_PROBE_INPUT_FILE_HASH_INVALID")
    return {
        "schema":PROBE_SCHEMA,
        "policy_sha256":policy_hash,
        "source_context_declared_not_verified":source_context,
        "input_file_sha256":event_file_sha256,
        "pilot_schema":report["schema"],
        "observed_stage":STAGE,
        "cutoff_minutes_exact":CUTOFF,
        "physical_services_completed_pre_cutoff":count,
        "stage_count_ingest_status":baseline_status,
        "two_known_worlds_consistency_status":outcome,
        "compatible_prior_known_worlds":matches,
        "known_pair_only_not_exclusion_of_other_physical_worlds":True,
        "not_d_b_m_inference_or_predictive_score":True,
        "not_necessarily_reproducible_sensor_measurement":True,
        "no_event_dropouts_identifiable_from_count_alone":True,
        "pilot_event_clock_calibration_verified":False,
        "pilot_event_capture_completeness_verified":False,
        "source_origin_independently_attested":False,
        "source_world_independent_of_EV01_verified":False,
        "observed_count_is_not_a_scientifically_identified_mechanism":True,
        "scientific_identification":"NOT_ESTABLISHED",
        "new_condition_O2_admitted_to_A1_arms":False,
        "arm_models_or_inference_executed":False,
        "uses_no_later_than_t6_events":True,
        "no_case_records_or_event_timestamps_released":True,
        "method_incremental_value":"NOT_TESTED",
        "F5_independent_reserve":"NOT_CREATED",
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
        "provider_calls":0,
    }


def _write_new(path,data):
    p=Path(path)
    need(not p.exists(),"F5_SENSOR_REFUSE_OVERWRITE")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(canonical(data)+b"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    freeze=sub.add_parser("freeze")
    freeze.add_argument("--out",type=Path,required=True)
    run=sub.add_parser("probe")
    run.add_argument("--policy",type=Path,required=True)
    run.add_argument("--events",type=Path,required=True)
    run.add_argument("--source-context",choices=(
        "synthetic_fixture","real_pilot_declared"),required=True)
    run.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.command=="freeze":
        p=policy()
        _write_new(args.out,p)
        print(json.dumps({
            "status":"POSTHOC_SELECTION_FROZEN_FOR_FUTURE_DATA_ONLY",
            "policy_sha256":p["policy_sha256"],
            "G5":"NOT_RUN"},sort_keys=True))
    else:
        p=json.loads(args.policy.read_text(encoding="utf-8"))
        rows=pilot.read_rows(args.events,pilot.EVENT_FIELDS)
        sha="sha256:"+hashlib.sha256(args.events.read_bytes()).hexdigest()
        out=probe(p,rows,source_context=args.source_context,
                  event_file_sha256=sha)
        _write_new(args.out,out)
        print(json.dumps({
            "status":out["two_known_worlds_consistency_status"],
            "scientific_identification":out["scientific_identification"],
            "G5":out["G5"]},sort_keys=True))


if __name__=="__main__":
    main()
