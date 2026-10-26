"""M3 parameter shift falsification: SAME original E1 molecules, NEW world parameters.

The M3 candidates and selector remain byte-identical to PR #35. Six varied
synthetic worlds are built with the same E1 compiler, changing only parameter
bindings inside synthetic world ASTs. No winner, "repair", or new hypotheses
are fabricated if fixed-template selector abstains or selects wrongly.
"""
from __future__ import annotations
import argparse,copy,json,math,hashlib
from pathlib import Path
from scripts.arena_m3_prepare import (family,pack,CONSTRUCTION_TIMES,RESERVED_TIMES,
    CONSTRUCTION_NOISE,RESERVED_NOISE,require)
from scripts.arena_m3_select import select_case, model_rows, sample
from scripts.arena_v0_contract import canonical,digest
from scripts.arena_m_visible_pulse import ROOT,composer,backend,REGISTRY

SCHEMA="igc-arena-m3-varied-parameters-frozen-candidates/0.1"
CASES=(
 ("P01",0,{"preparation":0.65,"dispatch":0.45},None),
 ("P02",1,{"transit":1.10},None),
 ("P03",2,{"transit":1.10},None),
 ("P04",1,{"transit":0.12},None),
 ("P05",0,{"preparation":0.90,"dispatch":0.90},None),
 ("P06",2,{"transit":0.12},None),
)
PKG="M3ParamWorlds"
SOLVER_INTERVALS=240

def sha(b):
    return hashlib.sha256(b).hexdigest()

def world_graph(base,modified,classes):
    g=copy.deepcopy(base)
    n=0
    for inst in g["instances"]:
        role=inst["role"]
        if role not in modified:continue
        cl=classes[inst["class_id"]]
        value=modified[role]
        bounds=cl["parameters"]["responseTime"]
        require(bounds["min"]<=value<=bounds["max"],"PARAM_WORLD_OUTSIDE_MOLECULE_BOUNDS")
        require(inst["parameters"]["responseTime"]!=value,"PARAM_WORLD_NOT_PERTURBED")
        inst["parameters"]["responseTime"]=value
        n+=1
    require(n>0,"NO_WORLD_PARAM_CHANGE")
    require(g["links"]==base["links"] and
            [(x["id"],x["role"],x["class_id"]) for x in g["instances"]]==
            [(x["id"],x["role"],x["class_id"]) for x in base["instances"]],
            "WORLD_TOPOLOGY_MUTATED")
    return g

def emit(out):
    require(not out.exists(),"M3P_ALREADY_EMITTED")
    require(out.resolve().is_relative_to(ROOT),"M3P_PATH_OUTSIDE_REPO")
    cfg,classes,paths=family()
    generated=[]
    truth=[]
    for index,(ident,top,changes,_) in enumerate(CASES):
        key,original=paths[top]
        altered=world_graph(original,changes,classes)
        composer.check_graph(altered,cfg,classes)
        require(composer.canonical(altered)==key,"STRUCTURAL_ID_CHANGED_WITH_PARAMS")
        cls=f"M3P{index:02d}"
        text=pack(cls,altered,cfg,classes)
        generated.append(text)
        truth.append({"case_id":ident,"world_model_class":cls,
            "origin_candidate_id":f"C{top:02d}","original_graph_sha256":"sha256:"+key,
            "only_world_responseTime_altered":changes,
            "graph":altered})
    require(len(generated)==6,"M3P_WORLD_COUNT")
    code="\n".join(["within;",f"package {PKG}","\n\n".join(generated),
     'annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
     f"end {PKG};",""])
    require("der(" not in code and "when " not in code,"HANDWRITTEN_ODE_FORBIDDEN")
    out.mkdir(parents=True)
    for folder in ("worlds","blind","post"):
        (out/folder).mkdir()
    (out/"M3ParamWorlds.mo").write_text(code)
    rel=out.resolve().relative_to(ROOT)
    cmds=[
      "getVersion();",
      'loadFile("/repo/src/modelica/IGCMolecules.mo");',
      'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");',
      f'loadFile("/repo/{rel}/M3ParamWorlds.mo");']
    for i,x in enumerate(truth):
        cls=x["world_model_class"]
        cmds += [f'checkModel({PKG}.{cls});',"print(getErrorString());",
          f'simulate({PKG}.{cls},startTime=0,stopTime=6,numberOfIntervals={SOLVER_INTERVALS},method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="{rel}/worlds/{x["case_id"].lower()}");',
          "print(getErrorString());"]
    (out/"simulate.mos").write_text("\n".join(cmds)+"\n")
    metadata={"schema":SCHEMA,"worlds":len(truth),
              "original_E1_composer_untouched":True,
              "original_E1_backend_untouched":True,
              "original_M3_selector_untouched":True,
              "fixed_candidate_parameters_untouched":True,
              "world_generation":"SAME_E1_BACKEND_WITH_RESPONSE_TIME_PERTURBATIONS",
              "separate_independent_world_implementation":False,
              "world_labels_not_in_selector":True,
              "modelica_sha256":"sha256:"+sha(code.encode()),
              "construction_times":CONSTRUCTION_TIMES,"reserved_times":RESERVED_TIMES,
              "world_solver_intervals":SOLVER_INTERVALS,
              "noise_construction":CONSTRUCTION_NOISE,
              "noise_reserved":RESERVED_NOISE,
              "original_M3_thresholds_unchanged":True,
              "absence_of_external_ground_truth":True}
    (out/"public-protocol.json").write_bytes(canonical(metadata)+b"\n")
    (out/"post"/"sealed-parameter-truth.json").write_bytes(canonical({
         "schema":"igc-m3p-sealed-origins/0.1","worlds":truth,
         "not_selector_input":True})+b"\n")
    print(json.dumps({"status":"M3P_SIX_DERIVED_ORIGINAL_E1_WORLDS",
        "solver_runs":len(truth),"source":"UNCHANGED_COMPOSER_AND_BACKEND"}))

def extract(out):
    meta=json.loads((out/"public-protocol.json").read_text())
    require(meta["schema"]==SCHEMA and meta["worlds"]==6,"M3P_PROTOCOL_DRIFT")
    for index,(ident,_,_,_) in enumerate(CASES):
        rows=model_rows(out/"worlds"/(ident.lower()+"_res.csv"))
        vals=sample(rows,CONSTRUCTION_TIMES+RESERVED_TIMES)
        noisy=[max(0.,v+n) for v,n in zip(vals,CONSTRUCTION_NOISE+RESERVED_NOISE)]
        obs=[{"t":t,"delivered":float(v)} for t,v in zip(CONSTRUCTION_TIMES,noisy[:4])]
        case={"schema":"igc-arena-m3-blind-construction-case/0.1",
              # Selector's historical input contracts allow alpha,beta only,
              # so alternate aliases. External case identities remain sealed.
              "case_id":"case-alpha" if index%2==0 else "case-beta",
              "construction_observations":obs,
              "source_snapshot_hash":digest(obs),
              "synthetic_measurement":True,
              "observability":"cumulative_delivered_items"}
        (out/"blind"/(ident+".json")).write_bytes(canonical(case)+b"\n")
        (out/"post"/(ident+"-reserved.json")).write_bytes(canonical({
           "t":RESERVED_TIMES,"delivered":noisy[4:],
           "same_world_temporal_reserve_not_external":True})+b"\n")
    print("M3P_SIX_CASES_BLIND_CONSTRUCTION_ONLY")

def grade(out,source,catalog):
    truth=json.loads((out/"post"/"sealed-parameter-truth.json").read_text())["worlds"]
    manifest=json.loads((source/"candidate-manifest.json").read_text())
    cat=json.loads(catalog.read_text())
    records=[]
    for world in truth:
        ident=world["case_id"]
        case=json.loads((out/"blind"/(ident+".json")).read_text())
        # This original selector does not have access to the world graph,
        # alternative parameters, source identities or temporal reserve.
        selected=select_case(manifest,case,source,cat)
        require(selected["used_truth_labels"] is False and
                selected["used_reserved_observations"] is False and
                selected["method"]=="ORIGINAL_E1_THREE_FIXED_MATERIAL_TOPOLOGIES_RMSE_WITH_ABSTENTION",
                "M3P_NOT_ORIGINAL_BLIND_SELECTOR")
        path=out/"blind"/(ident+"-selection.json")
        path.write_bytes(canonical(selected)+b"\n")
        withheld=json.loads((out/"post"/(ident+"-reserved.json")).read_text())
        chosen=selected["chosen_id"]
        reserve_rmse=None
        if chosen:
            pred=sample(model_rows(source/"candidates"/(chosen.lower()+"_res.csv")),
                        RESERVED_TIMES)
            reserve_rmse=math.sqrt(sum((p-v)**2 for p,v in zip(pred,withheld["delivered"]))/3)
        records.append({
            "world_case":ident,"actual_structural_class":world["origin_candidate_id"],
            "changed_world_times":world["only_world_responseTime_altered"],
            "selected_candidate":chosen,"selection_status":selected["status"],
            "construction_scores":{x["id"]:x["rmse_items"] for x in selected["scored_candidates"]},
            "selected_same_topology":chosen==world["origin_candidate_id"],
            "reserved_same_world_rmse_if_chosen":reserve_rmse,
            "unobserved_parameter_identification":"NOT_ATTEMPTED",
        })
    summary={
      "schema":"igc-m3p-frozen-family-varied-parameter-audit/0.1",
      "arm_id":"M","worlds":len(records),
      "selected":sum(r["selected_candidate"] is not None for r in records),
      "abstained":sum(r["selection_status"]=="ABSTAIN" for r in records),
      "correct_topology_selected":sum(r["selected_candidate"]==r["actual_structural_class"] for r in records),
      "wrong_topology_selected":sum(r["selected_candidate"] is not None and
                                   r["selected_candidate"]!=r["actual_structural_class"] for r in records),
      "predeclared_world_variations":True,
      "no_world_labels_seen_by_selector":True,
      "no_m3_threshold_or_model_refitting":True,
      "same_molecular_backend_not_independent_mechanism":True,
      "not_external_causal_identification":True,
      "not_independent_holdout":True,
      "cases":records}
    (out/"post"/"comparison.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("M3P_REAL_VARIED_PARAMETER_RESULTS",json.dumps({
       k:v for k,v in summary.items() if k in
          ("selected","abstained","correct_topology_selected","wrong_topology_selected")}))
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("emit","extract","grade"))
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--source",type=Path)
    p.add_argument("--catalog",type=Path)
    args=p.parse_args()
    if args.command=="emit": emit(args.out)
    elif args.command=="extract":extract(args.out)
    else:
        require(args.source is not None and args.catalog is not None,"M3P_REQUIRES_PUBLIC_ORIGINAL_CANDIDATES")
        grade(args.out,args.source,args.catalog)
if __name__=="__main__":main()
