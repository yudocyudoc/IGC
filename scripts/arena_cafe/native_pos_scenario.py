"""A1 CAF native D/E1 scenario driven by *public* POS arrival timestamps.

Native engineering benchmark ONLY: positive predeclared nominal parameters,
no calibration, no model selection or causal inference. The only alterations to
original generated Modelica are the EXTERNAL stimulus expression and package.
No EV01/DES import and no inference from evaluator-private physical parameters.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
from pathlib import Path
import json
import hashlib
import sys

from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-cafe-a1-pos-native-scenario/0.1"
BIN_MIN=Q(1,2)
# Nominal benchmark chosen BEFORE comparing any simulated curves.
# 20 orders/hour and 0.5 hour per stock, matching the *declared E1
# registry*, not a measurement of the private DES stations.
D_NOMINAL={"capacity":20/60,"response_time":30.0,"loss_time":30.0}


def bins_from_pos(visible,condition):
    validate_a1_visible(visible,condition)
    cutoff=Q(visible["observability"]["cutoff_minutes_exact"])
    need(cutoff % BIN_MIN == 0 and cutoff <= 120,
         "A1_NATIVE_CUTOFF_NOT_REPRESENTABLE")
    arrivals=[Q(x["t_minutes_exact"]) for x in
              visible["construction"]["pos_arrival_events"]]
    bins=[]
    for i in range(int(cutoff/BIN_MIN)):
        start=i*BIN_MIN;end=start+BIN_MIN
        n=sum(start<=t<end for t in arrivals)
        bins.append({"start_minutes_exact":str(start),
                     "end_minutes_exact":str(end),
                     "orders":n,
                     "rate_orders_per_minute_exact":str(Q(n,1)/BIN_MIN)})
    need(sum(row["orders"] for row in bins)==len(arrivals),
         "A1_NATIVE_ARRIVAL_MASS_LOST")
    need(len(arrivals)==visible["construction"]["observation_series"][-1][
        "orders_created_cumulative"],"A1_NATIVE_POS_PARITY")
    return bins


def expression(bins,scale):
    # Piecewise-constant *reconstruction* of observed point events:
    # place each observed event's unit mass uniformly over its 0.5-min bin.
    # This is an explicit approximation, NOT a known instantaneous arrival
    # rate and NOT the secret generator's input process.
    terms=[]
    for row in bins:
        t=float(Q(row["end_minutes_exact"])/scale)
        v=float(Q(row["rate_orders_per_minute_exact"])*scale)
        terms.append("if time < "+format(t,".17g")+
                     " then "+format(v,".17g")+" else ")
    return "".join(terms)+"0"


def _make_d(bins):
    from scripts.arena_d_v01 import modelica, topology
    structure=topology(2,False)  # D2 original own stock-flow grammar
    candidate={"structure":structure,"structure_hash":digest(structure),
               "nominal_parameters":dict(D_NOMINAL),
               "parameter_status":"EXPLICIT_ENGINEERING_ASSUMPTIONS_NOT_ESTIMATED"}
    source=modelica(candidate,{"kind":"pulse","rate":1.0,"duration":1.0})
    original="inputRate = if time < pulseDuration then pulseRate else 0;"
    need(source.count(original)==1,"A1_NATIVE_D_SOURCE_DRIFT")
    source=source.replace(original,"inputRate = "+expression(bins,Q(1))+";")
    need(source.count("der(")==4,"A1_NATIVE_D_DIFFERENTIAL_GRAMMAR_CHANGED")
    return {"name":"DStockFlow_"+candidate["structure_hash"][7:19],
            "modelica":source,
            "candidate":{"arm_id":"D",**candidate},
            "time_unit":"minute",
            "rate_unit":"orders/minute"}


def _make_m(bins):
    from scripts.arena_m_visible_pulse import backend, composer, choose_one, stimulus_only_replace
    from scripts.arena_m_short_e1 import REGISTRIES
    registry=Path("experiments/e1/registry.base.json").resolve()
    need(registry in REGISTRIES,"A1_NATIVE_M_REGISTRY_NOT_PINNED")
    cfg,classes,_=composer.load_registry(registry)
    key,graph=choose_one(composer.enumerate_graphs(cfg,classes))
    composer.check_graph(graph,cfg,classes)
    name="A1Molecular_"+key[:12]
    original=backend.render_model(name,graph,cfg,classes)
    staged=stimulus_only_replace(original,1.0,1.0)
    old="Modelica.Blocks.Sources.RealExpression stimulus(y=if time < 1 then 1 else 0);"
    need(staged.count(old)==1,"A1_NATIVE_E1_STIMULUS_ANCHOR_DRIFT")
    adapted=staged.replace(old,
        "Modelica.Blocks.Sources.RealExpression stimulus(y="+
        expression(bins,Q(60))+");")
    need(adapted.count("    connect(stimulus.y,")==1,
         "A1_NATIVE_E1_EXTERNAL_PORT_DISCONNECTED")
    need("der(" not in adapted and "when " not in adapted,
         "A1_NATIVE_E1_MECHANISM_INSERTED")
    result="\n".join(["within;","package ArenaCafeM",adapted,
        '  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
        "end ArenaCafeM;",""])
    return {"name":name,"modelica":result,
            "candidate":{"arm_id":"M","canonical_sha256":"sha256:"+key,
                         "ast":graph,"full_ast_sha256":digest(graph),
                         "registry_sha256":digest(cfg),
                         "parameters_origin":"E1_ORIGINAL_FIXED_REGISTRY_NOT_FITTED"},
            "time_unit":"hour","rate_unit":"orders/hour"}


def build(visible,arm,condition):
    need(arm in ("D","M"),"A1_NATIVE_ONLY_D_M")
    bins=bins_from_pos(visible,condition)
    model=_make_d(bins) if arm=="D" else _make_m(bins)
    source=model["modelica"]
    cutoff=Q(visible["observability"]["cutoff_minutes_exact"])
    horizon=float(cutoff/(Q(60) if arm=="M" else Q(1)))
    name=model["name"]
    package="ArenaCafeM." if arm=="M" else ""
    prep=[
        "getVersion();",
        'loadModel(Modelica, {"4.0.0"});',
    ]
    if arm=="M":
        prep += [
            'loadModel(SystemDynamics, {"2.1.2"});',
            'loadFile("/repo/src/modelica/IGCMolecules.mo");',
            'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");']
    prep += [
        'loadFile("native.mo");',
        f'checkModel({package}{name});',
        'print(getErrorString());',
        f'simulate({package}{name},startTime=0,stopTime={format(horizon,".17g")},',
    ]
    # Construct one contiguous Modelica command (not two split records).
    prep[-1] += ('numberOfIntervals=1000,method="dassl",tolerance=1e-9,'
                 'outputFormat="csv",fileNamePrefix="native");')
    prep += ['print(getErrorString());']
    manifest={
        "schema":SCHEMA,"arm_id":arm,"condition_id":condition,
        "input_hash":digest(visible),
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "pos_event_source":"PUBLIC_CREATION_EVENTS_ONLY",
        "pos_event_count":len(visible["construction"]["pos_arrival_events"]),
        "stimulus_semantics":"UNIFORM_MASS_PER_HALF_MINUTE_BIN_NOT_OBSERVED_RATE",
        "bin_width_minutes_exact":str(BIN_MIN),
        "total_reconstructed_orders":sum(x["orders"] for x in bins),
        "nominal_parameters_origin":"ASSUMED_ENGINEERING_BENCHMARK_NOT_CALIBRATED",
        "candidate":model["candidate"],
        "native_model_name":name,
        "time_unit":model["time_unit"],"rate_unit":model["rate_unit"],
        "time_stop":horizon,
        "expected_solver":"OpenModelica_DASSL_GITHUB_ACTIONS",
        "scientific_inference":"NOT_ESTABLISHED",
        "G2":"NOT_RUN_AT_EMISSION","G3":"NOT_RUN",
        "evaluator_private_truth_read":False,
        "B_calls":0,
        "modelica_sha256":"sha256:"+hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "reconstruction_bins":bins,
    }
    return source,"\n".join(prep)+"\n",manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--arm",choices=("D","M"),required=True)
    p.add_argument("--condition",choices=("O0","O1"),required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"A1_NATIVE_REFUSE_OVERWRITE")
    input=json.loads(args.input.read_text())
    model,mos,manifest=build(input,args.arm,args.condition)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/"native.mo").write_text(model,encoding="utf-8")
    (args.out/"simulate.mos").write_text(mos,encoding="utf-8")
    (args.out/"manifest.json").write_bytes(canonical(manifest)+b"\n")
    print(json.dumps({"arm":args.arm,"condition":args.condition,
                      "orders":manifest["total_reconstructed_orders"],
                      "status":"NATIVE_MODEL_EMITTED_NOT_SIMULATED"}))


if __name__=="__main__":
    main()
