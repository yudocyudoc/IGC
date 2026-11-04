"""F3 · Short E1 O1 fixed-registry necessary-capacity certificate.

A conditional, exact *incompatibility* diagnostic on original molecular
graphs; it is NOT a discrete-event operator, sensor-calibrated H_j, parameter
fit, model selector, or claim that E1 cannot be calibrated in another regime.

The measured count is the number of physically COMPLETED preparation
services strictly before cutoff. The Short E1 role exposes a continuous
FLOW<ReadyOrder>, bounded by maxThroughput units/hour. Only under the
UNVERIFIED bridge 'one completed physical preparation -> one ReadyOrder unit'
could its time integral be compared to the count. Under that explicit bridge,
a necessary condition is count <= maxThroughput * horizon_hours.

This evaluates original registered graph classes and fixed parameters
without access to the evaluator's private FULL event trace or DES.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as Q
from pathlib import Path

from scripts.arena_cafe.native_handoff import need,validate_a1_visible
from scripts.arena_cafe import observation_ports
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-cafe-f3-m-o1-fixed-registry-necessary-bound/0.1"
REGISTRY=Path("experiments/e1/registry.base.json")
EXPECTED_ROLE="preparation"
EXPECTED_CLASS="bounded-queue"
ASSUMPTION="UNVERIFIED_ONE_DISCRETE_COMPLETION_EQUALS_ONE_E1_READYORDER_UNIT"


def bound(count,max_throughput,cutoff_minutes):
    """Exact bound. No uncertainty margin is inferred from a model residual."""
    need(type(count) is int and count>=0,
         "F3M_O1_BAD_DISCRETE_COUNT")
    need(type(max_throughput) in (int,float,str,Q)
         and type(cutoff_minutes) in (int,str,Q),
         "F3M_O1_BAD_BOUND_INPUT_TYPE")
    try:
        capacity=Q(str(max_throughput))
        cutoff=Q(str(cutoff_minutes))
    except (ValueError,ZeroDivisionError):
        raise ValueError("F3M_O1_BAD_BOUND_NUMBER") from None
    need(capacity>0 and cutoff>0 and cutoff<=120,
         "F3M_O1_BAD_CAPACITY_OR_CUTOFF")
    mass_max=capacity*cutoff/60
    observed=Q(count)
    return {
        "max_throughput_units_per_hour_exact":str(capacity),
        "cutoff_minutes_exact":str(cutoff),
        "maximum_possible_cumulative_completed_mass_exact":str(mass_max),
        "observed_discrete_services_completed_pre_cutoff":count,
        "necessary_average_rate_to_equal_count_units_per_hour_exact":
            str(observed*60/cutoff),
        "shortfall_of_nominal_max_mass_to_count_exact":
            str(max(Q(0),observed-mass_max)),
        "necessary_one_to_one_condition_satisfied":observed<=mass_max,
    }


def certificate(visible,candidate,registry=REGISTRY):
    validate_a1_visible(visible,"O1")
    need(Path(registry).resolve()==REGISTRY.resolve(),
         "F3M_O1_REGISTRY_NOT_F0_APPROVED")
    # The original E1 loader authenticates the catalog and typed connections.
    path,cfg,classes,catalog=observation_ports._get_registry(REGISTRY)
    need(catalog["schema_version"]=="igc-v3/e0.1" and
         cfg["schema"]=="igc-v3/e1.1",
         "F3M_O1_ORIGINAL_E1_CATALOG_DRIFT")
    from scripts.arena_m_short_e1 import get_composer
    composer=get_composer()
    original_graphs=composer.enumerate_graphs(cfg,classes)
    need(len(original_graphs)>0 and
         candidate.get("arm_id")=="M" and
         candidate.get("parameters_origin")==
             "E1_ORIGINAL_FIXED_REGISTRY_NOT_FITTED",
         "F3M_O1_NOT_ORIGINAL_FIXED_M_CANDIDATE")
    graph=candidate.get("ast")
    need(type(graph) is dict,"F3M_O1_AST_MISSING")
    composer.check_graph(graph,cfg,classes)
    key=composer.canonical(graph)
    mapping=dict(original_graphs)
    need(key in mapping and graph==mapping[key] and
         candidate.get("canonical_sha256")=="sha256:"+key and
         candidate.get("full_ast_sha256")==digest(graph) and
         candidate.get("registry_sha256")==digest(cfg),
         "F3M_O1_CANDIDATE_NOT_AUTHENTIC_OR_PARAMETERS_CHANGED")

    # Validate the *actual* native component is capped; neither a role
    # name nor an annotation alone proves the numerical bound.
    from scripts.arena_m_short_e1 import ROOT
    physical=ROOT/"src/modelica/IGCMolecules.mo"
    code=physical.read_text(encoding="utf-8")
    need("model BoundedQueue" in code and
         "SystemDynamics.Rates.RRate release(minFlow=0,maxFlow=maxThroughput);"
         in code and
         "connect(release.y,completed);" in code,
         "F3M_O1_E1_NATIVE_RELEASE_CAP_NOT_VERIFIED")
    physical_digest="sha256:"+hashlib.sha256(code.encode("utf-8")).hexdigest()

    # Check every member of the *existing finite typed E1 graph enumeration*
    # (not a new parameter grid) really carries one identical nominal
    # bounded-queue preparation stage.
    nominal_capacities=set()
    observed_roles=[]
    for _,original in original_graphs:
        prep=[x for x in original["instances"] if
              x["role"]==EXPECTED_ROLE]
        need(len(prep)==1 and
             prep[0]["class_id"]==EXPECTED_CLASS and
             type(prep[0]["parameters"].get("maxThroughput")) in (int,float),
             "F3M_O1_ORIGINAL_GRAPH_NOT_ONE_BOUNDED_PREPARATION")
        nominal_capacities.add(Q(str(prep[0]["parameters"]["maxThroughput"])))
        observed_roles.append(prep[0]["id"])
    need(len(nominal_capacities)==1 and
         nominal_capacities.pop()==Q(20),
         "F3M_O1_FIXED_NOMINAL_CAPACITY_DRIFT")
    need(sum(x["role"]==EXPECTED_ROLE for x in graph["instances"])==1,
         "F3M_O1_SELECTED_PREP_NOT_UNIQUE")

    selected=next(x for x in graph["instances"] if
                  x["role"]==EXPECTED_ROLE)
    need(selected["class_id"]==EXPECTED_CLASS and
         Q(str(selected["parameters"]["maxThroughput"]))==Q(20),
         "F3M_O1_SELECTED_PREP_BOUND_CHANGED")
    # Check the declared FLOW semantic type, not just variable spelling.
    port=observation_ports.m_port(visible,"O1",REGISTRY)
    mapped=[item for item in port["observation_operators"] if
            item["observed"]=="n_completed_stage_services"]
    need(len(mapped)==1 and
         mapped[0]["target"]["role"]==EXPECTED_ROLE and
         mapped[0]["target"]["port"]=="completed" and
         mapped[0]["target"]["type"]=="FLOW<ReadyOrder>" and
         mapped[0]["target"]["native_unit"]=="units/hour" and
         mapped[0]["status"]==
            "CANDIDATE_ROLE_ASSOCIATION_FROM_DISCLOSED_STAGE_NOT_IDENTIFIED",
         "F3M_O1_EXPECTED_CONTINUOUS_PREPARATION_FLOW_DRIFT")
    o1=visible["construction"]["physical_observation"]
    need(o1["measurement_limit"]==
         "completed_preparation_intervals_only_pre_cutoff" and
         o1["stage_disclosed"]=="preparacion" and
         o1["source_semantics"]=="synthetic_direct_physical_instrumentation",
         "F3M_O1_SOURCE_NOT_PHYSICAL_CENSORED_SERVICES")
    count=o1["n_completed_stage_services"]
    need(count==mapped[0]["observed_count"],
         "F3M_O1_PORT_NOT_SAME_COUNT")
    result=bound(count,selected["parameters"]["maxThroughput"],
                 visible["observability"]["cutoff_minutes_exact"])
    # This diagnoses the *fixed E1 baseline* under the conditional 1:1
    # projection, not an empirical incompatibility of the entire class.
    failed=not result["necessary_one_to_one_condition_satisfied"]
    return {
        "schema":SCHEMA,
        "arm_id":"M",
        "condition_id":"O1",
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "visible_input_hash":digest(visible),
        "original_candidate_full_ast_sha256":digest(graph),
        "original_candidate_canonical_sha256":"sha256:"+key,
        "original_E1_catalog_version":catalog["schema_version"],
        "original_E1_registry_sha256":digest(cfg),
        "original_Modelica_physical_class_sha256":physical_digest,
        "fixed_original_E1_graphs_checked":len(original_graphs),
        "enumerated_graphs_are_existing_typed_candidates_not_parameter_grid":True,
        "all_original_fixed_graphs_same_preparation_cap":True,
        "source_measurement_kind":
           "DISCRETE_COMPLETED_PHYSICAL_PREPARATION_SERVICES_PRE_CUTOFF",
        "native_measurement_kind":
           "CONTINUOUS_FLOW_READYORDER_UNITS_PER_HOUR",
        "bridge_assumption":ASSUMPTION,
        "bridge_empirically_verified":False,
        "bound_under_unverified_bridge":result,
        "conditional_fixed_nominal_candidate_status":(
            "EXCLUDED_BY_NECESSARY_CAPACITY_BOUND_IF_ONE_TO_ONE_BRIDGE"
            if failed else "NOT_EXCLUDED_BY_THIS_NECESSARY_BOUND_ONLY"),
        "inference_about_other_E1_parameters_or_structures":"NOT_ESTABLISHED",
        "native_model_generation_uses_O1":False,
        "O1_used_for_fixed_candidate_compatibility_audit":True,
        "candidate_selected_or_fitted_using_O1":False,
        "real_sensor_error_known":False,
        "statistical_falsification":"NOT_CLAIMED",
        "method_level_scientific_G3":"NOT_ESTABLISHED",
        "physical_mean_service_not_converted_to_responseTime":True,
        "physical_mean_wait_not_converted_to_stock_waiting":True,
        "no_truth_FULL_or_private_DES":True,
        "no_parameter_search_or_new_modelica":True,
        "provider_calls":0,
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--o1",type=Path,required=True)
    p.add_argument("--native-manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"F3M_O1_REFUSE_OVERWRITE")
    o1=json.loads(args.o1.read_text(encoding="utf-8"))
    m=json.loads(args.native_manifest.read_text(encoding="utf-8"))
    need(m.get("arm_id")=="M" and m.get("condition_id")=="O1" and
         m.get("input_hash")==digest(o1) and
         m.get("source_snapshot_hash")==o1["source_snapshot_hash"],
         "F3M_O1_MANIFEST_FOREIGN_INPUT")
    result=certificate(o1,m["candidate"])
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({
        "status":result["conditional_fixed_nominal_candidate_status"],
        "bridge_verified":result["bridge_empirically_verified"],
        "A3":result["A3"],"G4":result["G4"],"G5":result["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
