"""PT02 R2: preserve Buffalo's one real native revision and try unchanged G0/G2/G3.

Never alter native equations; a failed translation or build is a result.
No independent holdout, causal identification or cross-arm winner.
"""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_b_native_to_modelica import generate
from scripts.arena_b_construction_check import assess
from scripts.arena_r1_buffalo_postonly import ORIGINAL_NATIVE_SHA, SHARED_SOURCE
from scripts.arena_v0_contract import canonical, digest

EXPECTED_REQUEST="sha256:d0426c72a2b19856cb9d1a9ff5f6e322a7aaa8f31395ead032588065ba76ad4c"
SCHEMA="igc-arena-r2-b-16k-actual-revision/0.1"


def required(ok,code):
    if not ok:
        raise ValueError(code)


def load(p):
    return json.loads(Path(p).read_text())


def bytes_hash(path):
    return "sha256:"+sha256(Path(path).read_bytes()).hexdigest()


def prepare(visible,live,folder):
    root=Path(live)
    folder=Path(folder)
    required(not folder.exists(),"R2_B_PHYSICAL_ALREADY_EXISTS")
    folder.mkdir(parents=True)
    source=load(visible)
    receipt=load(root/"receipt.json")
    request=load(root/"cf-request-metadata.json") if (root/"cf-request-metadata.json").exists() else {}
    native=root/"native-output.json"
    raw=root/"cloudflare-raw.json"
    required(source["source_snapshot_hash"]==SHARED_SOURCE,
             "R2_B_NOT_ORIGINAL_COMMON_SOURCE")
    required(receipt.get("feedback_type")=="R2_OWN_R1_FAILED_MODEL" and
             receipt.get("parent_bytes_sha256")=="sha256:"+ORIGINAL_NATIVE_SHA and
             receipt.get("request_sha256")==EXPECTED_REQUEST and
             receipt.get("r2_feedback_seen") is True and
             receipt.get("current_model_seen") is True and
             receipt.get("live_provider_calls") in (0,1),
             "R2_B_PARENT_REQUEST_OR_NUMBER_OF_CALLS_INVALID")
    if request:
        required(request["actual_model"]=="@cf/zai-org/glm-5.3-flash"
                 and request["parameter_overrides"]["max_completion_tokens"]==16000,
                 "R2_B_WRONG_MODEL_OR_OUTPUT_BUDGET")
    info={
        "schema":SCHEMA,"phase":"G0_OR_BLOCK","r1_parent_sha256":"sha256:"+ORIGINAL_NATIVE_SHA,
        "source_snapshot_hash":SHARED_SOURCE,
        "request_sha256":EXPECTED_REQUEST,
        "provider_calls":receipt["live_provider_calls"],
        "http_status":receipt.get("cf_http_status"),
        "provider_result":receipt.get("status"),
        "input_bytes":receipt.get("r2_input_utf8_bytes"),
        "actual_real_response_sha256":bytes_hash(raw) if raw.exists() else None,
        "actual_native_bytes_sha256":bytes_hash(native) if native.exists() else None,
        "g0":"NOT_TRANSLATED","g2":"NOT_RUN","g3":"NOT_COMPUTABLE",
        "no_evaluator_repairs":True,"holdout":"NOT_ACCESSED",
        "previous_b_g3":"NOT_COMPUTABLE",
        "previous_d_m_not_shared_with_producer":True,
    }
    if raw.exists():
        u=load(raw)
        usage=(u.get("result") or {}).get("usage") or u.get("usage") or {}
        inp=usage.get("prompt_tokens",usage.get("input_tokens"))
        out=usage.get("completion_tokens",usage.get("output_tokens"))
        if type(inp) is int and type(out) is int:
            info["reported_input_tokens"]=inp
            info["reported_output_tokens"]=out
            info["cost_usd_estimate"]=round((0.15*inp+0.5*out)/1000000,8)
            info["budget_observed"]=inp<=8000 and out<=16000
        else:
            info["budget_observed"]="USAGE_UNAVAILABLE"
    if native.exists() and receipt["live_provider_calls"]==1:
        try:
            name,code,translation=generate(load(native))
            info.update(g0="TRANSLATED_CONDITIONALLY",model_name=name,
                        translation=translation,
                        modelica_sha256="sha256:"+sha256(code.encode()).hexdigest())
            (folder/(name+".mo")).write_text(code,encoding="utf-8")
            (folder/"check.mos").write_text("\n".join([
                f'loadFile("/work/artifacts/r2-b-physical/{name}.mo");',
                'print(getErrorString());',
                f'checkModel({name});','print(getErrorString());',
                f'simulate({name},stopTime=8,numberOfIntervals=64,method="euler",outputFormat="csv");',
                'print(getErrorString());',""]),encoding="utf-8")
        except (ValueError,TypeError,KeyError,OverflowError) as exc:
            info["g0"]="BLOCKED_UNSUPPORTED_OR_INVALID_NATIVE"
            info["g0_reason"]=str(exc)[:280]
    else:
        info["g0"]="NO_NATIVE_RESULT_PRESERVED_FOR_REVIEW"
    (folder/"pre.json").write_bytes(canonical(info)+b"\n")
    return info


def finalize(visible,live,folder,output):
    folder=Path(folder)
    info=load(folder/"pre.json")
    r={**info,"phase":"FINAL","g1":"NOT_FULLY_DEMONSTRATED",
       "r2_outcome":"B_R2_NOT_PHYSICALLY_EVALUATED",
       "r2_authorization":"NEW_16K_ONE_CALL_ONLY_NO_RETRIES",
       "r2_decision":"REVIEW_16K_NATIVE_IF_RETURNED",
       "comparison_to_r1_b_rmse":"UNDEFINED_R1_NO_TRAJECTORY"}
    if info["g0"]=="TRANSLATED_CONDITIONALLY":
        csv_path=folder/(info["model_name"]+"_res.csv")
        if csv_path.is_file():
            try:
                with csv_path.open(newline="",encoding="utf-8-sig") as fp:
                    rows=list(csv.DictReader(fp))
                analysis=assess(rows,load(visible))
                r["g2"]="G2_SIMULATED_WITH_MASS_BALANCE_VERIFIED"
                r["g3"]=analysis
                r["r2_outcome"]="B_R2_REAL_CONDITIONAL_PHYSICAL_TRAJECTORY"
                r["solver_csv_sha256"]=bytes_hash(csv_path)
            except (ValueError,KeyError,TypeError,IndexError) as exc:
                r["g2"]="G2_OR_G3_REJECTED"
                r["g2_reason"]=str(exc)[:280]
        else:
            r["g2"]="FAILED_TO_BUILD_OR_NO_SOLVER_CSV"
    output=Path(output)
    required(not output.exists(),"R2_B_REPORT_EXISTS")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(canonical(r)+b"\n")
    return r


def main():
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=["pre","final"])
    p.add_argument("--visible",type=Path,required=True)
    p.add_argument("--live",type=Path,required=True)
    p.add_argument("--physical",type=Path,required=True)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.phase=="pre": result=prepare(a.visible,a.live,a.physical)
    else:
        required(a.out is not None,"R2_FINAL_NEEDS_OUTPUT")
        result=finalize(a.visible,a.live,a.physical,a.out)
    print(json.dumps({"phase":a.phase,"g0":result["g0"],
                     "g2":result["g2"],"r2_outcome":result.get("r2_outcome"),
                     "report_sha256":digest(result)}))


if __name__=="__main__":
    main()
