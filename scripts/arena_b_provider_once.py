"""Single-call Cloudflare transport for pinned Buffalo quantitative prompt.

This ports the upstream process prompt (not the original NodeJS runtime).
No retry, no hidden data, no molecular/D rules, no fixture fallback.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_b_sdai_v0 import make_request, accept, BuffaloBridgeError

MODEL = "@cf/zai-org/glm-5.3-flash"
AUTHORIZATION = "RUN_BUFFALO_B1_SINGLE_PROVIDER_CALL"
SCHEMA = "igc-buffalo-one-call-receipt/0.1"

class ProviderError(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise ProviderError(code)

def save(path, obj):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(obj)+b"\n")

def request_body(prepared):
    require(prepared.get("arm_id")=="B" and
            prepared.get("provider_status")=="NOT_CALLED_PREPARATION_ONLY" and
            prepared.get("currentModel")=={"variables":[],"relationships":[]},
            "INVALID_BUFFALO_REQUEST")
    return {"messages":[
        {"role":"system","content":prepared["prompt"]["system"]},
        {"role":"user","content":prepared["prompt"]["user"]}],
        "temperature":0,"reasoning_effort":"low",
        "max_completion_tokens":4096}

def extract_native(message):
    require(type(message) is str and 0 < len(message) < 250000,
            "MISSING_PROVIDER_CONTENT")
    content=message.strip()
    fence=chr(96)*3
    if content.startswith(fence):
        require(content.endswith(fence),"INCOMPLETE_JSON_FENCE")
        content=content[3:-3].strip()
        if content.startswith("json"):
            content=content[4:].strip()
    try:
        parsed=json.loads(content)
    except ValueError as exc:
        raise ProviderError("PROVIDER_CONTENT_NOT_JSON") from exc
    require(type(parsed) is dict,"PROVIDER_JSON_NOT_OBJECT")
    if type(parsed.get("model")) is dict:
        parsed=parsed["model"]
    else:
        parsed={key:parsed[key] for key in ("variables","relationships","specs")
                if key in parsed}
    require("variables" in parsed and "relationships" in parsed,
            "PROVIDER_JSON_NOT_SD_JSON")
    return parsed

def one_call(*, visible_path, output, env=None, sender=urlopen):
    env=os.environ if env is None else env
    require(env.get("IGC_BUFFALO_B1_AUTHORIZATION")==AUTHORIZATION and
            env.get("GITHUB_RUN_ATTEMPT","1")=="1","CALL_NOT_AUTHORIZED")
    account=env.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=env.get("CLOUDFLARE_API_TOKEN","").strip()
    require(re.fullmatch(r"[0-9a-fA-F]{32}",account) is not None and bool(token),
            "MISSING_CLOUDFLARE_SECRETS")
    data=json.loads(Path(visible_path).read_text())
    prepared=make_request(data)
    body=request_body(prepared)
    root=Path(output)
    require(not root.exists(),"OUTPUT_ALREADY_EXISTS")
    root.mkdir(parents=True,exist_ok=False)
    state={"schema":SCHEMA,"arm_id":"B","upstream_commit":prepared["upstream_commit"],
           "method":prepared["method"],"model":MODEL,
           "input_hash":prepared["input_hash"],"request_hash":digest(body),
           "calls_planned":1,"calls_started":0,"calls_completed":0,
           "retries":0,"raw_preserved":False,"status":"PREPARED",
           "holdout_accessed":False,"independent_attestation":False,
           "modelica_generated":False}
    save(root/"buffalo-process-request.json",prepared)
    save(root/"provider-body.json",body)
    save(root/"receipt.json",state)
    address=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    req=Request(address,data=canonical(body),method="POST",
                headers={"Authorization":"Bearer "+token,
                         "Content-Type":"application/json","Accept":"application/json"})
    state["calls_started"]=1
    state["status"]="STARTED_NO_RETRY"
    save(root/"receipt.json",state)
    start=time.perf_counter()
    try:
        with sender(req,timeout=150) as response:
            raw=json.load(response)
            state["http_status"]=response.status
        state["duration_ms"]=round((time.perf_counter()-start)*1000)
        state["calls_completed"]=1
        save(root/"response-raw.json",raw)
        state["raw_preserved"]=True
        require(type(raw) is dict and raw.get("success") is True,
                "PROVIDER_UNSUCCESSFUL")
        result=raw.get("result")
        require(type(result) is dict and result.get("model")==MODEL,
                "PROVIDER_MODEL_MISMATCH")
        choice=result["choices"][0]
        state["finish_reason"]=choice.get("finish_reason")
        state["usage"]=result.get("usage")
        state["provider_id"]=result.get("id")
        require(state["finish_reason"]=="stop","TRUNCATED_GENERATION")
        sd_json=extract_native(choice["message"].get("content"))
        native={"origin":"BUFFALO_PROCESS_PORT_LIVE",
                "source":"Cloudflare Workers AI model " + MODEL,
                "model":sd_json}
        save(root/"sd-ai-native-provider-output.json",native)
        try:
            accepted=accept(data,native,root/"accepted-model")
            state["modelica_generated"]=True
            state["hypothesis_id"]=accepted["hypothesis_id"]
            state["status"]="B1_NATIVE_SFD_TRANSLATED_G2_NOT_YET_TESTED"
        except BuffaloBridgeError as exc:
            state["status"]="B1_NATIVE_SFD_UNSUPPORTED_BY_BOUNDED_MODELICA_ADAPTER"
            state["translator_diagnostic"]=str(exc)[:180]
        save(root/"receipt.json",state)
        return state
    except HTTPError as exc:
        state["http_status"]=exc.code
        state["status"]="HTTP_FAILURE_NO_RETRY"
    except (URLError,TimeoutError,OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        state["status"]="PROVIDER_OR_PARSE_FAILURE_NO_RETRY"
        state["error_type"]=type(exc).__name__
        if isinstance(exc,ValueError):
            state["diagnostic"]=str(exc)[:180]
    save(root/"receipt.json",state)
    raise ProviderError(state["status"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    r=one_call(visible_path=a.input,output=a.out)
    print(json.dumps({"status":r["status"],"calls_completed":r["calls_completed"],
                      "modelica_generated":r["modelica_generated"],
                      "usage":r.get("usage")},sort_keys=True))

if __name__=="__main__":
    main()
