#!/usr/bin/env python3
"""CAF-01 M producer input and model-source admission; NO numerical solvers.

Reads only two authorized construction evidence views and the M E1 material
catalogue. Never imports/copies D output, B model, G4 references, or DES truth.
It does not claim that nine sources are already native G2 verified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from caf01_g3 import CONTRACT, digest, validate_evidence
from caf01_m_equivalence import certificate
from caf01_m_native_preflight import checked_models, render_bundle

HERE=Path(__file__).resolve().parent
PUB=HERE/"public_inputs"/"run_40915090599"
WORLD="sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"
EVIDENCE_FILES={
    "CAF01":("727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb",
             (0,5,10,15,20,30,40)),
    "CAFN":("8112019ffad402ff1f1e0deafa3b4f1786bb37488258d5c7fe16e0404e22d5a1",
            (0,40)),
}

def need(ok,reason):
    if not ok:
        raise ValueError(reason)

def load_public(case,contract,pub=PUB):
    need(case in EVIDENCE_FILES,"M_UNKNOWN_CONSTRUCTION_CASE")
    expected,times_expected=EVIDENCE_FILES[case]
    raw=(pub/(case+".json")).read_bytes()
    need(hashlib.sha256(raw).hexdigest()==expected,
         "M_OFFICIAL_CONSTRUCTION_BYTES_CHANGED_"+case)
    evidence=json.loads(raw)
    times,_=validate_evidence(evidence,contract)
    need(tuple(times)==times_expected
         and evidence["source_snapshot_sha256"]==WORLD,
         "M_MASK_OR_SOURCE_CHANGED_"+case)
    return evidence

def packet(contract,pub=PUB):
    m=contract["methods"]["M"]
    need(m["structural_classes"]==["C00","C01","C02"]
         and m["proposed_bounded_capacity_grid_items_per_hour"]==[20,72,100]
         and m["OpenModelica_construction_max"]==9
         and m["CAFN_extra_candidate_solver_runs"]==0,
         "M_METHOD_CONTRACT_CHANGED")
    items=checked_models(contract)
    cert=certificate(contract)
    need(cert["status"]=="STATIC_UPPER_BOUND_ONLY"
         and cert["inactive_capacities"]==[72,100]
         and cert["nominal_configurations"]==9
         and cert["within_structure_upper_bound_classes"]==6,
         "M_EQUIVALENCE_CERTIFICATE_CHANGED")
    allowed=["C00","C01","C02"]
    members=[]
    for structure in allowed:
        for capacity in (20,72):
            matching=[x for x in items if x["structure"]==structure and
                      x["capacity"]==capacity]
            need(len(matching)==1,"M_CLASS_SOURCE_MISSING")
            item=matching[0]
            members.append({
                "id":f"M_{structure}_C{capacity}",
                "class_name":item["name"],
                "structure":structure,
                "capacity_items_per_hour":capacity,
                "nominal_capacity_aliases":[capacity] if capacity==20 else [72,100],
                "source_sha256":"sha256:"+hashlib.sha256(
                    item["model"].encode("utf-8")).hexdigest(),
                "E1_graph_sha256":item["original_graph_sha256"],
            })
    need(len(members)==6,"M_SIX_CLASSES_REQUIRED")
    source_models=[{
        "model_name":i["name"],"structure":i["structure"],
        "capacity_items_per_hour":i["capacity"],
        "source_sha256":"sha256:"+hashlib.sha256(i["model"].encode()).hexdigest(),
    } for i in items]
    views={}
    for case in ("CAF01","CAFN"):
        evidence=load_public(case,contract,pub)
        views[case]={
            "evidence":evidence,
            "original_file_sha256":"sha256:"+EVIDENCE_FILES[case][0],
            "evidence_semantic_sha256":digest(evidence),
        }
    return {
        "schema":"igc-caf01-m-producer-independent/0.1",
        "status":"ADMISSION_ONLY_NATIVE_SIMULATION_PENDING",
        "source_DES_construction_public_snapshot":WORLD,
        "contract_semantic_sha256":digest(contract),
        "allowed_arms":["M"],
        "public_construction_views":views,
        "frozen_time_unit":"hours",
        "construction_pulse":{"rate_per_hour":72,"duration_hours":"1/3",
                              "horizon_hours":"2/3"},
        "six_structural_capacity_classes":members,
        "nine_nominal_model_sources":source_models,
        "static_equivalence": {
            "kind":"UPPER_BOUND_CONDITIONAL",
            "inactive_capacities":[72,100],
            "not_equivalent_across_structures":True,
            "native_conservation_still_required":True,
        },
        "budget":{
            "M_construction_OpenModelica_original_ceiling":9,
            "M_six_class_conditional_ceiling":6,
            "M_construction_OpenModelica_used_by_this_packet":0,
            "M_negative_control_additional_solver_calls":0,
        },
        "G0":"CONTRACT_STAGED",
        "G1":"NATIVE_CHECKMODEL_OUTSIDE_THIS_PACKET",
        "G2":"NOT_RUN",
        "future_evaluation_observations_read":False,
        "Buffalo_provider_calls":0,
        "DES_evaluation_invocations":0,
        "notes":[
            "CAF-N carries endpoints t=0/40 only, not intermediary observations.",
            "C72/C100 alias is conditional on frozen E1 library and native conservation.",
            "No native numerical output or candidate scores are in this packet.",
        ],
    }

def generate(out):
    need(not out.exists(),"M_OUTPUT_ALREADY_EXISTS")
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    p=packet(contract)
    models,check_only,_=render_bundle(contract)
    need("simulate(" not in check_only
         and check_only.count("checkModel(")==9
         and "der(" not in models,
         "M_NATIVE_PREFLIGHT_SOURCE_CHANGED")
    # This stage stores the nine unchanged source models and six chosen
    # canonical class labels; no OpenModelica is executed.
    out.mkdir(parents=True,exist_ok=False)
    (out/"M_PRODUCER_PACKET.json").write_text(
        json.dumps(p,sort_keys=True,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    (out/"CAF01MPreflight.mo").write_text(models,encoding="utf-8")
    (out/"M_NO_SOLVER_README.txt").write_text(
        "NO SIMULATION HAS RUN. Use the separate approved G2 runner; this is "
        "the construction-only input and native-source staging packet.\n",
        encoding="utf-8")
    return p

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--out",required=True,type=Path)
    a=arg.parse_args()
    p=generate(a.out)
    print(json.dumps({"status":p["status"],
                      "nominal_sources":len(p["nine_nominal_model_sources"]),
                      "candidate_classes":len(p["six_structural_capacity_classes"]),
                      "M_native_sims":0,
                      "negative_observations":len(p["public_construction_views"]["CAFN"]["evidence"]["observations"])}))

if __name__=="__main__":
    main()
