"""E1/O1 semantic-bridge audit: a type match is not an observation model.

The E1 BoundedQueue output is a bounded continuous flow of ReadyOrder units.
The O1 preparation observation is a count of discrete completion EVENTS on
[0,T), plus conditional means among completed cases. Matching the unit names
does not prove equality of either time paths or totals at T.

A cumulative continuous flow is continuous (indeed Lipschitz when bounded),
while a counting process with any events has jumps. Therefore pointwise
identity of these two time paths is mathematically impossible for n>0.

An equality N_pre_cutoff = integral_0^T f(t)dt is an ADDITIONAL finite-window
observation bridge which requires independently justified material mapping,
event alignment/censoring and an error budget; it does not follow from a
typed port. The prior numeric capacity inequality remains valid ONLY IF this
stronger exact-cutoff bridge is assumed. No fitted parameters or sensors.
"""
from __future__ import annotations

from fractions import Fraction as Q

from scripts.arena_cafe.native_handoff import need,validate_a1_visible
from scripts.arena_v0_contract import digest

SCHEMA="igc-arena-m-o1-discrete-continuous-bridge-audit/0.1"
H_UNIT="UNVERIFIED_ONE_PHYSICAL_PREP_COMPLETION_IS_ONE_READYORDER_UNIT"
H_CUTOFF="UNVERIFIED_EXACT_COUNT_EQUALS_INTEGRAL_AT_SAME_CUTOFF"
H_DISCREPANCY="NO_INDEPENDENT_DISCRETIZATION_OR_MEASUREMENT_ERROR_BUDGET"


def audit(visible,necessary_bound):
    """Only known O1 and *already checked* fixed-E1 necessary capacity data.

    Does NOT read evaluator FULL, infer latent services, calibrate clocks,
    infer a discrete-event intensity, or modify E1's original composition.
    """
    validate_a1_visible(visible,"O1")
    need(type(necessary_bound) is dict and
         set(("observed_discrete_services_completed_pre_cutoff",
              "max_throughput_units_per_hour_exact",
              "cutoff_minutes_exact",
              "maximum_possible_cumulative_completed_mass_exact",
              "shortfall_of_nominal_max_mass_to_count_exact",
              "necessary_one_to_one_condition_satisfied")).issubset(
                  necessary_bound),
         "F3M_BRIDGE_MISSING_NATIVE_BOUND")
    observed=visible["construction"]["physical_observation"]
    count=observed["n_completed_stage_services"]
    cutoff=Q(visible["observability"]["cutoff_minutes_exact"])
    max_flow=Q(necessary_bound[
        "max_throughput_units_per_hour_exact"])
    mass_max=Q(necessary_bound[
        "maximum_possible_cumulative_completed_mass_exact"])
    gap=Q(necessary_bound[
        "shortfall_of_nominal_max_mass_to_count_exact"])
    need(observed["stage_disclosed"]=="preparacion" and
         observed["measurement_limit"]==
             "completed_preparation_intervals_only_pre_cutoff" and
         count==necessary_bound[
             "observed_discrete_services_completed_pre_cutoff"] and
         cutoff==Q(necessary_bound["cutoff_minutes_exact"]) and
         max_flow>0 and
         mass_max==max_flow*cutoff/60 and
         gap==max(Q(0),Q(count)-mass_max) and
         necessary_bound["necessary_one_to_one_condition_satisfied"]==
            (Q(count)<=mass_max),
         "F3M_BRIDGE_BOUND_NOT_BOUND_TO_O1")
    need(type(count) is int and count>=0 and cutoff>0,
         "F3M_BRIDGE_BAD_COUNT_OR_TIME")
    # The A1 O1 payload intentionally provides no physical case-by-case
    # preparation completions and no instrument calibration metadata.
    need(set(visible["construction"])=={
        "pos_arrival_events","observation_series","units",
        "observation_window","data_origin","physical_observation"},
        "F3M_BRIDGE_UNAUTHORIZED_PRIVATE_EVENT_FIELDS")
    # A continuous bounded flux has Lipschitz cumulative integral M(t).
    # Any nonempty finite event process N(t)=sum 1(t_i<t) has a jump of >=1.
    # Exact equality as trajectories is impossible independently of capacity.
    # Equality at ONE cutoff is a separate modeling assumption not proved here.
    path_impossible=count>0
    return {
        "schema":SCHEMA,
        "condition_id":"O1",
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "visible_input_sha256":digest(visible),
        "observed_process":"FINITE_DISCRETE_PREPARATION_COMPLETION_COUNTING_PROCESS",
        "native_process":"BOUNDED_CONTINUOUS_RATE_OF_READYORDER_UNITS",
        "stock_flow_time_unit":"hour",
        "physical_time_unit":"minute",
        "physical_window_rule":"EVENTS_STRICTLY_BEFORE_T",
        "original_positive_event_count":count,
        "unit_identity_requirement":H_UNIT,
        "unit_identity_empirically_verified":False,
        "exact_cutoff_mass_equality_requirement":H_CUTOFF,
        "exact_cutoff_mass_equality_empirically_verified":False,
        "independent_error_budget_requirement":H_DISCREPANCY,
        "independent_error_budget_available":False,
        "pointwise_event_vs_continuous_integral_identity":(
            "MATHEMATICALLY_IMPOSSIBLE_WITH_POSITIVE_EVENTS"
            if path_impossible else "NOT_DECIDED_BY_ZERO_EVENTS"),
        "pointwise_impossibility_is_not_cutoff_mismatch_proof":True,
        "no_case_level_preparation_completion_timestamps_in_O1":True,
        "no_per_completion_readyorder_measurement_links_in_O1":True,
        "mean_service_and_wait_are_completed_case_conditional_not_event_clock":True,
        "strict_before_cutoff_requires_declared_boundary_policy":True,
        "necessary_nominal_max_mass_exact":str(mass_max),
        "necessary_shortfall_IF_EXACT_CUTOFF_BRIDGE_exact":str(gap),
        "necessary_absolute_discrepancy_to_avoid_exclusion_under_1_to_1_exact":
            str(gap),
        "necessary_discrepancy_is_not_empirical_sensor_error":True,
        "conditional_nominal_capacity_status":(
            "EXCLUDED_ONLY_IF_EXACT_CUTOFF_COUNTER_EQUALS_MODEL_MASS"
            if gap>0 else "NOT_EXCLUDED_BY_THIS_NECESSARY_BOUND_ONLY"),
        "unconditional_scientific_model_verdict":"NOT_IDENTIFIED_BY_AGGREGATED_O1",
        "bridge_readiness":"NOT_VALIDATED",
        "native_e1_model_generated_or_fitted_from_O1":False,
        "sensor_calibration_or_discretization_fit":"NOT_RUN",
        "required_additional_evidence":[
            "PER_CASE_PREPARATION_ENTER_START_FINISH_WITH_COMMON_CLOCK_AND_CUTOFF",
            "INDEPENDENT_ITEM_TO_READYORDER_MATERIAL_MAPPING_AND_REWORK_POLICY",
            "MODEL_TO_EVENT_CUMULATIVE_OBSERVATION_OPERATOR_DEFINED_A_PRIORI",
            "INDEPENDENT_SENSOR_AND_FLUID_DISCRETIZATION_ERROR_ALLOWANCE",
            "TEMPORAL_REPLICATION_TO_TEST_OPERATOR_OUTSIDE_DEVELOPMENT_WORLD",
        ],
        "F3":"PARTIAL","G3":"NOT_ESTABLISHED","G4":"NOT_RUN","G5":"NOT_RUN",
    }
