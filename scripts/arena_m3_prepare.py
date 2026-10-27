"""Arena M3 structural challenge: original Short E1 composer + original backend.

A bounded *new* experiment, independent from historical M2 budgets/results.
Five real OpenModelica simulations: 3 representative material paths (2,3,4
queues), plus 2 separately executed synthetic generator paths at twice the
time resolution. A signal-only filter cannot be identified by deliveredTotal,
so do NOT treat the other three E1 graphs as discriminable material models.

No upstream molecule, equation, queue parameter, or original compositor edit.
The evaluator key stays separate and is not passed to the selector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from scripts.arena_m_visible_pulse import ROOT, REGISTRY, composer, backend, stimulus_only_replace
from scripts.arena_v0_contract import digest, canonical

METHOD="short-e1-m3-fixed-family-evidence-structural-test/0.1"
TRIAL="igc-arena-m3-structure-recovery-challenge/0.1"
MODEL_PACKAGE="ArenaM3Generated"
INPUT_PROFILE={"kind":"pulse","rate":1.7,"duration":2.0}
CONSTRUCTION_TIMES=[0,1,2,3]
RESERVED_TIMES=[4,5,6]
CONSTRUCTION_NOISE=[0.0,0.002,-0.003,0.004]
RESERVED_NOISE=[-0.003,0.002,-0.004]
CASE_IDS=["case-alpha","case-beta"]


def require(ok,msg):
    if not ok: raise ValueError(msg)


def family():
    cfg,classes,_=composer.load_registry(REGISTRY)
    graphs=composer.enumerate_graphs(cfg,classes)
    require(len(graphs)==6,"E1_BASE_REPERTOIRE_DRIFT")
    paths={}
    for key,graph in graphs:
        composer.check_graph(graph,cfg,classes)
        roles=Counter(x["role"] for x in graph["instances"])
        n=roles["transit"]
        require(n in (0,1,2) and roles["preparation"]==roles["dispatch"]==1,
                "M3_UNEXPECTED_PHYSICAL_PATH")
        if roles["report"]==0: # Observable is deliveredTotal; filter is invisible.
            require(n not in paths,"DUPLICATE_MATERIAL_TOPOLOGY")
            paths[n]=(key,graph)
    require(set(paths)=={0,1,2},"M3_EXPECTED_THREE_MATERIAL_PATHS")
    return cfg,classes,paths


def pack(name,graph,cfg,classes):
    txt=backend.render_model(name,graph,cfg,classes)
    txt=stimulus_only_replace(txt,INPUT_PROFILE["rate"],INPUT_PROFILE["duration"])
    require("der(" not in txt and "when " not in txt and "connect(" in txt,
            "HANDWRITTEN_MOLECULAR_DYNAMICS_FORBIDDEN")
    return txt


def prepare(out):
    require(not out.exists(),"OUTPUT_ALREADY_EXISTS")
    require(out.resolve().is_relative_to(ROOT),"OUTPUT_OUTSIDE_REPOSITORY")
    cfg,classes,paths=family()
    candidates=[]
    models=[]
    commands=["getVersion();",
      'loadFile("/repo/src/modelica/IGCMolecules.mo");',
      'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");']
    base=out.resolve().relative_to(ROOT)
    for n in (0,1,2):
        key,graph=paths[n]
        name=f"M3C{n:02d}"
        models.append(pack(name,graph,cfg,classes))
        candidates.append({
            "id":f"C{n:02d}","class":name,"canonical_sha256":"sha256:"+key,
            "material_queues":2+n,"transit_instances":n,
            "graph":graph,"parameters_origin":"UNCHANGED_ORIGINAL_E1_REGISTRY",
        })
    # A separate Modelica run (different class, 240 vs 120 intervals) creates
    # each blind case. This verifies recoverability of the existing catalog,
    # NOT identification of an independent real-world causal mechanism.
    truth=[]
    for idx,kind in enumerate((0,1)):
        key,graph=paths[kind]
        name=f"M3W{idx:02d}"
        models.append(pack(name,graph,cfg,classes))
        truth.append({"case_id":CASE_IDS[idx],"world_class":name,
                      "source_canonical_sha256":"sha256:"+key,
                      "expected_candidate_id":f"C{kind:02d}",
                      "constructed_from_existing_E1_material_path":True})
    pkg="\n".join(["within;",f"package {MODEL_PACKAGE}",
                   "\n\n".join(models),
                   '  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
                   f"end {MODEL_PACKAGE};",""])
    require("der(" not in pkg and "when " not in pkg,"INJECTED_ODE")
    out.mkdir(parents=True)
    (out/"M3Generated.mo").write_text(pkg)
    commands.append(f'loadFile("/repo/{base}/M3Generated.mo");')
    for c in candidates:
        name=c["class"]; ident=c["id"].lower()
        commands += [f"checkModel({MODEL_PACKAGE}.{name});","print(getErrorString());",
                     f'simulate({MODEL_PACKAGE}.{name},startTime=0,stopTime=6,numberOfIntervals=120,method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="{base}/candidates/{ident}");',
                     "print(getErrorString());"]
    for idx,x in enumerate(truth):
        name=x["world_class"]
        commands += [f"checkModel({MODEL_PACKAGE}.{name});","print(getErrorString());",
                     f'simulate({MODEL_PACKAGE}.{name},startTime=0,stopTime=6,numberOfIntervals=240,method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="{base}/worlds/w{idx:02d}");',
                     "print(getErrorString());"]
    (out/"simulate.mos").write_text("\n".join(commands)+"\n")
    for folder in ("candidates","worlds","cases","grading"):
        (out/folder).mkdir()
    public={
        "schema":TRIAL,"arm_id":"M","method":METHOD,
        "source":"ORIGINAL_SHORT_E1_COMPOSER_AND_BACKEND_UNMODIFIED",
        "registry_sha256":digest(cfg),
        "universe_count":6,
        "observable_equivalence_classes":3,
        "excluded_information_only_aliases":3,
        "rationale":"report filter changes a signal, not cumulative deliveredTotal",
        "candidate_simulations":3,"world_simulations":2,
        "world_solver_intervals":240,"candidate_solver_intervals":120,
        "candidate_parameter_fitting":False,
        "world_source":"SYNTHETIC_OWN_CATALOG_NOT_EXTERNAL_GOLD",
        "construction_times":CONSTRUCTION_TIMES,
        "reserve_times":RESERVED_TIMES,
        "construction_noise":CONSTRUCTION_NOISE,
        "reserve_noise":RESERVED_NOISE,
        "predeclared_min_gap_rmse_items":0.035,
        "predeclared_max_best_rmse_items":0.02,
        "stimulus":INPUT_PROFILE,"simulation_horizon_hour":6,
        "g3_construction":"BLIND_OBSERVATIONS_ONLY",
        "temporal_reserved_evaluation":"AFTER_SELECTION_NOT_EXTERNAL_VALIDATION",
        "candidates":candidates,
        "modelica_sha256":"sha256:"+hashlib.sha256(pkg.encode()).hexdigest(),
        "upstream_edited":False,
    }
    (out/"candidate-manifest.json").write_bytes(canonical(public)+b"\n")
    # Never pass evaluator key to selector.
    (out/"grading"/"sealed-source-key.json").write_bytes(canonical({
        "schema":"igc-m3-sealed-source-labels/0.1",
        "cases":truth,"not_selector_input":True,
    })+b"\n")
    print(json.dumps({"status":"M3_ORIGINAL_E1_THREE_PHYSICAL_CANDIDATES_TWO_SEPARATE_WORLDS",
                      "graphs":6,"representatives":len(candidates),
                      "solver_runs":5,"modelica_sha":public["modelica_sha256"]}))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    prepare(a.out)


if __name__=="__main__":main()
