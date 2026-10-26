"""D2 corrected G2: emit and simulate the OWN revised deterministic hypotheses.

Accepts only the exact original D2 visible artifact; NEVER reads the
evaluator's Modelica world or other-arm outputs. Preserves each candidate's
native graph and uses D2 revised_best_parameters, not D1's best_grid.
G2 numerical execution and D/OM parity are not causal identification or
fresh predictive evidence.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_d_v01 import generate, modelica, validate_case, verify_csv
from scripts.arena_d_v1_screen import assess, integrate, compare_omc_csv
from scripts.arena_d_v2_revision import validate_trial, SCHEMA as D2_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "igc-arena-d2-revised-modelica-g2/0.1"
ORIGINAL_ACTIONS = "https://github.com/yudocyudoc/IGC/actions/runs/40248817463"
# Raw, immutable file bytes of the D-only archive, NOT the evaluator artifact.
PARENT_FILE_SHA256 = {
    "d2-revision.json": "a0d63faf208d1b0aadd5a2b9ffc928ca633866c668f1f26249f5c109666651b6",
    "screen.json": "c2c7df809fd1520cbad4eb4354f5d0371682ae250866ea9e8bee7c37d0d83c46",
    "d2-trial-visible.json": "e2d27b7419055b1963e6c9268ec6a90076d3ea701874760a2eeb7d4edb2e5e5d",
    "memory-events.json": "4947d47efc72db0710934aec72671e833cca26a6f143f5803fd8158bba14affe",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_parent(directory):
    raw={}
    for name, expected in PARENT_FILE_SHA256.items():
        b=(directory / name).read_bytes()
        require(sha256(b).hexdigest()==expected, "D2_PARENT_BYTES_CHANGED:"+name)
        raw[name]=json.loads(b)
    return (raw["d2-revision.json"],raw["screen.json"],
            raw["d2-trial-visible.json"],raw["memory-events.json"])


def verify_lineage(data, protocol, d2, prior, trial, events):
    validate_case(data)
    original = generate(data)
    require(d2.get("status")=="D2_REVISED_AND_REMEMBERED", "NOT_COMPLETED_D2_OWN_REVISION")
    report=d2.get("report")
    require(isinstance(report,dict) and report.get("schema")==D2_SCHEMA
            and report.get("arm_id")=="D", "INVALID_D2_REPORT")
    require(report.get("investigation_id")==data["investigation_id"]
            and report.get("round_id")==data["round_id"], "FOREIGN_D2_ROUND")
    require(prior==assess(data,protocol), "D1_SCREEN_DRIFT")
    require(prior["input_hash"]==original["input_hash"], "D1_CASE_HASH_MISMATCH")
    require(report.get("parent_d1_hash")==digest(prior)
            and report.get("trial_hash")==digest(trial), "D2_PARENT_OR_TRIAL_MISMATCH")
    validate_trial(data,protocol,prior,trial)
    require(isinstance(events,list) and len(events)==2, "MISSING_D0_D1_EVENT_CHAIN")
    initial,screen=events
    def event_hash_ok(event):
        return isinstance(event,dict) and event.get("event_hash")==digest(
            {k:v for k,v in event.items() if k!="event_hash"})
    require(all(map(event_hash_ok,events)) and
            event_hash_ok(d2.get("d2_trace_event",{})), "CORRUPTED_D_EVENTS")
    require(initial["arm_id"]==screen["arm_id"]==d2["d2_trace_event"]["arm_id"]=="D"
            and initial["event_type"]=="HYPOTHESIS_PROPOSED"
            and screen["event_type"]=="SIMULATION_REPORTED"
            and d2["d2_trace_event"]["event_type"]=="HYPOTHESIS_REVISED"
            and screen["previous_event_hash"]==initial["event_hash"]
            and d2["d2_trace_event"]["previous_event_hash"]==screen["event_hash"]
            and d2["d2_trace_event"]["payload_hash"]==digest(report)
            and screen["payload_hash"]==digest(prior), "INVALID_OWN_D_EVENT_LINEAGE")
    require(d2["current_support"]==report["conditionally_supported_ids"]
            and d2["atms_after"]["truth_status"]=="NOT_DETERMINED_BY_ATMS",
            "ATMS_RESULT_MISMATCH")
    native={c["id"]:c for c in original["candidates"]}
    require(len(report.get("results",[]))==len(native), "REVISED_CANDIDATE_COUNT_CHANGED")
    require(len(native)<=data["resources"]["max_simulations"],"D2_G2_SIMULATION_BUDGET_EXCEEDED")
    require(set(x["candidate_id"] for x in report["results"])==set(native),"D2_UNRECOGNIZED_CANDIDATE")
    for item in report["results"]:
        cid=item["candidate_id"];base=native[cid]
        require(item["structure_hash"]==base["structure_hash"]
                and item["structure_changed"] is False
                and item["revised_best_parameters"] is not None,
                "D2_UNAUTHORIZED_STRUCTURE_OR_PARAMETER")
        require(all(k in protocol["parameter_grid"] and
                    item["revised_best_parameters"][k] in protocol["parameter_grid"][k]
                    for k in ("capacity","response_time","loss_time")),
                "D2_PARAMETER_OUTSIDE_GRID")
    return native


def build(data,protocol,d2,prior,trial,events):
    original=verify_lineage(data,protocol,d2,prior,trial,events)
    report=d2["report"]
    candidates=[]
    sources={}
    commands=[]
    profile=data["construction"]["input_profile"]
    for item in report["results"]:
        c=dict(original[item["candidate_id"]])
        # Crucial: exactly D2 revised grid parameters, NOT nominal or D1.
        c["nominal_parameters"]=dict(item["revised_best_parameters"])
        before=c["structure_hash"]
        raw=modelica(c,profile)
        name="D2fit_"+before[7:19]
        old="DStockFlow_"+before[7:19]
        require(raw.count("model "+old)==1 and raw.count("end "+old+";")==1,
                "D0_MODELICA_TEMPLATE_CHANGED")
        text=raw.replace("model "+old,"model "+name).replace("end "+old+";","end "+name+";")
        require("  parameter Real capacity = " in text and
                "  parameter Real responseTime = " in text, "D2_PARAMETER_NOT_EMITTED")
        sources[name+".mo"]=text
        commands.extend([
            f'loadFile("/work/artifacts/arena-d2/{name}.mo");',
            'print(getErrorString());',
            f'checkModel({name});',
            'print(getErrorString());',
            f'simulate({name},startTime=0,stopTime=8,numberOfIntervals=160,method="dassl",tolerance=1e-8,outputFormat="csv");',
            'print(getErrorString());',
        ])
        candidates.append({
            "candidate_id":item["candidate_id"],
            "structure_hash":before,
            "modelica_class":name,
            "modelica_sha256":"sha256:"+sha256(text.encode()).hexdigest(),
            "stocks":len(c["structure"]["stocks"]),
            "loss":c["structure"]["loss"],
            "d1_parameters":item["prior_best_parameters"],
            "d2_parameters":item["revised_best_parameters"],
            "parameters_changed":item["parameter_changed"],
            "d2_revision_status":item["revision_status"],
            "d2_compatible_witnesses":item["compatible_joint_grid_points"],
            "conditionally_supported":item["candidate_id"] in d2["current_support"],
        })
    manifest={
        "schema":SCHEMA,"arm_id":"D","method":"D2_PARAMETERS_TO_ORIGINAL_D0_MODELICA",
        "revision_input_hash":digest(d2["report"]),
        "parent_d1_hash":digest(prior),
        "visible_trial_hash":digest(trial),
        "source_original_actions":ORIGINAL_ACTIONS,
        "origin":"D2_REVISED_BEST_GRID_PARAMETERS",
        "not_evaluator_world":True,
        "solver":{"name":"OpenModelica","startTime":0,"stopTime":8,
                  "numberOfIntervals":160,"method":"dassl"},
        "candidates":candidates,
        "current_support":d2["current_support"],
        "g2_status":"AWAITING_REAL_MODELICA",
        "g3_construction":"NOT_ASSESSED_BY_EMITTER",
        "heldout":"NOT_RUN",
    }
    return manifest,sources,"\n".join(commands)+"\n"


def assess_real_csv(root,manifest,data,protocol):
    profile=data["construction"]["input_profile"]
    observations=data["construction"]["observations"]
    report={}
    for item in manifest["candidates"]:
        csv_path=root/(item["modelica_class"]+"_res.csv")
        mass=verify_csv(csv_path,item["stocks"],profile)
        sample_times=sorted(set([r["t"] for r in observations]+[8.]))
        expected=integrate(item["stocks"],item["loss"],item["d2_parameters"],
                           profile,sample_times,protocol["integration_max_step"])
        parity=compare_omc_csv(csv_path,list(zip(sample_times,expected)),atol=.012)
        with csv_path.open(newline="") as f:
            rows=list(csv.DictReader(f))
        values=[]
        for t in sample_times:
            hits=[float(x["delivered"]) for x in rows if abs(float(x["time"])-t)<1e-7]
            require(bool(hits) and all(math.isfinite(z) for z in hits),"D2_MISSING_OR_NONFINITE_OUTPUT")
            values.append(hits[-1])
        residuals=[z-x["delivered"] for z,x in zip(values[:-1],observations)]
        max_abs=max(abs(z) for z in residuals+[values[-1]-data["_d2_trial_delivered"]])
        rmse_construction=math.sqrt(sum(z*z for z in residuals)/len(residuals))
        report[item["candidate_id"]]={
            "source_modelica_class":item["modelica_class"],
            "d2_parameters":item["d2_parameters"],
            "g2_mass":mass,"d2_rk4_parity":parity,
            "predicted_visible_times":dict(zip((str(x) for x in sample_times),values)),
            "construction_rmse_all_items":rmse_construction,
            "construction_rmse_noninitial_items":math.sqrt(
                sum(z*z for z in residuals[1:])/(len(residuals)-1)),
            "joint_max_abs_error_including_visible_reset":max_abs,
            "noise_absolute_bound":protocol["noise_absolute_bound"],
            "g3_status":"CONSTRUCTION_AND_VISIBLE_RESET_DESCRIPTIVE_ONLY",
        }
    return {"schema":"igc-arena-d2-real-own-modelica-check/0.1",
            "arm_id":"D","models_verified":len(report),
            "current_support":manifest["current_support"],
            "not_world_evaluator":True,"not_new_holdout":True,
            "engine":"PINNED_OPENMODELICA_REAL_CSV",
            "g2_status":"ALL_REVISED_CANDIDATES_SIMULATED_AND_MASS_BALANCED",
            "g3_construction_status":"DESCRIPTIVE_AND_INSTRUMENT_BOUND_CONDITIONAL",
            "heldout_status":"NOT_RUN",
            "by_candidate":report}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=("emit","verify"))
    ap.add_argument("--parent-dir",type=Path)
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--manifest",type=Path)
    a=ap.parse_args()
    data=json.loads(a.input.read_text())
    protocol=json.loads(a.protocol.read_text())
    if a.command=="emit":
        require(a.parent_dir is not None and not a.out.exists(),"BAD_EMIT_PATH")
        d2,prior,trial,events=read_parent(a.parent_dir)
        manifest,sources,commands=build(data,protocol,d2,prior,trial,events)
        a.out.mkdir(parents=True)
        for fname,content in sources.items():
            (a.out/fname).write_text(content)
        (a.out/"d2.mos").write_text(commands)
        (a.out/"manifest.json").write_bytes(canonical(manifest)+b"\n")
        print(json.dumps({"status":"SIX_D2_REVISED_MODELS_EMITTED_FROM_OWN_REPORT",
                          "models":len(manifest["candidates"]),
                          "supported":manifest["current_support"],
                          "no_evaluator_world":True}))
    else:
        require(a.manifest is not None and a.parent_dir is not None, "MISSING_VERIFY_INPUTS")
        manifest=json.loads(a.manifest.read_text())
        d2,prior,trial,events=read_parent(a.parent_dir)
        expected, sources,_=build(data,protocol,d2,prior,trial,events)
        require(manifest==expected,"TAMPERED_OR_FOREIGN_D2_MANIFEST")
        for fname,source in sources.items():
            require((a.manifest.parent/fname).read_text()==source,"TAMPERED_D2_MODELICA")
        case=dict(data)
        case["_d2_trial_delivered"]=trial["measurement"]["delivered"]
        result=assess_real_csv(a.manifest.parent,manifest,case,protocol)
        require(not a.out.exists(),"OUTPUT_ALREADY_EXISTS")
        a.out.write_bytes(canonical(result)+b"\n")
        print(json.dumps({"status":result["g2_status"],"models":result["models_verified"],
                          "support":result["current_support"],"not_world_evaluator":True}))


if __name__=="__main__":
    main()
