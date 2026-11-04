"""F4 evaluator-only one-count observability witness for the KNOWN A/B pair.

This is *post-hoc experimental design* over the existing O0 grid, NOT an
authorized O2 observation, a sensor actually installed, an optimal sensor
over all designs, or a blind D/B/M inference. Both previously known worlds
have identical POS deliveries and O1 preparation aggregate, but differ in
a single stage-specific completed-dispatch count at the inherited t=6
checkpoint. Future tests need independent worlds and precommitted policy.

All event and case-level information is restricted to the evaluator.
The public report contains only the stage-level cumulative counts from
an already disclosed DEVELOPMENT control; no case ids or event times.
"""
from __future__ import annotations

import argparse
import json
from fractions import Fraction as Q
from pathlib import Path

from scripts.arena_cafe import f4_b2_processing_intervention as apm
from scripts.arena_cafe import f4_latent_downstream_symmetry as symmetry
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-arena-f4-dispatch-single-count-observability/0.1"
GRID=tuple(Q(i) for i in (0,2,4,6,8,10))
SENSOR_STAGE="despacho"
DISCRIMINATING_CUTOFF=Q(6)
LATER_NONDISCRIMINATING_CUTOFF=Q(10)
KEYS=symmetry.BASELINE_KEYS


def completed_service_times(events,stage,expected_cases):
    """Validate end timestamps as a physical *stage-labeled* event channel.

    The start/finish pairs are used only to authenticate the synthetic
    evaluator's case continuity; the proposed scalar measurement is the
    aggregated completion COUNT, not its full private event list.
    """
    need(stage in apm.STAGES,"F4O2_UNKNOWN_STAGE")
    need(type(events) is list and bool(events) and
         type(expected_cases) is set and len(expected_cases)==15,
         "F4O2_MISSING_PHYSICAL_EVALUATOR_EVENTS")
    visits={}
    for row in events:
        if row.get("stage")!=stage:
            continue
        need(type(row) is dict and
             set(row)=={"case_id","stage","event_type","t_minutes_exact",
                        "resource_id","source"} and
             row["event_type"] in ("etapa_entrada",
                                   "servicio_inicio","servicio_fin") and
             row["source"]=="instrumentacion_fisica" and
             row["case_id"] in expected_cases,
             "F4O2_UNAUTHORIZED_STAGE_EVENT")
        data=visits.setdefault(row["case_id"],{})
        kind=row["event_type"]
        need(kind not in data,"F4O2_DUPLICATE_STAGE_EVENT")
        try:
            timestamp=Q(row["t_minutes_exact"])
        except (ValueError,ZeroDivisionError,TypeError):
            need(False,"F4O2_INVALID_STAGE_CLOCK")
        need(timestamp>=0,"F4O2_INVALID_STAGE_CLOCK")
        resource=row["resource_id"]
        need((resource is None if kind=="etapa_entrada" else
              type(resource) is str and resource.startswith(stage+"-r")),
             "F4O2_INVALID_RESOURCE_PROVENANCE")
        data[kind]=(timestamp,resource)
    need(set(visits)==expected_cases,
         "F4O2_STAGE_CASE_COVERAGE_INCOMPLETE")
    ends=[]
    for case in expected_cases:
        visit=visits[case]
        need(set(visit)=={"etapa_entrada","servicio_inicio","servicio_fin"},
             "F4O2_STAGE_INTERVAL_INCOMPLETE")
        enter,start,finish=(visit[k][0] for k in (
            "etapa_entrada","servicio_inicio","servicio_fin"))
        need(enter<=start<finish,
             "F4O2_NONPHYSICAL_SERVICE_INTERVAL")
        need(visit["servicio_inicio"][1]==visit["servicio_fin"][1],
             "F4O2_RESOURCE_CHANGED_DURING_SERVICE")
        ends.append(finish)
    return tuple(sorted(ends))


def counts_before(times,grid=GRID):
    """Strictly before each cutoff; an event AT a cutoff is not counted."""
    need(len(grid)>=2 and all(type(t) is Q for t in grid) and
         grid[0]==0 and all(a<b for a,b in zip(grid,grid[1:])),
         "F4O2_INVALID_COUNT_GRID")
    return tuple(sum(t<cutoff for t in times) for cutoff in grid)


def closest_event_margin(times,cutoff=DISCRIMINATING_CUTOFF):
    """Post-hoc oracle-only timestamp-jitter bound, not measured accuracy."""
    need(times and type(cutoff) is Q and cutoff>0,
         "F4O2_MARGIN_INPUT_INVALID")
    margin=min(abs(t-cutoff) for t in times)
    need(margin>0,"F4O2_COUNT_ON_CUTOFF_UNSTABLE")
    return margin


def two_candidate_decision(observed_count,candidate_counts):
    """Finite pair consistency only; NOT identification of other worlds."""
    need(type(observed_count) is int and observed_count>=0,
         "F4O2_BAD_OBSERVED_INTEGER_COUNT")
    need(type(candidate_counts) is dict and
         set(candidate_counts)==set(KEYS) and
         all(type(v) is int and v>=0 for v in candidate_counts.values()),
         "F4O2_BAD_ORACLE_PAIR_COUNTS")
    matches=[name for name in KEYS
             if observed_count==candidate_counts[name]]
    if len(matches)==2:
        status="AMBIGUOUS_WITHIN_DECLARED_TWO_WORLD_PAIR"
    elif len(matches)==1:
        status="ONLY_ONE_OF_THE_TWO_DECLARED_WORLDS_COMPATIBLE"
    else:
        status="NEITHER_OF_TWO_DECLARED_WORLDS_COMPATIBLE"
    return {
        "status":status,
        "number_of_compatible_declared_worlds":len(matches),
        "compatible_declared_world_keys":matches,
        "other_unmodeled_worlds_excluded":False,
        "blind_or_general_causal_identification":False,
    }


def build(o0,o1):
    """Known-truth pair, baseline only, no intervention data in O2 sensor."""
    validate_a1_visible(o0,"O0")
    validate_a1_visible(o1,"O1")
    ref=apm.build(o0,o1)
    need(ref["same_O0_O1_public_evidence_for_both_known_worlds"] and
         ref["all_15_baseline_terminal_timestamps_identical"] and
         ref["baseline_deliveries_t10"]==dict.fromkeys(KEYS,8) and
         ref["stressed_deliveries_t10"]==
            {KEYS[0]:6,KEYS[1]:8},
         "F4O2_REFERENCE_F4_PAIR_CHANGED")
    arrivals=tuple(Q(x["t_minutes_exact"]) for x in
                   o0["construction"]["pos_arrival_events"])
    cases={x["case_id"] for x in
           o0["construction"]["pos_arrival_events"]}
    need(len(cases)==15,"F4O2_PUBLIC_POS_CASES_DRIFT")
    pair=symmetry.private_pair()
    sample={}
    terminal={}
    prep={}
    margins={}
    for key,config in zip(KEYS,pair):
        intervals=apm.analytic_intervals(config,arrivals)
        apm.verify_des_snapshots(config,arrivals,intervals)
        if key==KEYS[0]:
            apm.verify_original_full(intervals)
        events=apm.physical_event_rows(intervals)
        d=completed_service_times(events,SENSOR_STAGE,cases)
        p=completed_service_times(events,"preparacion",cases)
        t=completed_service_times(events,"transferencia_final",cases)
        sample[key]=counts_before(d)
        prep[key]=counts_before(p)
        terminal[key]=counts_before(t)
        margins[key]=closest_event_margin(d)
    need(sample[KEYS[0]]==(0,0,2,4,6,9) and
         sample[KEYS[1]]==(0,0,2,5,7,9),
         "F4O2_KNOWN_DISPATCH_STAGE_COUNT_DRIFT")
    need(terminal[KEYS[0]]==terminal[KEYS[1]]==
         (0,0,2,4,6,8) and
         prep[KEYS[0]]==prep[KEYS[1]],
         "F4O2_UPSTREAM_OR_TERMINAL_NEGATIVE_CONTROL_CHANGED")
    informative=[str(t) for i,t in enumerate(GRID)
                 if sample[KEYS[0]][i]!=sample[KEYS[1]][i]]
    need(informative==["6","8"] and
         sample[KEYS[0]][-1]==sample[KEYS[1]][-1]==9,
         "F4O2_ONLY_RETROSPECTIVE_GRID_WITNESS_CHANGED")
    candidate={key:sample[key][GRID.index(DISCRIMINATING_CUTOFF)]
               for key in KEYS}
    ambiguity={key:sample[key][-1] for key in KEYS}
    need(candidate=={KEYS[0]:4,KEYS[1]:5} and
         ambiguity==dict.fromkeys(KEYS,9),
         "F4O2_SINGLE_COUNT_DISCRIMINATION_LOST")
    need(two_candidate_decision(4,candidate)[
         "number_of_compatible_declared_worlds"]==1 and
         two_candidate_decision(5,candidate)[
         "number_of_compatible_declared_worlds"]==1 and
         two_candidate_decision(9,ambiguity)[
         "number_of_compatible_declared_worlds"]==2,
         "F4O2_PAIR_CONSISTENCY_RULE_DRIFT")
    minimum_oracle_margin=min(margins.values())
    need(minimum_oracle_margin==Q(108,935),
         "F4O2_POSTHOC_JITTER_MARGIN_DRIFT")
    return {
        "schema":SCHEMA,
        "phase":"F4_KNOWN_EVALUATOR_POSTHOC_SENSOR_WITNESS_NOT_G5",
        "source_o0_hash":o0["source_snapshot_hash"],
        "source_o1_hash":o1["source_snapshot_hash"],
        "prior_f4_b2_evaluator_report_sha256":digest(ref),
        "worlds_already_disclosed":True,
        "existing_grid_minutes_exact":[str(t) for t in GRID],
        "candidate_new_observation":
            "ONE_STAGE_LABELED_DISPATCH_COMPLETIONS_CUMULATIVE_BEFORE_T6",
        "candidate_source":"NEW_DISPATCH_FINISH_COUNTER_NOT_IN_O0_OR_O1",
        "count_of_additional_aggregated_scalars":1,
        "measurement_window":"[0,6)_UNSTRESSED_BASELINE",
        "same_preexisting_POS_O0_and_PREPARATION_O1_in_both_worlds":True,
        "posthoc_stage_and_cutoff_selection_after_worlds_known":True,
        "not_minimum_across_all_possible_sensors_or_worlds":True,
        "not_installed_or_independently_validated_sensor":True,
        "requires_correct_stage_and_event_type_labels":True,
        "no_missing_duplicated_or_misattributed_events_assumed":True,
        "candidate_completed_dispatch_counts_by_grid":{
            key:list(sample[key]) for key in KEYS},
        "negative_control_terminal_counts_by_grid":{
            key:list(terminal[key]) for key in KEYS},
        "negative_control_preparation_counts_identical":True,
        "informative_grid_cutoffs_in_this_known_pair":informative,
        "dispatch_count_at_t6_by_world":candidate,
        "dispatch_count_at_t10_by_world":ambiguity,
        "t6_two_world_rule_for_count_4":two_candidate_decision(
            4,candidate),
        "t6_two_world_rule_for_count_5":two_candidate_decision(
            5,candidate),
        "t10_two_world_rule_for_count_9":two_candidate_decision(
            9,ambiguity),
        "posthoc_smallest_distance_to_t6_of_any_dispatch_completion_exact":
            str(minimum_oracle_margin),
        "timestamp_error_guarantee_conditional_on_per_event_bound":
            "STRICTLY_LESS_THAN_POSTHOC_MARGIN_WITH_PERFECT_EVENT_CAPTURE",
        "timing_margin_is_oracle_RETROSPECTIVE_not_sensor_calibration":True,
        "t6_baseline_measurement_is_from_a_separate_run_before_any_stress":True,
        "counterfactual_stress_would_reset_initial_state_at_t0":True,
        "no_post_t6_events_used_to_compute_observed_t6_count":True,
        "no_stage_event_logs_or_case_ids_in_report":True,
        "no_private_event_data_sent_to_D_B_M":True,
        "O2_experiment_actually_performed":False,
        "O2_authorized_as_arm_input":False,
        "F5_independent_reserve":"NOT_CREATED",
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
        "P_PM14":"NOT_TRIGGERED","provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--o0",type=Path,required=True)
    p.add_argument("--o1",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"F4O2_REFUSE_OVERWRITE")
    o0=json.loads(args.o0.read_text(encoding="utf-8"))
    o1=json.loads(args.o1.read_text(encoding="utf-8"))
    result=build(o0,o1)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({
        "phase":result["phase"],
        "cutoffs":result["informative_grid_cutoffs_in_this_known_pair"],
        "t6":result["dispatch_count_at_t6_by_world"],
        "t10":result["dispatch_count_at_t10_by_world"],
        "G5":result["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
