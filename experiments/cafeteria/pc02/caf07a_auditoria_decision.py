#!/usr/bin/env python3
"""CAF-07A: audit and correct the decision criterion of CAF-07 (PR #116).

NO changes to the sealed CAF-07 original experiment. Reconstruct and hash its
12x10 hypothesis predictions (NOT additional evaluation-world simulations),
then BEFORE any new world DES: audit cost-weight sensitivity, guaranteed
decision purity under +/-1 deterministic observation bands, and affordable
two-action combinations. Preserve the Pareto frontier rather than pretending
ordinal cost and pair counts share calibrated units.

Then explore a predeclared 55-110/h integer capacity sweep and off-family
negative controls. These are diagnostics of model fragility, NOT a
prospectively independent validation nor a statistical population estimate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from fractions import Fraction
from itertools import combinations, product
import io
import json
from pathlib import Path

import caf07_selector_evidencia as legacy
import caf02_lab_exploratorio as lab
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf07a-decision-calibration-audit/0.1"
PR116_PLAN_SHA="sha256:2c34db4649508745acdd5cdae9e398a5a4b660160bbc9ab7d3f0e131e354e8f0"
STAGES=legacy.STAGES
CAPACITY_SWEEP=tuple(range(55,111))
NEGATIVE_DOUBLE_CAP=(55,90)
NEGATIVE_EXTRA_CAP=(70,100)
LAMBDA_POINTS=("0","1/2","1","4/3","3/2","2","3","5")
AFFORDABLE=tuple(a for a in legacy.ACTION_MENU
                 if a["cost"]<=legacy.BUDGET_COST_UNITS)
LOWEST_COST=min(a["cost"] for a in AFFORDABLE)
PAIR_MENU=tuple(
    (a,b) for a,b in combinations(AFFORDABLE,2)
    if a["cost"]+b["cost"]<=legacy.BUDGET_COST_UNITS)
# No ability to equate measured real economic burden to an ordinal unit.
MODE="UNRESOLVED_TRADEOFF_PRESENT_PARETO_FRONTIER"


def need(ok,code):
    if not ok:raise ValueError(code)


def historical_bank():
    """Verify exact archived PR116 pre-observation plan, not only source code."""
    bank=legacy.hypotheses()
    predictions=legacy.precompute(bank)
    original_policy=legacy.caf05.d.POLICY.read_bytes()
    obj={
        "schema":legacy.SCHEMA,
        "hypotheses":bank,"candidate_observation_predictions":predictions,
        "new_public_worlds":legacy.worlds(),
        "baseline":{"rate":legacy.T0_RATE,"minute":legacy.T0_MINUTE,
                    "channels":[["delivered",None]]},
        "actions":list(legacy.ACTION_MENU),
        "tolerance_orders":legacy.TOLERANCE_ORDERS,
        "budget_illustrative_units":legacy.BUDGET_COST_UNITS,
        "pairwise_separation_cost_weight":legacy.COST_WEIGHT,
        "two_stage_truth_labels_not_in_measurement_selector":True,
        "all_hypothesis_DES_runs_completed":len(bank)*(1+len(legacy.ACTION_MENU)),
        "new_world_DES_runs_before_plan":0,
        "external_custody":False,
        "M_D_stock_operators_not_modified":True,
        "CAF02_original_policy_sha256":lab.sha(original_policy),
    }
    actual=lab.sha(lab.canonical(obj))
    need(actual==PR116_PLAN_SHA,
         "CAF07A_ORIGINAL_PR116_FORECASTS_NOT_REPRODUCED")
    return bank,predictions


def scenario_sets(bank,predictions):
    """Stratify by every K0 measurement that existing bank predicts."""
    values=sorted({p["baseline"][0] for p in predictions.values()})
    return [
        {"initial_delivery":value,
         "ids":legacy.surviving(bank,predictions,
                                 {"baseline":[value]})}
        for value in values
    ]


def plausible_around(vector):
    """All integer measurement vectors within deterministic +/-1 bands."""
    need(type(vector) is list and all(type(v) is int and v>=0
                                     for v in vector),
         "CAF07A_INVALID_PREDICTION_VECTOR")
    return product(*(range(max(0,n-legacy.TOLERANCE_ORDERS),
                           n+legacy.TOLERANCE_ORDERS+1)
                     for n in vector))


def guarantee_for_action(bank,predictions,ids,action_ids):
    """Decision-purity per *hypothesis* over ALL plausible observations.

    No probabilistic weights: an hypothesis counts as guaranteed only if
    EVERY possible +/-1 integer observation under it leaves exclusively the
    same true bottleneck class. Worst-case stage ambiguity is also returned.
    """
    by_id={h["id"]:h["bottleneck"] for h in bank}
    need(all(a in {x["id"] for x in legacy.ACTION_MENU}
             for a in action_ids),"CAF07A_UNKNOWN_ACTION")
    per_stage={s:{"guaranteed":0,"total":0} for s in STAGES}
    guaranteed_ids=[]
    worst_classes=0
    for h in ids:
        stage=by_id[h]
        per_stage[stage]["total"]+=1
        prepared=[predictions[h][a] for a in action_ids]
        robust=True
        for candidate_vectors in product(
            *(tuple(plausible_around(v)) for v in prepared)):
            evidence=dict(zip(action_ids,
                              (list(v) for v in candidate_vectors)))
            surviving=legacy.surviving(
                bank,predictions,evidence,prior_ids=ids)
            classes=legacy.decisions(bank,surviving)
            need(stage in classes,
                 "CAF07A_TRUE_MODEL_NOT_COMPATIBLE_WITH_OWN_NOISE")
            worst_classes=max(worst_classes,len(classes))
            if classes!=[stage]:
                robust=False
        if robust:
            guaranteed_ids.append(h)
            per_stage[stage]["guaranteed"]+=1
    return {
        "per_stage":per_stage,
        "guaranteed_hypotheses":len(guaranteed_ids),
        "guaranteed_ids":guaranteed_ids,
        "total_hypotheses":len(ids),
        "worst_case_remaining_bottleneck_classes":worst_classes,
        "pure_over_every_plus_minus_one_observation":True,
        "no_prior_probability_used":True,
    }


def action_metrics(bank,predictions,ids):
    rows=[]
    for action in AFFORDABLE:
        guaranteed=guarantee_for_action(
            bank,predictions,ids,(action["id"],))
        possible,robust=legacy.pair_separation(
            bank,predictions,ids,action["id"])
        rows.append({
            "action_id":action["id"],"cost_units":action["cost"],
            "pair_count":possible,"pair_separated":robust,
            **guaranteed,
        })
    return rows


def pareto_frontier(rows):
    """No scalar conversion from ordinal costs to decision-count units."""
    def dominates(a,b):
        g=lambda x,s:x["per_stage"][s]["guaranteed"]
        return (a["cost_units"]<=b["cost_units"] and
                all(g(a,s)>=g(b,s) for s in STAGES) and
                (a["cost_units"]<b["cost_units"] or
                 any(g(a,s)>g(b,s) for s in STAGES)))
    return sorted([r["action_id"] for r in rows
                   if not any(dominates(q,r) for q in rows if q is not r)])


def corrected_decision(bank,predictions,ids):
    labels=legacy.decisions(bank,ids)
    if not ids:
        return {"status":legacy.MODEL_GAP,"pareto":[],"next_action":None}
    if len(labels)<=1:
        return {"status":"STOP_DECISION_ALREADY_RESOLVED",
                "pareto":[],"next_action":None}
    m=action_metrics(bank,predictions,ids)
    if not any(x["guaranteed_hypotheses"]>0 for x in m):
        return {"status":"STOP_NO_GUARANTEED_RESOLUTION",
                "pareto":pareto_frontier(m),"next_action":None,
                "meaning":"This menu cannot guarantee a unique stage under +/-1"}
    front=pareto_frontier(m)
    # Declared multi-objective nonprobabilistic criterion. Do not select
    # between different cost and quality tradeoffs until a preference is given.
    if len(front)>1:
        return {"status":MODE,"pareto":front,"next_action":None,
                "meaning":"Multiple nondominated cost/purity alternatives; preference needed"}
    return {"status":"SINGLE_DOMINATING_ACTION","pareto":front,
            "next_action":front[0]}


def lambda_audit(rows):
    audit=[]
    for k in LAMBDA_POINTS:
        lam=Fraction(k)
        # Legacy tie-break: highest original score, then separation count,
        # then lowest cost, then lexicographical name.
        ordered=sorted(rows,key=lambda r:(
            -Fraction(r["pair_separated"])+lam*r["cost_units"],
            -r["pair_separated"],r["cost_units"],r["action_id"]))
        top=ordered[0]
        audit.append({
            "lambda":k,"chosen":top["action_id"],
            "pairs":top["pair_separated"],"cost":top["cost_units"],
            "score":str(Fraction(top["pair_separated"])-
                         lam*top["cost_units"]),
        })
    # Exact intersection of any two lines can change the original order.
    thresholds=set()
    for a,b in combinations(rows,2):
        d=a["cost_units"]-b["cost_units"]
        if d:
            x=Fraction(a["pair_separated"]-b["pair_separated"],d)
            if x>=0:thresholds.add(x)
    return {
        "sweep":audit,
        "all_nonnegative_pairwise_crossover_lambdas":[str(x)
                 for x in sorted(thresholds)],
        "lambda_is_unmeasured_conversion_of_paired_hypotheses_to_cost":True,
        "original_CAF07_lambda":legacy.COST_WEIGHT,
        "prior_uniform_not_asserted_but_equal_pair_weights_implicit":True,
    }


def fixed_two_measurement_audit(bank,predictions,ids,singles):
    """Nonadaptive pairs, same total budget; stronger than one action menu.

    This does not yet implement optimal conditional second-step selection.
    """
    evaluated=[]
    for first,second in PAIR_MENU:
        p=guarantee_for_action(
            bank,predictions,ids,(first["id"],second["id"]))
        evaluated.append({
            "first_action":first["id"],"second_action":second["id"],
            "cost_units":first["cost"]+second["cost"],
            "guaranteed_hypotheses":p["guaranteed_hypotheses"],
            "per_stage":p["per_stage"],
            "worst_case_remaining_classes":
                p["worst_case_remaining_bottleneck_classes"],
        })
    paired=sorted(evaluated,key=lambda r:(
        -r["guaranteed_hypotheses"],r["cost_units"],
        r["first_action"],r["second_action"]))
    best_single=sorted(singles,key=lambda r:(
        -r["guaranteed_hypotheses"],r["cost_units"],r["action_id"]))
    return {
        "n_pairs_budget_feasible":len(PAIR_MENU),
        "best_fixed_pair_nominal_rule":paired[0] if paired else None,
        "best_single_nominal_rule":{
            "action_id":best_single[0]["action_id"],
            "cost_units":best_single[0]["cost_units"],
            "guaranteed_hypotheses":
                best_single[0]["guaranteed_hypotheses"],
            "per_stage":best_single[0]["per_stage"],
        },
        "adaptive_second_measurement_NOT_implemented":True,
        "ranking_by_hypothesis_count_is_descriptive_not_probability":True,
    }


def baseline_decision_gap(bank,predictions,baseline):
    ids=legacy.surviving(bank,predictions,{"baseline":baseline})
    return ids,corrected_decision(bank,predictions,ids)


def measure_physical(config,rate,time,channels):
    # Evaluator strictly checks the assumption behind named physical channels.
    cfg=des.validate_private_config(config)
    if len(cfg)!=len(STAGES):
        return {"status":"UNSUPPORTED_TOPOLOGY_FOUR_STAGES",
                "measurement":None}
    v=legacy.simulate_config(config,rate,time,channels)
    return {"status":"OBSERVED","measurement":v}


def sweep_worlds():
    worlds=[{
        "id":f"IN_{c}_{i}",
        "type":"one_bottleneck_in_family_topology",
        "capacity_h":c,"true_stage":stage,
        "config":legacy.configuration(stage,c),
    } for c in CAPACITY_SWEEP for i,stage in enumerate(STAGES)]
    for c in NEGATIVE_DOUBLE_CAP:
        for i,j in combinations(range(3),2):
            stages=[
                {"servers":1 if k in (i,j) else 2,
                 "service_minutes":str(Fraction(60,c))
                    if k in (i,j) else "1"}
                for k in range(3)]
            worlds.append({
                "id":f"NEG_DOUBLE_{c}_{i}{j}",
                "type":"two_simultaneous_bottlenecks",
                "capacity_h":c,"true_stage":None,
                "config":{"schema":des.SCHEMA,
                          "tie_policy":des.TIE_POLICY,
                          "stages":stages},
            })
    for c in NEGATIVE_EXTRA_CAP:
        stages=[{"servers":2,"service_minutes":"1"}
                for _ in range(4)]
        stages[3]={"servers":1,"service_minutes":str(Fraction(60,c))}
        worlds.append({
            "id":f"NEG_EXTRA_{c}",
            "type":"four_stages_not_in_sensor_contract",
            "capacity_h":c,"true_stage":None,
            "config":{"schema":des.SCHEMA,
                      "tie_policy":des.TIE_POLICY,
                      "stages":stages},
        })
    need(len(worlds)==176 and
         len({r["id"] for r in worlds})==176,
         "CAF07A_UNDECLARED_SWEEP_WORLDS")
    return worlds


def evaluate_sweep_one(world,bank,predictions):
    base=measure_physical(
        world["config"],legacy.T0_RATE,legacy.T0_MINUTE,
        (("delivered",None),))
    if base["status"]!="OBSERVED":
        return {
            "world_id":world["id"],"type":world["type"],
            "capacity_h":world["capacity_h"],"true_stage":world["true_stage"],
            "baseline":None,"baseline_hypotheses":None,
            "diagnostics_status":base["status"],"actions":{},
            "evaluation_DES_calls":0,
        }
    raw=base["measurement"]
    ids,choice=baseline_decision_gap(bank,predictions,raw)
    action_out={}
    for action in AFFORDABLE:
        observed=measure_physical(
            world["config"],action["rate"],action["minute"],
            action["channels"])
        need(observed["status"]=="OBSERVED",
             "CAF07A_VALID_ACTION_OPERATOR_FAILED")
        updated=legacy.adjudicate(bank,predictions,ids,
                                  action["id"],observed["measurement"])
        guess=updated["diagnosis"]
        classification=(
            "MODEL_GAP" if updated["status"]==legacy.MODEL_GAP else
            "ABSTAIN" if guess is None else
            "CORRECT" if world["true_stage"]==guess else "WRONG"
        )
        action_out[action["id"]]={
            "observation":observed["measurement"],
            "diagnosis":guess,
            "posterior_status":updated["status"],
            "hypothesis_count_after":len(updated["hypotheses_after"]),
            "verdict":classification,
        }
    return {
        "world_id":world["id"],"type":world["type"],
        "capacity_h":world["capacity_h"],"true_stage":world["true_stage"],
        "nearest_grid_distance_h":min(abs(world["capacity_h"]-x)
                                      for x in legacy.TRAIN_CAPACITIES),
        "baseline":raw,"baseline_hypotheses":len(ids),
        "diagnostics_status":choice["status"],
        "selector_pareto_front":choice["pareto"],
        "actions":action_out,
        "evaluation_DES_calls":1+len(AFFORDABLE),
    }


def summary_sweep(rows):
    out={}
    for typ in sorted({r["type"] for r in rows}):
        subset=[r for r in rows if r["type"]==typ]
        with_outputs=[r for r in subset if r["evaluation_DES_calls"]]
        action_stats={}
        for action in AFFORDABLE:
            labels=Counter(row["actions"][action["id"]]["verdict"]
                           for row in with_outputs)
            action_stats[action["id"]]=dict(labels)
        out[typ]={
            "world_count":len(subset),
            "no_operator":sum(r["diagnostics_status"]==
                              "UNSUPPORTED_TOPOLOGY_FOUR_STAGES"
                              for r in subset),
            "initial_model_gap":sum(r["baseline_hypotheses"]==0
                                     for r in with_outputs),
            "multiobjective_tradeoff":sum(r["diagnostics_status"]==MODE
                                           for r in with_outputs),
            "action_outcomes":action_stats,
        }
    return out


def csv_sweep(rows):
    b=io.StringIO(newline="")
    w=csv.writer(b)
    w.writerow(["world","type","capacity_h","stage","distance_to_grid",
                "initial_delivered","n_hypotheses_K0","selector_status",
                "action","action_cost","diagnosis","outcome","hypotheses_after"])
    for row in rows:
        for action_id,v in row["actions"].items():
            cost=next(x["cost"] for x in AFFORDABLE
                      if x["id"]==action_id)
            w.writerow([
                row["world_id"],row["type"],row["capacity_h"],
                row["true_stage"],row["nearest_grid_distance_h"],
                row["baseline"][0],row["baseline_hypotheses"],
                row["diagnostics_status"],action_id,cost,
                v["diagnosis"],v["verdict"],v["hypothesis_count_after"],
            ])
        if not row["actions"]:
            w.writerow([row["world_id"],row["type"],
                        row["capacity_h"],row["true_stage"],"",
                        "","","","","","","UNSUPPORTED_TOPOLOGY",""])
    return b.getvalue()


def markdown(report):
    focus=report["focus_K0_delivered_9"]
    s=report["summary"]
    best=focus["two_measurements"]
    lines=[
        "# CAF-07A — Corrección metodológica de CAF-07",
        "",
        "**Diagnóstico retrospectivo; CAF-07 original no se reescribe.**",
        f"El plan original de PR #116 reproduce el SHA-256 {PR116_PLAN_SHA}.",
        "Se recalcularon sus 120 predicciones de hipótesis, sin nuevas",
        "simulaciones de evaluación antes de cerrar esta auditoría.",
        "",
        "## Problema y corrección",
        "",
        "- CAF-07 maximiza pares de hipótesis de *distintas etapas*",
        "con separación >2 y resta el costo por un factor arbitrario λ=1.",
        "Esa separación parcial NO garantiza un diagnóstico de etapa única.",
        "- CAF-07A enumera para cada hipótesis todas las observaciones",
        "enteras dentro de ±1 y cuenta solo las que **siempre** dejan",
        "una única etapa compatible. Se reporta por etapa para",
        "evitar ocultar el desequilibrio detrás del total.",
        "- La elección corregida presenta la frontera no dominada en",
        "(costo, resolución garantizada por etapa). Si la frontera",
        "tiene varias opciones, **no impone una tasa arbitraria de",
        "intercambio**; devuelve TRADEOFF y requiere preferencia.",
        "- Se compara también la mejor pareja FIJA de mediciones bajo",
        "presupuesto acumulado ≤8; NO es todavía un plan adaptativo",
        "de dos pasos.",
        "",
        "## Sensibilidad a λ, mismo conjunto K0=9 (9 hipótesis)",
        "",
        "| λ | Ganador de pares − λ×costo | Pares separados | Costo |",
        "|---:|---|---:|---:|",
    ]
    for r in focus["lambda_sensitivity"]["sweep"]:
        lines.append(
            f"| {r['lambda']} | {r['chosen']} | {r['pairs']} | "+
            f"{r['cost']} |")
    lines+=["",
        "## Pureza robusta de decisión por acción",
        "",
        "| Acción | Costo | Pares separados | Garantizado (prep/despacho/entrega) | Peor número de clases compatibles | Frontera |",
        "|---|---:|---:|---|---:|---|",
    ]
    for a in focus["action_metrics"]:
        by=a["per_stage"]
        vals="/".join(str(by[s]["guaranteed"]) for s in STAGES)
        lines.append(
            f"| {a['action_id']} | {a['cost_units']} | "+
            f"{a['pair_separated']}/{a['pair_count']} | {vals} | "+
            f"{a['worst_case_remaining_bottleneck_classes']} | "+
            f"{'sí' if a['action_id'] in focus['corrected_selector']['pareto'] else 'no'} |")
    lines+=["",
        f"**Nuevo selector:** {focus['corrected_selector']['status']}.",
        f"**Frontera Pareto:** {', '.join(focus['corrected_selector']['pareto'])}.",
        "",
        f"**Mejor pareja fija explorada (orden no adaptativo):** "
        f"{best['best_fixed_pair_nominal_rule']}.",
        f"**Mejor acción simple por recuento:** "
        f"{best['best_single_nominal_rule']}.",
        "",
        "## Barrido físico y controles negativos posteriores a la auditoría",
        "",
        f"- Mundos con un cuello y capacidades enteras 55–110/h: "+
          f"{s['one_bottleneck_in_family_topology']['world_count']}.",
        f"- Mundos con dos cuellos: "+
          f"{s['two_simultaneous_bottlenecks']['world_count']}.",
        f"- Mundos con cuatro etapas y operador incompatible: "+
          f"{s['four_stages_not_in_sensor_contract']['world_count']}.",
        "",
        "### Frecuencias por acción en los 168 mundos de un solo cuello",
        "",
        "| Acción | Correcto | Erróneo | Abstiene | Brecha |",
        "|---|---:|---:|---:|---:|",
    ]
    stats=s["one_bottleneck_in_family_topology"]["action_outcomes"]
    for a in AFFORDABLE:
        o=stats[a["id"]]
        lines.append(
            f"| {a['id']} | {o.get('CORRECT',0)} | "+
            f"{o.get('WRONG',0)} | {o.get('ABSTAIN',0)} | "+
            f"{o.get('MODEL_GAP',0)} |")
    lines+=["",
        "## Precauciones",
        "",
        "- Estos 168 casos son un barrido **deliberado y correlacionado**;",
        "no 168 muestras independientes, ni una estimación poblacional.",
        "- El motor DES es el mismo para banco y evaluaciones. La",
        "prueba sirve para detectar fragilidad **dentro del mecanismo**;",
        "no generalización a otros mecanismos físicos.",
        "- Las dos restricciones simultáneas constituyen controles",
        "negativos. Una clasificación de etapa única ahí es un",
        "diagnóstico excesivo, NO un acierto.",
        "- La cuarta etapa devuelve un rechazo explícito de topología;",
        "no se pasa como si fueran 3 etapas ni se presume brecha estadística.",
        "- No se incluyeron tiempos estocásticos: exigirían otro motor",
        "o una extensión rigurosa; no se simula variabilidad ficticia.",
        "- La tolerancia ±1 es un convenio de observación determinista,",
        "no un intervalo de confianza ni evidencia de potencia estadística.",
        "- La regla de frontera Pareto compara costos ilustrativos en",
        "la misma escala únicamente como restricción y dominancia;",
        "no monetiza información ni calcula VoI.",
        "- M/D/ATMS intactos; observaciones por etapa no son operadores",
        "válidos de esos modelos por analogía de nombres.",
        "",
    ]
    return "\n".join(lines)


def run(out):
    out=Path(out).resolve()
    need(not out.exists(),"CAF07A_OUTPUT_ALREADY_EXISTS")
    bank,preds=historical_bank()
    scenarios=scenario_sets(bank,preds)
    initial_9=next(v for v in scenarios if v["initial_delivery"]==9)
    ids=initial_9["ids"]
    need(len(ids)==9 and len(legacy.decisions(bank,ids))==3,
         "CAF07A_ORIGINAL_NINE_HYPOTHESES_CHANGED")
    metrics=action_metrics(bank,preds,ids)
    sensitivity=lambda_audit(metrics)
    selector=corrected_decision(bank,preds,ids)
    combo=fixed_two_measurement_audit(bank,preds,ids,metrics)
    focus={
        "baseline":9,"compatible_ids":ids,
        "action_metrics":metrics,
        "lambda_sensitivity":sensitivity,
        "corrected_selector":selector,
        "two_measurements":combo,
    }
    candidates=sweep_worlds()
    # FIRST create exclusive immutable audit+design, THEN evaluate physical DES.
    out.mkdir(parents=True,exist_ok=False)
    written={}
    def write(name,contents):
        written[name]=lab.write_new(out,name,contents)
    write("00_AUDITORIA_Y_PRECOMPROMISO.json",{
        "schema":SCHEMA,
        "PR116_original_plan_SHA256":PR116_PLAN_SHA,
        "hypothesis_bank":bank,"forecasts":preds,
        "K0_cases":scenarios,
        "focus_original_K0_9":focus,
        "all_sweep_worlds_predeclared":candidates,
        "baseline_and_action_menus_locked":list(AFFORDABLE),
        "model_family_only_single_bottleneck":True,
        "evaluation_world_DES_calls_before_plan":0,
        "tests_are_exploratory_not_independent":True,
        "no_M_D_stock_operators_authorized":True,
        "no_external_custody":True,
    })
    write("00B_CHECKPOINT_PRE_SWEEP.json",{
        "precommit_sha256":written["00_AUDITORIA_Y_PRECOMPROMISO.json"],
        "new_world_DES_calls_so_far":0,
        "all_lambda_and_purity_results_locked":True,
        "external_witness":False,
    })
    evaluation=[evaluate_sweep_one(w,bank,preds) for w in candidates]
    report={
        "schema":SCHEMA,
        "status":"CAF07A_METHOD_CORRECTION_AUDITED_AND_SWEEP_EXECUTED",
        "original_PR116_sha256_verified":True,
        "legacy_PR116_outputs_changed":False,
        "training_hypothesis_DES_runs_recomputed":120,
        "evaluation_DES_runs":sum(r["evaluation_DES_calls"]
                                  for r in evaluation),
        "new_world_count":len(evaluation),
        "focus_K0_delivered_9":focus,
        "summary":summary_sweep(evaluation),
        "evaluation":evaluation,
        "no_M_D_ATMS_changes":True,
        "no_probabilities_or_empirical_costs":True,
        "no_claim_of_independence":True,
    }
    write("01_RESULTADOS.json",report)
    write("02_BARRIDO_CASOS.csv",csv_sweep(evaluation))
    write("03_INFORME.md",markdown(report))
    write("04_MANIFIESTO.json",{
        "files_sha256":dict(written),
        "prior_digests_reconstructed":True,
        "no_external_custody":True,
        "precommit_before_all_new_worlds":True,
    })
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    result=run(p.parse_args().out)
    print(json.dumps({
        "status":result["status"],"original_hash_verified":
            result["original_PR116_sha256_verified"],
        "evaluation_DES_runs":result["evaluation_DES_runs"],
        "summary":result["summary"],
        "focus_pareto":result["focus_K0_delivered_9"][
            "corrected_selector"],
        "sensitivity":result["focus_K0_delivered_9"][
            "lambda_sensitivity"]["sweep"],
        "two_measurements":result["focus_K0_delivered_9"][
            "two_measurements"],
    },sort_keys=True))


if __name__=="__main__":
    main()
