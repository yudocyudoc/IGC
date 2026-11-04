"""F3 known-control adjudication: independent evidence bundles, NOT blind G5.

Consumes four authentic D/M OMC bundles and six original-method worker receipts.
B in mock mode NEVER becomes native inference. All FULL/B1/B2 material remains
on the evaluator's side; no F3 worker receives hidden config or physical logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts.arena_cafe import (
    native_pos_scenario as scenario, native_pos_verify as verifier,
    observation_eval as hj, observation_ports as ports, scoped_memory,
    f2_physical_controls as physical, m_o1_capacity_certificate,
)
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-cafe-a3-f3-known-control-adjudication/0.1"
ARMS=("D","B","M")
CONDITIONS=("O0","O1")
E1_REGISTRY=Path("experiments/e1/registry.base.json")


def _read(path):
    path=Path(path)
    need(path.is_file(),"F3_REQUIRED_ARTIFACT_MISSING:"+path.name)
    return json.loads(path.read_text(encoding="utf-8"))


def _rmse(rows):
    need(len(rows)==6 and
         [r["t_minutes"] for r in rows]==[0.,2.,4.,6.,8.,10.],
         "F3_MEASUREMENT_GRID_MISMATCH")
    need(all(math.isfinite(r["residual_orders"]) and
             math.isfinite(r["native_prediction"]) for r in rows),
         "F3_NONFINITE_HJ")
    return math.sqrt(sum(x["residual_orders"]**2 for x in rows)/len(rows))


def compare_native_conditions(o0_native, o1_native, arm):
    """Distinguish a fixed nominal regression from legitimate O1 assimilation.

    Equal POS evidence does NOT generally require equal model scores.
    In this exact existing D/M native POS benchmark, a byte-identical
    generated Modelica source with the same deterministic setup should give
    the same *prediction curve*, within solver numerical tolerance. Different
    sources could be legitimate once a method consumes O1, but a changed
    source alone is NOT evidence of such consumption.
    """
    need(arm in ("D","M"),"F3_CONDITION_BAD_ARM")
    for native in (o0_native,o1_native):
        need(native.get("native_model_sha256") and
             native.get("full_candidate_hash") and
             native.get("metrics") and
             isinstance(native["metrics"].get("delivery_curve_predicted"),list) and
             len(native["metrics"]["delivery_curve_predicted"])==6,
             "F3_CONDITION_INCOMPLETE_NATIVE_PROVENANCE")
    same_source=(o0_native["native_model_sha256"]==
                 o1_native["native_model_sha256"])
    same_candidate=(o0_native["full_candidate_hash"]==
                    o1_native["full_candidate_hash"])
    need(not same_source or same_candidate,
         "F3_IDENTICAL_SOURCE_CANDIDATE_INCONSISTENT")
    delta=max(abs(float(a)-float(b)) for a,b in zip(
        o0_native["metrics"]["delivery_curve_predicted"],
        o1_native["metrics"]["delivery_curve_predicted"]))
    need(math.isfinite(delta),"F3_CONDITION_NONFINITE_FORECAST")
    if same_source:
        need(delta<1e-7,"F3_SAME_NATIVE_SOURCE_NUMERIC_REGRESSION_DRIFT")
    return {
        "arm_id":arm,
        "same_native_source_bytes":same_source,
        "same_original_candidate":same_candidate,
        "delivery_curve_max_abs_difference_orders":delta,
        "conditional_O1_generation_use":(
            "NOT_CONSUMED_IN_IDENTICAL_POS_ONLY_NATIVE_SOURCE"
            if same_source else
            "NOT_VERIFIED_BY_SOURCE_DIFFERENCE_REQUIRES_NATIVE_CONSUMPTION_TRACE"),
        "O1_extra_preparation_in_input_envelope":True,
        "O1_extra_preparation_not_encoded_by_current_generator":
            same_source,
        "equal_scores_are_not_general_condition_criterion":True,
        "scientific_calibration_or_selection":"NOT_RUN",
    }


def _read_scope(root, visible, arm, cond, run_kind):
    expected=scoped_memory.scope(visible,arm,cond,run_kind)
    prefix="ledger.sqlite" if run_kind=="native" else "scoped-ledger.sqlite"
    stamp=_read(Path(root)/"memory-receipt.json")
    reloaded=_read(Path(root)/"memory-rebuild.json")
    need(stamp["context"]==expected and reloaded["context"]==expected
         and stamp["revisions"]==4 and reloaded["revisions"]==4
         and stamp["ledger_integrity_verified"] is True
         and reloaded["ledger_integrity_verified"] is True
         and stamp["atms_projection_hash"]==reloaded["atms_projection_hash"]
         and stamp["empirical_truth_from_ATMS"]=="NOT_ESTABLISHED",
         "F3_LEDGER_SCOPE_OR_PROVENANCE_MISMATCH")
    reconstructed=scoped_memory.inspect(
        Path(root)/prefix,visible,arm,cond,run_kind,
        at=stamp["recorded_as_of"])
    need(reconstructed["atms_projection_hash"]==stamp["atms_projection_hash"],
         "F3_LEDGER_NOT_REPRODUCIBLE")
    return {"case_id":expected["case_id"],
            "projection_hash":stamp["atms_projection_hash"],
            "revisions":4,"app_level_isolation":True,
            "actual_SQLite_reconstruction":True,
            "scope_not_OS_ACL":True}


def _worker(root,visible,arm,cond):
    report=_read(Path(root)/"worker-receipt.json")
    expected={
        "D":"BLOCKED_NOMINAL_PULSE_MISSING",
        "B":"ORIGINAL_ENGINE_OFFLINE_MOCK",
        "M":"ORIGINAL_E1_ENUMERATOR_ENGINEERING_ONLY",
    }[arm]
    need(report.get("arm")==arm and report.get("condition")==cond
         and report.get("visible_input_hash")==digest(visible)
         and report.get("source_snapshot_hash")==visible["source_snapshot_hash"]
         and report.get("worker_input_count")==1
         and report.get("private_generator_present") is False
         and report.get("provider_calls")==0
         and report.get("scientific_use_proven") is False
         and report.get("status")==expected,
         "F3_WORKER_NOT_BOUND_TO_OWN_EVIDENCE_OR_MOCK")
    state="BLOCKED_BEFORE_RUN" if arm=="D" else "COMPLETED"
    used="UNSUPPORTED_DOCUMENTED" if arm=="D" else "NOT_VERIFIED"
    if arm=="B":
        need(report.get("native_method_run") is True
             and len(report.get("user_prompt_hashes",[]))>=1,
             "F3_B_MOCK_PROMPT_NOT_RUN")
        used="UNSUPPORTED_DOCUMENTED" # offline mock cannot demonstrate inference use
    if arm=="M":
        need(report.get("native_method_run") is True
             and report.get("candidate_count",0)>0,
             "F3_M_ORIGINAL_ENUMERATOR_NOT_RUN")
    memory=_read_scope(root,visible,arm,cond,"worker")
    return {"state":state,"status":expected,
            "interface_original_port":used,
            "inference_authenticated":False,
            "worker_receipt_hash":digest(report),
            "prompt_hashes":report.get("user_prompt_hashes",[]),
            "memory":memory}


def _native(root,visible,arm,cond):
    root=Path(root)
    manifest=_read(root/"manifest.json")
    original_model,original_script,regenerated=scenario.build(
        visible,arm,cond)
    need(manifest==regenerated
         and (root/"native.mo").read_text()==original_model
         and (root/"simulate.mos").read_text()==original_script,
         "F3_ORIGINAL_NATIVE_REGEN_DRIFT")
    verified=verifier.audit(
        visible,manifest,root/"native.mo",root/"simulate.mos",
        root/"native_res.csv",root/"INVOCATION_STARTED",root/"exit_code.txt")
    stored_g2=_read(root/"g2-report.json")
    need(verified==stored_g2 and
         verified["status"]=="NATIVE_G2_MATERIAL_BALANCE_PASS_ENGINEERING_ONLY",
         "F3_G2_ATTEMPT_OR_INTEGRITY_NOT_VERIFIED")
    registry=E1_REGISTRY if arm=="M" else None
    candidate=manifest["candidate"] if arm=="M" else None
    selected_port=ports.port(visible,arm,cond,registry=registry)
    actual_hj=hj.evaluate(visible,selected_port,
                          trace_csv=root/"native_res.csv",
                          candidate=candidate,registry=registry)
    need(actual_hj==_read(root/"hj.json")
         and actual_hj["trace_sha256"]==verified["solver_csv_sha256"]
         and actual_hj["source_snapshot_hash"]==visible["source_snapshot_hash"],
         "F3_HJ_NOT_REPRODUCIBLE")
    delivery=[x for x in actual_hj["comparisons"]
              if x["observable"]=="delivered_cumulative"]
    arrivals=[x for x in actual_hj["comparisons"]
              if x["observable"]=="orders_created_cumulative"]
    need(len(delivery)==len(arrivals)==6,"F3_MISSING_REQUIRED_OBSERVABLE")
    observed=visible["construction"]["observation_series"]
    need([x["observed_orders"] for x in delivery]==
         [x["delivered_cumulative"] for x in observed] and
         [x["observed_orders"] for x in arrivals]==
         [x["orders_created_cumulative"] for x in observed],
         "F3_HJ_ORIGINAL_EVIDENCE_DRIFT")
    memory=_read_scope(root,visible,arm,cond,"native")
    # Construction score is not a preregistered acceptance decision.
    # No calibrating on observed deliveries, no selection nor G4/G5.
    m={
        "delivery_rmse_orders":_rmse(delivery),
        "arrival_rmse_orders":_rmse(arrivals),
        "delivery_at_cutoff_predicted":delivery[-1]["native_prediction"],
        "delivery_at_cutoff_observed":delivery[-1]["observed_orders"],
        "delivery_at_cutoff_residual":delivery[-1]["residual_orders"],
        "delivery_curve_predicted":[r["native_prediction"] for r in delivery],
        "grid_minutes":[r["t_minutes"] for r in delivery],
        "comparison_semantics":"SAME_PUBLIC_POS_DELIVERED_COUNTS_AND_HJ",
    }
    extras=[x for x in actual_hj["comparisons"]
            if x["observable"]=="n_completed_stage_services"]
    if arm=="M" and cond=="O1":
        need(len(extras)==1 and
             "DISCRETE_COMPLETED_SERVICES" in extras[0].get("limit",""),
             "F3_O1_NOT_MAPPED_SEMANTICALLY")
        # A necessary physical-capacity implication can be checked without
        # making the UNVERIFIED discrete-completion vs continuous-flow bridge
        # into a G3 score or a fitted maxThroughput. O1 is read only here in
        # the evaluator, not inside the frozen native E1 composer.
        bound_certificate=m_o1_capacity_certificate.certificate(
            visible,manifest["candidate"])
        m["preparation"]={
            "observed":extras[0]["observed_orders"],
            "model_integrated_flow":extras[0]["native_prediction"],
            "status":"PROVISIONAL_NON_EQUIVALENT_MEASUREMENT_NO_G3_SCORE",
            "conditional_original_E1_bound":bound_certificate}
    else:
        need(not extras,"F3_ILLEGITIMATE_PHYSICAL_MEASUREMENT")
    return {
        "status":"REAL_ORIGINAL_D_OR_E1_SIMULATION_COMPLETED",
        "G0":"PASS_GENERATOR_REGENERATED_ORIGINAL_GRAMMAR",
        "G1":"PASS_DECLARED_UNITS_AND_A1_STOCK_FLOW_CONTRACT_ONLY",
        "G2":"PASS_REAL_OMC_MATERIAL_BALANCE_ENGINEERING",
        "G3":"CONSTRUCTION_DESCRIPTIVE_ONLY_NO_ADMISSIBILITY_THRESHOLD",
        "interface_POS":"SUPPORTED_AND_CONSUMED_BY_DECLARED_STIMULUS",
        "generator_evidence_consumed":["pos_arrival_events"],
        "O1_extra_preparation_used_to_construct_native_model":False,
        "O1_extra_preparation_used_for_conditional_bound_audit":
            arm=="M" and cond=="O1",
        "O1_extra_preparation_role":"NOT_AVAILABLE"
            if cond=="O0" else (
                "EVALUATOR_HJ_PROVISIONAL_NON_EQUIVALENT"
                if arm=="M" else "UNSUPPORTED_NATIVE_PORT"),
        "interface_O1_physical":(
            "PARTIALLY_MAPPED_NOT_CALIBRATED"
            if arm=="M" and cond=="O1" else
            "UNSUPPORTED_DOCUMENTED" if cond=="O1" else "NOT_APPLICABLE"),
        "native_model":manifest["native_model_name"],
        "native_model_sha256":verified["native_model_sha256"],
        "trace_sha256":verified["solver_csv_sha256"],
        "source_snapshot_hash":manifest["source_snapshot_hash"],
        "full_candidate_hash":verified["candidate_full_hash"],
        "max_material_residual_orders":verified["max_material_residual_orders"],
        "independent_forecast":"NOT_RUN",
        "parameters_nominal_unfitted":True,
        "no_structure_selection":True,
        "metrics":m,"memory":memory}


def adjudicate(visible, roots, workers, f2):
    need(set(visible)==set(CONDITIONS) and set(roots)==
         {(c,a) for c in CONDITIONS for a in ("D","M")}
         and set(workers)=={(c,a) for c in CONDITIONS for a in ARMS},
         "F3_MISSING_OR_EXTRA_EXECUTION_SCOPE")
    for c,v in visible.items():
        validate_a1_visible(v,c)
    need(visible["O0"]["construction"]["pos_arrival_events"]==
         visible["O1"]["construction"]["pos_arrival_events"] and
         visible["O0"]["construction"]["observation_series"]==
         visible["O1"]["construction"]["observation_series"],
         "F3_CONDITIONS_NOT_SAME_PUBLIC_POS")
    need(f2["schema"]==physical.SCHEMA and f2["B0"]["status"]==
         "B0_POS_MATERIAL_BALANCE_PASS" and
         f2["B1"]["status"]=="B1_DIRECT_FULL_INSTRUMENTATION_PASS" and
         f2["B2"]["status"]=="B2_EXACT_RESOURCE_PERIODS_PASS",
         "F3_PHYSICAL_EVALUATOR_REFERENCE_MISSING")
    known=f2["B0"]["checkpoints"]
    for c in CONDITIONS:
        public=visible[c]["construction"]["observation_series"]
        ref=[x for x in known if float(x["time_minutes_exact"])<=10]
        need(len(ref)==len(public) and all(
            x["delivered_cumulative"]==y["delivered_cumulative"]
            and x["orders_created_cumulative"]==y["orders_created_cumulative"]
            for x,y in zip(ref,public)),"F3_B0_NOT_SAME_PUBLIC_OBSERVATIONS")
    arms={}
    for cond in CONDITIONS:
        arms[cond]={}
        for arm in ARMS:
            own=_worker(workers[(cond,arm)],visible[cond],arm,cond)
            if arm=="B":
                arms[cond][arm]={
                    "worker":own,
                    "execution_state":"BLOCKED_NEW_EV01_PROVIDER_AUTHORIZATION",
                    "native_generation":"NO_LIVE_LLM_OUTPUT",
                    "G0":"NOT_RUN_GENUINE_INFERENCE",
                    "G1":"NOT_RUN","G2":"NOT_RUN","G3":"NOT_RUN",
                    "method_abstention":False,
                    "mock_is_not_method_inference":True,
                    "interface":"OFFLINE_TRANSPORT_ONLY_EV01_LIVE_NOT_TESTED"}
            else:
                n=_native(roots[(cond,arm)],visible[cond],arm,cond)
                arms[cond][arm]={
                    "worker":own,"native":n,
                    "execution_state":"COMPLETED_ENGINEERING_NATIVE",
                    "method_abstention":False}
    need(arms["O0"]["B"]["worker"]["prompt_hashes"]!=
         arms["O1"]["B"]["worker"]["prompt_hashes"],
         "F3_B_MOCK_NOT_CONDITION_DISTINCT")
    # Model source identity, not equality of RMSE, explains the nominal
    # O0/O1 similarity. A future method MAY legitimately change its output
    # after consuming O1; source inequality alone is not consumption proof.
    condition_fidelity={}
    for arm in ("D","M"):
        a,b=arms["O0"][arm]["native"],arms["O1"][arm]["native"]
        condition_fidelity[arm]=compare_native_conditions(a,b,arm)
    distinct_case_ids=[arms[c][a]["worker"]["memory"]["case_id"]
                       for c in CONDITIONS for a in ARMS]
    distinct_case_ids +=[arms[c][a]["native"]["memory"]["case_id"]
                         for c in CONDITIONS for a in ("D","M")]
    need(len(set(distinct_case_ids))==10,"F3_MEMORY_CROSS_SCOPE")
    return {"schema":SCHEMA,
        "world":"EV01_KNOWN_SYNTHETIC_CONTROL",
        "cutoff_minutes":"[0,10), sample at t=10 strict-before",
        "mode":"ENGINEERING_RETROSPECTIVE_NOT_BLIND_HOLDOUT",
        "A3":"PARTIAL",
        "MODEL-01":"PARTIAL_D_M_REAL_B_LIVE_NOT_AUTHORIZED",
        "CONDITION-01":"PARTIAL_APP_ISOLATION_NOT_GITHUB_ACL",
        "MEMORY-01":"PARTIAL_ORIGINAL_LEDGER_PER_SCOPE_RECONSTRUCTED",
        "interface_shared_POS":"SUPPORTED_AND_USED_IN_D_M_INPUT",
        "native_condition_fidelity":condition_fidelity,
        "O1_additional_evidence_consumed_by_D_M_generator":False,
        "O1_extra_preparation_only_in_evaluator_HJ_for_M":True,
        "M_O1_fixed_E1_candidate_necessary_bound_audited":True,
        "M_O1_discrete_to_continuous_bridge":"NOT_EMPIRICALLY_VERIFIED",
        "M_O1_unit_identity":"NOT_EMPIRICALLY_VERIFIED",
        "M_O1_exact_cutoff_mass_equality":"NOT_EMPIRICALLY_VERIFIED",
        "M_O1_unconditional_scientific_model_verdict":"NOT_IDENTIFIED_BY_AGGREGATED_O1",
        "M_O1_model_generation_or_calibration_from_extra_evidence":"NOT_RUN",
        "O1_native_assimilation":"NOT_DEMONSTRATED",
        "A1_B_MOCK_ORIGINAL_ENGINE":"TRANSPORT_ONLY_NOT_SCIENTIFIC_CONSUMPTION",
        "physical_evaluator_reference":{
            "B0":"SAME_PUBLIC_OBSERVATIONS",
            "B1":"EVALUATOR_ONLY_NOT_COMPARABLE_AS_EQUAL_EVIDENCE_TO_O0",
            "B2":"EVALUATOR_ONLY_CAPACITY_STATES_NOT_D_OR_M_INPUT",
            "physical_full_source_not_given_to_workers":True},
        "arms":arms,
        "execution_scopes":{"worker_and_native_lineages":len(distinct_case_ids),
                            "unique_case_ids":len(set(distinct_case_ids)),
                            "memory_access_control":"APPLICATION_FILTER_ONLY"},
        "G4":"NOT_RUN","G5":"NOT_RUN",
        "diagnostic_only":"No tolerance, no heldout prediction, no structure selection",
        "provider_calls":0,
        "no_genuine_buffalo_inference_in_this_EV01_run":True,
        "historical_B_cloudflare_capability":{
            "status":"REAL_INFERENCE_DEMONSTRATED_ON_OTHER_EXPERIMENTS_NOT_EV01",
            "provider_model":"@cf/zai-org/glm-5.3-flash",
            "original_engine":"UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc",
            "prior_CI_runs":{
                "initial_native":"40255975864",
                "R1_physical_attempt":"40452596916",
                "R2_truncated":"40486060023",
                "R2_16k_simulated_with_stimulus_divergence":"40490534985"},
            "prior_G2_is_not_EV01_G2":True,
            "prior_outputs_not_scored_as_EV01_predictions":True}}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--public",type=Path,required=True)
    p.add_argument("--workers",type=Path,required=True)
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),"F3_REFUSE_OVERWRITE")
    visible={c:_read(a.public/(c+"_VISIBLE.json")) for c in CONDITIONS}
    roots={(c,arm):a.native/("a1-cafe-omc-"+c+"-"+arm)
           for c in CONDITIONS for arm in ("D","M")}
    workers={(c,arm):a.workers/("a1-cafe-native-"+c+"-"+arm)
             for c in CONDITIONS for arm in ARMS}
    f2=physical.build() # evaluator-only; never uploaded as producers' input
    output=adjudicate(visible,roots,workers,f2)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(output)+b"\n")
    print(json.dumps({"A3":output["A3"],
       "MODEL-01":output["MODEL-01"],
       "native_G2":[(c,a) for c in CONDITIONS for a in ("D","M")],
       "Buffalo":"BLOCKED_LIVE_UNAUTHORIZED",
       "case_scopes":output["execution_scopes"]["unique_case_ids"]}))


if __name__=="__main__":main()
