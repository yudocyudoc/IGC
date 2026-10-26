"""Two bounded, independently graded CLEF pilots on FROZEN Short E1 material paths.

Pilot A: Clef versus deterministic original-M3 RMSE policy, same numeric
construction observations and already simulated candidates.
Pilot B: Clef on operational-language evidence versus a predeclared lexical
rule baseline given the SAME notes. No numeric predictions are fabricated.

Provider-facing requests contain neither the labels nor graders. The real
provider is called ONLY in the one-shot opt-in GitHub Actions step. Each
response is archived BEFORE any interpretation. Never change E1/M3, D or B.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from scripts.arena_m3_select import decide

MODEL="@cf/cloudflare/clef"
SCHEMA="igc-clef-two-small-pilots/0.1"
RUNTIME_AUTH="RUN_ONCE_CLEF_TWO_PILOTS_20261026"
NAMES=("C00","C01","C02")
DESCRIPTIONS={
    "C00":"Preparation queue -> dispatch queue -> final delivered counter. No physical holding station after dispatch.",
    "C01":"Preparation queue -> dispatch queue -> exactly one serial physical holding station -> final delivered counter.",
    "C02":"Preparation queue -> dispatch queue -> exactly two successive serial physical holding stations -> final delivered counter.",
}
TIMES=(0,1,2,3)
NOISE=(0,.002,-.003,.004)
EPS=.02
POLICY_P_YES=.70
POLICY_P_NO=.30
MAX_REAL_CALLS=17


def require(condition,why):
    if not condition: raise ValueError(why)


def canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)


def sha(x):
    return "sha256:"+hashlib.sha256((x if isinstance(x,bytes) else canonical(x).encode())).hexdigest()


def rows(csvfile):
    with open(csvfile,encoding="utf-8-sig",newline="") as f:
        result=list(csv.DictReader(f))
    require(len(result)>100,"MISSING_ORIGINAL_M3_SOLVER_CSV")
    return result


def sample(rs,ts):
    out=[]
    for t in ts:
        hit=[float(x["deliveredTotal"]) for x in rs if abs(float(x["time"])-t)<1e-7]
        require(hit and max(hit)-min(hit)<1e-5,"AMBIGUOUS_M3_REAL_OMC_TIME")
        out.append(hit[-1])
    return out


def numerical_cases(pred,source):
    a=[float(x["delivered"]) for x in source["alpha"]["construction_observations"]]
    b=[float(x["delivered"]) for x in source["beta"]["construction_observations"]]
    g=[max(0.,x+n) for x,n in zip(pred["C02"],NOISE)]
    avg=[(x+y)/2 for x,y in zip(pred["C00"],pred["C01"])]
    # X06 is ambiguous, because its uncertainty interval encloses two paths.
    # X04 is out-of-catalog; X05 is insufficient.
    return [
      ("N01",a,EPS,"REUSE_ARCHIVED_M3_ALPHA"),
      ("N02",b,EPS,"REUSE_ARCHIVED_M3_BETA"),
      ("N03",g,EPS,"C02_REAL_OMC_PREDICTION_PLUS_FIXED_NOISE"),
      ("N04",[0.,0.,0.,0.],EPS,"OUT_OF_CATALOG_ALL_ZERO"),
      ("N05",[],EPS,"INSUFFICIENT_NO_OBSERVED_TIMES"),
      ("N06",avg,.76,"MIXED_CURVE_WIDE_ERROR_ALLOW_TWO_STRUCTURES"),
      ("N07",a,3.0,"VERY_WIDE_ERROR_ALL_THREE_COMPATIBLE"),
      ("N08",[0.,6.,9.,13.],EPS,"OUT_OF_FAMILY_HIGH_TRAJECTORY"),
    ]


def semantic_cases():
    # All are SYNTHETIC, hand-authored operating notes, not cafeteria field facts.
    # X names do not disclose labels; graders receive fixed judgments separately.
    return [
      ("S01","An exhaustive shift audit says every finished drink is handed over immediately by dispatch to the guest; no completed item is ever held between dispatch and the final delivery counter.",("C00",)),
      ("S02","An exhaustive handoff trace follows each finished drink: dispatch puts it into exactly one downstream holding rack; later it is removed from that rack and handed to the guest. No other post-dispatch holding stage exists.",("C01",)),
      ("S03","An exhaustive trace follows each completed item: dispatch places it in the first holding rack, staff transfer it to a second rack, and only then it is handed to the customer. Exactly these two serial storage stages exist.",("C02",)),
      ("S04","An electronic status screen shows which beverage is ready, but no observer watched where the physical drinks go after dispatch.",("C00","C01","C02")),
      ("S05","A complete map reveals that dispatch splits finished orders between two separate physical holding stations in PARALLEL and both later feed the delivery counter. Neither station feeds the other.",()),
      ("S06","Two reliable witnesses disagree: one observed a single physical waiting stage after dispatch and the other observed two serial waiting stages. Both insist at least one such stage exists, but timing and which witness is correct are unknown.",("C01","C02")),
      ("S07","Every completed order makes one stop on a trolley beside the pickup hatch; none leaves the trolley without being claimed. The trolley is the only place where items accumulate between the dispatch handoff and final pickup.",("C01",)),
      ("S08","The queue displayed on a tablet grows during rush hour. No material stock or delivery-stage movements were observed, and the tablet could be reporting, rather than storing, drinks.",("C00","C01","C02")),
      ("S09","From dispatch, each drink goes to a single intermediate shelf, stays until called, and then goes to final collection; the observer explicitly ruled out any additional intermediate shelf.",("C01",)),
    ]


def compatibility(points,curves,tolerance):
    if not points:return list(NAMES)
    result=[]
    for n in NAMES:
        if all(abs(p["delivered"]-curves[n][TIMES.index(p["t"])])<=tolerance+1e-9
               for p in points):
            result.append(n)
    return result


def policy_m3(points,curves):
    if len(points)!=4:return {"status":"ABSTAIN","chosen_id":None,"reason":"INSUFFICIENT"}
    scores=[]
    for i,n in enumerate(NAMES):
        err=math.sqrt(sum((p["delivered"]-curves[n][j])**2
                          for j,p in enumerate(points))/4)
        scores.append({"id":n,"rmse_items":err,"material_queues":i+2})
    d=decide(scores)
    return {"status":d["status"],"chosen_id":d["chosen_id"],"reason":d["reason"],
            "margin":d["margin"],"scores":scores}


def lexical_baseline(note):
    """Predeclared weak literal-pattern baseline; NOT a substitute for a human."""
    s=note.lower()
    if "in parallel" in s:return []
    if "two serial storage stages" in s:return ["C02"]
    if "exactly one downstream holding rack" in s:return ["C01"]
    if "handed over immediately" in s:return ["C00"]
    return list(NAMES)


def prepare(source_dir,output):
    require(not output.exists(),"EXPERIMENT_ALREADY_EXISTS")
    out=output
    out.mkdir(parents=True)
    (out/"raw").mkdir()
    manifest=json.loads((source_dir/"candidate-manifest.json").read_text())
    require(manifest["arm_id"]=="M" and
            [x["id"] for x in manifest["candidates"]]==list(NAMES) and
            manifest["universe_count"]==6 and
            manifest["observable_equivalence_classes"]==3,
            "NOT_AUTHENTIC_M3_FIXED_REPERTOIRE")
    curves={n:sample(rows(source_dir/"candidates"/(n.lower()+"_res.csv")),TIMES)
            for n in NAMES}
    cs={
        "alpha":json.loads((source_dir/"cases/case-alpha.json").read_text()),
        "beta":json.loads((source_dir/"cases/case-beta.json").read_text()),
    }
    candidates=[{"id":n,"structure":DESCRIPTIONS[n],
                 "material_queue_count":i+2}
                for i,n in enumerate(NAMES)]
    public=[]
    key={}
    benchmarks=[]
    for ident,vals,tol,origin in numerical_cases(curves,cs):
        pts=[{"t":TIMES[i],"delivered":v} for i,v in enumerate(vals)]
        supported=compatibility(pts,curves,tol)
        key[ident]={"track":"numeric","support":supported,"source":origin,
                    "epistemic":"ONLY_COMPATIBILITY_WITH_FIXED_MODEL_TRACES"}
        baseline=policy_m3(pts,curves)
        benchmarks.append({"case_id":ident,"M3_fixed_policy":baseline,
                           "interval_compatibility":supported})
        state={
            "domain":"system_dynamics_closed_short_e1_material_paths",
            "task":"For EACH graph decide whether observations CONTRADICT the graph. No graph should be ruled out merely because another fits better. Missing data do not eliminate graphs.",
            "candidate_graphs":candidates,
            "real_OpenModelica_candidate_cumulative_deliveries_at_times":{
                n:dict(zip((str(t) for t in TIMES),curves[n])) for n in NAMES
            },
            "construction_observations":pts,
            "absolute_measurement_error_per_point_items":tol,
            "note":"Each true cumulative delivery could be within its stated absolute error; no generator labels, no reserved times."
        }
        public.append({"case_id":ident,"track":"numeric","state":state,
                       "candidate_order":list(NAMES)})
    for ident,note,correct in semantic_cases():
        key[ident]={"track":"semantic","support":list(correct),
                    "source":"AUTHOR_DECLARED_SYNTHETIC_EXHAUSTIVE_OR_INCOMPLETE_FACTS",
                    "epistemic":"MATERIAL_GRAPH_CONSISTENCY_NOT_REAL_CAUSAL_TRUTH"}
        benchmarks.append({"case_id":ident,"matched_text_lexical_baseline":lexical_baseline(note)})
        order=list(("C02","C00","C01") if ident=="S09" else NAMES)
        state={
           "domain":"operational_structure_consistency_not_curve_fitting",
           "task":"Which candidate material paths are contradicted by the notes? A candidate remains POSSIBLE unless evidence rules it out. Do not infer the absence of a buffer from absence of mention. Explicit exhaustive observations can rule paths out.",
           "operational_notes":note,
           "terms":"A material holding stage is a physical stock of completed items AFTER dispatch and BEFORE final delivery. A display-only screen is not a material stock. Serial and parallel are distinct.",
           "candidate_graphs":[next(c for c in candidates if c["id"]==name) for name in order],
           "construction_numeric_curves":"NOT_PROVIDED_IN_THIS_SEMANTIC_TEST"
        }
        public.append({"case_id":ident,"track":"semantic","state":state,
                       "candidate_order":order})
    require(len(public)==MAX_REAL_CALLS,"UNEXPECTED_CALL_BUDGET")
    for row in public:
        order=row["candidate_order"]
        state=row["state"]
        questions={}
        for name in order:
            questions["path_"+name]={
               "type":"noul",
               "instructions":(
                 "Is material path "+name+" STILL PHYSICALLY POSSIBLE given only the "+
                 "observations and restrictions in the state? Answer YES if it is not "+
                 "contradicted, NO if there is evidence specifically ruling it out. "+
                 "Judge each path independently, without selecting a forced winner. "+
                 "Absence of evidence is not evidence of absence. The probability is "+
                 "a judgment score, not a calibrated causal likelihood."
               )
            }
        row["body"]={"model":"clef","state":canonical(state),"questions":questions}
        del row["state"]
    # Critical: public provider requests do not include any grader key or answer.
    public_doc={"schema":SCHEMA,"model":MODEL,"cases":public,
      "max_provider_calls":MAX_REAL_CALLS,"provider_mode":"GITHUB_MARKER_SINGLE_RUN_NO_RETRY",
      "response_interpretation_predeclared":{"compatible_if_p_gte":POLICY_P_YES,
         "incompatible_if_p_lte":POLICY_P_NO,
         "uncertain_between_thresholds":"RETAIN_POSSIBILITY_NO_FALSE_EXCLUSION"},
      "source":"ORIGINAL_M3_REAL_OMC_TRACES_AND_SYNTHETIC_OPERATING_NOTES",
      "no_truth_in_provider_state":True,"case_order_fixed":True,
      "no_other_arm_outputs":True}
    (out/"public.json").write_text(json.dumps(public_doc,indent=2,ensure_ascii=False)+"\n")
    (out/"private-oracle.json").write_text(json.dumps({
      "schema":"igc-clef-pilots-sealed-evaluator/0.1","cases":key,
      "cannot_use_to_prepare_provider_prompts":True},indent=2,ensure_ascii=False)+"\n")
    (out/"deterministic-baselines.json").write_text(json.dumps(benchmarks,indent=2,ensure_ascii=False)+"\n")
    (out/"freeze.json").write_text(json.dumps({
      "schema":SCHEMA,"source_manifest_sha256":sha((source_dir/"candidate-manifest.json").read_bytes()),
      "source_csv_sha256":{n:sha((source_dir/"candidates"/(n.lower()+"_res.csv")).read_bytes()) for n in NAMES},
      "source_case_sha256":{n:sha((source_dir/"cases"/("case-"+n+".json")).read_bytes()) for n in ("alpha","beta")},
      "public_requests_sha256":sha(public_doc),"provider_calls_budget":MAX_REAL_CALLS,
      "no_numeric_holdout":True,"simulations_already_archived":True,
      "experimental_repetition":False
    },indent=2)+"\n")
    print("CLEF_TWO_PILOTS_FROZEN",len(public),"8_numeric_9_semantic",sha(public_doc))


def answer_probability(raw,question):
    if not isinstance(raw,dict) or raw.get("success") is False:return None
    result=raw.get("result",raw)
    if not isinstance(result,dict):return None
    answers=result.get("answers")
    if not isinstance(answers,dict):return None
    val=answers.get(question)
    if isinstance(val,(int,float)) and not isinstance(val,bool):
        p=float(val)
    elif isinstance(val,dict):
        p=None
        for field in ("probability","p_true","probability_true","yes_probability","probability_yes"):
            if isinstance(val.get(field),(float,int)):
                p=float(val[field]);break
        if p is None:
            probs=val.get("probabilities")
            if isinstance(probs,dict):
                for field in ("true","yes","YES"):
                    if isinstance(probs.get(field),(float,int)):
                        p=float(probs[field]);break
    else:return None
    return p if p is not None and math.isfinite(p) and 0<=p<=1 else None


def run_real(out,authorization):
    require(authorization==RUNTIME_AUTH,"ONE_USE_AUTHORIZATION_MISSING")
    data=json.loads((out/"public.json").read_text())
    require(data["schema"]==SCHEMA and len(data["cases"])==MAX_REAL_CALLS,
            "NOT_FROZEN_PROVIDER_REQUESTS")
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    require(re.fullmatch("[0-9a-fA-F]{32}",account) is not None and bool(token),
            "NO_REAL_PROVIDER_CREDENTIALS")
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    index=[]
    for idx,case in enumerate(data["cases"]):
        target=out/"raw"/(case["case_id"]+".json")
        require(not target.exists(),"ONE_SHOT_RESPONSE_ALREADY_EXISTS")
        req=case["body"]
        started=time.monotonic()
        request=Request(url,data=canonical(req).encode(),method="POST",
                        headers={"Authorization":"Bearer "+token,
                                 "Content-Type":"application/json",
                                 "Accept":"application/json"})
        httpcode=None
        try:
            with urlopen(request,timeout=65) as response:
                httpcode=response.status
                body=response.read()
        except Exception as err:
            # Intentional no retry; earlier responses must remain archived.
            target.write_text(json.dumps({"transport_failure":type(err).__name__,
                 "request_sha256":sha(req),"run_index":idx})+"\n")
            raise RuntimeError("CLEF_ONE_SHOT_PROVIDER_FAILED_NO_RETRY:"+case["case_id"]) from None
        elapsed=int((time.monotonic()-started)*1000)
        try:raw=json.loads(body)
        except Exception:
            target.write_text(json.dumps({"non_json_body_sha256":sha(body),
                                "http_code":httpcode,"run_index":idx})+"\n")
            raise RuntimeError("CLEF_NON_JSON_NO_RETRY:"+case["case_id"]) from None
        target.write_text(json.dumps({"case_id":case["case_id"],"http_status":httpcode,
                  "latency_ms":elapsed,"request_sha256":sha(req),
                  "provider_raw":raw},indent=2,ensure_ascii=False)+"\n")
        index.append({"case_id":case["case_id"],"request_sha256":sha(req),
                      "response_sha256":sha(raw),"latency_ms":elapsed,"http_status":httpcode})
        (out/"provider-progress.json").write_text(json.dumps({
           "completed":len(index),"planned":MAX_REAL_CALLS,"calls":index},indent=2)+"\n")
        print("CLEF_REAL_CAPTURED",idx+1,MAX_REAL_CALLS,case["case_id"],httpcode,elapsed,flush=True)
        require(httpcode==200 and raw.get("success") is not False,
                "CLEF_PROVIDER_RESPONSE_ERROR_NO_RETRY")
    print("CLEF_REAL_ALL_CALLS_CAPTURED",len(index))


def grade(out):
    pub=json.loads((out/"public.json").read_text())
    oracle=json.loads((out/"private-oracle.json").read_text())
    bases={x["case_id"]:x for x in json.loads((out/"deterministic-baselines.json").read_text())}
    require(len(pub["cases"])==MAX_REAL_CALLS,"PROTOCOL_DRIFT")
    reports=[]
    for c in pub["cases"]:
        name=c["case_id"]
        f=out/"raw"/(name+".json")
        require(f.exists(),"CLEF_REAL_RESPONSE_NOT_PRESENT:"+name)
        raw=json.loads(f.read_text())
        require(raw.get("request_sha256")==sha(c["body"]) and
                raw.get("http_status")==200 and
                isinstance(raw.get("provider_raw"),dict),
                "PROVIDER_RESPONSE_OR_REQUEST_MISSING")
        scores={k:answer_probability(raw["provider_raw"],"path_"+k) for k in NAMES}
        true=set(oracle["cases"][name]["support"])
        included={k for k,v in scores.items() if v is not None and v>=POLICY_P_YES}
        excluded={k for k,v in scores.items() if v is not None and v<=POLICY_P_NO}
        unknown=set(NAMES)-included-excluded
        possible=set(NAMES)-excluded
        reports.append({
          "case_id":name,"track":c["track"],
          "oracle_support":sorted(true),
          "probabilities_compatible":scores,
          "possible_not_excluded":sorted(possible),
          "strongly_included":sorted(included),
          "strongly_excluded":sorted(excluded),
          "uncertain_or_invalid":sorted(unknown),
          "false_exclusions":sorted(excluded&true),
          "false_strong_supports":sorted(included-true),
          "compatible_set_exact":included==true,
          "conservative_possible_set_exact":possible==true,
          "all_three_answers_parseable":all(x is not None for x in scores.values()),
          "baseline":bases[name],
          "response_record_sha256":sha(f.read_bytes())
        })
    summary={"schema":"igc-clef-two-small-pilots-real-results/0.1",
             "model":MODEL,"real_calls_archived":len(reports),
             "policy":{"yes_gte":POLICY_P_YES,"no_lte":POLICY_P_NO},
             "hypothesis":"PROBABILITIES_ARE_UNCALIBRATED_JUDGMENTS",
             "tracks":{},
             "caveats":["small hand-built synthetic notes","M3 original tolerances fixed and not tuned to broad-error cases",
                 "raw response saved ahead of grading",
                 "semantic lexical baseline is only a simple weak heuristic",
                 "real cafeteria observations not used","no independent physical mechanism world"],
             "by_case":reports}
    for track in ("numeric","semantic"):
        rs=[x for x in reports if x["track"]==track]
        summary["tracks"][track]={
          "cases":len(rs),
          "parseable":sum(x["all_three_answers_parseable"] for x in rs),
          "exact_strong_support_sets":sum(x["compatible_set_exact"] for x in rs),
          "exact_conservative_sets":sum(x["conservative_possible_set_exact"] for x in rs),
          "false_exclusions":sum(len(x["false_exclusions"]) for x in rs),
          "false_strong_supports":sum(len(x["false_strong_supports"]) for x in rs),
        }
    (out/"results.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print("CLEF_TWO_PILOTS_GRADED",json.dumps(summary["tracks"],sort_keys=True))
    return summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","run","grade"))
    p.add_argument("--source",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--auth",default="")
    args=p.parse_args()
    if args.command=="prepare":
        require(args.source is not None,"SOURCE_REQUIRED")
        prepare(args.source,args.out)
    elif args.command=="run":run_real(args.out,args.auth)
    else:grade(args.out)
if __name__=="__main__": main()
