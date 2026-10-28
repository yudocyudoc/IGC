"""PT-08 paired Clef real six-call run, strictly from predeclared archive.

Provider requests use the PREEXISTING PR #69 original public-six-requests file.
Zero OpenModelica, no refit, zero retries, no re-prompting. Raw is written
BEFORE interpretation; run/grade never read private oracle together.
"""
from __future__ import annotations
import argparse,json,os,re,time
from hashlib import sha256
from pathlib import Path
from urllib.request import Request,urlopen
from scripts.arena_pt08_clef_paired_preflight import (
    SCHEMA,MODEL,MAX_CALLS,THRESHOLDS,guard)
from scripts.arena_clef_dual_pilot import answer_probability
from scripts.arena_v0_contract import canonical,digest

ORIGINAL_PUBLIC_SHA="sha256:89fd4178609774b63a5d1913ea2abb10034f5038e08e162b546b80206e807e0f"
ORIGINAL_PREREG_RUN=40620696061
RUN_AUTH="AUTHORIZED_SIX_REAL_CLEF_CALLS_PT08_20261028"
IDS=("P01-SCREEN-ONLY","P02-PARTIAL-PHYSICAL","P03-EXHAUSTIVE-ONE-STAGE")
CLASSES=("C00","C01","C02")

def hashbytes(content):
    return "sha256:"+sha256(content).hexdigest()

def authenticate(source):
    root=Path(source)
    pub=json.loads((root/"public-six-requests-NOT-SENT.json").read_text())
    manifest=json.loads((root/"manifest.json").read_text())
    guard(pub["schema"]==SCHEMA and digest(pub)==ORIGINAL_PUBLIC_SHA and
          manifest["public_six_request_sha256"]==ORIGINAL_PUBLIC_SHA and
          manifest["provider_requests_planned"]==6 and
          manifest["source_candidate_run_id"]==40578550337 and
          manifest["source_T2_construction_run_id"]==40582633807 and
          manifest["future_provider_authorization"]=="NOT_GRANTED" and
          manifest["new_provider_calls_now"]==manifest["new_solver_calls_now"]==0 and
          len(manifest["source_27_candidate_csv_sha256"])==27 and
          manifest["original_clef_thresholds"]==THRESHOLDS and
          len(pub["requests"])==MAX_CALLS,
          "PT08_ORIGINAL_REQUEST_ARCHIVE_INTEGRITY_FAILURE")
    expected=[f"{ident}:{mode}" for ident in IDS
              for mode in ("NUMERIC_ONLY","NUMERIC_PLUS_NOTE")]
    guard([x["request_id"] for x in pub["requests"]]==expected and
          all(x["model"]==MODEL and
              x["body"]["model"]=="clef" and
              set(x["body"]["questions"])=={"path_"+k for k in CLASSES}
              for x in pub["requests"]),
          "PT08_SIX_PREDECLARED_IDS_OR_PROMPTS_DRIFT")
    for i in range(0,6,2):
        a,b=pub["requests"][i:i+2]
        left,right=json.loads(a["body"]["state"]),json.loads(b["body"]["state"])
        guard(left["fixed_27_physical_candidate_curves_at_same_hours"]==
              right["fixed_27_physical_candidate_curves_at_same_hours"] and
              left["observed_deliveredTotal_at_hours"]==
              right["observed_deliveredTotal_at_hours"] and
              len(left["fixed_27_physical_candidate_curves_at_same_hours"])==27 and
              a["body"]["questions"]==b["body"]["questions"] and
              left["operational_note"]=="NOT_PROVIDED" and
              right["operational_note"]!="NOT_PROVIDED",
              "PT08_UNPAIRED_NUMERIC_DATA")
    return pub,manifest

def run_real(source,out,auth):
    guard(auth==RUN_AUTH,"PT08_SIX_CALLS_EXPLICIT_AUTH_MISSING")
    pub,manifest=authenticate(source)
    out=Path(out)
    guard(not out.exists(),"PT08_REAL_OUTPUT_ALREADY_EXISTS")
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    guard(bool(re.fullmatch(r"[0-9a-fA-F]{32}",account)) and bool(token),
          "PT08_PROVIDER_CREDENTIALS_UNAVAILABLE")
    root=out/"raw"
    root.mkdir(parents=True)
    # Save only public inputs and frozen manifest, never the evaluator's oracle.
    (out/"public-original.json").write_bytes(canonical(pub)+b"\n")
    (out/"original-manifest.json").write_bytes(canonical(manifest)+b"\n")
    progress={"schema":"igc-arena-pt08-clef-real-six-progress/0.1",
              "original_public_sha256":ORIGINAL_PUBLIC_SHA,
              "calls_budget":6,"calls_started":0,"calls_saved":[],"no_retry":True}
    (out/"provider-progress.json").write_bytes(canonical(progress)+b"\n")
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    for i,case in enumerate(pub["requests"]):
        ident=case["request_id"]
        file=root/(f"{i+1:02d}.json")
        guard(not file.exists(),"PT08_ONE_SHOT_RESPONSE_ALREADY_PRESENT")
        body=canonical(case["body"])
        progress["calls_started"]=i+1
        (out/"provider-progress.json").write_bytes(canonical(progress)+b"\n")
        start=time.monotonic()
        req=Request(url,method="POST",data=body,
                    headers={"Authorization":"Bearer "+token,
                             "Content-Type":"application/json",
                             "Accept":"application/json"})
        try:
            with urlopen(req,timeout=65) as response:
                status=response.status
                reply=response.read()
        except Exception as err:
            # No automatic retry, and no failed request replaced.
            receipt={"request_id":ident,"call_index":i+1,
                     "request_sha256":hashbytes(body),
                     "transport_failure":type(err).__name__,
                     "no_automatic_retries":True}
            file.write_bytes(canonical(receipt)+b"\n")
            print("PT08_PROVIDER_FAILED_NO_RETRY",i+1,ident,type(err).__name__,flush=True)
            raise RuntimeError("PT08_ONE_SHOT_PROVIDER_FAILED:"+ident) from None
        duration=int((time.monotonic()-start)*1000)
        try:
            raw=json.loads(reply)
        except Exception:
            file.write_bytes(canonical({
                "request_id":ident,"call_index":i+1,
                "request_sha256":hashbytes(body),
                "http_status":status,"non_json_response_sha256":hashbytes(reply)})+b"\n")
            raise RuntimeError("PT08_PROVIDER_NON_JSON_NO_RETRY:"+ident) from None
        row={"request_id":ident,"call_index":i+1,
             "request_sha256":hashbytes(body),"http_status":status,
             "elapsed_ms":duration,"provider_raw":raw}
        # RAW ARCHIVAL PRECEDES any interpretation.
        file.write_bytes(canonical(row)+b"\n")
        progress["calls_saved"].append({"request_id":ident,
            "response_record_sha256":hashbytes(file.read_bytes()),
            "http_status":status,"elapsed_ms":duration})
        (out/"provider-progress.json").write_bytes(canonical(progress)+b"\n")
        print("PT08_ORIGINAL_RAW_ARCHIVED",i+1,ident,status,duration,flush=True)
        guard(status==200 and isinstance(raw,dict) and raw.get("success") is not False,
              "PT08_PROVIDER_ERROR_NO_RETRY:"+ident)
    print("PT08_SIX_REAL_CALLS_CAPTURED_NO_GRADE",len(progress["calls_saved"]))

def grade(source,raw_root,out):
    pub,manifest=authenticate(source)
    private=json.loads((Path(source)/"researcher-private/paired-oracle-NOT-FOR_PROVIDER.json").read_text())
    guard(private["schema"]==SCHEMA and
          digest(private)==manifest["private_oracle_sha256"] and
          len(private["private"])==6,
          "PT08_ORACLE_AND_PREREG_MISMATCH")
    oracle={x["request_id"]:x for x in private["private"]}
    output=Path(out)
    guard(not output.exists(),"PT08_GRADE_ALREADY_EXISTS")
    records=[]
    for i,case in enumerate(pub["requests"]):
        f=Path(raw_root)/"raw"/f"{i+1:02d}.json"
        guard(f.exists(),"PT08_REAL_PROVIDER_RESULT_MISSING")
        result=json.loads(f.read_text())
        guard(result.get("request_id")==case["request_id"] and
              result.get("request_sha256")==hashbytes(canonical(case["body"])) and
              result.get("http_status")==200 and
              isinstance(result.get("provider_raw"),dict),
              "PT08_RAW_PROVIDER_HTTP_OR_SHA_INVALID")
        probabilities={k:answer_probability(result["provider_raw"],"path_"+k)
                       for k in CLASSES}
        guard(all(v is not None for v in probabilities.values()),
              "PT08_PROVIDER_ANSWERS_NOT_PARSEABLE")
        exclusions={k for k,v in probabilities.items() if v<=THRESHOLDS["no_lte"]}
        strong_support={k for k,v in probabilities.items() if v>=THRESHOLDS["yes_gte"]}
        possibilities=set(CLASSES)-exclusions
        target=set(oracle[case["request_id"]]["note_based_compatibility"])
        records.append({"request_id":case["request_id"],
           "paired_case":case["paired_case"],"condition":case["condition"],
           "probabilities":probabilities,
           "not_excluded":sorted(possibilities),
           "excluded":sorted(exclusions),
           "strongly_supported":sorted(strong_support),
           "oracle_compatible":sorted(target),
           "false_exclusions":sorted(exclusions&target),
           "false_strong_supports":sorted(strong_support-target),
           "conservative_set_exact":possibilities==target,
           "strong_support_exact":strong_support==target,
           "raw_http_status":result["http_status"],
           "elapsed_ms":result["elapsed_ms"],
           "raw_record_sha256":hashbytes(f.read_bytes()),
           "all_answers_parseable":True})
    pairs=[]
    for i in range(0,6,2):
        base,treat=records[i:i+2]
        guard(base["paired_case"]==treat["paired_case"] and
              base["condition"]=="NUMERIC_ONLY" and
              treat["condition"]=="NUMERIC_PLUS_NOTE","PT08_GRADE_PAIRS_BROKEN")
        pairs.append({"paired_case":base["paired_case"],
          "numeric_only_possible":base["not_excluded"],
          "with_note_possible":treat["not_excluded"],
          "target_with_note":treat["oracle_compatible"],
          "numeric_only_exact":base["conservative_set_exact"],
          "with_note_exact":treat["conservative_set_exact"],
          "note_reduced_possible_set":len(treat["not_excluded"])<len(base["not_excluded"]),
          "note_false_exclusions":treat["false_exclusions"],
          "lost_compatibles_due_to_note":sorted(
              (set(base["not_excluded"])-set(treat["not_excluded"]))&
              set(treat["oracle_compatible"]))})
    summary={
      "schema":"igc-arena-pt08-clef-paired-six-real-results/0.1",
      "model":MODEL,"source_public_sha256":ORIGINAL_PUBLIC_SHA,
      "source_manifest_sha256":digest(manifest),
      "total_real_provider_calls":6,
      "total_new_OpenModelica_simulations":0,
      "automatic_retries":0,
      "response_archived_before_grading":True,
      "number_of_matched_pairs":3,
      "numeric_only_exact_sets":sum(x["conservative_set_exact"] for x in records if x["condition"]=="NUMERIC_ONLY"),
      "with_note_exact_sets":sum(x["conservative_set_exact"] for x in records if x["condition"]=="NUMERIC_PLUS_NOTE"),
      "numeric_only_false_exclusions":sum(len(x["false_exclusions"]) for x in records if x["condition"]=="NUMERIC_ONLY"),
      "with_note_false_exclusions":sum(len(x["false_exclusions"]) for x in records if x["condition"]=="NUMERIC_PLUS_NOTE"),
      "total_raw_elapsed_ms":sum(x["elapsed_ms"] for x in records),
      "hypothetical_saved_candidate_simulations":"NOT_COUNTED_AS_ACTUAL_SAVING",
      "deterministic_numerical_baseline":"THREE_CLASSES_COMPATIBLE_WITH_T2_FOUR_POINTS",
      "deterministic_structured_note_baseline":"AUTHOR_DECLARED_ORACLE_NO_SEMANTIC_INFERENCE_COST",
      "independence":"THREE_TREATMENTS_ONE_SYNTHETIC_SOURCE_NOT_REAL_FIELD_VALIDATION",
      "causal_or_general_superiority":"NOT_ESTABLISHED",
      "decision_if_no_gain":"DO_NOT_PROMOTE_CLEF_AUTOMATICALLY",
      "by_pair":pairs,"by_call":records}
    output.write_bytes(canonical(summary)+b"\n")
    print("PT08_SIX_REAL_RESULTS_GRADED",json.dumps({
       "numeric_exact":summary["numeric_only_exact_sets"],
       "note_exact":summary["with_note_exact_sets"],
       "numeric_false_exclusions":summary["numeric_only_false_exclusions"],
       "note_false_exclusions":summary["with_note_false_exclusions"],
       "calls":6,"pairs":pairs},sort_keys=True))
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("verify","run","grade"))
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path)
    p.add_argument("--raw",type=Path)
    p.add_argument("--auth",default="")
    a=p.parse_args()
    if a.action=="verify":
        pub,m=authenticate(a.source)
        print("PT08_AUTHENTIC_PREDECLARED_REQUESTS",digest(pub),
              len(pub["requests"]))
    elif a.action=="run":
        guard(a.out is not None,"PT08_OUTPUT_REQUIRED")
        run_real(a.source,a.out,a.auth)
    else:
        guard(a.out is not None and a.raw is not None,"PT08_GRADE_OUTPUT_REQUIRED")
        grade(a.source,a.raw,a.out)
if __name__=="__main__":
    main()
