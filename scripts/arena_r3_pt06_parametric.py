"""PT-06 / R3: preregister a bounded per-structure M3 parameter-search variant.

PREPARATION ONLY. No worlds, no observations, no OpenModelica and no LLM.
This variant is separate from original M3, which remains a frozen comparator.
M3-P six historical cases are DEVELOPMENT evidence, not new validation.
"""
from __future__ import annotations

import argparse
import copy
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_m3_prepare import family, require, CONSTRUCTION_TIMES, CONSTRUCTION_NOISE
from scripts.arena_m3_select import decide as frozen_m3_decide
from scripts.arena_m_visible_pulse import ROOT, composer, backend, stimulus_only_replace
from scripts.arena_v0_contract import canonical, digest

METHOD="short-e1-r3-bounded-parametric-per-structure/0.1"
SCHEMA="igc-arena-r3-pt06-parametric-preregister/0.1"
CANDIDATE_LIMIT=27
TOPOLOGIES=("C00","C01","C02")
GRID=(0.25,0.5,1.0)
CONSTRUCTION_TOLERANCE=0.02
M3_FROZEN_MIN_GAP=0.035
PACKAGE="ArenaR3Parametric"
CASE_PLAN={
    "case_id":"R3-T1-SHIFTED-REPRESENTABLE",
    "case_type":"SYNTHETIC_WITHIN_E1_FAMILY_NOT_EXTERNAL_HOLDOUT",
    "generating_material_class":"C00",
    "generating_role_responseTime_hours":{"preparation":0.75,"dispatch":0.30},
    "public_stimulus":{"kind":"pulse","rate":1.7,"duration_hours":2.0},
    "construction_times_hours":[0,1,2,3],
    "declared_noise_items":[0.0,0.002,-0.003,0.004],
    "measurement_bound":"NONE_ESTABLISHED",
    "status":"CASE_BLUEPRINT_ONLY_NO_WORLD_OR_OBSERVATIONS_GENERATED",
    "observability":"deliveredTotal",
    "not_from_m3p_historical_cases":True
}


def guard(ok,reason):
    if not ok: raise ValueError(reason)


def _bounds(cfg,classes,role):
    spec=cfg["roles"][role]
    return classes[spec["class_id"]]["parameters"]["responseTime"]


def plan():
    cfg,classes,paths=family()
    guard(set(paths)=={0,1,2},"R3_M3_MATERIAL_REPERTOIRE_DRIFT")
    # Restrict this FIRST bounded case to two well-specified dimensions.
    # Transit timing stays fixed at the original E1 value (1.6h); the
    # limitation is explicit rather than implicitly fitting all parameters.
    bounds={role:_bounds(cfg,classes,role) for role in ("preparation","dispatch")}
    for value in GRID:
        guard(all(x["min"]<=value<=x["max"] for x in bounds.values()),
              "R3_GRID_OUTSIDE_CATALOG")
    guard(all(bounds[r]["min"]<=CASE_PLAN["generating_role_responseTime_hours"][r]
              <=bounds[r]["max"] for r in bounds),"R3_WORLD_BLUEPRINT_OUTSIDE_CATALOG")
    candidates=[]
    classes_text=[]
    for n in range(3):
        key,base=paths[n]
        for j,prep in enumerate(GRID):
            for k,dispatch in enumerate(GRID):
                ix=j*len(GRID)+k
                graph=copy.deepcopy(base)
                for instance in graph["instances"]:
                    if instance["role"] in ("preparation","dispatch"):
                        instance["parameters"]["responseTime"]=(
                            prep if instance["role"]=="preparation" else dispatch)
                composer.check_graph(graph,cfg,classes)
                guard(composer.canonical(graph)==key,
                      "R3_PARAMETER_MUTATION_CHANGED_MATERIAL_STRUCTURE")
                guard(graph["links"]==base["links"] and
                      [(x["id"],x["role"],x["class_id"]) for x in graph["instances"]]==
                      [(x["id"],x["role"],x["class_id"]) for x in base["instances"]],
                      "R3_MATERIAL_TOPOLOGY_MUTATED")
                for ai,bi in zip(graph["instances"],base["instances"]):
                    if ai["role"] not in ("preparation","dispatch"):
                        guard(ai==bi,"R3_UNDECLARED_PARAMETER_CHANGE")
                    else:
                        guard({a:b for a,b in ai["parameters"].items() if a!="responseTime"}==
                              {a:b for a,b in bi["parameters"].items() if a!="responseTime"},
                              "R3_NON_RESPONSE_TIME_PARAM_CHANGED")
                name=f"R3C{n:02d}P{ix:02d}"
                model=stimulus_only_replace(backend.render_model(name,graph,cfg,classes),1.7,2.0)
                guard("der(" not in model and "when " not in model and
                      "connect(" in model,"R3_HANDWRITTEN_EQUATIONS_FORBIDDEN")
                candidate={
                    "id":f"C{n:02d}P{ix:02d}",
                    "material_class":f"C{n:02d}",
                    "class_name":name,
                    "original_material_graph_sha256":"sha256:"+key,
                    "graph":graph,
                    "role_responseTime_hours":{"preparation":prep,"dispatch":dispatch},
                    "transit_responseTime":"UNCHANGED_E1_1_6_HOURS_WHERE_PRESENT",
                    "all_other_parameters":"FROZEN_E1_CATALOG",
                    "is_frozen_m3_nominal":prep==dispatch==0.5,
                    "compiled_class_sha256":"sha256:"+sha256(model.encode()).hexdigest()
                }
                candidates.append(candidate)
                classes_text.append(model)
    guard(len(candidates)==CANDIDATE_LIMIT and
          len(set(x["id"] for x in candidates))==CANDIDATE_LIMIT and
          sum(x["is_frozen_m3_nominal"] for x in candidates)==3,
          "R3_GRID_OR_FIXED_REFERENCE_DRIFT")
    package="\n".join(["within;",f"package {PACKAGE}",
                     "\n\n".join(classes_text),
                     'annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
                     f"end {PACKAGE};",""])
    manifest={
        "schema":SCHEMA,"method":METHOD,
        "arm_id":"M","version_kind":"NEW_VARIANT_NOT_MODIFIED_M3",
        "source":"UNCHANGED_SHORT_E1_COMPOSER_BACKEND_AND_MOLECULES",
        "registry_sha256":digest(cfg),
        "observable":"deliveredTotal","unit":"items",
        "public_stimulus":{"kind":"pulse","rate_items_per_hour":1.7,"duration_hours":2.0},
        "construction_times_hours":CONSTRUCTION_TIMES,
        "fixed_m3_policy":{"max_best_rmse_items":CONSTRUCTION_TOLERANCE,
                           "min_gap_rmse_items":M3_FROZEN_MIN_GAP},
        "new_policy":{"criterion":"ALL_COMPATIBLE_CLASSES_OR_ABSTAIN",
                      "compatibility_threshold_items":CONSTRUCTION_TOLERANCE,
                      "threshold_kind":"POLICY_CUTOFF_NOT_INSTRUMENT_ERROR_BOUND",
                      "selection_without_observed_trajectory":"PROHIBITED"},
        "search":{"topologies":list(TOPOLOGIES),
                  "parameters_varied_by_role":["preparation.responseTime",
                                               "dispatch.responseTime"],
                  "grid_hours":list(GRID),
                  "topologies_count":3,"parameter_configs_per_topology":9,
                  "max_candidate_evaluations":CANDIDATE_LIMIT,
                  "nominal_M3_representatives":3,
                  "transit_responseTime_fixed_hours":1.6,
                  "values_origin":"DESIGN_GRID_WITHIN_E0_CATALOG_0_1_TO_5_0_HOURS_NOT_KNOWN_WORLD_TRUTH",
                  "search_method":"FINITE_CARTESIAN_GRID_NO_OPTIMIZER",
                  "solver":"DASSL_0_TO_6_HOURS_120_INTERVALS_M3_NATIVE_METHOD"},
        "candidates":candidates,
        "modelica_package_sha256":"sha256:"+sha256(package.encode()).hexdigest(),
        "method_status":"PREFLIGHT_ONLY_NOT_SIMULATED",
        "candidate_solver_calls":0,"world_solver_calls":0,
        "world_generation":"NOT_RUN",
        "test_plan":{"first_case_id":CASE_PLAN["case_id"],
                     "first_case_blueprint_stored_separately":True,
                     "remaining_cases":["AMBIGUITY_TO_DESIGN_BEFORE_SIMULATION",
                                        "INCOMPATIBILITY_TO_DESIGN_BEFORE_SIMULATION"],
                     "historical_M3_P_SIX_CASES":"DEVELOPMENT_NOT_INDEPENDENT_VALIDATION"},
        "prohibited_claims":["M3_FIXED_POLICY_IMPROVED","G3_PASS",
                              "EXTERNAL_CAUSAL_IDENTIFICATION","BLIND_HOLDOUT"]
    }
    return manifest,package


def classify(scores, manifest):
    """Only construction RMSE of 27 REAL, verified future traces. No world labels."""
    guard(manifest["schema"]==SCHEMA and manifest["method"]==METHOD,
          "R3_DIFFERENT_PREREGISTRATION")
    guard(manifest["new_policy"]["compatibility_threshold_items"]==0.02 and
          manifest["search"]["max_candidate_evaluations"]==27,
          "R3_POSTHOC_POLICY_OR_BUDGET_CHANGE")
    by_id={v["id"]:v for v in manifest["candidates"]}
    guard(len(by_id)==27 and len(scores)==27 and
          {x.get("id") for x in scores}==set(by_id),"R3_MISSING_OR_EXTRA_CANDIDATE")
    minima={}
    for item in scores:
        guard(set(item)=={"id","rmse_items","csv_sha256","g2_status"} and
              type(item["rmse_items"]) in (int,float) and
              math.isfinite(item["rmse_items"]) and item["rmse_items"]>=0 and
              item["g2_status"]=="G2_SIMULATED_CONDITIONALLY" and
              isinstance(item["csv_sha256"],str) and
              item["csv_sha256"].startswith("sha256:"),
              "R3_INVALID_UNVERIFIED_CANDIDATE")
        cl=by_id[item["id"]]["material_class"]
        old=minima.get(cl)
        if old is None or (item["rmse_items"],item["id"])<(old["rmse_items"],old["id"]):
            minima[cl]=item
    compatible=sorted(k for k,s in minima.items()
                      if s["rmse_items"]<=CONSTRUCTION_TOLERANCE)
    if not compatible:
        state="ABSTAIN_ADMISSIBLE_GRID_HAS_NO_COMPATIBLE_STRUCTURE"
    elif len(compatible)>1:
        state="AMBIGUOUS_MULTIPLE_COMPATIBLE_STRUCTURES"
    else:
        state="ONE_COMPATIBLE_STRUCTURE_IN_GRID_NOT_CAUSALLY_IDENTIFIED"
    frozen=[s for s in scores if by_id[s["id"]]["is_frozen_m3_nominal"]]
    frozen_scores=[{"id":by_id[s["id"]]["material_class"],
                    "material_queues":2+int(by_id[s["id"]]["material_class"][-1]),
                    "rmse_items":s["rmse_items"]} for s in frozen]
    baseline=frozen_m3_decide(frozen_scores,min_gap=0.035,max_best=0.02)
    return {"schema":"igc-arena-r3-pt06-bounded-grid-result/0.1",
            "method":METHOD,"status":state,
            "compatible_material_classes":compatible,
            "per_structure_best":{k:{"candidate_id":s["id"],
                                    "rmse_items":s["rmse_items"],
                                    "csv_sha256":s["csv_sha256"]}
                                  for k,s in sorted(minima.items())},
            "frozen_m3_original_policy":baseline,
            "candidate_evaluations":len(scores),
            "parameters_fitted_only_on_construction":True,
            "independent_holdout":"NOT_RUN",
            "not_trustworthy_outside_finite_grid":True,
            "no_causal_structure_identification":True}



def generate_first_case_world_modelica():
    """Researcher-side synthetic case source ONLY; not an observation or test run."""
    cfg,classes,paths=family()
    key,graph=paths[0]
    graph=copy.deepcopy(graph)
    for item in graph["instances"]:
        role=item["role"]
        if role in ("preparation","dispatch"):
            item["parameters"]["responseTime"]=CASE_PLAN[
                "generating_role_responseTime_hours"][role]
    composer.check_graph(graph,cfg,classes)
    guard(composer.canonical(graph)==key,"R3_T1_WORLD_TOPOLOGY_DRIFT")
    guard(not any(
        x["parameters"]["responseTime"] in GRID
        for x in graph["instances"] if x["role"] in ("preparation","dispatch")),
        "R3_T1_WORLD_NOT_OFF_GRID")
    model=stimulus_only_replace(
        backend.render_model("R3WorldT1",graph,cfg,classes),
        CASE_PLAN["public_stimulus"]["rate"],
        CASE_PLAN["public_stimulus"]["duration_hours"])
    guard("der(" not in model and "when " not in model and
          "connect(" in model,"R3_WORLD_EQUATIONS_NOT_ORIGINAL_E1")
    content="\n".join(["within;","package ArenaR3World",
             model,'annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
             "end ArenaR3World;",""])
    return content


def write_plan(folder):
    folder=Path(folder)
    guard(not folder.exists(),"R3_OUTPUT_EXISTS")
    manifest,modelica=plan()
    folder.mkdir(parents=True)
    (folder/"manifest.json").write_bytes(canonical(manifest)+b"\n")
    (folder/(PACKAGE+".mo")).write_bytes(modelica.encode())
    (folder/"ArenaR3WorldT1-NOT-SIMULATED.mo").write_bytes(
        generate_first_case_world_modelica().encode())
    # This file is deliberately *not* in any selector input: source truth may
    # never be used for choosing the 27 candidate scores.
    (folder/"researcher-case-blueprint-NOT-SELECTOR-INPUT.json").write_bytes(
        canonical(CASE_PLAN)+b"\n")
    return manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    manifest=write_plan(a.out)
    print(json.dumps({"status":"R3_PT06_PREFLIGHT_ONLY_NO_SOLVER_CALLS",
                      "methods":{"fixed":"ORIGINAL_M3_UNMODIFIED","new":METHOD},
                      "candidate_limit":manifest["search"]["max_candidate_evaluations"],
                      "manifest_sha256":digest(manifest)}))


if __name__=="__main__":
    main()
