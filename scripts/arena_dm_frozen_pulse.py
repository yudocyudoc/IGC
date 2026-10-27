"""DM frozen-model discriminating-excitation test, no generator or hidden truth.

Use EXACT archived D2 supported and M2 revised Modelica outputs. Change only
the EXTERNAL stimulus amplitude 1.7 -> 4.0 items/h, duration unchanged 2 h.
Numerical outputs are conditional predictions, NOT field truth, holdout, or
method comparison with equivalent data/simulation semantics.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path

D_NAME="D2fit_1b03f4d80336"
M_NAME="MolecularArenaM2_f250c7b99b2c"
D_SHA="c0bec9482f045b9f5cfc652c08d72eb1f0492ecf31865073d530094d26de3750"
M_SHA="8c7dfad2d9e3b4ef2619f4d9bb468bbab5dbd7c3cb3f30801b84f050df85f2f9"
OUT_SCHEMA="igc-dm-frozen-discriminating-excitation/0.1"
D_MARK="  parameter Real pulseRate = 1.7;"
M_MARK="stimulus(y=if time < 2 then 1.7 else 0)"
RATE=4.0
DURATION=2.0
TIMES=(0.,1.,2.,4.,6.,8.)


def require(p,msg):
    if not p: raise ValueError(msg)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def originals(d,m):
    db=d.read_bytes();mb=m.read_bytes()
    require(sha(db)==D_SHA and sha(mb)==M_SHA,"FROZEN_MODEL_BYTES_CHANGED")
    dt=db.decode();mt=mb.decode()
    require(dt.count(D_MARK)==1 and mt.count(M_MARK)==1,
            "SOURCE_STIMULUS_CHANGED")
    require("  parameter Real capacity = 2;" in dt
            and "  parameter Real responseTime = 1;" in dt
            and "maxThroughput=20,responseTime=1.0" in mt
            and mt.count("maxThroughput=20,responseTime=1.0")==2
            and mt.count("  model "+M_NAME)==1,
            "FROZEN_MODEL_MECHANISM_DRIFT")
    require("pulseDuration = 2;" in dt,"PULSE_DURATION_DRIFT")
    return dt,mt


def emit(d,m,out):
    require(not out.exists(),"DM_OUTPUT_EXISTS")
    dt,mt=originals(d,m)
    # Input boundary is the sole authorized alteration; no equations, classes,
    # stock-flow connections or parameter calibration are modified.
    dd=dt.replace(D_MARK,"  parameter Real pulseRate = 4;")
    mm=mt.replace(M_MARK,"stimulus(y=if time < 2 then 4 else 0)")
    require(dd.replace("  parameter Real pulseRate = 4;",D_MARK)==dt
            and mm.replace("stimulus(y=if time < 2 then 4 else 0)",M_MARK)==mt,
            "UNAUTHORIZED_FROZEN_MODEL_EDIT")
    out.mkdir(parents=True)
    (out/(D_NAME+".mo")).write_text(dd)
    (out/"ArenaM2Generated.mo").write_text(mm)
    (out/"d2.mos").write_text("\n".join([
        f'loadFile("/repo/artifacts/dm-frozen/{D_NAME}.mo");',
        f'checkModel({D_NAME});','print(getErrorString());',
        f'simulate({D_NAME},startTime=0,stopTime=8,numberOfIntervals=160,method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="artifacts/dm-frozen/d2");',
        'print(getErrorString());',""
    ]))
    (out/"m2.mos").write_text("\n".join([
        'loadFile("/repo/src/modelica/IGCMolecules.mo");',
        'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");',
        'loadFile("/repo/artifacts/dm-frozen/ArenaM2Generated.mo");',
        f'checkModel(ArenaM2Generated.{M_NAME});','print(getErrorString());',
        f'simulate(ArenaM2Generated.{M_NAME},startTime=0,stopTime=8,numberOfIntervals=160,method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="artifacts/dm-frozen/m2");',
        'print(getErrorString());',""
    ]))
    manifest={
        "schema":OUT_SCHEMA,
        "purpose":"DISCRIMINATE_ALREADY_FROZEN_CAPACITY_REGIMES_NOT_NEW_EVIDENCE_OF_TRUTH",
        "D":"OWN_D2_ONLY_SUPPORTED_STRUCTURE_PREVIOUS_CANDIDATE",
        "M":"OWN_M2_REVISED_STRUCTURE_PREVIOUS_CANDIDATE",
        "D_original_SHA256":"sha256:"+D_SHA,
        "M_original_SHA256":"sha256:"+M_SHA,
        "D_amplitude_only_SHA256":"sha256:"+sha(dd.encode()),
        "M_amplitude_only_SHA256":"sha256:"+sha(mm.encode()),
        "stimulation":{"type":"pulse","rate_items_per_hour":RATE,"duration_hours":DURATION},
        "reason_predeclared":"4 exceeds D nominal throughput 2 but not M queue throughput 20",
        "observed_common_outcome":"cumulative_delivered",
        "frozen_graphs":True,"parameter_fit":False,
        "source_original_runs":{"D2":40284851680,"M2":40283319745},
        "simulation":{"method":"dassl","intervals":160,"stopTime":8,
                      "D_openmodelica":"1.27.1","M_openmodelica":"1.26.5"},
        "expected_possible_difference":"CAPACITY_SATURATION_NOT_PREJUDGED_CAUSAL_TRUTH",
        "t_sample_hours":TIMES,
        "a_priori_min_predicted_separation_items":0.05,
        "heldout_real_world":"NOT_RUN",
        "not_a_synthetic_world_truth_comparison":True,
    }
    (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    return manifest


def trace(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    require(len(rows)>100,"MISSING_REAL_MODELICA_SAMPLES")
    unique=[]
    for x in rows:
        t=float(x["time"])
        require(math.isfinite(t) and (not unique or t>=unique[-1][0]-1e-8),
                "NONMONOTONE_SAMPLES")
        if unique and abs(unique[-1][0]-t)<1e-8:unique[-1]=(t,x)
        else:unique.append((t,x))
    return unique


def value(row,name):
    require(name in row,"MISSING_COLUMN:"+name)
    v=float(row[name])
    require(math.isfinite(v),"NONFINITE_COLUMN:"+name)
    return v


def sample(rows,t):
    hit=[x for x in rows if abs(x[0]-t)<1e-7]
    require(len(hit)==1,"NO_UNIQUE_SAMPLE_TIME:"+str(t))
    return hit[0][1]


def verify(out,d,m):
    dt,mt=originals(d,m)
    manifest=json.loads((out/"manifest.json").read_text())
    require(manifest["schema"]==OUT_SCHEMA and
            manifest["D_original_SHA256"]=="sha256:"+D_SHA and
            manifest["M_original_SHA256"]=="sha256:"+M_SHA and
            manifest["stimulation"]=={
                "type":"pulse","rate_items_per_hour":RATE,"duration_hours":DURATION},
            "DM_PROTOCOL_CHANGED")
    require((out/(D_NAME+".mo")).read_text()==dt.replace(D_MARK,"  parameter Real pulseRate = 4;")
            and (out/"ArenaM2Generated.mo").read_text()==mt.replace(M_MARK,"stimulus(y=if time < 2 then 4 else 0)"),
            "MODEL_MECHANISM_EDITED_AFTER_FREEZE")
    drows=trace(out/"d2_res.csv")
    mrows=trace(out/"m2_res.csv")
    comparisons=[]
    maxdev={"D":0.0,"M":0.0}
    for t in TIMES:
        dr=sample(drows,t);mr=sample(mrows,t)
        delivered_D=value(dr,"delivered")
        delivered_M=value(mr,"deliveredTotal")
        balance_D=value(dr,"s1")+value(dr,"s2")+delivered_D+value(dr,"lost")
        balance_M=value(mr,"preparation0.waiting")+value(mr,"dispatch0.waiting")+delivered_M
        expected=RATE*min(t,DURATION)
        maxdev["D"]=max(maxdev["D"],abs(balance_D-expected))
        maxdev["M"]=max(maxdev["M"],abs(balance_M-expected))
        comparisons.append({
            "t_hours":t,"D_delivered_items":delivered_D,
            "M_delivered_items":delivered_M,
            "difference_M_minus_D_items":delivered_M-delivered_D,
            "D_material_balance":balance_D,"M_material_balance":balance_M,
            "expected_input_items":expected
        })
    require(max(maxdev.values())<0.025,"DM_COMMON_PULSE_MASS_OR_NUMERICAL_MISMATCH")
    diffs=[abs(x["difference_M_minus_D_items"]) for x in comparisons if x["t_hours"]>=2]
    separated=max(diffs)>manifest["a_priori_min_predicted_separation_items"]
    result={
        "schema":"igc-dm-frozen-discriminating-excitation-outcome/0.1",
        "manifest_sha256":"sha256:"+sha((out/"manifest.json").read_bytes()),
        "status":"G2_BOTH_FROZEN_MODELS_REAL_OPENMODELICA_AND_MASS_BALANCED",
        "prediction_discriminated_at_some_predeclared_time":separated,
        "predeclared_threshold_items":manifest["a_priori_min_predicted_separation_items"],
        "maximum_absolute_gap_items":max(diffs),
        "mass_balance_max_items":maxdev,
        "trajectory":comparisons,
        "same_external_stimulus":True,
        "different_pinned_solver_versions":True,
        "no_observations_to_rank_accuracy":True,
        "winner":None,"causal_truth":"NOT_IDENTIFIED",
        "g3_predictive_validation":"NOT_RUN","heldout":"NOT_RUN",
        "interpretation":"DIFFERENT_FROZEN_MODELS_PREDICT_DIFFERENT_DELIVERIES_WHEN_CAPACITY_STRESSED",
    }
    (out/"comparison.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("operation",choices=("emit","verify"))
    p.add_argument("--d",type=Path,required=True)
    p.add_argument("--m",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    v=emit(a.d,a.m,a.out) if a.operation=="emit" else verify(a.out,a.d,a.m)
    print(json.dumps({
        "status":v.get("status",v["schema"]),
        "separated":v.get("prediction_discriminated_at_some_predeclared_time"),
        "max_gap":v.get("maximum_absolute_gap_items"),"no_gold":True
    }))

if __name__=="__main__":main()
