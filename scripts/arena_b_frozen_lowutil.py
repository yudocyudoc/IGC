"""Buffalo B2 versus B3 frozen mechanism probe, LOW arrivals, no LLM.

The only mutation is the original exogenous input variable "arrival rate":
1.7 -> 0.4 items/hour. Keep B2/B3 endogenous equations and relationships
byte-equivalent after reversing that one literal. Run both through the existing
strict Buffalo-native -> Modelica adapter under the SAME pinned OMC solver.
No new observed outcome, causal certification, or model fitting.
"""
from __future__ import annotations
import argparse,copy,csv,hashlib,json,math
from pathlib import Path
from scripts.arena_b_native_to_modelica import generate

B2="d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9"
B3="dfe45d3128bbf9aaa91a2d0be0028f4b8be29610b42d9114e4dae09fc4a14c2b"
RATE=0.4
TIMES=(0.,.25,.5,.75,1.,1.5,2.,3.,4.,6.,8.)
SCHEMA="igc-b-frozen-low-arrivals-linear-versus-square/0.1"

def check(ok,msg):
    if not ok:raise ValueError(msg)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def original(path,expected):
    b=path.read_bytes()
    check(digest(b)==expected,"ORIGINAL_BUFFALO_NATIVE_CHANGED")
    doc=json.loads(b)
    vars=doc["model"]["variables"]
    src=[v for v in vars if v["name"]=="arrival rate"]
    check(len(src)==1 and src[0]["equation"]=="1.7","INPUT_RATE_LITERAL_CHANGED")
    check(any(v["name"]=="completions" for v in vars),"NO_COMPLETION_FLOW")
    return doc

def clone(doc):
    probe=copy.deepcopy(doc)
    src=next(v for v in probe["model"]["variables"] if v["name"]=="arrival rate")
    src["equation"]="0.4"
    assert probe["model"]["specs"]==doc["model"]["specs"]
    restored=copy.deepcopy(probe)
    next(v for v in restored["model"]["variables"] if v["name"]=="arrival rate")["equation"]="1.7"
    check(restored==doc,"PROBE_ALTERED_ENDOGENOUS_STRUCTURE")
    return probe

def emit(path_b2,path_b3,out):
    check(not out.exists(),"PROBE_OUT_EXISTS")
    a=original(path_b2,B2);b=original(path_b3,B3)
    av={v["name"]:v for v in a["model"]["variables"]}
    bv={v["name"]:v for v in b["model"]["variables"]}
    check(av["completions"]["equation"]=="completion_capacity * capacity_utilization"
          and bv["completions"]["equation"]=="completion_capacity"
          and av["nominal capacity"]["equation"]==bv["nominal capacity"]["equation"]=="0.6",
          "B2_B3_FROZEN_CORE_MECHANISMS_CHANGED")
    out.mkdir(parents=True)
    info=[]
    commands=[]
    for label,doc in (("B2",a),("B3",b)):
        altered=clone(doc)
        name,code,translation=generate(altered)
        (out/(name+".mo")).write_text(code)
        commands.extend([
          f'loadFile("/repo/artifacts/b-lowutil/{name}.mo");',
          'print(getErrorString());',f'checkModel({name});',
          'print(getErrorString());',
          f'simulate({name},startTime=0,stopTime=8,numberOfIntervals=64,method="euler",outputFormat="csv",fileNamePrefix="artifacts/b-lowutil/{label.lower()}");',
          'print(getErrorString());'
        ])
        info.append({"id":label,"name":name,"omc_file":name+".mo",
                     "modelica_sha256":"sha256:"+digest(code.encode()),
                     "source_sha256":"sha256:"+(B2 if label=="B2" else B3),
                     "only_exogenous_arrival_rate_changed":True,
                     "adapter_translation":translation})
    (out/"simulate.mos").write_text("\n".join(commands)+"\n")
    manifest={
      "schema":SCHEMA,"mode":"FROZEN_EXOGENOUS_LOWER_RATE",
      "arm_id":"B","two_models":info,
      "stimulus":{"rate_items_per_hour":RATE,"pulse_duration_hours":2.},
      "reason":"arrival lower than nominal capacity 0.6 should extend partial utilization, where linear and squared multiplier differ",
      "preregistered_early_window_hours":[0,2],
      "predeclared_min_divergence_items":0.025,
      "native_parent_sha":[B2,B3],
      "engine":"PINNED_OPENMODELICA_1_27_1_EULER_DT_0_125",
      "parameters_reestimated":False,"equations_changed":False,
      "no_field_observations":True,"heldout_status":"NOT_RUN",
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as fd:
        rows=list(csv.DictReader(fd))
    check(len(rows)>60,"MISSING_REAL_OMC_TRACE")
    unique=[]
    for x in rows:
        t=float(x["time"])
        check(math.isfinite(t) and (not unique or t>=unique[-1][0]-1e-9),
              "BACKWARDS_TIME")
        if unique and abs(unique[-1][0]-t)<1e-9:unique[-1]=(t,x)
        else:unique.append((t,x))
    return unique

def value(r,k):
    check(k in r,"MISSING_OMC_SIGNAL:"+k)
    x=float(r[k])
    check(math.isfinite(x),"NONFINITE_SIGNAL:"+k)
    return x

def at(rows,t):
    hits=[r for x,r in rows if abs(x-t)<1e-8]
    check(len(hits)==1,"MISSING_SAMPLE:"+str(t))
    return hits[0]

def verify(out):
    doc=json.loads((out/"manifest.json").read_text())
    check(doc.get("schema")==SCHEMA and
          doc["stimulus"]=={"rate_items_per_hour":RATE,"pulse_duration_hours":2.0}
          and doc["native_parent_sha"]==[B2,B3]
          and doc["parameters_reestimated"] is False
          and doc["equations_changed"] is False,"PROTOCOL_CHANGED")
    rows={k:read(out/(k.lower()+"_res.csv")) for k in ("B2","B3")}
    result=[]
    maxbal={"B2":0.0,"B3":0.0}
    for t in TIMES:
        obs={}
        for k in rows:
            r=at(rows[k],t)
            delivered=value(r,"delivered_work")
            pending=value(r,"pending_work")
            input_total=RATE*min(t,2.)
            maxbal[k]=max(maxbal[k],abs(delivered+pending-input_total))
            obs[k]=delivered
        result.append({"t_hours":t,"B2_delivered":obs["B2"],
                       "B3_delivered":obs["B3"],
                       "difference_B3_minus_B2":obs["B3"]-obs["B2"]})
    check(max(maxbal.values())<0.03,"NOT_SAME_INPUT_OR_CONSERVATION_FAILED")
    early=[abs(r["difference_B3_minus_B2"]) for r in result if r["t_hours"]<=2]
    outp={
      "schema":"igc-b-frozen-low-util-prediction-contrast/0.1",
      "g2":"PASS_REAL_OMC_BOTH_FROZEN_MODELS",
      "heldout":"NOT_RUN",
      "predictive_accuracy":"UNKNOWN_NO_EXTERNAL_OBSERVATIONS",
      "causal_identification":"NOT_DEMONSTRATED",
      "partial_utilization_probe":True,
      "predeclared_threshold":doc["predeclared_min_divergence_items"],
      "max_early_absolute_gap_items":max(early),
      "early_predictions_separate":max(early)>doc["predeclared_min_divergence_items"],
      "material_balance_max_items":maxbal,
      "trajectory":result,
      "native_b2_sha256":"sha256:"+B2,
      "native_b3_sha256":"sha256:"+B3,
      "only_input_rate_changed":True,
      "not_a_model_ranking":True,
    }
    (out/"comparison.json").write_text(json.dumps(outp,indent=2)+"\n")
    return outp

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("emit","verify"))
    p.add_argument("--b2",type=Path)
    p.add_argument("--b3",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.command=="emit":
        check(a.b2 is not None and a.b3 is not None,"MISSING_ORIGINAL_NATIVE")
        result=emit(a.b2,a.b3,a.out)
    else:result=verify(a.out)
    print(json.dumps({"status":result["schema"],
        "gap_early":result.get("max_early_absolute_gap_items"),
        "discriminated":result.get("early_predictions_separate"),
        "without_truth":True}))
if __name__=="__main__":main()
