"""R1 Buffalo physical evaluator. Never repair native model or recast G0 failures.

The initial call is made only by the original upstream Buffalo engine. All
replays after that point require archived native bytes and do not invoke AI.
"""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
from scripts.arena_b_native_to_modelica import generate, TranslationBlocked
from scripts.arena_b_construction_check import assess as assess_b
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-arena-r1-buffalo-physical/0.1"


def require(ok,reason):
    if not ok: raise ValueError(reason)


def load(path):
    return json.loads(Path(path).read_text())


def filehash(path):
    return "sha256:"+sha256(Path(path).read_bytes()).hexdigest()


def from_live(visible_path, live_dir):
    visible=load(visible_path)
    root=Path(live_dir)
    receipt_path=root/"receipt.json"
    require(receipt_path.is_file(),"R1_B_MISSING_PROVIDER_RECEIPT")
    receipt=load(receipt_path)
    started=receipt.get("live_provider_calls",0)
    require(started in (0,1),"R1_B_MULTIPLE_PROVIDER_CALLS")
    require(receipt.get("r1_common_initial") is True and
            receipt.get("common_input_sha256",{}).__class__ is str,
            "R1_B_FOREIGN_EXPERIMENT")
    req=root/"cf-request-metadata.json"
    cap=load(req).get("parameter_overrides",{}).get("max_completion_tokens") if req.exists() else None
    require(cap in (None,7000) and (started==0 or cap==7000),
            "R1_B_OUTPUT_BUDGET_CHANGED")
    meta={"provider_calls_started":started,
          "receipt_sha256":filehash(receipt_path),
          "raw_response_sha256":filehash(root/"cloudflare-raw.json")
                                 if (root/"cloudflare-raw.json").exists() else None,
          "native_sha256":filehash(root/"native-output.json")
                          if (root/"native-output.json").exists() else None,
          "provider_status":receipt.get("status"),
          "inference_origin":receipt.get("inference_source"),
          "source_snapshot_hash":visible["source_snapshot_hash"],
          "visible_input_sha256":digest(visible),
          "reported_usage":receipt.get("provider_usage"),
          "max_output_tokens":cap,
          "cost_usd_estimate":None}
    # Cloudflare Workers AI currently bills GLM-5.3-Flash $0.15/M input,
    # $0.50/M output; rates are external and must be dated separately.
    raw=root/"cloudflare-raw.json"
    if raw.is_file():
        rr=load(raw)
        usage=rr.get("result",{}).get("usage") or rr.get("usage") or {}
        inp=usage.get("prompt_tokens") or usage.get("input_tokens")
        out=usage.get("completion_tokens") or usage.get("output_tokens")
        if type(inp) is int and type(out) is int and inp>=0 and 0<=out<=7000:
            meta["reported_usage"]={"input_tokens":inp,"output_tokens":out}
            meta["cost_usd_estimate"]=round((0.15*inp+0.50*out)/1000000,8)
    return meta


def pre(visible_path,live_dir,output):
    result={"schema":SCHEMA,"phase":"G0_ADAPTER_ATTEMPT",
            "source":"REAL_ORIGINAL_BUFFALO_UNMODIFIED_NATIVE",
            "g0_status":"NOT_RUN","g2_status":"NOT_RUN",
            "g3_status":"NOT_RUN","holdout":"NOT_ACCESSED",
            "new_proposal_not_prior_b2_b5":True,
            "no_cross_arm_models_inferred":True}
    out=Path(output)
    require(not out.exists(),"R1_B_G0_OUTPUT_EXISTS")
    out.mkdir(parents=True)
    result["provider"]=from_live(visible_path,live_dir)
    native=Path(live_dir)/"native-output.json"
    if result["provider"]["provider_calls_started"]!=1 or not native.exists():
        result["g0_status"]="NATIVE_RETURN_NOT_AVAILABLE"
    else:
        try:
            document=load(native)
            name,code,report=generate(document)
            result.update({"g0_status":"TRANSLATED_CONDITIONALLY",
                           "translation_report":report,"model_name":name,
                           "modelica_sha256":"sha256:"+sha256(code.encode()).hexdigest()})
            (out/(name+".mo")).write_text(code)
            (out/"check.mos").write_text("\n".join([
                f'loadFile("/work/artifacts/r1-b-physical/{name}.mo");',
                'print(getErrorString());',
                f'checkModel({name});','print(getErrorString());',
                f'simulate({name},stopTime=8,numberOfIntervals=64,method="euler",outputFormat="csv");',
                'print(getErrorString());',""]))
        except (ValueError,TypeError,KeyError,OverflowError) as error:
            result["g0_status"]="BLOCKED_UNSUPPORTED_OR_INVALID_NATIVE"
            result["blocked_reason"]=str(error)[:200]
    (out/"pre-physical.json").write_bytes(canonical(result)+b"\n")
    return result


def finalize(visible_path,live_dir,physical_dir,shared_report,output):
    predata=load(Path(physical_dir)/"pre-physical.json")
    source=load(visible_path)
    report={"schema":"igc-arena-r1-three-arm-construction/0.1",
            "source_snapshot_hash":source["source_snapshot_hash"],
            "round_id":source["round_id"],
            "status":"PARTIAL_UNTIL_B_PHYSICALLY_ASSESSED",
            "B":{"initial_native_sha256":predata["provider"]["native_sha256"],
                 "status":predata["g0_status"],"g0":predata["g0_status"],
                 "g2":"NOT_RUN","g3":"NOT_RUN",
                 "provider":predata["provider"]},
            "holdout":"NOT_ACCESSED","feedback":"NOT_DELIVERED",
            "joint_atms_ledger":"NOT_RUN","ref_baseline":"NOT_RUN",
            "winner":"NOT_DECLARED",
            "source_other_arms":"PR53_REAL_G2_ONLY_NOT_SENT_TO_BUFFALO"}
    if predata["g0_status"]=="TRANSLATED_CONDITIONALLY":
        model=predata["model_name"]
        csvfile=Path(physical_dir)/(model+"_res.csv")
        if csvfile.exists():
            try:
                with csvfile.open(newline="",encoding="utf-8-sig") as f:
                    rows=list(csv.DictReader(f))
                assessed=assess_b(rows,source)
                report["B"].update({
                    "status":"G2_REAL_G3_CONSTRUCTION_DESCRIPTIVE",
                    "g2":"REAL_EULER_SIMULATED_MASS_BALANCED",
                    "g3":assessed,
                    "solver_csv_sha256":filehash(csvfile),
                    "modelica_sha256":predata["modelica_sha256"],
                    "g0_limits":predata["translation_report"]["limits"],
                })
                report["status"]="R1_THREE_ARM_INITIAL_ATTEMPTS_DOCUMENTED"
            except (ValueError,KeyError,TypeError,IndexError) as e:
                report["B"].update({
                    "status":"G2_OR_G3_PHYSICAL_CHECK_FAILED",
                    "reason":str(e)[:250]})
        else:
            report["B"].update({"status":"G2_FAILED_OR_NO_SOLVER_CSV"})
    elif predata["g0_status"]=="BLOCKED_UNSUPPORTED_OR_INVALID_NATIVE":
        report["B"]["blocked_reason"]=predata["blocked_reason"]
    shared=Path(shared_report)
    if shared.exists():
        old=load(shared)
        require(old["source_snapshot_hash"]==source["source_snapshot_hash"] and
                len(old["arms"]["D"]["candidates"])==6 and
                len(old["arms"]["M"]["candidates"])==3,
                "R1_B_OTHER_ARM_ARCHIVE_WRONG_SOURCE")
        report["D"]=old["arms"]["D"]
        report["M"]=old["arms"]["M"]
        report["d_m_source_run"]="40450646600"
        report["d_m_source_artifact"]="12709988124"
    else:
        report["D"]="EARLIER_PHYSICAL_RESULT_NOT_JOINED"
        report["M"]="EARLIER_PHYSICAL_RESULT_NOT_JOINED"
    out=Path(output)
    require(not out.exists(),"R1_B_FINAL_ALREADY_EXISTS")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(canonical(report)+b"\n")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=["pre","final"])
    p.add_argument("--visible",required=True,type=Path)
    p.add_argument("--live",required=True,type=Path)
    p.add_argument("--physical",required=True,type=Path)
    p.add_argument("--shared",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.phase=="pre":
        result=pre(a.visible,a.live,a.physical)
    else:
        require(a.shared is not None,"R1_B_SHARED_ARG_REQUIRED")
        result=finalize(a.visible,a.live,a.physical,a.shared,a.out)
    print(json.dumps({"phase":a.phase,"status":result.get("status",result.get("g0_status")),
                      "sha256":digest(result)}))


if __name__=="__main__":
    main()
