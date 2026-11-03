"""RF-02H: read-only observable/operator and parameter-provenance gate.

This consumes *already executed* O0 G2 engineering artifacts from D and M.
It does not run a solver, infer parameters, compute fit/residuals vs POS
deliveries, select a model, or conduct G3. The native G2 validators are
re-executed on frozen CSV files to bind the 12 candidate identities.

Only engineering mapping of delivered cumulative outputs is checked.
Measurement/causal semantic adequacy remains NOT ESTABLISHED, and H_j for
preparation/waiting/service is never forced across arms.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction as Q
from pathlib import Path

from scripts.arena_v0_contract import canonical,digest
from scripts.arena_cafe.native_handoff import need,validate_a1_visible
from scripts.arena_cafe import observation_eval as oe
from scripts.arena_cafe import r2_causal_pos_signal as causal
from scripts.arena_cafe import r2_causal_g2 as d_g2
from scripts.arena_cafe import r2_m_six_causal_g2 as m_g2
from scripts.arena_cafe import r2_observational_contracts as r2

SCHEMA="igc-arena-rf02-hj-parameter-readiness/0.1"
OBS_SCHEMA="igc-arena-rf02-hj-admissibility/0.1"
PARAM_SCHEMA="igc-arena-rf02-parameter-admissibility/0.1"
SCOPE="O0_PUBLIC_SYNTHETIC_PRE_G3_ENGINEERING_PROVENANCE_ONLY"
DECISION="BLOCKED_G3_NEEDS_SCIENTIFIC_ADMISSION"
D_ORIGIN_RUN=41589895721
M_ORIGIN_RUN=41591727790
A1_ORIGIN_RUN=41575917332
MIN_SAMPLES=1000


def _sha_file(path):
    return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _assert_real_g2(visible,d_root,m_root):
    """Delegate exact source/candidate/CSV/G2 verification to tested validators."""
    d_root,m_root=Path(d_root),Path(m_root)
    d_manifest=_load(d_root/"manifest.json")
    m_manifest=_load(m_root/"manifest.json")
    need(d_manifest.get("condition_id")=="O0" and
         m_manifest.get("condition_id")=="O0" and
         d_manifest.get("source_snapshot_hash")==
         m_manifest.get("source_snapshot_hash")==visible["source_snapshot_hash"] and
         d_manifest.get("public_view_sha256")==
         m_manifest.get("public_input_sha256")==digest(visible),
         "RF02H_SCOPE_OR_VIEW_CONDITION_MISMATCH")
    # Real source and solver-provenance controls live in these two validators;
    # mere self-reported manifest status is NOT enough.
    d=d_g2.verify(visible,d_root)
    m=m_g2.verify(visible,m_root)
    need(d["G2"]==m["G2"]=="PASS_REAL_OMC_ENGINEERING_ONLY" and
         d["candidate_count"]==m["candidate_count"]==6 and
         d["G3"]==m["G3"]=="NOT_RUN" and
         d["G4"]==m["G4"]=="NOT_RUN" and
         d["G5"]==m["G5"]=="NOT_RUN" and
         d["selection_actor"]==m["selection_owner"]=="NONE" and
         d["provider_calls"]==m["provider_calls"]==0,
         "RF02H_G2_NOT_SIX_OR_G3_ALREADY_RUN")
    need(d["signal_sha256"]==m["same_causal_signal_hash_as_D"]==
         d_manifest["signal_sha256"]==
         m_manifest["causal_stimulus"]["event_rate_signal_sha256"] and
         d_manifest["signal"]==m_manifest["causal_stimulus"],
         "RF02H_DIFFERENT_MATERIAL_INPUTS")
    # Reports are inherited fixed-run attestations, and must match what the
    # native independent auditor recomputes from the six CSVs.
    need(digest(_load(d_root/"g2-report.json"))==digest(d) and
         digest(_load(m_root/"g2-report.json"))==digest(m),
         "RF02H_FROZEN_G2_REPORT_NOT_REPRODUCIBLE")
    return d_manifest,m_manifest,d,m


def _extract_delivered(csv_path,arm,cutoff):
    """A time/value shape audit, not a forecast evaluation.

    No event/observed delivery series is read. Checks exact required native
    output names and engineering monotonicity and unit conversion.
    """
    need(arm in ("D","M"),"RF02H_UNRECOGNIZED_ARM")
    name={"D":"delivered","M":"deliveredTotal"}[arm]
    factor=1.0 if arm=="D" else 60.0
    rows=oe._rows(Path(csv_path))
    need(len(rows)>=MIN_SAMPLES,"RF02H_TOO_FEW_SAMPLES")
    t0=None
    previous_t=-1.0
    previous_out=-1.0
    first_value=None
    final_value=None
    for record in rows:
        t=oe._column(record,"time")*factor
        delivered=oe._column(record,name)
        need(t>=previous_t-1e-8 and
             -1e-7<=t<=cutoff+1e-6 and
             delivered>=-1e-6 and delivered>=previous_out-1e-6,
             "RF02H_BAD_TIME_OR_NONMONOTONE_DELIVERY")
        if t0 is None:
            t0=t
            first_value=delivered
        previous_t,previous_out=t,delivered
        final_value=delivered
    need(abs(t0)<=1e-7 and abs(previous_t-cutoff)<=1e-6 and
         abs(first_value)<=1e-6 and math.isfinite(final_value),
         "RF02H_INCOMPLETE_OR_NONZERO_INITIAL_STOCK")
    # Hash of the trace is allowed. Deliberately NO forecast values or
    # observed delivery residuals are exported into a candidate scorecard.
    return {
        "native_output_variable":name,
        "native_time_unit":"minute" if arm=="D" else "hour",
        "common_time_unit":"minute",
        "quantity_unit":"orders",
        "operator":"DIRECT_CUMULATIVE_DELIVERY_STOCK",
        "temporal_conversion":"IDENTITY" if arm=="D" else "HOURS_TO_MINUTES_EXACT_FACTOR_60",
        "has_no_interpolation_or_fitting":True,
        "sample_rows":len(rows),
        "window_minutes":{"start":"0","end":str(Q(str(cutoff)))},
        "initial_value_zero":True,
        "monotonic_nonnegative":True,
        "trace_sha256":_sha_file(csv_path),
        "trajectory_values_exported":False,
        "scoring_against_observations":"NOT_RUN",
        "engineering_operator":"PASS",
        "scientific_measurement_equivalence":"NOT_ESTABLISHED",
    }


def _parameter_policy(d_manifest,m_manifest):
    from scripts.arena_cafe.r2_causal_g2 import validate_fixture
    # The actual nominal values are read solely to verify they are exactly
    # the engineering fixture. No inference from observed deliveries.
    fixture=_load(Path(__file__).resolve().parents[2]/
                  "tests/fixtures/rf02_g2_fixture_nominals.json")
    d_params=validate_fixture(fixture)
    need(d_manifest["nominal_fixture_sha256"]==digest(fixture) and
         d_manifest["nominal_parameters"]==d_params and
         d_manifest["nominal_parameters_are_non_empirical"] is True and
         d_manifest["no_EV01_parameter_inference"] is True,
         "RF02H_D_FIXED_CONFORMANCE_PRIORS_WRONG")
    # Explicit check rather than a hidden registry hash in a conditional.
    composer=m_g2.get_composer()
    cfg,classes,_=composer.load_registry(r2.BASE_PATH)
    need(m_manifest["registry_sha256"]==digest(cfg) and
         m_manifest["original_E1_parameters_fixed_not_fit_to_POS"] is True and
         m_manifest["preparation_dispatch_mandatory_roles_are_priors"] is True and
         m_manifest["registry_variant"]=="registry.base.json",
         "RF02H_M_REGISTRY_NOT_ORIGINAL")
    native_specs={}
    for key in ("preparation","dispatch","transit","report"):
        values=cfg["roles"][key]["parameters"]
        native_specs[key]={
            "parameter_values":values,
            "source":"SHORT_E1_BASE_REGISTRY_PREEXISTING_PRIOR",
            "calibrated_from_EV01":False,
        }
    return {
        "schema":PARAM_SCHEMA,
        "scope":SCOPE,
        "D":{
            "native_method":"ORIGINAL_D_GRAMMAR_WITH_VERSIONED_POS_STIMULUS",
            "observational_parameter_fit":"NOT_RUN",
            "source":"RF02G_EXPLICIT_NON_EMPIRICAL_SIMULATOR_FIXTURE",
            "parameter_fields":sorted(d_params),
            "fixture_sha256":digest(fixture),
            "values_source_status":"ENGINEERING_FIXTURE_NOT_EV01_ESTIMATE",
            "origin_verified":True,
            "admissible_as_empirical_parameters":False,
            "eligible_for_G3":False,
        },
        "M":{
            "native_method":"SHORT_E1_BASE_REGISTRY_SIX_ORIGINAL_AST",
            "observational_parameter_fit":"NOT_RUN",
            "source":"ORIGINAL_E1_FIXED_PRIORS_NOT_OBSERVATION_ESTIMATES",
            "original_registry_sha256":digest(cfg),
            "roles":native_specs,
            "origin_verified":True,
            "admissible_as_empirical_parameters":False,
            "eligible_for_G3":False,
        },
        "B":{
            "native_method":"BUFFALO",
            "real_EV01_generation":"NOT_RUN",
            "parameter_provenance":"NOT_AVAILABLE",
            "eligible_for_G3":False,
        },
        "estimation_rule":"MUST_BE_PROSPECTIVELY_SPECIFIED_INDEPENDENT_OF_HIDDEN_TRUTH",
        "prohibit_copy_from_other_arm":True,
        "no_data_driven_calibration_from_O0_or_O1_this_run":True,
        "comparison_with_unequal_priors_is_not_method_comparison":True,
        "G3":"NOT_RUN",
    }


def _observables(visible):
    """Semantics from RF-02 H_j, with additional trace-bound engineering mapping."""
    scope=r2.comparable_observables(visible,"O0")
    need(scope["condition_id"]=="O0" and
         scope["source_snapshot_hash"]==visible["source_snapshot_hash"] and
         scope["primary_policy"]==
             "DELIVERED_CUMULATIVE_CONDITIONAL_ON_PER_ARM_SEMANTIC_GATE",
         "RF02H_HJ_POLICY_DRIFT")
    return {
        "schema":OBS_SCHEMA,
        "condition_id":"O0",
        "modeling_input":{
            "observation":"15_PUBLIC_POS_CREATION_EVENTS_BEFORE_CUTOFF",
            "native_signal":"CAUSAL_RECTANGULAR_APPROXIMATION",
            "input_rate_is_measured":False,
            "rate_kernel_scientifically_approved":False,
            "input_created_counts_scored_as_prediction":False,
            "source_integral_is_identical_for_D_M":True,
            "input_cutoff_mass_need_not_equal_all_events":True,
        },
        "delivery_cumulative":{
            "status":"ENGINEERING_OPERATOR_WELL_TYPED_FOR_D_AND_M_ONLY",
            "common_quantity":"CUMULATIVE_DELIVERED_ORDERS",
            "common_unit":"orders",
            "common_time_unit":"minute",
            "D_native":"delivered",
            "M_native":"deliveredTotal",
            "B_native":"NOT_AVAILABLE",
            "operator_shape":"PASS_D_M_DIRECT_NATIVE_STOCKS",
            "scientific_semantic_equivalence":"NOT_ESTABLISHED",
            "G3_ADMISSIBLE":False,
        },
        "O0_other":{
            "orders_created_cumulative":"INPUT_NOT_SCOREABLE",
            "orders_minus_delivered":"NOT_NATIVE_WIP_WITH_LOSSES_OR_DEFERRED_INPUT",
            "report_signal":"NOT_MATERIAL_AND_NOT_A_DELIVERY_COUNT",
        },
        "O1_only":{
            "completed_preparation_services":
                "NOT_TESTED_IN_O0_NOT_CROSS_ARM_EQUIVALENT",
            "wait_service_intervals":
                "NOT_NATIVE_RESPONSE_TIME_PARAMETER",
        },
        "comparability_is_not_quality_of_fit":True,
        "no_scoring_or_rankings":True,
        "G3":"NOT_RUN",
    }


def build(visible,d_root,m_root):
    validate_a1_visible(visible,"O0")
    d_manifest,m_manifest,d_verified,m_verified=_assert_real_g2(
        visible,d_root,m_root)
    params=_parameter_policy(d_manifest,m_manifest)
    obs=_observables(visible)
    cutoff=float(Q(visible["observability"]["cutoff_minutes_exact"]))
    result=[]
    seen=set()
    for arm,root,manifest,proven in (
            ("D",Path(d_root),d_manifest,d_verified),
            ("M",Path(m_root),m_manifest,m_verified)):
        by_key={
            (x["candidate_id"] if arm=="D" else x["canonical_sha256"]):x
            for x in proven["candidates"]}
        need(len(by_key)==6,"RF02H_DUPLICATE_NATIVE_CANDIDATE")
        for candidate in manifest["candidates"]:
            native_id=(candidate["candidate_id"] if arm=="D" else
                       candidate["canonical_sha256"])
            need((arm,native_id) not in seen and native_id in by_key,
                 "RF02H_UNEXPECTED_OR_DUPLICATE_CANDIDATE")
            seen.add((arm,native_id))
            csv_name=candidate["csv_prefix"]+"_res.csv"
            path=root/csv_name
            op=_extract_delivered(path,arm,cutoff)
            need(op["trace_sha256"]==(
                by_key[native_id]["csv_sha256"] if arm=="D"
                else by_key[native_id]["solver_csv_sha256"]),
                "RF02H_CSV_IS_NOT_G2_VERIFIED_CANDIDATE")
            result.append({
                "arm_id":arm,"candidate_id":native_id,
                "source_run_id":D_ORIGIN_RUN if arm=="D" else M_ORIGIN_RUN,
                "native_structure_sha256":(
                    candidate["structure_hash"] if arm=="D"
                    else candidate["full_ast_sha256"]),
                "input_signal_sha256":d_verified["signal_sha256"],
                "H_j":op,
                "parameter_state":(
                    "NON_EMPIRICAL_D_FIXTURE" if arm=="D"
                    else "E1_FIXED_UNCALIBRATED_PRIORS"),
                "G2":"ENGINEERING_PASS_ORIGINAL_FROZEN_TRACE",
                "G3":"NOT_RUN",
            })
    need(len(result)==12 and len(seen)==12 and
         sum(x["arm_id"]=="D" for x in result)==6 and
         sum(x["arm_id"]=="M" for x in result)==6,
         "RF02H_NOT_ALL_TWELVE_BINDINGS")
    source=causal.from_visible(visible,"O0")
    need(d_verified["signal_sha256"]==
         source["signal"]["event_rate_signal_sha256"] and
         m_verified["same_causal_signal_hash_as_D"]==
         d_verified["signal_sha256"],
         "RF02H_SOURCE_NOT_SAME_AFTER_TIME_UNIT_CONVERSION")
    return {
        "schema":SCHEMA,"scope":SCOPE,
        "condition_id":"O0",
        "public_source_snapshot_hash":visible["source_snapshot_hash"],
        "public_view_sha256":digest(visible),
        "artifact_sources":{
            "A1_public_run_id":A1_ORIGIN_RUN,
            "D_G2_engineering_run_id":D_ORIGIN_RUN,
            "M_G2_engineering_run_id":M_ORIGIN_RUN,
        },
        "G2_source_audits_recomputed":True,
        "D_G2_report_sha256":digest(d_verified),
        "M_G2_report_sha256":digest(m_verified),
        "common_signal_sha256":d_verified["signal_sha256"],
        "M_time_unit_converted_hours_to_minutes":True,
        "rate_kernel_width_minutes_exact":
             source["signal"]["width_minutes_exact"],
        "source_events_count":source["signal"]["events_count"],
        "source_mass_before_cutoff_exact":
             source["signal"]["mass_before_cutoff_orders_exact"],
        "source_mass_deferred_after_cutoff_exact":
             source["signal"]["mass_deferred_after_cutoff_orders_exact"],
        "candidate_count":12,
        "candidates":result,
        "observables":obs,
        "parameters":params,
        "gates":{
            "G0_G1":"PREVIOUS_ENGINEERING_SOURCE_ONLY",
            "G2_D_M":"PASS_REAL_OMC_ENGINEERING_ONLY",
            "G2_B":"NOT_RUN",
            "Hj_D_M_engineering_operator":"PASS",
            "Hj_scientific_semantic_equivalence":"NOT_ESTABLISHED",
            "D_parameters_scientifically_admissible":False,
            "M_parameters_calibrated_for_EV01":False,
            "B_real_native_EV01_generated":False,
            "G3": "NOT_RUN", "G4":"NOT_RUN", "G5":"NOT_RUN",
            "A3":"PARTIAL",
        },
        "decision":DECISION,
        "blockers":[
            "SCIENTIFIC_SEMANTIC_MAPPING_AND_HJ_ADMISSION",
            "D_INDEPENDENT_EMPIRICAL_PARAMETER_POLICY_OR_EXPLICIT_ABSTAIN",
            "M_ORIGINAL_FIXED_PRIORS_NOT_ESTIMATED_FROM_EV01",
            "REAL_B_NATIVE_EV01_GENERATION_UNEXECUTED",
            "G3_PROSPECTIVE_SCORING_AND_EVIDENCE_SEPARATION_NOT_APPROVED",
        ],
        "no_fit_to_observed_deliveries":True,
        "no_native_model_selection":True,
        "no_priors_copied_across_arms":True,
        "no_private_truth_access":True,
        "cloudflare_provider_calls":0,
        "omc_invocations_in_this_job":0,
        "independent_scientific_review":"NOT_REQUESTED_FOR_THIS_ENGINEERING_GATE",
    }


def main():
    p=argparse.ArgumentParser(description="Read-only H_j + parameter provenance")
    p.add_argument("--visible",required=True,type=Path)
    p.add_argument("--d-native-dir",required=True,type=Path)
    p.add_argument("--m-native-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    need(not args.out.exists(),"RF02H_REFUSE_OVERWRITE")
    report=build(_load(args.visible),args.d_native_dir,args.m_native_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+bytes([10]))
    print(json.dumps({"decision":report["decision"],
                      "candidate_count":report["candidate_count"],
                      "G3":report["gates"]["G3"],
                      "Hj_engineering":report["gates"]["Hj_D_M_engineering_operator"]},
                     sort_keys=True))


if __name__=="__main__":
    main()
