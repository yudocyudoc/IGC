"""Audited one-shot Cloudflare S/P campaign. Provider inference is opt-in.

No new Worker, Access, HMAC or callback. The capture directory is created
exclusively before the first request to prevent accidental replay of the same
campaign path. Partial runs remain incomplete; reusing their path fails.
Local hashes and claimed run-ref establish integrity, NOT third-party identity,
independent custody, or proof that a remote provider was actually called.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from typing import Callable, Any
from urllib.request import urlopen

from .arena_round import canonical, exclusive_json, hash_obj, no_hidden
from .arena_sp_producers import (AUTHORIZATION, ORDER, ProviderError,
                                 _validate_schedule, run_authorized,
                                 parse_responses)

SCHEMA="igc-arena-provider-receipt/0.1"
TOKEN_PAIRS=(("prompt_tokens","completion_tokens"),
             ("input_tokens","output_tokens"))


def capture_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def usage_of(response: dict) -> dict:
    """Only observed provider counters, never estimates or fabricated zeros."""
    result=response.get("result",{})
    candidates=[response.get("usage"),result.get("usage") if isinstance(result,dict) else None]
    usage=next((x for x in candidates if isinstance(x,dict)),{})
    counters={}
    for key in ("prompt_tokens","completion_tokens","input_tokens",
                "output_tokens","total_tokens","neurons"):
        x=usage.get(key)
        if type(x) in (int,float) and math.isfinite(x) and x>=0:
            counters[key]=x
    token_total=None
    for k1,k2 in TOKEN_PAIRS:
        if k1 in counters and k2 in counters:
            token_total=int(counters[k1]+counters[k2]) if (
                float(counters[k1]).is_integer() and float(counters[k2]).is_integer()
            ) else None
            break
    if token_total is None and "total_tokens" in counters:
        x=counters["total_tokens"]
        token_total=int(x) if float(x).is_integer() else None
    return {"provider_reported":counters,
            "token_total":token_total,
            "token_status":"REPORTED" if token_total is not None else "UNAVAILABLE"}


def build_receipt(package:dict,responses:dict,observations:list[dict], *,
                  run_ref:str, capture_method:str) -> dict:
    """A receipt is a local audit manifest, never independent attestation."""
    _validate_schedule(package)
    if set(responses)!=set(ORDER) or len(observations)!=3:
        raise ProviderError("CAPTURE_INCOMPLETE")
    if not isinstance(run_ref,str) or not run_ref.strip():
        raise ProviderError("missing run reference")
    if capture_method not in ("INJECTED_TEST_SENDER","PYTHON_URLLIB"):
        raise ProviderError("unknown capture method")
    rows=[]
    for i,(name,obs) in enumerate(zip(ORDER,observations)):
        if (obs.get("model_name")!=name or obs.get("sequence")!=i+1
            or obs.get("response_hash")!=hash_obj(responses[name])
            or type(obs.get("duration_ms")) not in (int,float)
            or not math.isfinite(obs["duration_ms"]) or obs["duration_ms"]<0):
            raise ProviderError("CAPTURE_MISMATCH")
        if obs.get("usage")!=usage_of(responses[name]):
            raise ProviderError("CAPTURE_USAGE_MISMATCH")
        rows.append(dict(obs))
    token_values=[row["usage"]["token_total"] for row in rows]
    receipt={
        "schema":SCHEMA,"run_ref":run_ref,"capture_method":capture_method,
        "mock":capture_method!="PYTHON_URLLIB",
        "requests_hash":package["manifest"]["requests_hash"],
        "response_hashes":{k:hash_obj(responses[k]) for k in ORDER},
        "calls_planned":3,"calls_completed":3,"retries":0,
        "observations":rows,
        "total_duration_ms":sum(row["duration_ms"] for row in rows),
        "tokens":sum(token_values) if all(x is not None for x in token_values) else None,
        "tokens_status":"REPORTED_ALL" if all(x is not None for x in token_values)
                        else "PARTIAL_OR_UNAVAILABLE",
        "cost_status":"PROVIDER_CURRENCY_NOT_VERIFIED",
        "independent_attestation":False,
        "empirical_causality":"NOT_PROVEN"
    }
    no_hidden(receipt)
    receipt["receipt_hash"]=hash_obj(receipt)
    return receipt


def check_receipt(receipt:dict,package:dict,responses:dict,
                  *, require_live:bool=False) -> None:
    clone=dict(receipt)
    signature=clone.pop("receipt_hash",None)
    if signature!=hash_obj(clone):
        raise ProviderError("PROVIDER_RECEIPT_TAMPERED")
    expected=build_receipt(package,responses,receipt["observations"],
                           run_ref=receipt["run_ref"],
                           capture_method=receipt["capture_method"])
    if expected!=receipt:
        raise ProviderError("PROVIDER_RECEIPT_MISMATCH")
    if require_live and (receipt["mock"] is not False or
                         receipt["capture_method"]!="PYTHON_URLLIB"):
        raise ProviderError("MOCK_IS_NOT_LIVE_PROVIDER")
    # A locally formed receipt alone never proves a remote call happened.


def run_capture(package:dict,catalog:dict,*, authorization:str,
                output_dir:Path,run_ref:str,
                sender:Callable=urlopen,
                capture_method:str="PYTHON_URLLIB",
                clock:Callable=time.perf_counter,
                env:dict | None=None) -> dict:
    """Single use; journal every successful call before the next API call."""
    _validate_schedule(package)
    if authorization != AUTHORIZATION:
        raise ProviderError("NO_INFERENCE: explicit campaign authorization required")
    if capture_method not in ("PYTHON_URLLIB","INJECTED_TEST_SENDER"):
        raise ProviderError("unknown capture method")
    if capture_method=="INJECTED_TEST_SENDER" and sender is urlopen:
        raise ProviderError("TEST_SENDER_REQUIRED")
    if capture_method=="PYTHON_URLLIB" and sender is not urlopen:
        raise ProviderError("LIVE_CAPTURE_REQUIRES_REAL_HTTP_TRANSPORT")
    # Guard against rerunning a partial campaign after a timeout. No retry.
    output_dir.mkdir(parents=True,exist_ok=False)
    exclusive_json(output_dir/"manifest.json",{
        "schema":SCHEMA,"run_ref":run_ref,
        "requests_hash":package["manifest"]["requests_hash"],
        "state":"STARTED_NOT_COMPLETED","started_at":capture_time()})
    observations=[]
    def observed(name: str, response: dict, duration_ms: float):
        obs={"sequence":len(observations)+1,
             "model_name":name,"response_hash":hash_obj(response),
             "duration_ms":round(duration_ms,3),
             "usage":usage_of(response)}
        observations.append(obs)
        exclusive_json(output_dir/f"call-{len(observations)}.json",
                       {"observation":obs,"response":response})
    responses=run_authorized(package,authorization=authorization,
                             sender=sender,on_result=observed,clock=clock,env=env)
    draft=parse_responses(package,responses,catalog)
    receipt=build_receipt(package,responses,observations,
                          run_ref=run_ref,capture_method=capture_method)
    check_receipt(receipt,package,responses)
    exclusive_json(output_dir/"provider-responses.json",responses)
    exclusive_json(output_dir/"provider-drafts.json",draft)
    exclusive_json(output_dir/"provider-receipt.json",receipt)
    exclusive_json(output_dir/"completed.json",{
        "schema":SCHEMA,"state":"COMPLETE_NOT_EMPIRICALLY_EVALUATED",
        "receipt_hash":receipt["receipt_hash"],
        "draft_hash":draft["output_hash"]})
    return receipt


def main():
    parser=argparse.ArgumentParser(description="One-shot captured S/P inference")
    parser.add_argument("--package",type=Path,required=True)
    parser.add_argument("--catalog",type=Path,required=True)
    parser.add_argument("--out-dir",type=Path,required=True)
    parser.add_argument("--run-ref",required=True)
    parser.add_argument("--authorization",required=True)
    args=parser.parse_args()
    read=lambda p:json.loads(p.read_text(encoding="utf-8"))
    receipt=run_capture(read(args.package),read(args.catalog),
                        authorization=args.authorization,
                        output_dir=args.out_dir,run_ref=args.run_ref)
    print(json.dumps({"status":"COMPLETE_NOT_EMPIRICALLY_EVALUATED",
                      "calls":receipt["calls_completed"],
                      "tokens_status":receipt["tokens_status"],
                      "receipt_hash":receipt["receipt_hash"]}))


if __name__=="__main__":
    main()
