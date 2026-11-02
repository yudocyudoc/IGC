#!/usr/bin/env python3
"""CAF-06: fixed three-queue, two-time bottleneck rule vs CAF-05 one sensor.

Declared prior to ANY new DES calls:
 - Nine new PUBLIC physical worlds, one 65/85/95 orders/h bottleneck located
   at preparation, dispatch or delivery, other stages 120/h.
 - Demand LOW=.8, MATCHED=1.5, HIGH=1.8 orders/min, 20-minute arrivals;
   sample waiting queue in three named stages at t10 and t20.
 - Diagnosis = UNIQUE strictly-positive MAXIMUM increase in queue count
   from t10 to t20, else ABSTAIN. No learned prototypes, no true-label use.
 - CAF-05 baseline = original frozen dispatch stage-stock classifier at t10
   evaluated ONLY for 1.5/min (its predeclared training condition).

This is a comparison of an inexpensive *single-channel* prior heuristic versus
an instrument-rich *three-channel/two-time* rule. Difference is not isolating
algorithm skill; it is measuring more information. No M/D stock operator,
fitted M/D, real cafe, external witness or prospectively independent source.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import io
import json
from pathlib import Path

import caf02_lab_exploratorio as lab
import caf05_contrato_y_sensor as prior
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf06-three-queue-temporal-delta-and-capacity-transfer/0.1"
CAPACITIES=(65,85,95)
STAGES=("preparacion","despacho","entrega")
STAGE_CODES=("P","D","E")
RATES=(("LOW","4/5"),("MATCHED","3/2"),("HIGH","9/5"))
TIMES=(10,20)
# All higher-capacity nonbottleneck stages: 2 servers *1 min => 120/h.
OTHER={"servers":2,"service_minutes":"1"}
QUEUE_RULE={
    "name":"STRICT_UNIQUE_POSITIVE_MAX_WAITING_QUEUE_GROWTH",
    "required_stages":list(STAGES),
    "observations_t_min":list(TIMES),
    "equation":"growth_i=waiting_i(t20)-waiting_i(t10)",
    "if_max_growth_lte_zero":"ABSTAIN_NO_POSITIVE_GROWTH",
    "if_two_or_more_stages_tied_at_max":"ABSTAIN_TIED_GROWTH",
    "otherwise":"PREDICT_STAGE_OF_LARGEST_POSITIVE_GROWTH",
    "uses_ground_truth_labels":False,
    "does_not_require_capacity_input":True,
}
SINGLE_BASELINE_RATE="MATCHED"


def need(ok,reason):
    if not ok:raise ValueError(reason)


def specs():
    result=[]
    for capacity in CAPACITIES:
        for stage_code,stage_name in zip(STAGE_CODES,STAGES):
            duration=Fraction(60,capacity)
            cfg={
                "schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
                "stages":[
                    ({"servers":1,"service_minutes":str(duration)}
                     if i==STAGES.index(stage_name) else dict(OTHER))
                    for i in range(3)],
            }
            nominal=min(Fraction(n,1)/d*60 for n,d
                        in des.validate_private_config(cfg))
            need(nominal==capacity,"CAF06_WRONG_PHYSICAL_CAPACITY")
            result.append({
                "id":f"W{capacity}{stage_code}",
                "true_bottleneck":stage_name,
                "nominal_capacity_per_hour":capacity,
                "config":cfg,
                "world_parameters_public":True,
            })
    need(len(result)==9 and len({r["id"] for r in result})==9
         and len({lab.sha(lab.canonical(r["config"]))
                  for r in result})==9,"CAF06_WORLD_REGISTRY_WRONG")
    return result


def frozen_baseline():
    reference=prior.known_reference()
    choice=prior.select_from_previous_only(reference)
    need(choice["classifier"]["prototypes"]==
         {"preparacion":1,"despacho":6,"entrega":2}
         and choice["measurement"]["field"]=="stage_stock"
         and choice["measurement"]["stage"]=="despacho"
         and choice["measurement"]["minute"]==10
         and choice["measurement"]["arrival_rate_per_minute"]=="3/2",
         "CAF06_CAF05_BASELINE_DRIFT")
    return choice


def diagnose_growth(wait_t10,wait_t20):
    need(type(wait_t10) in (tuple,list)
         and type(wait_t20) in (tuple,list)
         and len(wait_t10)==len(wait_t20)==3
         and all(type(x) is int and x>=0 for x in
                 (*wait_t10,*wait_t20)),"CAF06_INVALID_QUEUE_OBSERVATION")
    growth=[b-a for a,b in zip(wait_t10,wait_t20)]
    m=max(growth)
    if m<=0:
        label=None
        status="ABSTAIN_NO_POSITIVE_GROWTH"
    elif growth.count(m)>1:
        label=None
        status="ABSTAIN_TIED_GROWTH"
    else:
        label=STAGES[growth.index(m)]
        status="PREDICTED"
    return {
        "status":status,"predicted_bottleneck":label,
        "growth_by_stage":dict(zip(STAGES,growth)),
        "maximum_growth":m,
        "rule_frozen_before_any_new_DES":True,
    }


def observe(world,rate_name,rate,baseline):
    need(rate_name in dict(RATES),"CAF06_UNDECLARED_RATE")
    snaps=des.run_toy_engine(
        world["config"],des.half_open_arrivals(rate,20),
        (0,*TIMES,40))
    need(len(snaps)==4 and
         snaps[0].accepted_cum_orders==0 and
         snaps[0].pending_orders==0,"CAF06_WORLD_NOT_INITIALIZED_EMPTY")
    out=[]
    nominal_servers=[x["servers"] for x in world["config"]["stages"]]
    for snap in snaps[1:3]:
        q=list(snap.stage_waiting)
        active=list(snap.stage_in_service)
        stocks=[a+b for a,b in zip(q,active)]
        need(snap.accepted_cum_orders==
             snap.delivered_cum_orders+sum(stocks)
             and all(0<=a<=n for a,n in zip(active,nominal_servers))
             and snap.pending_orders==sum(stocks),
             "CAF06_PHYSICAL_MASS_OR_SERVER_LIMIT_FAILED")
        out.append({
            "minute":int(snap.t_min),
            "accepted":snap.accepted_cum_orders,
            "delivered":snap.delivered_cum_orders,
            "total_pending":snap.pending_orders,
            "waiting_by_stage":dict(zip(STAGES,q)),
            "in_service_by_stage":dict(zip(STAGES,active)),
            "stock_by_stage":dict(zip(STAGES,stocks)),
        })
    need([s["minute"] for s in out]==list(TIMES),
         "CAF06_BAD_OBSERVATION_TIMES")
    w10=[out[0]["waiting_by_stage"][stage] for stage in STAGES]
    w20=[out[1]["waiting_by_stage"][stage] for stage in STAGES]
    rule=diagnose_growth(w10,w20)
    if rate_name==SINGLE_BASELINE_RATE:
        original_stock=out[0]["stock_by_stage"][
            baseline["measurement"]["stage"]]
        base=prior.predict_one(original_stock,baseline)
        base={
            "status":base["status"],
            "prediction":base["prediction"],
            "observed_dispatch_stock_t10":original_stock,
            "prototype_distance_by_class":base["distance_by_class"],
            "original_frozen_classifier_from_CAF05":True,
        }
    else:
        base={
            "status":"NOT_APPLIED_OUTSIDE_CAF05_1_5_PER_MIN",
            "prediction":None,
            "observed_dispatch_stock_t10":out[0]["stock_by_stage"]["despacho"],
            "original_frozen_classifier_from_CAF05":True,
        }
    return {
        "world":world["id"],
        "capacity_per_hour":world["nominal_capacity_per_hour"],
        "true_bottleneck":world["true_bottleneck"],
        "rate_name":rate_name,"arrival_rate_per_minute":rate,
        "t10":out[0],"t20":out[1],
        "three_queue_temporal_rule":rule,
        "one_sensor_CAF05_fixed_baseline":base,
    }


def status(prediction,truth):
    return ("ABSTAIN" if prediction is None else
            "CORRECT" if prediction==truth else "WRONG")


def summarize(rows):
    comparison={}
    for rate_name,_ in RATES:
        subset=[r for r in rows if r["rate_name"]==rate_name]
        need(len(subset)==len(CAPACITIES)*len(STAGES),
             "CAF06_MISSING_RATE_CASES")
        comparison[rate_name]={}
        for cap in CAPACITIES:
            group=[x for x in subset if x["capacity_per_hour"]==cap]
            need(len(group)==3,"CAF06_MISSING_BOTTLENECK_CLASSES")
            pred=[x["three_queue_temporal_rule"]["predicted_bottleneck"]
                  for x in group]
            truth=[x["true_bottleneck"] for x in group]
            comparison[rate_name][str(cap)]={
                "n":3,
                "multi_correct":sum(status(p,t)=="CORRECT"
                                    for p,t in zip(pred,truth)),
                "multi_wrong":sum(status(p,t)=="WRONG"
                                  for p,t in zip(pred,truth)),
                "multi_abstain":sum(p is None for p in pred),
                "n_distinct_t10_deliveries":
                    len({x["t10"]["delivered"] for x in group}),
                "n_distinct_t20_deliveries":
                    len({x["t20"]["delivered"] for x in group}),
                "n_distinct_t20_queues":
                    len({tuple(x["t20"]["waiting_by_stage"][stage]
                              for stage in STAGES) for x in group}),
                "single_CAF05_baseline":{
                    "evaluated":rate_name==SINGLE_BASELINE_RATE,
                    "correct":sum(status(
                        x["one_sensor_CAF05_fixed_baseline"]["prediction"],
                        x["true_bottleneck"])=="CORRECT" for x in group)
                        if rate_name==SINGLE_BASELINE_RATE else None,
                    "wrong":sum(status(
                        x["one_sensor_CAF05_fixed_baseline"]["prediction"],
                        x["true_bottleneck"])=="WRONG" for x in group)
                        if rate_name==SINGLE_BASELINE_RATE else None,
                    "abstain":sum(x[
                        "one_sensor_CAF05_fixed_baseline"]["prediction"] is None
                        for x in group) if rate_name==SINGLE_BASELINE_RATE
                        else None,
                },
            }
    return comparison


def csv_rows(rows):
    b=io.StringIO(newline="")
    w=csv.writer(b)
    w.writerow(["world","capacity_h","true_bottleneck","rate",
                "t10_delivered","t20_delivered","t10_waiting_P",
                "t10_waiting_D","t10_waiting_E",
                "t20_waiting_P","t20_waiting_D","t20_waiting_E",
                "growth_P","growth_D","growth_E","multi_status",
                "multi_prediction","CAF05_single_status","CAF05_single_prediction"])
    for r in rows:
        g=r["three_queue_temporal_rule"]
        single=r["one_sensor_CAF05_fixed_baseline"]
        w.writerow([
            r["world"],r["capacity_per_hour"],r["true_bottleneck"],
            r["rate_name"],
            r["t10"]["delivered"],r["t20"]["delivered"],
            *[r["t10"]["waiting_by_stage"][s] for s in STAGES],
            *[r["t20"]["waiting_by_stage"][s] for s in STAGES],
            *[g["growth_by_stage"][s] for s in STAGES],
            g["status"],g["predicted_bottleneck"],
            single["status"],single["prediction"],
        ])
    return b.getvalue()


def markdown(report):
    lines=[
        "# CAF-06 — Observaciones combinadas y robustez ante capacidad",
        "",
        "**Estudio DES exploratorio, no prueba confirmatoria de M/D.**",
        "Nueve mundos nuevos (65,85,95 pedidos/h x tres cuellos) y tres",
        "presiones: 0.8, 1.5 y 1.8 pedidos/min, con 27 corridas DES.",
        "Preparación, despacho y entrega son etapas físicas del DES.",
        "",
        "La regla combinada, FIJA antes de observar los nuevos mundos:",
        "medir la cola en espera de cada una de las tres etapas en t10 y",
        "t20; recomendar la etapa con crecimiento positivo estrictamente",
        "mayor. Si no hay crecimiento positivo o hay empate, abstenerse.",
        "",
        "La comparación CAF-05 usa exclusivamente el antiguo clasificador",
        "de stock total en despacho al t10, con prototipos de 60/h",
        "(1,6,2). Solo se ejecuta a 1.5 pedidos/min, como originalmente.",
        "**La regla combinada usa tres canales y dos tiempos,",
        "la referencia uno solo y un tiempo: no es igualdad de información.**",
        "",
        "## Diagnóstico con información interna",
        "",
        "| Tasa | Capacidad/h | Regla 3 colas (correcto/erróneo/abstiene) | CAF05 sensor único (correcto/erróneo/abstiene) | Entregas distintas al t20 |",
        "|---:|---:|---|---|---:|",
    ]
    for rn,rate in RATES:
        for cap in CAPACITIES:
            x=report["comparisons"][rn][str(cap)]
            s=x["single_CAF05_baseline"]
            single=(
                f"{s['correct']}/{s['wrong']}/{s['abstain']}"
                if s["evaluated"] else "no aplica"
            )
            lines.append(
                f"| {float(Fraction(rate)):.2f} | {cap} | "+
                f"{x['multi_correct']}/{x['multi_wrong']}/{x['multi_abstain']} | "+
                f"{single} | {x['n_distinct_t20_deliveries']}/3 |")
    lines+=["",
        "## Diagnósticos en todos los mundos a demanda 1.5/min",
        "",
        "| Mundo | Cuello real | Colas t10 | Colas t20 | Crecimiento | Diagnóstico |",
        "|---|---|---|---|---|---|",
    ]
    for r in report["observations"]:
        if r["rate_name"]!="MATCHED":continue
        vectors=lambda t: [r[t]["waiting_by_stage"][s] for s in STAGES]
        g=r["three_queue_temporal_rule"]
        lines.append(
            f"| {r['world']} | {r['true_bottleneck']} | {vectors('t10')} | "+
            f"{vectors('t20')} | "+
            f"{[g['growth_by_stage'][s] for s in STAGES]} | "+
            f"{g['predicted_bottleneck'] or g['status']} |")
    lines+=["",
        "## Interpretación",
        "",
        "- Si desaparece la cola al operar con holgura, la regla debe",
        "abstenerse; eso no significa que cambie la infraestructura real.",
        "- Mayor presión puede hacer detectable una restricción que",
        "permanece oculta en baja demanda. La presión misma tiene",
        "costos operativos que este modelo NO cuantifica.",
        "- En estas cafeterías las colas son directamente visibles al",
        "evaluador DES; todavía NO son observables admitidos por las",
        "gramáticas M/D como sensores de estado propios.",
        "- La elección de tres colas se fundó en el mecanismo de",
        "acumulación y la evidencia CAF-04/05, pero no se ajustó",
        "usando ninguna observación de estos nueve mundos.",
        "- Se comparan reglas con distinta cantidad de información;",
        "una ventaja no prueba superioridad de inferencia per se.",
        "- Modelos físicos deterministas, configuraciones públicas;",
        "sin validación externa, sin costes de sensores y sin riesgos",
        "reales de ejecutar pruebas de demanda.",
        f"- Corridas DES: {report['DES_runs']}; confirmatorias: 0;",
        "M/D, ATMS y política CAF-02 intactos.",
        "",
    ]
    return "\n".join(lines)


def run(out):
    root=Path(out).resolve()
    need(not root.exists(),"CAF06_OUTPUT_ALREADY_EXISTS")
    world_specs=specs()
    baseline=frozen_baseline()
    policy_bytes=prior.d.POLICY.read_bytes()
    contract=prior.observation_contract()
    # The old M/D prohibition on stage scoring remains intact.
    for arm,fams in (("M",prior.M_FAMILIES),("D",prior.D_FAMILIES)):
        for family in fams:
            for stage in STAGES:
                try:
                    prior.require_scoring_support(
                        contract,arm,family,"waiting",stage)
                except ValueError as exc:
                    need(str(exc)=="CAF05_NO_VALID_MODEL_OBSERVATION_OPERATOR",
                         "CAF06_WRONG_OBSERVATION_CONTRACT_FAILURE")
                else:
                    need(False,"CAF06_UNJUSTIFIED_STOCK_OPERATOR_ACCEPTED")
    root.mkdir(parents=True,exist_ok=False)
    hashes={}
    def write(name,datum):
        hashes[name]=lab.write_new(root,name,datum)
    write("00_PLAN_PRE_DES.json",{
        "schema":SCHEMA,
        "worlds":world_specs,"demands":dict(RATES),
        "times_minutes":list(TIMES),
        "three_queue_frozen_rule":QUEUE_RULE,
        "CAF05_frozen_baseline":baseline,
        "CAF05_prior_reference_SHA256":lab.sha(prior.REF_PATH.read_bytes()),
        "CAF02_official_policy_SHA256":lab.sha(policy_bytes),
        "M_D_stage_observation_contract_SHA256":lab.sha(lab.canonical(contract)),
        "world_executions_before_plan":0,
        "future_world_outcomes_seen":False,
        "separate_training_from_new_world_evaluation":True,
        "three_queue_channels_not_information_equal_to_baseline":True,
        "no_external_witness":True,
    })
    write("00B_CHECKPOINT_PRE_DES.json",{
        "source_plan_sha256":hashes["00_PLAN_PRE_DES.json"],
        "DES_calls_so_far":0,
        "frozen_rule_precedes_every_new_DES":True,
        "witnessed_externally":False,
    })
    rows=[]
    for world in world_specs:
        for rate_name,rate in RATES:
            rows.append(observe(world,rate_name,rate,baseline))
    need(len(rows)==len(CAPACITIES)*len(STAGES)*len(RATES)==27,
         "CAF06_DES_RUN_COUNT_NOT_27")
    need(prior.d.POLICY.read_bytes()==policy_bytes,
         "CAF06_OFFICIAL_POLICY_CHANGED")
    report={
        "schema":SCHEMA,
        "status":"CAF06_THREE_STAGE_QUEUES_CAPACITY_TRANSFER_EXECUTED",
        "classification":"EXPLORATORY_PUBLIC_DES_NOT_INDEPENDENT",
        "DES_runs":len(rows),"DES_confirmatory_runs":0,
        "world_count":len(world_specs),
        "capacity_grid":list(CAPACITIES),
        "stage_labels":list(STAGES),
        "pressure_grid":dict(RATES),
        "three_queue_frozen_rule":QUEUE_RULE,
        "previous_CAF05_classifier_frozen":True,
        "M_D_stage_stock_mapping_already_blocked":True,
        "no_change_to_CAF02_M_D_or_ATMS":True,
        "comparison_not_equal_information":True,
        "observations":rows,
        "comparisons":summarize(rows),
    }
    write("01_RESULTADOS.json",report)
    write("02_COMPARACION.csv",csv_rows(rows))
    write("03_INFORME.md",markdown(report))
    write("04_MANIFIESTO.json",{
        "schema":SCHEMA,"files_sha256":dict(hashes),
        "pre_DES_plan_and_checkpoint_written":True,
        "external_custody":False,"retries":0,
        "M_D_grammars_modified":False,
    })
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    arg=p.parse_args()
    res=run(arg.out)
    print(json.dumps({
        "status":res["status"],
        "DES_runs":res["DES_runs"],
        "comparisons":res["comparisons"],
    },sort_keys=True))


if __name__=="__main__":
    main()
