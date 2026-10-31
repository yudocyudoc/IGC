#!/usr/bin/env python3
"""CAF-07: evidence selector driven by explicit physical hypotheses and decisions.

NOT a probabilistic POMDP, VoI estimate, or a new M/D stock observation
operator. A finite bank of typed DES physical hypotheses predicts actual
observables, with numerical tolerance and costs as declared design inputs.
A deterministic greedy rule chooses the best *affordable* measurement to
separate alternative bottleneck decisions, or STOP_NO_INFORMATION.

Train/predict with a FIXED public capacity bank 60/75/90/105 orders/h.
Evaluate on separate NEW publicly predeclared 72/88/102/h worlds, each
with a different bottleneck stage. All 12 hypothesis response curves and
action menu are written BEFORE running the first new-world baseline DES.
Per-world candidate sets and chosen action are durably written BEFORE that
world's follow-up DES. Do not look at world labels/config in selection.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import io
import json
from pathlib import Path

import caf02_lab_exploratorio as lab
import caf05_contrato_y_sensor as caf05
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf07-deterministic-evidence-selection/0.1"
STAGES=("preparacion","despacho","entrega")
TRAIN_CAPACITIES=(60,75,90,105)
NEW_CAPACITIES=(72,88,102)
T0_RATE="6/5"
T0_MINUTE=10
TOLERANCE_ORDERS=1
BUDGET_COST_UNITS=8
COST_WEIGHT=1
# Costs are ordinal, illustrative, not MXN or measured operational costs.
# Normal: one cost unit per delivery query. A stage channel is 2 units.
# Any demand-pressure shift to 1.8 adds 3 cost units, not risk equivalent.
ACTION_MENU=(
    {"id":"delivered_15_t20","rate":"3/2","minute":20,
     "channels":[["delivered",None]],"cost":1,"field_stress":False},
    {"id":"prep_queue_15_t20","rate":"3/2","minute":20,
     "channels":[["waiting","preparacion"]],"cost":2,"field_stress":False},
    {"id":"dispatch_queue_15_t20","rate":"3/2","minute":20,
     "channels":[["waiting","despacho"]],"cost":2,"field_stress":False},
    {"id":"delivery_queue_15_t20","rate":"3/2","minute":20,
     "channels":[["waiting","entrega"]],"cost":2,"field_stress":False},
    {"id":"dispatch_stock_15_t20","rate":"3/2","minute":20,
     "channels":[["stage_stock","despacho"]],"cost":2,"field_stress":False},
    {"id":"prep_dispatch_15_t20","rate":"3/2","minute":20,
     "channels":[["waiting","preparacion"],["waiting","despacho"]],
     "cost":4,"field_stress":False},
    {"id":"all_queues_15_t20","rate":"3/2","minute":20,
     "channels":[["waiting",s] for s in STAGES],
     "cost":6,"field_stress":False},
    {"id":"prep_dispatch_18_t20","rate":"9/5","minute":20,
     "channels":[["waiting","preparacion"],["waiting","despacho"]],
     "cost":7,"field_stress":True},
    {"id":"all_queues_18_t20","rate":"9/5","minute":20,
     "channels":[["waiting",s] for s in STAGES],
     "cost":9,"field_stress":True},
)
NO_MEASURE="STOP_NO_INFORMATION"
MODEL_GAP="MODEL_GAP_NO_COMPATIBLE_HYPOTHESIS"
AMBIGUOUS="ABSTAIN_MULTIPLE_DECISIONS"
DECIDED="SINGLE_BOTTLENECK_CLASS"
STAGE_INDEX={s:i for i,s in enumerate(STAGES)}


def need(cond,msg):
    if not cond:
        raise ValueError(msg)


def configuration(bottleneck,capacity):
    need(bottleneck in STAGES and
         type(capacity) is int and 0<capacity<120,
         "CAF07_INVALID_PHYSICAL_HYPOTHESIS")
    entries=[
        {"servers":1 if stage==bottleneck else 2,
         "service_minutes":str(Fraction(60,capacity))
             if stage==bottleneck else "1"}
        for stage in STAGES
    ]
    config={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
            "stages":entries}
    vals=des.validate_private_config(config)
    need(min(Fraction(n,1)/t*60 for n,t in vals)==capacity,
         "CAF07_CAPACITY_NOT_EXACT")
    return config


def hypotheses():
    return [{
        "id":f"H{cap}_{STAGE_INDEX[stage]}",
        "bottleneck":stage,"capacity_h":cap,
        "physical_model":"THREE_STAGE_EXACT_DES_WITH_ONE_LIMITING_SERVER",
        "config":configuration(stage,cap),
    } for cap in TRAIN_CAPACITIES for stage in STAGES]


def worlds():
    return [{
        "id":f"NEW_{stage[:1]}_{cap}",
        "actual_bottleneck":stage,"capacity_h":cap,
        "config":configuration(stage,cap),
        "public_synthetic_world":True,
    } for cap,stage in zip(NEW_CAPACITIES,STAGES)]


def checked_action(action):
    need(type(action) is dict and
         action in ACTION_MENU,
         "CAF07_NOT_PREDECLARED_ACTION")
    need(action["minute"]==20 and
         action["rate"] in ("3/2","9/5") and
         action["cost"]>0 and
         all(field in ("delivered","waiting","stage_stock")
             and (stage in STAGES if field!="delivered" else stage is None)
             for field,stage in action["channels"]),
         "CAF07_BAD_SENSOR_OPERATOR")


def read_channels(snapshot,channels):
    waiting=dict(zip(STAGES,snapshot.stage_waiting))
    serving=dict(zip(STAGES,snapshot.stage_in_service))
    all_stock={s:waiting[s]+serving[s] for s in STAGES}
    values=[]
    for field,stage in channels:
        if field=="delivered" and stage is None:
            v=snapshot.delivered_cum_orders
        elif field=="waiting" and stage in STAGES:
            v=waiting[stage]
        elif field=="stage_stock" and stage in STAGES:
            v=all_stock[stage]
        else:
            raise ValueError("CAF07_UNSUPPORTED_OBSERVATION_OPERATOR")
        values.append(v)
    need(all(type(v) is int and v>=0 for v in values),
         "CAF07_BAD_OBSERVATION_VALUES")
    need(snapshot.accepted_cum_orders==snapshot.delivered_cum_orders+
         sum(all_stock.values()) and
         sum(all_stock.values())==snapshot.pending_orders,
         "CAF07_DES_PHYSICAL_MASS_VIOLATION")
    return values


def simulate_config(config,rate,time,channels):
    # One independent DES run for each specific pressure condition.
    # All hypothesis simulations happen before any evaluation-world run.
    observations=(0,10,20,40)
    data=des.run_toy_engine(config,des.half_open_arrivals(rate,20),
                            observations)
    item=data[observations.index(time)]
    return read_channels(item,channels)


def precompute(hypotheses_bank):
    result={}
    for h in hypotheses_bank:
        predictions={}
        predictions["baseline"]=simulate_config(
            h["config"],T0_RATE,T0_MINUTE,(("delivered",None),))
        for action in ACTION_MENU:
            checked_action(action)
            predictions[action["id"]]=simulate_config(
                h["config"],action["rate"],action["minute"],
                action["channels"])
        result[h["id"]]=predictions
    need(len(result)==12,"CAF07_HYPOTHESIS_BANK_NOT_12")
    return result


def compatible(expected,observed,tol=TOLERANCE_ORDERS):
    need(type(expected) is list and type(observed) is list and
         len(expected)==len(observed)>0 and
         all(type(v) is int and v>=0 for v in (*expected,*observed)),
         "CAF07_MISMATCHED_VECTOR_OR_UNITS")
    return all(abs(a-b)<=tol for a,b in zip(expected,observed))


def surviving(bank,predictions,evidence,prior_ids=None):
    ids=({h["id"] for h in bank} if prior_ids is None else set(prior_ids))
    need(ids <= {h["id"] for h in bank},
         "CAF07_UNKNOWN_HYPOTHESIS_ID")
    return sorted(h["id"] for h in bank if h["id"] in ids and
                  all(compatible(predictions[h["id"]][key],value)
                      for key,value in evidence.items()))


def decisions(bank,ids):
    by_id={h["id"]:h["bottleneck"] for h in bank}
    return sorted({by_id[i] for i in ids})


def pair_separation(bank,predictions,ids,action_id):
    by_id={h["id"]:h["bottleneck"] for h in bank}
    pairs=0
    robust=0
    # A signal is robustly distinct when two +/-1 envelopes cannot overlap.
    # This is NOT an expected probability of success.
    for idx,a in enumerate(ids):
        for b in ids[idx+1:]:
            if by_id[a]==by_id[b]:
                continue
            pairs+=1
            x=predictions[a][action_id]
            y=predictions[b][action_id]
            need(len(x)==len(y),"CAF07_SENSOR_VECTOR_SHAPE_CHANGED")
            if any(abs(a-b)>2*TOLERANCE_ORDERS for a,b in zip(x,y)):
                robust+=1
    return pairs,robust


def select_action(bank,predictions,ids,*,budget=BUDGET_COST_UNITS,
                  allowed_action_ids=None):
    need(type(budget) is int and budget>=0,
         "CAF07_NONDECLARED_OR_INVALID_COST_BUDGET")
    labels=decisions(bank,ids)
    if not ids:
        return {
            "status":MODEL_GAP,"action":None,"ranked_feasible":[],
            "remaining_bottleneck_labels":[],
            "reason":"No compatible physical model after baseline.",
        }
    if len(labels)==1:
        return {
            "status":"STOP_DECISION_ALREADY_RESOLVED","action":None,
            "ranked_feasible":[],"remaining_bottleneck_labels":labels,
            "reason":"Further structural location sensing not needed.",
        }
    permitted=(set(allowed_action_ids) if allowed_action_ids is not None
               else {a["id"] for a in ACTION_MENU})
    need(permitted <= {a["id"] for a in ACTION_MENU},
         "CAF07_UNKNOWN_SENSOR_ACTION")
    ranked=[]
    for action in ACTION_MENU:
        if action["id"] not in permitted or action["cost"]>budget:
            continue
        n,robust=pair_separation(bank,predictions,ids,action["id"])
        ranked.append({
            "action_id":action["id"],"cost_units":action["cost"],
            "cross_decision_pairs":n,"robustly_separated_pairs":robust,
            "pair_fraction_not_probability":robust/n if n else 0,
            "net_pair_coverage_minus_cost_penalty":robust-
                COST_WEIGHT*action["cost"],
        })
    # Deterministic predeclared heuristic, prioritizes pair separation net
    # of declared *illustrative* cost, then raw pair coverage, then cost.
    ranked.sort(key=lambda a:(
        -a["net_pair_coverage_minus_cost_penalty"],
        -a["robustly_separated_pairs"],
        a["cost_units"],a["action_id"]))
    selected=ranked[0] if ranked else None
    if selected is None or selected[
        "net_pair_coverage_minus_cost_penalty"]<=0:
        return {
            "status":NO_MEASURE,"action":None,"ranked_feasible":ranked,
            "remaining_bottleneck_labels":labels,
            "reason":"No affordable action with positive net discriminative value under the declared units.",
        }
    return {
        "status":"MEASURE_SELECTED",
        "action":next(a for a in ACTION_MENU if a["id"]==
                      selected["action_id"]),
        "ranked_feasible":ranked,
        "remaining_bottleneck_labels":labels,
        "reason":"Max robust cross-decision pair coverage minus illustrative cost; not Bayesian VoI.",
    }


def adjudicate(bank,predictions,prior_ids,action_id,measurement):
    updated=surviving(
        bank,predictions,{action_id:measurement},prior_ids=prior_ids)
    classes=decisions(bank,updated)
    if not updated:
        status=MODEL_GAP
        diagnosis=None
    elif len(classes)>1:
        status=AMBIGUOUS
        diagnosis=None
    else:
        status=DECIDED
        diagnosis=classes[0]
    return {
        "status":status,"hypotheses_after":updated,
        "bottleneck_labels_after":classes,
        "diagnosis":diagnosis,
        "not_a_posterior_probability":True,
    }


def evaluate_one(world,bank,predictions,root):
    identity=world["id"]
    # The selector sees only the masked output; no config or true label.
    b0=simulate_config(world["config"],T0_RATE,T0_MINUTE,
                        (("delivered",None),))
    prior_ids=surviving(bank,predictions,{"baseline":b0})
    selected=select_action(bank,predictions,prior_ids)
    path=root/f"01_PRE_PROBE_{identity}.json"
    lab.write_new(root,path.name,{
        "world_id":identity,"baseline_delivered_t10":b0,
        "pre_probe_candidate_ids":prior_ids,
        "selector_decision":selected,
        "followup_DES_calls_so_far":0,
        "future_followup_observation_seen":False,
        "model_truth_labels_not_passed_to_selector":True,
    })
    if selected["action"] is None:
        followup=None
        result={
            "status":selected["status"],
            "hypotheses_after":prior_ids,
            "bottleneck_labels_after":decisions(bank,prior_ids),
            "diagnosis":None,
            "not_a_posterior_probability":True,
        }
    else:
        a=selected["action"]
        followup=simulate_config(
            world["config"],a["rate"],a["minute"],a["channels"])
        result=adjudicate(bank,predictions,prior_ids,a["id"],followup)
    judgement=(
        "ABSTAIN" if result["diagnosis"] is None else
        "CORRECT" if result["diagnosis"]==world["actual_bottleneck"] else
        "WRONG"
    )
    return {
        "world":identity,
        "true_bottleneck_EVALUATOR_ONLY":world["actual_bottleneck"],
        "true_capacity_EVALUATOR_ONLY":world["capacity_h"],
        "baseline_delivery":b0,
        "baseline_hypothesis_count":len(prior_ids),
        "baseline_classes":decisions(bank,prior_ids),
        "selection":selected,
        "observed_followup":followup,
        "updated":result,
        "judgement_EVALUATOR_ONLY":judgement,
        "DES_world_calls":1+int(followup is not None),
    }


def report_md(report):
    lines=[
        "# CAF-07 — Selector de evidencia entre hipótesis",
        "",
        "**Exploración DES pública sin probabilidades artificiales ni inferencia M/D.**",
        "Se comparan 12 hipótesis físicas explícitas: cuellos en tres etapas,",
        "con capacidades 60/75/90/105 pedidos/h. Sus predicciones se",
        "calcularon y archivaron ANTES de observar cualquier mundo nuevo.",
        "",
        "La evidencia inicial es una única entrega acumulada K0 (1.2/min t10).",
        "La selección elige una acción entre nueve mediciones físicas",
        "permitidas (entregas, cola o stock por etapa, en t20 con demanda 1.5",
        "o 1.8/min), con **costos ilustrativos** de 1–9 unidades y",
        "presupuesto 8. Los modelos y las observaciones usan enteros DES.",
        "",
        "Regla: separar tantos pares de hipótesis con **decisiones distintas**",
        "como sea posible, exigiendo diferencia de >2 pedidos para dos bandas",
        "de tolerancia ±1 no superpuestas; restar el costo ilustrativo de",
        "la medición y elegir el mayor valor neto. No hay probabilidades",
        "ni cálculo validado de valor económico de información.",
        "",
        "## Mundos nuevos y decisiones congeladas ANTES de la segunda medición",
        "",
        "| Mundo | Cuello real | Capacidad/h | Entrega K0 | Hipótesis K0 | Medición seleccionada | Observación | Diagnóstico | Veredicto |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for r in report["evaluations"]:
        a=r["selection"]["action"]
        lines.append(
            f"| {r['world']} | {r['true_bottleneck_EVALUATOR_ONLY']} | "+
            f"{r['true_capacity_EVALUATOR_ONLY']} | "+
            f"{r['baseline_delivery'][0]} | "+
            f"{r['baseline_hypothesis_count']} | "+
            f"{a['id'] if a else r['selection']['status']} | "+
            f"{r['observed_followup']} | "+
            f"{r['updated']['diagnosis'] or r['updated']['status']} | "+
            f"{r['judgement_EVALUATOR_ONLY']} |")
    s=report["summary"]
    lines+=["",
        "## Resumen",
        "",
        f"- Mundos evaluados: {len(report['evaluations'])}.",
        f"- Diagnósticos correctos: {s['correct']}, erróneos: {s['wrong']},",
        f"  abstenciones: {s['abstain']}.",
        f"- Brechas de modelo (sin hipótesis compatibles): {s['model_gap']}.",
        f"- Decisiones de no medir por valor discriminativo/costo: {s['no_measure']}.",
        f"- DES ejecutados: {report['DES_runs']} en nuevos mundos;",
        f"  hipótesis simuladas antes: {report['hypothesis_DES_runs']}.",
        "",
        "## Límites metodológicos",
        "",
        "- Las acciones se seleccionan con predicciones de una gramática",
        "física DES de tres etapas; NO con M-C00/C01 ni D-D1/D2/D3.",
        "Sus stocks NO pueden asimilar datos internos de DES todavía.",
        "- El cálculo de pares separados es combinatorio, no esperado",
        "respecto de probabilidades. El costo es una utilidad ordinal",
        "de laboratorio, NO gasto de instrumentación observado.",
        "- La misma implementación DES construye predicciones y mundos",
        "públicos de evaluación: hay sesgo de familia de modelo y",
        "**no existe independencia estructural ni validación en cafeterías reales**.",
        "- Las capacidades de evaluación 72/88/102 NO están en el banco",
        "de hipótesis. Un resultado sin candidatos significa",
        "inadecuación de ese banco bajo la tolerancia fijada,",
        "no que el sistema físico sea imposible.",
        "- No se reinterpretan medidas después de conocer las",
        "etiquetas verdaderas. Los planes y selecciones locales se",
        "escribieron con fsync antes de realizar las pruebas.",
        "- No se equipara reducción de hipótesis con evidencia causal",
        "de que una intervención mejorará el rendimiento.",
        "",
    ]
    return "\n".join(lines)


def csv_output(data):
    buff=io.StringIO(newline="")
    w=csv.writer(buff)
    w.writerow(["world","actual_stage","capacity_h","baseline_D10",
                "n_prior_hypotheses","chosen_action","action_cost",
                "followup_measurement","posterior_count","diagnosis",
                "status","judgement","DES_world_calls"])
    for r in data["evaluations"]:
        a=r["selection"]["action"]
        w.writerow([
            r["world"],r["true_bottleneck_EVALUATOR_ONLY"],
            r["true_capacity_EVALUATOR_ONLY"],r["baseline_delivery"][0],
            r["baseline_hypothesis_count"],
            a["id"] if a else "",
            a["cost"] if a else "",
            "|".join(map(str,r["observed_followup"]))
                if r["observed_followup"] is not None else "",
            len(r["updated"]["hypotheses_after"]),
            r["updated"]["diagnosis"] or "",
            r["updated"]["status"],
            r["judgement_EVALUATOR_ONLY"],r["DES_world_calls"],
        ])
    return buff.getvalue()


def run(out):
    folder=Path(out).resolve()
    need(not folder.exists(),"CAF07_OUTPUT_ALREADY_EXISTS")
    bank=hypotheses()
    new=worlds()
    need(len(bank)==12 and len(new)==3 and
         set(NEW_CAPACITIES).isdisjoint(TRAIN_CAPACITIES),
         "CAF07_HYPOTHESIS_AND_EVALUATION_SEPARATION")
    original_policy=caf05.d.POLICY.read_bytes()
    obs_contract=caf05.observation_contract()
    for arm,fams in (("M",caf05.M_FAMILIES),("D",caf05.D_FAMILIES)):
        for family in fams:
            for stage in STAGES:
                try:
                    caf05.require_scoring_support(
                        obs_contract,arm,family,"waiting",stage)
                except ValueError as e:
                    need(str(e)=="CAF05_NO_VALID_MODEL_OBSERVATION_OPERATOR",
                         "CAF07_INVALID_M_D_STOCK_REJECTION")
                else:
                    need(False,"CAF07_M_D_STAGE_STOCK_OPERATOR_BYPASS")
    # All predictions (including candidate action responses) happen before
    # any *evaluation-world* DES calls; the truth must not be used in choice.
    predictions=precompute(bank)
    folder.mkdir(parents=True,exist_ok=False)
    local={}
    def write(name,datum):
        local[name]=lab.write_new(folder,name,datum)
    write("00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json",{
        "schema":SCHEMA,
        "hypotheses":bank,"candidate_observation_predictions":predictions,
        "new_public_worlds":new,
        "baseline": {"rate":T0_RATE,"minute":T0_MINUTE,
                     "channels":[["delivered",None]]},
        "actions":list(ACTION_MENU),"tolerance_orders":TOLERANCE_ORDERS,
        "budget_illustrative_units":BUDGET_COST_UNITS,
        "pairwise_separation_cost_weight":COST_WEIGHT,
        "two_stage_truth_labels_not_in_measurement_selector":True,
        "all_hypothesis_DES_runs_completed":len(bank)*(1+len(ACTION_MENU)),
        "new_world_DES_runs_before_plan":0,
        "external_custody":False,
        "M_D_stock_operators_not_modified":True,
        "CAF02_original_policy_sha256":lab.sha(original_policy),
    })
    write("00B_CHECKPOINT_PRE_DES.json",{
        "plan_sha256":local[
            "00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json"],
        "new_world_DES_calls_so_far":0,
        "all_predictions_locked":True,
        "external_witness":False,
    })
    evaluations=[evaluate_one(w,bank,predictions,folder) for w in new]
    need(caf05.d.POLICY.read_bytes()==original_policy,
         "CAF07_ORIGINAL_M_D_POLICY_CHANGED")
    total=sum(e["DES_world_calls"] for e in evaluations)
    summary={
        "correct":sum(e["judgement_EVALUATOR_ONLY"]=="CORRECT"
                      for e in evaluations),
        "wrong":sum(e["judgement_EVALUATOR_ONLY"]=="WRONG"
                    for e in evaluations),
        "abstain":sum(e["judgement_EVALUATOR_ONLY"]=="ABSTAIN"
                      for e in evaluations),
        "model_gap":sum(e["updated"]["status"]==MODEL_GAP
                        for e in evaluations),
        "no_measure":sum(e["selection"]["status"]==NO_MEASURE
                         for e in evaluations),
    }
    report={
        "schema":SCHEMA,
        "status":"CAF07_EVIDENCE_SELECTOR_EXPLORATORY_EXECUTED",
        "classification":"PUBLIC_EXPLORATORY_NOT_PROSPECTIVELY_INDEPENDENT",
        "hypotheses":len(bank),"new_worlds":len(new),
        "hypothesis_DES_runs":len(bank)*(1+len(ACTION_MENU)),
        "DES_runs":total,
        "confirmatory_DES_runs":0,
        "measurement_costs_are_illustrative":True,
        "probability_or_expected_VOI_estimated":False,
        "M_D_stage_observation_models_untouched":True,
        "evaluator_truth_not_used_in_selection":True,
        "evaluations":evaluations,
        "summary":summary,
    }
    write("01_RESULTADOS.json",report)
    write("02_COMPARACION.csv",csv_output(report))
    write("03_INFORME.md",report_md(report))
    write("04_MANIFIESTO.json",{
        "schema":SCHEMA,"files_sha256":dict(local),
        "no_external_custody":True,
        "all_three_actions_chosen_before_respective_followup_DES":True,
        "M_D_original_policy_unchanged":True,
    })
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=run(args.out)
    print(json.dumps({
        "status":result["status"],
        "hypothesis_DES_runs":result["hypothesis_DES_runs"],
        "evaluation_DES_runs":result["DES_runs"],
        "summary":result["summary"],
        "rows":[{
            "world":e["world"],"k0":e["baseline_delivery"],
            "chosen":e["selection"]["action"]["id"]
                if e["selection"]["action"] else None,
            "read":e["observed_followup"],
            "updated":e["updated"]["status"],
            "diagnosis":e["updated"]["diagnosis"],
            "judgement":e["judgement_EVALUATOR_ONLY"],
        } for e in result["evaluations"]],
    },sort_keys=True))


if __name__=="__main__":
    main()
