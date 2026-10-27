"""PT-06 / STR-03: predeclare two contrasting R3 cases WITHOUT simulation.

R3-T2 tests weak early-window observability (ambiguity is an outcome hypothesis).
R3-T3 tests incompatibility with the FROZEN 27-member finite parameter grid.

The original Short E1 compositor, backend, C00/C01/C02 candidates, frozen M3
selector, compatibility threshold and stimulus are NOT modified. All candidate
CSVs MUST be reused from genuine R3-T1 OpenModelica run #40578550337;
this module neither simulates worlds nor inspects their expected responses.
"""
from __future__ import annotations

import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_m3_prepare import family
from scripts.arena_m_visible_pulse import composer, backend, stimulus_only_replace
from scripts.arena_r3_pt06_parametric import plan, guard, PACKAGE
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-arena-r3-pt06-t2-t3-preregister/0.1"
WORLD_PACKAGE="ArenaR3T23Worlds"
ORIGINAL_GRID_SHA="sha256:d33cc4ca8c253226ff50efa6c47e40b9b8c32d0436f370907db2579c9dc0fde5"
R3_T1_EVIDENCE_RUN=40578550337
R3_T1_EVIDENCE_ARTIFACT=12769310740
THRESHOLD=0.020
CASES=(
    {
      "id":"R3-T2-EARLY-OBSERVABILITY",
      "scientific_target":"EARLY_WINDOW_STRUCTURAL_AMBIGUITY",
      "anticipated_outcome":"MULTIPLE_COMPATIBLE_STRUCTURES_UNDER_WEAK_EXCITATION_NOT_GUARANTEED",
      "world_material_class":"C01",
      "source_parameters":{},  # Nominal E1, not chosen in response to observed R3-T1 error.
      "times_hours":[0.0,0.05,0.10,0.15],
      "declared_noise_items":[0.0,0.0,0.0,0.0],
      "world_stop_hour":0.15,
      "world_intervals":120,
      "interpretation_limit":"EARLY_WINDOW_NEGATIVE_CONTROL_NOT_PROOF_OF_GLOBAL_EQUIVALENCE"
    },
    {
      "id":"R3-T3-GRID-INCOMPATIBILITY",
      "scientific_target":"FINITE_GRID_OUTSIDE_ADMISSIBLE_PARAMETER_ENVELOPE",
      "anticipated_outcome":"NO_COMPATIBLE_STRUCTURE_IN_FIXED_GRID_NOT_GUARANTEED",
      "world_material_class":"C02",
      "source_parameters":{"preparation":4.0,"dispatch":4.0,"transit":4.0},
      "times_hours":[0.0,1.0,2.0,3.0],
      "declared_noise_items":[0.0,0.002,-0.003,0.004],
      "world_stop_hour":3.0,
      "world_intervals":120,
      "interpretation_limit":"OUTSIDE_FINITE_GRID_NOT_OUTSIDE_ORIGINAL_E1_CATALOG"
    }
)

def make_world_graph(spec):
    cfg,classes,paths=family()
    n=int(spec["world_material_class"][-2:])
    guard(n in paths,"R3_T23_UNKNOWN_ORIGIN_STRUCTURE")
    key,base=paths[n]
    graph=copy.deepcopy(base)
    seen=set()
    for inst in graph["instances"]:
        role=inst["role"]
        if role not in spec["source_parameters"]: continue
        value=spec["source_parameters"][role]
        bounds=classes[inst["class_id"]]["parameters"]["responseTime"]
        guard(type(value) in (int,float) and bounds["min"]<=value<=bounds["max"],
              "R3_T23_GENERATING_PARAMETER_OUTSIDE_ORIGINAL_CATALOG")
        guard(value!=inst["parameters"]["responseTime"],
              "R3_T23_PARAMETER_CHANGE_NOT_REAL")
        inst["parameters"]["responseTime"]=value
        seen.add(role)
    guard(seen==set(spec["source_parameters"]),"R3_T23_MISSING_SOURCE_ROLE")
    composer.check_graph(graph,cfg,classes)
    guard(composer.canonical(graph)==key and graph["links"]==base["links"],
          "R3_T23_TOPOLOGY_OR_LINK_CHANGED")
    return cfg,classes,graph,key

def freeze():
    manifest,package=plan()
    guard(digest(manifest)==ORIGINAL_GRID_SHA,
          "R3_T23_T1_CANDIDATES_OR_POLICY_DRIFT")
    guard(len(manifest["candidates"])==27 and
          manifest["new_policy"]["compatibility_threshold_items"]==THRESHOLD,
          "R3_T23_UNAPPROVED_BUDGET_OR_THRESHOLD")
    root={
      "schema":SCHEMA,
      "phase":"PREDECLARED_NO_SIMULATION",
      "original_candidate_manifest_sha256":ORIGINAL_GRID_SHA,
      "original_candidate_modelica_sha256":manifest["modelica_package_sha256"],
      "archived_candidate_run_id":R3_T1_EVIDENCE_RUN,
      "archived_candidate_artifact_id":R3_T1_EVIDENCE_ARTIFACT,
      "reuse_original_candidate_csvs":True,
      "reuse_requires_all_27_real_G2_validated_csvs":True,
      "new_candidate_simulations":0,
      "new_world_simulations_requested_later":len(CASES),
      "total_new_simulations_executed":0,
      "new_ai_calls":0,
      "fixed_M3_method":"ORIGINAL_DECIDE_MAX_BEST_0_020_MIN_GAP_0_035",
      "R3_policy":"PER_TOPOLOGY_MIN_RMSE_ALL_COMPATIBLE_OR_ABSTAIN",
      "threshold_items":THRESHOLD,
      "threshold_kind":"POLICY_NOT_INSTRUMENT_ERROR_BOUND",
      "stimulus":{"kind":"pulse","rate":1.7,"duration":2.0},
      "no_R4_reserve_or_holdout":True,
      "no_new_molecules_or_structures":True,
      "no_R3_T1_posthoc_tuning":True,
      "case_protocols":[]
    }
    texts=[]
    sealed=[]
    for i,spec in enumerate(CASES):
        cfg,classes,graph,key=make_world_graph(spec)
        name=f"R3T{i+2}World"
        model=stimulus_only_replace(backend.render_model(name,graph,cfg,classes),1.7,2.0)
        guard("der(" not in model and "when " not in model and
              "connect(" in model and "stimulus(" in model,
              "R3_T23_NON_E1_EQUATIONS_OR_STIMULUS")
        texts.append(model)
        root["case_protocols"].append({
          "case_id":spec["id"],
          "question":spec["scientific_target"],
          "anticipated_outcome_NOT_AN_ASSUMED_RESULT":spec["anticipated_outcome"],
          "public_observation_times_hours":spec["times_hours"],
          "declared_noise_items":spec["declared_noise_items"],
          "observable":"deliveredTotal",
          "new_world_simulation_interval":[0,spec["world_stop_hour"]],
          "world_solver_steps":spec["world_intervals"],
          "world_time_reserved":[4,5,6],
          "world_reserved_times_simulated":False,
          "no_candidate_regeneration":True,
          "case_interpretation_limit":spec["interpretation_limit"],
          "evaluation":"FROZEN_27_CSVS_0_020_PER_STRUCTURE_COMPATIBLE_SET",
          "g3_heldout":"NOT_RUN"
        })
        sealed.append({
          "case_id":spec["id"],"synthetic_source_class":spec["world_material_class"],
          "source_response_times_changed":spec["source_parameters"],
          "original_graph_sha256":"sha256:"+key,
          "model_name":name,
          "model_text_sha256":"sha256:"+sha256(model.encode()).hexdigest(),
          "not_an_input_to_selector":True,
          "zero_simulations_now":True
        })
    guard(len(root["case_protocols"])==len(sealed)==2,"R3_T23_CASE_COUNT_CHANGED")
    world_package="\n".join(["within;",f"package {WORLD_PACKAGE}",
                   "\n\n".join(texts),
                   'annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
                   f"end {WORLD_PACKAGE};",""])
    root["world_package_sha256"]="sha256:"+sha256(world_package.encode()).hexdigest()
    return root,world_package,{"schema":SCHEMA,"sealed":sealed,
                               "not_input_to_any_selector":True,
                               "truth_visible_only_after_scoring":True}

def emit(folder):
    folder=Path(folder)
    guard(not folder.exists(),"R3_T23_PREFLIGHT_OUTPUT_EXISTS")
    protocol,model,sealed=freeze()
    folder.mkdir(parents=True)
    (folder/"researcher-private").mkdir()
    (folder/"protocol.json").write_bytes(canonical(protocol)+b"\n")
    (folder/(WORLD_PACKAGE+"-NOT-SIMULATED.mo")).write_bytes(model.encode())
    (folder/"researcher-private"/"sealed-worlds.json").write_bytes(canonical(sealed)+b"\n")
    return protocol

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=emit(a.out)
    print(json.dumps({"status":"R3_T2_T3_BOTH_PREREGISTERED_ZERO_NEW_SIMULATIONS",
      "reused_candidates":27,"new_candidate_simulations":0,
      "planned_world_simulations":2,"solver_calls_so_far":0,
      "protocol_hash":digest(result)},sort_keys=True))

if __name__=="__main__":
    main()
