"""F3 evaluator-only *descriptive* event-measure versus E1 fluid-window comparison.

Not a validated statistical observation operator. The FULL [0,T) physical
event trace may be supplied ONLY by the evaluator to compare with its original
known-synthetic O1 aggregate; it is never a permitted D/B/M arm input.

Compare N([a,b)) = #recorded physical preparation service_fin in [a,b)
to integral_a^b model preparation.completed dt on the SAME frozen O0/O1
clock grid, retaining separate types, units and measurement status.

No rounding E1 mass to integer events, no equality assumption, calibration,
selection, independent test, PM4Py, or new native method. Exact counting of
events and numeric trapezoidal integration of the actual authenticated
OpenModelica trace remain distinguishable throughout.
"""
from __future__ import annotations

import hashlib
from fractions import Fraction as Q
from pathlib import Path

from scripts import arena_event_observability as obs
from scripts.arena_cafe import evidence, observation_eval as hj
from scripts.arena_cafe.native_handoff import need,validate_a1_visible
from scripts.arena_v0_contract import digest

SCHEMA="igc-cafe-f3-m-o1-evaluator-window-measures/0.1"
STAGE="preparacion"
CHECKPOINTS=(Q(0),Q(2),Q(4),Q(6),Q(8),Q(10))



def count_completed_by_half_open_windows(times, checkpoints=CHECKPOINTS):
    """Exact independent window binning; t=b belongs to the next window.

    Input is already explicitly physical service_fin from the evaluator.
    A service at the final cutoff is excluded, never imputed as completed.
    """
    need(len(checkpoints)>=2 and all(
        type(x) is Q and x>=0 for x in checkpoints) and
        all(a<b for a,b in zip(checkpoints,checkpoints[1:])),
        "F3M_WINDOW_INVALID_GRID")
    values=tuple(Q(t) for t in times)
    need(all(0<=t<checkpoints[-1] for t in values),
         "F3M_WINDOW_EVENT_OUTSIDE_HALF_OPEN_HORIZON")
    counts=[sum(a<=t<b for t in values)
            for a,b in zip(checkpoints,checkpoints[1:])]
    need(sum(counts)==len(values),"F3M_WINDOW_PHYSICAL_COUNT_LOST")
    return counts


def preparation_censor_states(full, *, cutoff=CHECKPOINTS[-1]):
    """Validate order-local censored prep visits, not just total starts.

    The full telemetry is evaluator-only, with service_fin strictly before
    the cutoff; no service in progress is falsely counted as completed.
    """
    cases={}
    kinds=("etapa_entrada","servicio_inicio","servicio_fin")
    for r in full:
        if r.get("stage")!=STAGE or r.get("event_type") not in kinds:
            continue
        time=Q(r["t_minutes_exact"])
        need(0<=time<cutoff,"F3M_WINDOW_CENSOR_STATES_INVALID")
        seen=cases.setdefault(r["case_id"],{})
        kind=r["event_type"]
        need(kind not in seen,"F3M_WINDOW_CENSOR_STATES_INVALID")
        seen[kind]=time
    waiting=in_service=completed=0
    for events in cases.values():
        need("etapa_entrada" in events and
             (not ("servicio_inicio" in events) or
                events["etapa_entrada"]<=events["servicio_inicio"]) and
             (not ("servicio_fin" in events) or
                ("servicio_inicio" in events and
                 events["servicio_inicio"]<=events["servicio_fin"])),
             "F3M_WINDOW_CENSOR_STATES_INVALID")
        if "servicio_fin" in events:
            completed+=1
        elif "servicio_inicio" in events:
            in_service+=1
        else:
            waiting+=1
    return {"waiting":waiting,"in_service":in_service,
            "completed":completed,"entered":len(cases)}



def compare(visible,full_pre_cutoff,candidate,registry,native_trace_csv,
            native_csv_sha256,capacity_certificate):
    validate_a1_visible(visible,"O1")
    need(type(full_pre_cutoff) is list and bool(full_pre_cutoff),
         "F3M_WINDOW_PHYSICAL_EVENTS_REQUIRED")
    need(tuple(Q(x["t_minutes_exact"]) for x in
        visible["construction"]["observation_series"])==CHECKPOINTS and
        Q(visible["observability"]["cutoff_minutes_exact"])==CHECKPOINTS[-1],
        "F3M_WINDOW_PUBLIC_GRID_DRIFT")
    cutoff=CHECKPOINTS[-1]
    need(all(Q(row["t_minutes_exact"])<cutoff
             for row in full_pre_cutoff),
         "F3M_WINDOW_FUTURE_EVENTS_NOT_ALLOWED")
    # Reuse F0's strict public projection and original A1 event validation.
    # FULL is not the raw evaluator generator and never gets passed to M.
    pos=obs.project_events(full_pre_cutoff,"POS")
    pos,full=evidence._pos_and_full(pos,full_pre_cutoff,cutoff)
    # Check the physical event projection really belongs to this O1, not
    # merely to an arbitrary synthetic world with the same total 9.
    expected=visible["construction"]["observation_series"]
    need(evidence._counts(pos,list(CHECKPOINTS))==expected,
         "F3M_WINDOW_FULL_POS_NOT_SAME_O1")
    creations=sorted((
        r["case_id"],str(Q(r["t_minutes_exact"])))
        for r in pos if r["event_type"]=="pedido_creado")
    public_creations=sorted((
        r["case_id"],str(Q(r["t_minutes_exact"])))
        for r in visible["construction"]["pos_arrival_events"])
    need(creations==public_creations,"F3M_WINDOW_CASES_OR_TIMES_CHANGED")
    actual_aggregate=evidence._preparation(full)
    need(actual_aggregate==visible["construction"]["physical_observation"],
         "F3M_WINDOW_PHYSICAL_COMPLETION_AGGREGATE_NOT_O1")

    # Existing E1 candidate and bound were authenticated by F3.
    need(type(capacity_certificate) is dict and
         capacity_certificate["source_snapshot_hash"]==
             visible["source_snapshot_hash"] and
         capacity_certificate["original_candidate_full_ast_sha256"]==
             digest(candidate["ast"]) and
         capacity_certificate["bridge_empirically_verified"] is False and
         capacity_certificate["semantic_bridge_audit"]["bridge_readiness"]==
             "NOT_VALIDATED",
         "F3M_WINDOW_INVALID_OR_FALSELY_VALIDATED_BRIDGE")
    numeric_cap=Q(capacity_certificate["bound_under_unverified_bridge"][
        "max_throughput_units_per_hour_exact"])
    need(numeric_cap==Q(20),"F3M_WINDOW_FROZEN_E1_CAPACITY_DRIFT")

    file=Path(native_trace_csv)
    required="sha256:"+hashlib.sha256(file.read_bytes()).hexdigest()
    need(type(native_csv_sha256) is str and
         required==native_csv_sha256,
         "F3M_WINDOW_UNVERIFIED_NATIVE_CSV_HASH")
    roles=hj._candidate_roles(candidate,registry)
    samples=hj._numeric_samples(hj._rows(file),"M",float(cutoff),roles)
    masses=hj._integrate(samples,"prep_per_minute")
    at=[hj._at(samples,float(t),masses) for t in CHECKPOINTS]
    need(all(at[i+1]+1e-7>=at[i] for i in range(len(at)-1)),
         "F3M_WINDOW_NEGATIVE_INTEGRATED_FLOW")
    stage_finishes=[Q(r["t_minutes_exact"]) for r in full if
                   r["event_type"]=="servicio_fin" and
                   r.get("stage")==STAGE]
    counts=count_completed_by_half_open_windows(stage_finishes,CHECKPOINTS)
    need(sum(counts)==actual_aggregate["n_completed_stage_services"],
         "F3M_WINDOW_PHYSICAL_COUNT_LOST")
    censored=preparation_censor_states(full,cutoff=cutoff)
    need(censored["completed"]==sum(counts) and
         censored["entered"]==15,
         "F3M_WINDOW_CENSOR_STATES_INVALID")

    windows=[]
    for index,(a,b) in enumerate(zip(CHECKPOINTS,CHECKPOINTS[1:])):
        amount=at[index+1]-at[index]
        limit=numeric_cap*(b-a)/60
        need(amount>=-1e-7 and amount<=float(limit)+1e-5,
             "F3M_WINDOW_MODEL_FLUX_EXCEEDS_FIXED_E1_CAP")
        windows.append({
            "window_minutes_half_open":[str(a),str(b)],
            "observed_discrete_prep_completions":counts[index],
            "native_e1_integrated_continuous_readyorder_mass_numeric":amount,
            "nominal_E1_max_mass_exact":str(limit),
            "difference_count_minus_model_mass_DESCRIPTIVE_ONLY":
                counts[index]-amount,
            "counts_are_not_model_masses":True,
        })
    total=at[-1]-at[0]
    need(total>=-1e-7 and
         total<=float(numeric_cap*cutoff/60)+1e-5,
         "F3M_WINDOW_CUMULATIVE_E1_CAP_EXCEEDED")
    n=sum(counts)
    need(n==9 and n==capacity_certificate["bound_under_unverified_bridge"][
            "observed_discrete_services_completed_pre_cutoff"],
         "F3M_WINDOW_KNOWN_O1_COUNT_DRIFT")
    return {
        "schema":SCHEMA,
        "arm_id":"M",
        "condition_id":"O1",
        "origin":"KNOWN_SYNTHETIC_EV01_EVALUATOR_ONLY_DEVELOPMENT",
        "visible_source_snapshot_hash":visible["source_snapshot_hash"],
        "o1_visible_input_hash":digest(visible),
        "evaluator_pre_cutoff_FULL_sha256":digest(full),
        "native_solver_csv_sha256":required,
        "native_trace_authentication":
            "INHERITS_CALLER_F3_G2_REAUDIT_NOT_ESTABLISHED_IN_THIS_OPERATOR",
        "physical_event_window_rule":"[t_i,t_i_plus_1)_EXACT_FRACTION",
        "native_numeric_integration":
            "EXISTING_HJ_TRAPEZOID_ON_ORIGINAL_OMC_OUTPUT_NO_ROUNDING",
        "windows":windows,
        "physical_total_completed_pre_cutoff":n,
        "native_continuous_prep_integral_numeric":total,
        "native_nominal_max_mass_exact":str(numeric_cap*cutoff/60),
        "physical_censored_waiting_at_cutoff":censored["waiting"],
        "physical_censored_in_service_at_cutoff":censored["in_service"],
        "completed_only_O1_mean_wait_and_service_crosschecked":True,
        "unit_identity_empirically_verified":False,
        "exact_cutoff_mass_equality_empirically_verified":False,
        "temporal_alignment_uncertainty_calibrated":False,
        "difference_is_not_sensor_error_or_model_fit":True,
        "no_private_case_timestamps_in_output":True,
        "no_full_event_log_given_to_native_M":True,
        "operator_sufficient_for_scientific_G3":False,
        "instrumented_F5_independent_pilot":"NOT_PERFORMED",
        "M_native_model_generated_or_selected_from_O1":False,
        "G3":"NOT_ESTABLISHED","G4":"NOT_RUN","G5":"NOT_RUN",
        "PM14":"NOT_TRIGGERED_EV01",
    }
