"""F4 evaluator-only O1 measurement operator for the two O0-compatible rivals.

Does NOT mutate F4 witnesses, use evaluator FULL data, infer hidden stages,
run PM, or deliver O1 to O0 producers. The sole observed O1 source is the
A1 *authorized* censored preparation aggregate. The correspondences are
conditional on each rival's explicitly posited "preparacion" stage.

Computes count of completed preparation services before t=10 from the
original DES's stage-0 conservation, and mean duration from the DES's exact,
constant service law. Never pretends that DES snapshots contain wait times
of individual orders or that observational sensor error was measured.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import json
from pathlib import Path

from scripts.arena_v0_contract import canonical,digest
from scripts.arena_cafe.native_handoff import need,validate_a1_visible
from scripts.arena_cafe import f4_rival_bottleneck_witness as f4
from scripts.arena_physical import des_engine as des

SCHEMA="igc-arena-f4-o1-preparation-observation-operator/0.1"
EARLY=Q(1,1000000)
HYPOTHESES=(("PREP_SLOW_A",f4.A_SERVICE),
            ("DISPATCH_SLOW_B",f4.B_SERVICE))


def _completed_preparation(config,arrivals,cutoff):
    """Number that left first stage by (strictly) cutoff.

    Run two exact rational snapshots, the latter used only to ensure there
    is no equality-at-cutoff event that invalidates the strict rule.
    This does NOT count delivery, and adds no private event-log access.
    """
    need(cutoff>EARLY,"F4O1_CUTOFF_TOO_SMALL")
    a,b=des.run_toy_engine(config,arrivals,(Q(0),cutoff-EARLY,cutoff))[1:]
    completed=lambda s:s.accepted_cum_orders-(
        s.stage_waiting[0]+s.stage_in_service[0])
    count_a,count_b=completed(a),completed(b)
    need(count_a==count_b and 0<count_a<=len(arrivals),
         "F4O1_CUTOFF_BOUNDARY_OR_INVALID_PREP_COUNT")
    return count_a


def build(o0,o1,witness):
    validate_a1_visible(o0,"O0")
    validate_a1_visible(o1,"O1")
    need(witness.get("schema")==f4.SCHEMA and
         witness.get("source_snapshot_hash")==o0["source_snapshot_hash"] and
         witness.get("source_visible_sha256")==digest(o0) and
         witness.get("phase")=="F4_DEVELOPMENT_CONSTRUCTIVE_WITNESS_NOT_F5" and
         witness.get("F5_new_independent_worlds")=="NOT_CREATED" and
         witness.get("G4")==witness.get("G5")=="NOT_RUN",
         "F4O1_UNTRUSTED_OR_FOREIGN_F4_WITNESS")
    need(o0["observability"]["world_public_id"]==
         o1["observability"]["world_public_id"] and
         o0["observability"]["cutoff_minutes_exact"]==
         o1["observability"]["cutoff_minutes_exact"]=="10" and
         o0["construction"]["pos_arrival_events"]==
         o1["construction"]["pos_arrival_events"] and
         o0["construction"]["observation_series"]==
         o1["construction"]["observation_series"],
         "F4O1_NOT_SAME_KNOWN_PHYSICAL_WORLD")
    p=o1["construction"]["physical_observation"]
    need(p["stage_disclosed"]=="preparacion" and
         p["source_semantics"]=="synthetic_direct_physical_instrumentation" and
         p["measurement_limit"]=="completed_preparation_intervals_only_pre_cutoff" and
         type(p["n_completed_stage_services"]) is int and
         p["n_completed_stage_services"]>0 and
         p["mean_service_minutes_exact"] is not None,
         "F4O1_UNCOMPARABLE_OR_EMPTY_PREPARATION_EVIDENCE")
    obs_n=p["n_completed_stage_services"]
    obs_service=Q(p["mean_service_minutes_exact"])
    obs_wait=Q(p["mean_wait_minutes_exact"])
    need(obs_service>0 and obs_wait>=0,"F4O1_INVALID_PHYSICAL_DURATION")
    cutoff=Q(o1["observability"]["cutoff_minutes_exact"])
    arrivals=tuple(Q(e["t_minutes_exact"]) for e in
                   o0["construction"]["pos_arrival_events"])
    need(all(a<b for a,b in zip(arrivals,arrivals[1:])) and
         all(Q(0)<=t<cutoff for t in arrivals),
         "F4O1_ARRIVAL_INPUT_INCONSISTENT")
    comparisons=[]
    for name,times in HYPOTHESES:
        prior=witness["S0_model_baselines"][name]
        need(prior["service_minutes_exact"]==dict(zip(f4.STAGES,times)) and
             prior["delivered_cumulative"]==
                 witness["S0_observed_delivered_cumulative"],
             "F4O1_MODEL_WITNESS_CHANGED")
        cfg=f4._config(times)
        count=_completed_preparation(cfg,arrivals,cutoff)
        # Every observed COMPLETED service in this deterministic DES
        # has exactly this stage-0 service time. This is a valid H_j
        # for mean service, NOT for mean waits or real noisy cafés.
        predicted_service=Q(times[0])
        comparisons.append({
            "candidate_id":name,
            "model_preparation_stage_operator":
                "EXACT_STAGE0_COMPLETION_COUNT_AND_CONSTANT_SERVICE_DURATION",
            "model_prep_completed_services_before_cutoff":count,
            "model_prep_mean_service_minutes_exact":str(predicted_service),
            "observed_prep_completed_services_before_cutoff":obs_n,
            "observed_prep_mean_service_minutes_exact":str(obs_service),
            "count_matches_exactly":count==obs_n,
            "mean_service_matches_exactly":predicted_service==obs_service,
            "both_preparation_observables_match_exactly":
                count==obs_n and predicted_service==obs_service,
            "mean_service_residual_minutes_exact":
                str(predicted_service-obs_service),
            "observed_wait_minutes_exact_not_scored":str(obs_wait),
            "time_of_service_measurable_in_this_deterministic_model":True,
            "stage_label_mapping_is_a_hypothesis_not_discovered_from_POS":True,
            "not_validated_with_measurement_noise_or_heterogeneity":True,
        })
    survivors=[v["candidate_id"] for v in comparisons
               if v["both_preparation_observables_match_exactly"]]
    need(len(comparisons)==2,"F4O1_WRONG_WITNESS_COUNT")
    return {
        "schema":SCHEMA,
        "source_o0_snapshot_hash":o0["source_snapshot_hash"],
        "source_o1_snapshot_hash":o1["source_snapshot_hash"],
        "witness_sha256":digest(witness),
        "status":(
           "BOTH_KNOWN_F4_RIVALS_EXCLUDED_BY_EXACT_O1_PREPARATION_OPERATOR"
           if not survivors else
           "ONE_OR_MORE_KNOWN_RIVALS_MATCH_EXACT_O1_PREPARATION"),
        "operation":"POST_HOC_EVALUATOR_SENSITIVITY_NOT_NATIVE_INFERENCE",
        "observation_conditions":"S0_O0_ONLY_THEN_S1_O1_AGGREGATE",
        "S0_previous_P0_compatibility":True,
        "S1_o1_has_n_completed_preparation_services":obs_n,
        "S1_o1_mean_preparation_service_minutes_exact":str(obs_service),
        "S1_o1_mean_preparation_wait_minutes_exact_NOT_SCORED":str(obs_wait),
        "S1_two_hypothesis_measurement_comparisons":comparisons,
        "exact_matches_under_S1":survivors,
        "explicitly_not_a_unique_causal_identification":True,
        "S1_measures_are_censored_completed_only":True,
        "stage_to_real_business_operator_proven":False,
        "real_sensor_error_model_estimated":False,
        "no_false_single_winner":True,
        "PM_incremental_value_from_this_discriminator":"NOT_REQUIRED_FOR_THIS_SPECIFIC_PREPARATION_MEASUREMENT",
        "PM_general_value":"NOT_ADJUDICATED",
        "PM_with_without_P_ablation":"NOT_RUN",
        "need_F4_design_revision_before_claiming_O1_ambiguous":True,
        "no_new_generator_des_pm_omc_or_provider":True,
        "G4":"NOT_RUN","G5":"NOT_RUN","A3":"PARTIAL",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--o0",type=Path,required=True)
    p.add_argument("--o1",type=Path,required=True)
    p.add_argument("--f4",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"F4O1_REFUSE_OVERWRITE")
    read=lambda p:json.loads(p.read_text(encoding="utf-8"))
    report=build(read(args.o0),read(args.o1),read(args.f4))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "status":report["status"],
        "survivors":report["exact_matches_under_S1"],
        "A3":report["A3"],"G4":report["G4"],"G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
