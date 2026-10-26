"""Independent post-inference adjudication of Buffalo B3 on its own construction.

A failure to translate a new Buffalo-native subtype or Modelica solve is a
recorded *conditional G0/G2 failure*, never silently substituted by old B2
results. No D/M data, hidden generator, or holdout.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, subprocess, traceback
from pathlib import Path

from scripts.arena_b_native_to_modelica import generate, TranslationBlocked
from scripts.arena_b_construction_check import assess

IMAGE=("openmodelica/openmodelica:v1.27.1-minimal@"
       "sha256:ac9a0223e69b8055d444b42f58ccb9680342b56848c68b81385bf83d7c0ba824")
PARENT_HASH="d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9"
BASELINE_RMSE_N3=0.19290471909474044
BASELINE_RMSE_N4=0.1670603872459463

def safe_reason(exc):
    return str(exc).replace("\n"," ")[:250]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--prior-native",type=Path,required=True)
    p.add_argument("--feedback",type=Path,required=True)
    p.add_argument("--visible",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("OUTPUT_ALREADY_EXISTS")
    prior_bytes=a.prior_native.read_bytes()
    if hashlib.sha256(prior_bytes).hexdigest()!=PARENT_HASH:
        raise ValueError("NOT_BYTE_VERIFIED_OWN_PARENT")
    parent=json.loads(prior_bytes)["model"]
    feedback=json.loads(a.feedback.read_text())
    if feedback["parent_native_bytes_sha256"]!="sha256:"+PARENT_HASH:
        raise ValueError("WRONG_OWN_CONSTRUCTION_FEEDBACK")
    if feedback.get("no_cross_arm_information") is not True:
        raise ValueError("CROSSARM_FEEDBACK_FORBIDDEN")
    visible=json.loads(a.visible.read_text())
    native_bytes=a.native.read_bytes()
    result=json.loads(native_bytes)
    model=result.get("model") or {}
    variables=model.get("variables") or []
    def sem(v):
        return {"name":v.get("name"),"type":v.get("type"),
                "equation":v.get("equation"),"units":v.get("units"),
                "inflows":v.get("inflows"),"outflows":v.get("outflows"),
                "graphicalFunction":v.get("graphicalFunction"),
                "subType":v.get("subType")}
    baseline={x["name"]:sem(x) for x in parent["variables"]}
    revised={x.get("name"):sem(x) for x in variables}
    compare={
        "added_variables":sorted(set(revised)-set(baseline)),
        "removed_variables":sorted(set(baseline)-set(revised)),
        "modified_shared_variables":sorted(n for n in revised.keys() & baseline.keys()
                                           if revised[n]!=baseline[n])
    }
    outcome={
        "schema":"igc-b3-own-physical-feedback-adjudication/0.1","arm_id":"B",
        "parent_native_sha256":"sha256:"+PARENT_HASH,
        "revised_native_sha256":"sha256:"+hashlib.sha256(native_bytes).hexdigest(),
        "origin":"REAL_CLOUDFLARE_ORIGINAL_BUFFALO_CURRENTMODEL",
        "revision_changed_native":model!=parent,
        "native_changes":compare,
        "feedback_from_own_model_only":True,
        "original_budget":"EXTENDED_SEPARATE_EXPERIMENT_NOT_ORIGINAL_B_ROUND",
        "g0_status":"NOT_CHECKED","g2_status":"NOT_RUN",
        "g3_construction_status":"NOT_EVALUATED",
        "heldout_evaluation":"NOT_RUN",
        "baseline_rmse_n3":BASELINE_RMSE_N3,"baseline_rmse_n4":BASELINE_RMSE_N4,
        "causal_truth":"NOT_DEMONSTRATED",
    }
    a.out.mkdir(parents=True)
    try:
        name,code,translation=generate(result)
        outcome["g0_status"]="TRANSLATED_CONDITIONALLY_LOOKUPS_REQUIRE_EQUIVALENCE_CHECK"
        outcome["translation_report"]=translation
        (a.out/(name+".mo")).write_text(code)
        mos="\n".join([
            f'loadFile("/work/{(a.out/(name+".mo")).as_posix()}");',
            'print(getErrorString());',
            f'checkModel({name});',
            'print(getErrorString());',
            f'simulate({name},stopTime=8,numberOfIntervals=64,method="euler",outputFormat="csv");',
            'print(getErrorString());',""
        ])
        (a.out/"check.mos").write_text(mos)
        cwd=Path.cwd()
        completed=subprocess.run(
            ["docker","run","--rm","-v",str(cwd)+":/work",
             "-w","/work/"+a.out.as_posix(),IMAGE,"omc","check.mos"],
            capture_output=True,text=True,timeout=150,check=False)
        log=(completed.stdout or "")+"\n"+(completed.stderr or "")
        (a.out/"omc.log").write_text(log)
        if completed.returncode!=0 or any(w in log for w in (
            "Error:","Failed to load","Simulation execution failed","Error occurred")):
            outcome["g2_status"]="OPENMODELICA_COMPILATION_OR_SIMULATION_FAILED"
            outcome["solver_exit_code"]=completed.returncode
        else:
            csv_path=a.out/(name+"_res.csv")
            if not csv_path.exists():raise ValueError("REAL_OPENMODELICA_CSV_NOT_FOUND")
            with csv_path.open(newline="") as fd:rows=list(csv.DictReader(fd))
            measured=assess(rows,visible)
            outcome["g2_status"]="PASS_REAL_OPENMODELICA_OWN_CANDIDATE"
            outcome["g3_construction_status"]="DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND"
            outcome["construction_check"]=measured
            outcome["rmse_n3"]=measured["rmse_noninitial_observations_items"]
            outcome["rmse_n4"]=measured["rmse_all_observations_items"]
            outcome["construction_delta_n3"]=outcome["rmse_n3"]-BASELINE_RMSE_N3
            outcome["construction_delta_n4"]=outcome["rmse_n4"]-BASELINE_RMSE_N4
            outcome["construction_change"]=(
                "IMPROVED_IN_SAMPLE" if outcome["construction_delta_n3"]<-1e-10
                else "WORSENED_IN_SAMPLE" if outcome["construction_delta_n3"]>1e-10
                else "NO_MEASURABLE_CHANGE_IN_SAMPLE"
            )
    except (TranslationBlocked,ValueError,KeyError,TypeError,TimeoutError,subprocess.TimeoutExpired) as exc:
        if outcome["g0_status"]=="NOT_CHECKED":
            outcome["g0_status"]="BLOCKED_NATIVE_NOT_FAITHFULLY_SUPPORTED"
        elif outcome["g2_status"]=="NOT_RUN":
            outcome["g2_status"]="BLOCKED_MODEL_OR_NUMERICAL_CONTRACT"
        outcome["blocked_reason"]=safe_reason(exc)
    (a.out/"adjudication.json").write_text(json.dumps(outcome,indent=2)+"\n")
    print(json.dumps({"g0":outcome["g0_status"],"g2":outcome["g2_status"],
                      "g3":outcome["g3_construction_status"],
                      "changed":outcome["revision_changed_native"],
                      "change":outcome.get("construction_change"),
                      "blocker":outcome.get("blocked_reason")},sort_keys=True))

if __name__=="__main__":main()
