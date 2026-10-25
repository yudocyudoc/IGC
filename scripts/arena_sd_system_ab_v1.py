"""Pair baseline/v2 prompts on two fresh synthetic construction views.
No reserve, no retry, no S submission. Requires explicit Actions authorization.
"""
import argparse, hashlib, json, os, re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data/diagnostics/arena_sd_system_ab_v1_manifest.json"
OUT=Path("artifacts/arena-sd-system-ab-v1/results.json")
MODEL="@cf/zai-org/glm-5.3-flash"
IDS={"urn:igc:candidate:CS-01","urn:igc:candidate:CS-02"}
ORDER=[("WA","v2"),("WA","baseline"),("WB","baseline"),("WB","v2")]

def canon(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()

def sha(v):
    return "sha256:"+hashlib.sha256(canon(v)).hexdigest()

def check(ok,error):
    if not ok: raise ValueError(error)

def build():
    man=json.loads(MANIFEST.read_text(encoding="utf-8"))
    check(man["schema"]=="igc-sd-prompt-ab/0.1"
          and man["state"]=="FROZEN_BEFORE_INFERENCE"
          and man["model"]==MODEL and man["authorized_provider_calls"]==4
          and man["retries"]==0,"BAD_MANIFEST")
    check(man["purpose"]=="PAIRED_PROMPT_DIAGNOSTIC_NO_FORMAL_ARENA_S_SUBMISSION","BAD_PURPOSE")
    check(man["truth_commitment"]=="sha256:bcf4ae82747ef5656b7279a16ca56063952f670272cc15d62b95c9d382e46943","BAD_TRUTH_COMMIT")
    check([(x["case_id"],x["variant"]) for x in man["order"]]==ORDER,"BAD_CALL_ORDER")
    check(man["v2_system_path"]=="data/prompts/arena_sd_system_v2.txt","BAD_V2_SOURCE")
    cases={x["case_id"]:x["construction"] for x in man["cases"]}
    check(set(cases)=={"WA","WB"} and len(man["cases"])==2,"BAD_CASES")
    check({x["candidate_id"] for x in man["public_catalog"]}==IDS,"BAD_CATALOG")
    baseline=man["baseline_system"]
    v2=(ROOT/man["v2_system_path"]).read_text(encoding="utf-8").strip()
    check(baseline.startswith("You are SD-AI proposing candidate") and len(baseline)>350
          and v2.startswith("You are SD-AI, a critical practitioner") and len(v2)>3000,"BAD_SYSTEM")
    out=[]
    for case_id,variant in ORDER:
        case=cases[case_id]
        check(len(case["times"])==len(case["calibration_times"])==len(case["values"])
              and case["times"][-1]==0
              and case["independent_trial_reset_at_t0"] is True
              and case["unit"]=="units" and case["observable_id"]=="delivered","BAD_PRIMARY")
        state={
            "catalog":man["public_catalog"],"construction":case,
            "observability":man["observability"],"question":man["question"],
            "retrieval":None,"target_times":man["target_times"],
            "task":"propose_and_criticize_causal_structures"}
        user="State is: "+json.dumps(state,sort_keys=True,ensure_ascii=False)
        body={
            "messages":[{"role":"system","content":v2 if variant=="v2" else baseline},
                        {"role":"user","content":user}],
            "temperature":0,"reasoning_effort":"low","max_completion_tokens":4096}
        out.append({"case_id":case_id,"variant":variant,"body":body,
                    "body_hash":sha(body),"user_hash":hashlib.sha256(user.encode()).hexdigest()})
    for c in cases:
        pair=[x for x in out if x["case_id"]==c]
        check(len(pair)==2 and pair[0]["user_hash"]==pair[1]["user_hash"],"CROSS_ARM_DATA_DIFFER")
    return man,out

def parse(content):
    check(isinstance(content,str) and bool(content.strip()),"EMPTY_JSON")
    s=content.strip()
    fence=chr(96)*3
    if s.startswith(fence):
        m=re.fullmatch(re.escape(fence)+r"(?:json)?\s*([\s\S]*?)\s*"+re.escape(fence),s,re.I)
        check(m is not None,"BAD_FENCE")
        s=m.group(1).strip()
    try: obj=json.loads(s)
    except ValueError as exc: raise ValueError("INVALID_JSON") from exc
    check(isinstance(obj,dict) and set(obj)=={"selected_candidate_ids","rationale","falsifier","unknowns","next_test"},"BAD_SCHEMA")
    ids=obj["selected_candidate_ids"]
    check(isinstance(ids,list) and all(isinstance(x,str) for x in ids)
          and set(ids)<=IDS and len(ids)==len(set(ids)),"BAD_SELECTION")
    check(all(isinstance(obj[k],str) and obj[k].strip() for k in ("rationale","falsifier","next_test")),"BAD_EXPLANATION")
    check(isinstance(obj["unknowns"],list) and all(isinstance(x,str) for x in obj["unknowns"]),"BAD_UNKNOWNS")
    return obj

def save(v):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    temp=OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    temp.replace(OUT)

def run():
    man,reqs=build()
    check(os.getenv("GITHUB_RUN_ATTEMPT","1")=="1"
          and os.getenv("IGC_SD_AB_AUTHORIZATION")=="RUN_SDA_V1_4_CALLS","NOT_AUTHORIZED")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    check(re.fullmatch(r"[a-fA-F0-9]{32}",account) is not None and bool(token),"MISSING_CREDENTIALS")
    result={
        "schema":"igc-sd-prompt-ab-result/0.1","manifest_hash":sha(man),
        "model":MODEL,"purpose":man["purpose"],"truth_commitment":man["truth_commitment"],
        "planned_calls":4,"attempted_calls":0,"retries":0,
        "holdout_opened":False,"formal_s_submission":False,
        "prediction_lock_created":False,"steps":[]}
    save(result)
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    for call in reqs:
        label=call["case_id"]+":"+call["variant"]
        step={"case_id":call["case_id"],"variant":call["variant"],"body_hash":call["body_hash"],
              "user_hash":call["user_hash"],"status":"STARTED","http_status":None,"attempts":1}
        result["steps"].append(step)
        result["attempted_calls"]+=1
        save(result)
        try:
            req=Request(url,data=canon(call["body"]),method="POST",
                        headers={"Authorization":"Bearer "+token,
                                 "Content-Type":"application/json","Accept":"application/json"})
            with urlopen(req,timeout=150) as response:
                step["http_status"]=response.status
                raw=json.load(response)
            check(isinstance(raw,dict) and raw.get("success") is True,"PROVIDER_UNSUCCESSFUL")
            data=raw.get("result",{})
            check(isinstance(data,dict) and data.get("model")==MODEL,"MODEL_MISMATCH")
            choice=data["choices"][0]
            msg=choice["message"]
            step.update({"provider_request_id":data.get("id"),"finish_reason":choice.get("finish_reason"),
                         "usage":data.get("usage"),"content":msg.get("content"),
                         "reasoning_content_present":bool(msg.get("reasoning_content")),
                         "reasoning_content_archived":False})
            check(step["finish_reason"]=="stop","NON_STOP_FINISH")
            step["parsed"]=parse(step["content"])
            step["status"]="VALID_JSON"
            print("SD_AB_OK",label,"selected="+str(len(step["parsed"]["selected_candidate_ids"])),flush=True)
        except HTTPError as exc:
            step["http_status"]=exc.code
            step["status"]="RATE_LIMITED_NO_RETRY" if exc.code==429 else "PROVIDER_HTTP_ERROR_NO_RETRY"
        except (URLError,TimeoutError,OSError,ValueError,KeyError,IndexError,TypeError) as exc:
            step["status"]="INVALID_OR_TRANSPORT_NO_RETRY"
            step["error_code"]=str(exc)[:100] if isinstance(exc,ValueError) else type(exc).__name__
        finally: save(result)
        if step["status"]!="VALID_JSON":
            result["status"]="ABORTED_NO_RETRY"
            save(result)
            print("SD_AB_FAILED",label,step["status"],step["http_status"],flush=True)
            return 1
    result["status"]="FOUR_VALID_JSON_NO_HOLDOUT"
    save(result)
    print("SD_AB_COMPLETED_4_VALID_NO_HOLDOUT",flush=True)
    return 0

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["check","execute"])
    mode=p.parse_args().mode
    if mode=="check":
        man,reqs=build()
        for req in reqs: print("SD_AB_PREPARED",req["case_id"],req["variant"],req["body_hash"],req["user_hash"])
        print("SD_AB_PREPARED_NO_INFERENCE",sha(man))
    else: raise SystemExit(run())
