#!/usr/bin/env python3
"""CAF-01: exactly TWO selected MODEL forecast simulations (not DES truth).

Prepare uses only public construction G3 selection and unchanged native model
sources from two independently archived G2 receipts. It changes ONLY the known
public future input rate 72->90 orders/hour. No refit; no alternatives, no
Buffalo, no evaluation-world data, no ATMS feedback.

Finalization reads already-produced CSVs and ORIGINAL model bytes, calls the
predeclared G3.lock_forecasts and G4.prepare_preholdout_package, and emits
content for independent external custody. GitHub artifacts are NOT external
custody or authorization to expose the DES holdout.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from caf01_g3 import CONTRACT,lock_forecasts,digest
from caf01_g4 import prepare_preholdout_package,emit_custody_candidate
from caf01_m_producer_admission import published_caf_model_sources
from scripts.arena_d_v01 import topology, modelica
from scripts.arena_v0_contract import digest as topology_digest

HERE=Path(__file__).resolve().parent
TIMES=(5,10,15,20,30,40)
HORIZON=2/3
RATE=90
D_MODEL="D1_C72_T0.125"
M_MODEL="M_C00_C72"
D_ORIGINAL_SHA="sha256:b47ac5f7c3ffb04e52eaccab5d647e578833abeb4fdf070438665642d3cddce5"
M_PACKAGE_ORIGINAL_SHA="sha256:53966be7dd6275d33c5894a6c58063bc845a67ff8c9dfdacabc13eabc0794612"
G3_FILE_ORIGINAL_SHA="sha256:85e855d273dc46a3cff5abd3988ef61646d364c4ad0488b116a7437e3982ff28"
D_G2_SHA="sha256:5dfde7336db42bd0970a4b5efca2a597d1a173ade583be1a68d7c5ad4fe40f2d"
M_G2_SHA="sha256:537733f53f33fc5b4dd3ea054e54f21013040d28c26bac6ed34f415aed9c51c7"
PUBLIC_FILE_SHA="sha256:727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb"
WORLD="sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"

def need(test,msg):
    if not test: raise ValueError(msg)

def sha(raw):
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def hashfile(file):
    return sha(Path(file).read_bytes())

def save(path,value):
    path.write_text(json.dumps(value,sort_keys=True,ensure_ascii=False,
                               indent=2,allow_nan=False)+"\n",encoding="utf-8")

def inputs(d_folder,m_folder,g3_file):
    need(hashfile(g3_file)==G3_FILE_ORIGINAL_SHA,
         "FORECAST_G3_ORIGINAL_SELECTION_SHA_MISMATCH")
    s=json.loads(g3_file.read_bytes())
    need(s["selection_sha256"]==digest({
        k:v for k,v in s.items() if k!="selection_sha256"})
        and s["source_snapshot_sha256"]==WORLD
        and s["decision"]["D"]["winners"]==[D_MODEL]
        and s["decision"]["M"]["winners"]==[M_MODEL]
        and s["decision"]["B"]["winners"]==[]
        and s["decision"]["D"]["parameter_ambiguity"] is True
        and s["decision"]["D"]["winners_pending_g2"]==[]
        and s["decision"]["B"]["status"]=="NO_VALID_CANDIDATE",
         "FORECAST_G3_SELECTION_CHANGED_OR_B_ADMITTED")
    need(hashfile(d_folder/"D_G2_VERIFIED.json")==D_G2_SHA
         and hashfile(m_folder/"M_G2_AGGREGATE.json")==M_G2_SHA
         and hashfile(m_folder/"CAF01MPreflight.mo")==M_PACKAGE_ORIGINAL_SHA,
         "FORECAST_G2_SOURCE_BYTES_CHANGED")
    d=json.loads((d_folder/"D_G2_VERIFIED.json").read_bytes())
    m=json.loads((m_folder/"M_G2_AGGREGATE.json").read_bytes())
    need(d["status"]=="ALL_THREE_NATIVE_G2_PASSED"
         and m["status"]=="ALL_SIX_M_NATIVE_G2_PASS",
         "FORECAST_G2_NOT_CERTIFIED")
    d_recs=[x for x in d["native_candidates"] if x["id"]==D_MODEL]
    m_recs=[x for x in m["native_candidates"] if x["id"]==M_MODEL]
    need(len(d_recs)==len(m_recs)==1
         and d_recs[0]["status"]==m_recs[0]["status"]=="PASS"
         and d_recs[0]["native_source_sha256"]==D_ORIGINAL_SHA
         and m_recs[0]["native_model_source_sha256"].startswith("sha256:")
         and d_recs[0]["balance_max_abs"]<=.008
         and d_recs[0]["rk4_native_max_abs_delta"]<=.012
         and m_recs[0]["balance_max_abs"]<=.008,
         "FORECAST_G2_WINNERS_UNVERIFIED")
    return s,d_recs[0],m_recs[0]

def model_sources(m_folder,d_rec,m_rec):
    structure=topology(1,False)
    source=modelica(
        {"structure":structure,"structure_hash":topology_digest(structure),
         "nominal_parameters":{"capacity":72,"response_time":0.125,"loss_time":1}},
        {"kind":"pulse","rate":72,"duration":1/3})
    need(sha(source.encode())==D_ORIGINAL_SHA,
         "FORECAST_D_CONSTRUCTION_MODEL_NOT_IDENTICAL")
    d_key="parameter Real pulseRate = 72;"
    need(source.count(d_key)==1,"FORECAST_D_PULSE_TEMPLATE_CHANGED")
    d_future=source.replace(d_key,"parameter Real pulseRate = 90;")
    need(d_future.replace("parameter Real pulseRate = 90;",d_key)==source,
         "FORECAST_D_PARAMETERS_OR_TOPOLOGY_CHANGED")
    package=(m_folder/"CAF01MPreflight.mo").read_text(encoding="utf-8")
    manifest=json.loads((m_folder/"M_PRODUCER_PACKET.json").read_bytes())
    names=[x["model_name"] for x in manifest["nine_nominal_model_sources"]]
    sources=published_caf_model_sources(package,names)
    class_name="CAF01_C00_C72"
    need(class_name in sources
         and sha(sources[class_name].encode())==m_rec["native_model_source_sha256"],
         "FORECAST_M_CONSTRUCTION_CLASS_NOT_IDENTICAL")
    m_key="parameter Real publicRate=72;"
    need(package.count(m_key)==9,"FORECAST_M_EXACT_NINE_PULSES_MISSING")
    m_future=package.replace(m_key,"parameter Real publicRate=90;")
    need(m_future.replace("parameter Real publicRate=90;",m_key)==package,
         "FORECAST_M_NONPULSE_MODEL_CHANGE")
    return d_future,m_future,source,package

def prepare(d_folder,m_folder,g3_file,out):
    need(not out.exists(),"FORECAST_OUTPUT_EXISTS")
    selection,d_rec,m_rec=inputs(d_folder,m_folder,g3_file)
    d_src,m_src,d_old,m_old=model_sources(m_folder,d_rec,m_rec)
    out.mkdir(parents=True,exist_ok=False)
    d_class=d_src.split("\n",1)[0].split()[1]
    (out/(d_class+".mo")).write_bytes(d_src.encode())
    (out/"CAF01MPreflight.mo").write_bytes(m_src.encode())
    (out/"G3_CONSTRUCTION_SELECTION.json").write_bytes(g3_file.read_bytes())
    (out/"D_FORECAST.mos").write_text("\n".join([
        f'cd("{out.resolve().as_posix()}");',
        f'loadFile("{(out/(d_class+".mo")).resolve().as_posix()}");',
        f'checkModel({d_class});',
        f'simulate({d_class},startTime=0,stopTime=(2.0/3.0),'
        'numberOfIntervals=80,method="dassl",tolerance=1e-9,'
        'outputFormat="csv",fileNamePrefix="CAF01_D_FORECAST");',
        'print(getErrorString());',""]),encoding="utf-8")
    root=HERE.parents[2]
    (out/"M_FORECAST.mos").write_text("\n".join([
        f'cd("{out.resolve().as_posix()}");',
        f'loadFile("{(root/"src/modelica/IGCMolecules.mo").resolve().as_posix()}");',
        f'loadFile("{(root/"src/modelica/IGCInformationMolecules.mo").resolve().as_posix()}");',
        f'loadFile("{(out/"CAF01MPreflight.mo").resolve().as_posix()}");',
        f'checkModel(CAF01MPreflight.{class_name});',
        f'simulate(CAF01MPreflight.{class_name},startTime=0,'
        'stopTime=(2.0/3.0),numberOfIntervals=80,method="dassl",'
        'tolerance=1e-9,outputFormat="csv",fileNamePrefix="CAF01_M_FORECAST");',
        'print(getErrorString());',""]),encoding="utf-8")
    manifest={
        "schema":"igc-caf01-g4-model-forecast-first/0.1",
        "status":"PREPARED_NOT_SIMULATED",
        "source_G3_selection_sha256":selection["selection_sha256"],
        "source_G3_file_sha256":G3_FILE_ORIGINAL_SHA,
        "source_D_native_G2_sha256":D_G2_SHA,
        "source_M_native_G2_sha256":M_G2_SHA,
        "D_candidate":D_MODEL,"M_candidate":M_MODEL,
        "B_status":"G1_MATERIAL_FAIL_NO_MODEL_OR_FORECAST",
        "D_parameter_ambiguity":True,
        "D_model_frozen_sha256":D_ORIGINAL_SHA,
        "M_model_frozen_sha256":m_rec["native_model_source_sha256"],
        "D_original_model_sha256":sha(d_old.encode()),
        "M_original_package_sha256":sha(m_old.encode()),
        "D_forecast_model_sha256":sha(d_src.encode()),
        "M_forecast_package_sha256":sha(m_src.encode()),
        "changed_input_only":{"construction_rate_items_per_hour":72,
                              "evaluation_rate_items_per_hour":90,
                              "duration_hours":"1/3","horizon_hours":"2/3"},
        "max_new_model_OMC_attempts":2,
        "model_OMC_attempts_at_prepare":0,
        "DES_evaluation_world_runs":0,
        "evaluation_truth_accessed":False,
        "provider_inferences":0,"RK4_integrations":0,
        "custody":"NOT_CUSTODIED_DO_NOT_REVEAL_HOLDOUT"
    }
    save(out/"FORECAST_PREFLIGHT.json",manifest)
    return manifest

def verify_native(folder,arm):
    need(arm in ("D","M"),"FORECAST_BAD_ARM")
    p="CAF01_"+arm+"_FORECAST"
    name=p+"_res.csv"
    attempt=folder/(p+".attempt")
    code=folder/(p+".exit_code")
    csvfile=folder/name
    result={"arm":arm,"status":"FAIL","reason":None,
            "attempt_spent":attempt.is_file(),"csv_sha256":None,
            "model_input_sha256":hashfile(
                folder/("FORECAST_PREFLIGHT.json"))}
    try:
        need(attempt.is_file() and attempt.read_bytes()==b"INVOCATION_STARTED\n",
             "FORECAST_INVOCATION_NOT_RECORDED")
        need(code.is_file() and code.read_bytes()==b"0\n",
             "FORECAST_NATIVE_SOLVER_EXIT_NONZERO_OR_MISSING")
        need(csvfile.is_file(),"FORECAST_CSV_MISSING")
        result["csv_sha256"]=hashfile(csvfile)
        with csvfile.open(newline="",encoding="utf-8") as f:
            rows=list(csv.DictReader(f))
        require_D=arm=="D"
        stocks=(["s1"] if require_D else
                ["preparation0.stock.level","dispatch0.stock.level"])
        delivered="delivered" if require_D else "deliveredTotal"
        fields=["time",delivered,*stocks]+(["lost"] if require_D else
                                            ["receipt0.deliveries.level"])
        need(len(rows)>=81 and set(fields).issubset(rows[0]),
             "FORECAST_CSV_INCOMPLETE")
        prevt=-1.0
        prev_del=-1.0
        mass_max=0.0
        out=[]
        for row in rows:
            t=float(row["time"])
            d=float(row[delivered])
            state=[float(row[v]) for v in stocks]
            lost=float(row["lost"]) if require_D else 0.0
            extra=float(row["receipt0.deliveries.level"]) if not require_D else d
            need(all(math.isfinite(v) for v in [t,d,lost,extra,*state]),
                 "FORECAST_CSV_NONFINITE")
            need(t>=prevt-1e-8 and -1e-8<=t<=HORIZON+1e-7
                 and min([d,lost,*state])>=-.008 and d>=prev_del-1e-7,
                 "FORECAST_CSV_UNPHYSICAL")
            expected=RATE*min(max(t,0),1/3)
            mass_max=max(mass_max,abs(sum(state)+d+lost-expected))
            need(abs(d-extra)<.008,"FORECAST_M_DELIVERY_ALIAS_CHANGED")
            prevt,prev_del=t,d
        need(abs(float(rows[0]["time"]))<1e-8
             and abs(prevt-HORIZON)<1e-6
             and mass_max<=.008
             and abs(lost)<.008,
             "FORECAST_MASS_OR_GRID_FAILED")
        for minute in TIMES:
            samples=[float(row[delivered]) for row in rows
                     if abs(float(row["time"])-minute/60)<1e-6]
            need(len(samples)>=1,"FORECAST_MISSING_REQUIRED_TIME")
            out.append(samples[0])
        need(all(b+1e-6>=a for a,b in zip(out,out[1:]))
             and all(0<=x<=30.000001 for x in out),
             "FORECAST_FUTURE_UNPHYSICAL")
        result.update(status="PASS",reason=None,
                      delivered_at_six_minutes=out,balance_max_abs=mass_max,
                      native_csv_rows=len(rows))
    except Exception as err:
        result["reason"]=str(err)[:180]
    save(folder/(p+"_receipt.json"),result)
    return result

def finalize(folder,public_file,out):
    need(not out.exists(),"FORECAST_FINAL_OUTPUT_EXISTS")
    need(hashfile(public_file)==PUBLIC_FILE_SHA,
         "FORECAST_PUBLIC_EVIDENCE_CHANGED")
    selection=json.loads((folder/"G3_CONSTRUCTION_SELECTION.json").read_bytes())
    need(hashfile(folder/"G3_CONSTRUCTION_SELECTION.json")==G3_FILE_ORIGINAL_SHA,
         "FORECAST_SELECTION_CHANGED_POST_RUN")
    original=json.loads((folder/"FORECAST_PREFLIGHT.json").read_bytes())
    need(original["model_OMC_attempts_at_prepare"]==0
         and original["evaluation_truth_accessed"] is False
         and original["max_new_model_OMC_attempts"]==2
         and original["source_G3_selection_sha256"]==selection["selection_sha256"],
         "FORECAST_FROZEN_CONTEXT_CHANGED")
    d=verify_native(folder,"D")
    m=verify_native(folder,"M")
    status=("BOTH_MODEL_FORECASTS_NATIVE_PASS" if d["status"]==m["status"]=="PASS"
            else "PARTIAL_MODEL_FORECASTS_NO_RETRY")
    report={"schema":"igc-caf01-g4-postnative/0.1",
            "status":status,"D":d,"M":m,"B":"G1_FAIL_NO_FORECAST",
            "new_native_model_attempts_consumed":int(d["attempt_spent"])+int(m["attempt_spent"]),
            "new_RK4_integrations":0,"new_B_provider_inferences":0,
            "DES_evaluation_world_runs":0,"evaluation_truth_read":False}
    out.mkdir(parents=True)
    save(out/"G4_MODEL_FORECAST_ATTEMPTS.json",report)
    if status=="BOTH_MODEL_FORECASTS_NATIVE_PASS":
        submission={
          "schema":selection["schema"],
          "selection_sha256":selection["selection_sha256"],
          "source_snapshot_sha256":WORLD,
          "evaluation_pulse":{"kind":"pulse","rate_per_minute":1.5,
                              "duration_minutes":20},
          "forecast_by_candidate":{
              D_MODEL:d["delivered_at_six_minutes"],
              M_MODEL:m["delivered_at_six_minutes"]},
          "native_g2_checks":{}
        }
        contract=json.loads(CONTRACT.read_bytes())
        lock=lock_forecasts(contract,selection,submission)
        need(lock["arm_forecasts"]["D"]["status"]==
                  "ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE"
             and lock["arm_forecasts"]["D"]["prediction"] is None
             and lock["arm_forecasts"]["M"]["status"]==
                  "CONDITIONAL_POINT_FORECAST_NOT_STRUCTURAL_ID"
             and lock["arm_forecasts"]["B"]["status"]=="NO_VALID_CANDIDATE",
             "FORECAST_G3_ABSTENTION_AND_G1_GATE_MISMATCH")
        ev=json.loads(public_file.read_bytes())
        bundle=prepare_preholdout_package(contract,ev,selection,lock)
        receipt=emit_custody_candidate(bundle,out/"custody_candidate")
        need(receipt["evaluation_release_authorized"] is False,
             "FORECAST_EXTERNAL_REVEAL_FORBIDDEN")
        save(out/"G3_FORECAST_LOCK.json",lock)
        save(out/"G4_CUSTODY_CANDIDATE_RECEIPT.json",receipt)
    else:
        save(out/"FORECAST_FAILED_NOT_LOCKED.json",{
          "status":"NO_G4_LOCK_MODEL_FORECAST_FAILURE",
          "do_not_retry_without_NEW_EXPLICIT_BUDGET":True})
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["prepare","finalize"])
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--d-native",type=Path)
    ap.add_argument("--m-native",type=Path)
    ap.add_argument("--g3",type=Path)
    ap.add_argument("--folder",type=Path)
    ap.add_argument("--public",type=Path,default=HERE/"public_inputs/run_40915090599/CAF01.json")
    arg=ap.parse_args()
    if arg.mode=="prepare":
        need(all([arg.d_native,arg.m_native,arg.g3]),
             "FORECAST_PREPARE_SOURCES_REQUIRED")
        res=prepare(arg.d_native,arg.m_native,arg.g3,arg.out)
    else:
        need(arg.folder is not None,"FORECAST_FINALIZE_FOLDER_REQUIRED")
        res=finalize(arg.folder,arg.public,arg.out)
    print(json.dumps({"status":res["status"]},sort_keys=True))

if __name__=="__main__":
    main()
