#!/usr/bin/env python3
"""CAF-07B: decision-coverage threshold, cumulative budget and hidden topology.

New, separate exploratory experiment; PR #116/#117 remain immutable.
A minimum *per surviving decision class* guarantee replaces arbitrary
pair-count minus cost. The first measurement is deliberately fixed and cheap;
only the second is chosen conditionally, with the remaining shared budget.
Compare single-bottleneck bank to an expanded bank also admitting simultaneous
nominal bottlenecks. Unknown fourth stages are NOT revealed to the selector.
All claims of unique stage/class remain conditional on bank completeness.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

import caf07_selector_evidencia as caf07
import caf07a_auditoria_decision as caf07a
import caf02_lab_exploratorio as lab
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf07b-decision-threshold-conditional-second-probe/0.1"
STAGES=caf07.STAGES
TRAIN_CAPACITIES=caf07.TRAIN_CAPACITIES
BUDGET=8
MIN_GUARANTEED_PER_SURVIVING_CLASS=1
FIRST_ACTION_ID="delivered_15_t20"
# Explicitly hypothetical ordinal acquisition costs from the CAF07 menu.
ACTIONS=tuple(a for a in caf07.ACTION_MENU if a["cost"]<=BUDGET)
ACTION_BY_ID={a["id"]:a for a in ACTIONS}
FIRST=ACTION_BY_ID[FIRST_ACTION_ID]
TOLERANCE=1
DIVERGENCE_THRESHOLD=2*TOLERANCE
SOURCE_COMMIT_PATTERN=re.compile(r"^[0-9a-f]{40}$")
MODEL_GAP="MODEL_GAP_NO_COMPATIBLE_HYPOTHESIS"
THRESHOLD_FAIL="REQUIREMENT_NOT_MET"
STRUCTURAL_WARNING="WITHIN_BANK_ONLY_NOT_REAL_WORLD_CERTAINTY"
EVAL_SINGLE_CAPS=(72,88,102)
DOUBLE_CAPS=(55,90)
EXTRA_CAPS=(70,100)


def need(test,code):
    if not test:raise ValueError(code)


def klass(stages):
    return "+".join(stages)


def make_physical_config(stage_indices,cap,*,extra=False):
    need(type(cap) is int and 0<cap<120 and
         len(set(stage_indices))==len(stage_indices) and
         all(type(i) is int and 0<=i<3 for i in stage_indices),
         "CAF07B_INVALID_BOTTLENECK_CONFIGURATION")
    all_stages=[
        {"servers":1 if i in stage_indices else 2,
         "service_minutes":str(Fraction(60,cap))
             if i in stage_indices else "1"}
        for i in range(3)
    ]
    if extra:
        all_stages.append({"servers":1,
                           "service_minutes":str(Fraction(60,cap))})
    config={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
            "stages":all_stages}
    validated=des.validate_private_config(config)
    need(min(Fraction(n,1)/t*60 for n,t in validated)==cap,
         "CAF07B_CAPACITY_MISMATCH")
    return config


def bank(expanded):
    result=[]
    for cap in TRAIN_CAPACITIES:
        for stage_set in ((0,),(1,),(2,),((0,1)),((0,2)),((1,2))):
            if len(stage_set)>1 and not expanded:
                continue
            stages=[STAGES[i] for i in stage_set]
            result.append({
                "id":f"{'D' if len(stages)>1 else 'S'}_{cap}_{''.join(str(i) for i in stage_set)}",
                "decision_class":klass(stages),
                "nominal_limited_stages":stages,
                "capacity_per_hour":cap,
                "config":make_physical_config(stage_set,cap),
            })
    need(len(result)==(24 if expanded else 12),
         "CAF07B_BANK_COUNT_WRONG")
    return result


def precompute(bank_rows):
    prediction={}
    for h in bank_rows:
        vals={"baseline":read_physical(
            h["config"],caf07.T0_RATE,caf07.T0_MINUTE,
            (("delivered",None),))}
        for action in ACTIONS:
            vals[action["id"]]=read_physical(
                h["config"],action["rate"],action["minute"],
                action["channels"])
        prediction[h["id"]]=vals
    return prediction


def read_physical(config,rate,minute,channels):
    """Observe only named first-three stage channels; never expose topology.

    An unknown fourth stage is physically simulated, but not leaked as a
    configuration count to the selector. Conservation checks ALL stages,
    including those the selector cannot see.
    """
    observations=(0,10,20,40)
    need(minute in observations and minute>0,
         "CAF07B_INVALID_OBSERVATION_TIME")
    snapshots=des.run_toy_engine(config,des.half_open_arrivals(rate,20),
                                 observations)
    snap=snapshots[observations.index(minute)]
    allstocks=[x+y for x,y in zip(
        snap.stage_waiting,snap.stage_in_service)]
    need(snap.accepted_cum_orders==snap.delivered_cum_orders+
         sum(allstocks)==snap.delivered_cum_orders+snap.pending_orders,
         "CAF07B_PHYSICAL_CONSERVATION_FAILED")
    values=[]
    for field,stage in channels:
        if field=="delivered" and stage is None:
            values.append(snap.delivered_cum_orders)
        elif stage in STAGES:
            i=STAGES.index(stage)
            if field=="waiting":
                values.append(snap.stage_waiting[i])
            elif field=="stage_stock":
                values.append(allstocks[i])
            else:
                raise ValueError("CAF07B_BAD_OBSERVATION_OPERATOR")
        else:
            raise ValueError("CAF07B_BAD_STAGE_NAME")
    need(all(type(v) is int and v>=0 for v in values),
         "CAF07B_INVALID_MEASURED_VALUE")
    return values


def eligible(bank_rows,predictions,observations,previous=None):
    choices=({h["id"] for h in bank_rows} if previous is None
             else set(previous))
    need(choices.issubset(predictions),
         "CAF07B_UNKNOWN_HYPOTHESIS")
    return sorted(
        h["id"] for h in bank_rows
        if h["id"] in choices and all(
            caf07.compatible(predictions[h["id"]][key],obs)
            for key,obs in observations.items()))


def classes(bank_rows,ids):
    labels={h["id"]:h["decision_class"] for h in bank_rows}
    return sorted({labels[i] for i in ids})


def guarantee(bank_rows,predictions,ids,action_ids):
    """Exact robust per-class resolution for all +/-1 observations.

    Given independent rectangular integer error bands, two hypotheses may
    share an observation iff all coordinate prediction differences <=2.
    For each h, guarantee requires non-overlap against EVERY rival class.
    This is the exact all-response criterion, not a pair-count surrogate.
    """
    lookup={h["id"]:h["decision_class"] for h in bank_rows}
    by_class={name:{"total":0,"guaranteed":0}
              for name in classes(bank_rows,ids)}
    guaranteed=[]
    for hid in ids:
        label=lookup[hid]
        by_class[label]["total"]+=1
        safe=True
        for rival in ids:
            if lookup[rival]==label:continue
            distinct=False
            for aid in action_ids:
                x=predictions[hid][aid]
                y=predictions[rival][aid]
                need(len(x)==len(y)>0,
                     "CAF07B_PREDICTION_CHANNEL_MISMATCH")
                if any(abs(a-b)>DIVERGENCE_THRESHOLD
                       for a,b in zip(x,y)):
                    distinct=True
                    break
            if not distinct:
                safe=False
                break
        if safe:
            guaranteed.append(hid)
            by_class[label]["guaranteed"]+=1
    return {"by_class":by_class,"guaranteed_ids":guaranteed,
            "total_guaranteed":len(guaranteed),
            "all_classes_meet_minimum":all(
                v["guaranteed"]>=MIN_GUARANTEED_PER_SURVIVING_CLASS
                for v in by_class.values()),
            "minimum_per_class":MIN_GUARANTEED_PER_SURVIVING_CLASS,
            "semantics":"ROBUST_WITHIN_FINITE_BANK_ONLY"}


def choose_second(bank_rows,predictions,prior,*,remaining_budget,
                  used_actions):
    need(type(remaining_budget) is int and remaining_budget>=0,
         "CAF07B_INVALID_REMAINING_BUDGET")
    labels=classes(bank_rows,prior)
    if not prior:
        return {"status":MODEL_GAP,"action":None,
                "classes":labels,"candidates":[]}
    if len(labels)==1:
        return {"status":"STOP_SINGLE_CLASS_WITHIN_BANK",
                "action":None,"classes":labels,"candidates":[]}
    options=[]
    for action in ACTIONS:
        if action["id"] in used_actions or action["cost"]>remaining_budget:
            continue
        tested=guarantee(bank_rows,predictions,prior,(action["id"],))
        options.append({"action_id":action["id"],
                        "cost":action["cost"],
                        "robustness":tested})
    feasible=[r for r in options
              if r["robustness"]["all_classes_meet_minimum"]]
    feasible.sort(key=lambda r:(
        r["cost"],-min(x["guaranteed"] for x in
                       r["robustness"]["by_class"].values()),
        r["action_id"]))
    if not feasible:
        return {
            "status":THRESHOLD_FAIL,"action":None,"classes":labels,
            "candidates":options,
            "reason":"No budget-feasible action guarantees >=1 hypothesis per surviving decision class under +/-1."}
    chosen=ACTION_BY_ID[feasible[0]["action_id"]]
    return {"status":"MEASURE_SELECTED_AT_THRESHOLD",
            "action":chosen,"classes":labels,"candidates":options,
            "reason":"Cheapest feasible action meeting prespecified per-class robust resolution requirement."}


def update(bank_rows,predictions,prior,key,measurement):
    after=eligible(bank_rows,predictions,{key:measurement},prior)
    labels=classes(bank_rows,after)
    status=(MODEL_GAP if not after else
            "UNRESOLVED_MULTIPLE_CLASSES" if len(labels)>1 else
            "SINGLE_CLASS_WITHIN_BANK")
    return {"status":status,"after":after,"classes":labels,
            "diagnosis_within_bank":labels[0] if len(labels)==1 else None,
            "structural_warning":STRUCTURAL_WARNING,
            "real_world_validity_proven":False}


def scenarios():
    cases=[]
    for cap,ix in zip(EVAL_SINGLE_CAPS,range(3)):
        cases.append({
            "id":f"SINGLE_{cap}_{ix}",
            "truth_type":"single","truth_class":STAGES[ix],
            "capacity":cap,
            "config":make_physical_config((ix,),cap),
        })
    for cap in DOUBLE_CAPS:
        for ix,jx in ((0,1),(0,2),(1,2)):
            cases.append({
                "id":f"DUAL_{cap}_{ix}{jx}",
                "truth_type":"double",
                "truth_class":klass([STAGES[ix],STAGES[jx]]),
                "capacity":cap,
                "config":make_physical_config((ix,jx),cap),
            })
    for cap in EXTRA_CAPS:
        cases.append({
            "id":f"UNKNOWN_EXTRA_{cap}",
            "truth_type":"unknown-extra",
            "truth_class":None,"capacity":cap,
            "config":make_physical_config((),cap,extra=True),
        })
    need(len(cases)==11,"CAF07B_CASE_COUNT_WRONG")
    return cases


def evaluate_case(item,bank_rows,preds,bank_name,folder):
    case_id=item["id"]
    # Selector below sees measurements and bank only, never item config,
    # truth_type, truth_class or the number of physical stages.
    before=read_physical(item["config"],caf07.T0_RATE,
                         caf07.T0_MINUTE,(("delivered",None),))
    survivors=eligible(bank_rows,preds,{"baseline":before})
    first_measure=read_physical(
        item["config"],FIRST["rate"],FIRST["minute"],FIRST["channels"])
    after_first=eligible(
        bank_rows,preds,{FIRST_ACTION_ID:first_measure},survivors)
    first_labels=classes(bank_rows,after_first)
    left=BUDGET-FIRST["cost"]
    choice=choose_second(
        bank_rows,preds,after_first,remaining_budget=left,
        used_actions={FIRST_ACTION_ID})
    prefile=f"01_CHOICE_{case_id}_{bank_name}.json"
    lab.write_new(folder,prefile,{
        "schema":SCHEMA,"case_id":case_id,"bank":bank_name,
        "baseline_observation":before,"first_observation":first_measure,
        "after_first_hypotheses":after_first,
        "selected_next_measurement":choice,
        "spent_before_second":FIRST["cost"],
        "remaining_budget":left,
        "second_DES_calls_so_far":0,
        "second_observation_seen":False,
        "world_truth_not_passed_to_selector":True,
    })
    second_reading=None
    total_cost=FIRST["cost"]
    if choice["action"]:
        action=choice["action"]
        need(action["cost"]<=left,"CAF07B_CUMULATIVE_BUDGET_EXCEEDED")
        second_reading=read_physical(
            item["config"],action["rate"],action["minute"],
            action["channels"])
        total_cost+=action["cost"]
        result=update(bank_rows,preds,after_first,action["id"],
                      second_reading)
    else:
        status=(MODEL_GAP if not after_first else
                "SINGLE_CLASS_WITHIN_BANK" if len(first_labels)==1 else
                THRESHOLD_FAIL)
        result={"status":status,"after":after_first,
                "classes":first_labels,
                "diagnosis_within_bank":
                    first_labels[0] if len(first_labels)==1 else None,
                "structural_warning":STRUCTURAL_WARNING,
                "real_world_validity_proven":False}
    need(total_cost<=BUDGET,"CAF07B_TOTAL_COST_OVER_BUDGET")
    diagnosis=result["diagnosis_within_bank"]
    # Truth only in evaluator. A dual-control labeled single is a FALSE
    # SINGLE diagnosis, even though the bank was internally "pure".
    if diagnosis is None:
        verdict="MODEL_GAP" if result["status"]==MODEL_GAP else "ABSTAIN"
    elif item["truth_class"]==diagnosis:
        verdict="CORRECT_WITHIN_SIMULATED_WORLD"
    elif item["truth_type"] in ("double","unknown-extra") and "+" not in diagnosis:
        verdict="FALSE_SINGLE_DIAGNOSIS"
    else:
        verdict="WRONG_CLASS"
    return {"case":case_id,"bank":bank_name,
            "truth_class_EVALUATOR_ONLY":item["truth_class"],
            "truth_type_EVALUATOR_ONLY":item["truth_type"],
            "initial":before,
            "first_action":FIRST_ACTION_ID,"first_observation":first_measure,
            "survivors_after_first":after_first,
            "selection_before_second":choice,
            "second_observation":second_reading,"final":result,
            "cost_spent":total_cost,"evaluation_DES_runs":
                2+int(second_reading is not None),
            "verdict_EVALUATOR_ONLY":verdict}


def summarize(rows):
    bybank={}
    for bank_name in ("single_only","single_plus_dual"):
        subset=[r for r in rows if r["bank"]==bank_name]
        bytype={}
        for typ in ("single","double","unknown-extra"):
            items=[r for r in subset if r["truth_type_EVALUATOR_ONLY"]==typ]
            bytype[typ]={
                "n":len(items),
                "verdicts":dict(Counter(r["verdict_EVALUATOR_ONLY"]
                                        for r in items)),
                "n_second_measurement":sum(
                    r["second_observation"] is not None for r in items),
                "n_requirement_not_met":sum(
                    r["selection_before_second"]["status"]==THRESHOLD_FAIL
                    for r in items),
                "false_single":sum(
                    r["verdict_EVALUATOR_ONLY"]=="FALSE_SINGLE_DIAGNOSIS"
                    for r in items),
            }
        bybank[bank_name]=bytype
    return bybank


def markdown(result):
    lines=[
        "# CAF-07B — Corrección operativa y controles estructurales ocultos",
        "",
        "PR #116 y PR #117 no modificados. **Laboratorio DES exploratorio**.",
        "Se prioriza resolución robusta de decisión por clase y menor",
        "costo, no cantidad de pares separados ni una utilidad imaginaria.",
        "",
        f"Requisito predeclarado: al menos {MIN_GUARANTEED_PER_SURVIVING_CLASS}",
        "hipótesis robustamente resuelta POR CADA clase superviviente.",
        f"Primera prueba fija: {FIRST_ACTION_ID}, costo {FIRST['cost']}.",
        f"Presupuesto TOTAL por mundo y banco: {BUDGET} unidades ordinales.",
        "La segunda prueba se elige después de observar la primera, si",
        "alguna satisface el requisito con el presupuesto restante.",
        "No se llama óptima a esta primera prueba fija.",
        "",
        "## Comparación: banco antiguo de cuello único vs banco aumentado",
        "",
        "| Banco | Mundo | Verdad estructural | 1.a lectura | 2.a prueba | Lectura | Diagnóstico del banco | Resultado evaluado |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in result["evaluations"]:
        choice=r["selection_before_second"]
        lines.append(
            f"| {r['bank']} | {r['case']} | "+
            f"{r['truth_class_EVALUATOR_ONLY'] or r['truth_type_EVALUATOR_ONLY']} | "+
            f"{r['first_observation']} | "+
            f"{choice['action']['id'] if choice['action'] else choice['status']} | "+
            f"{r['second_observation']} | "+
            f"{r['final']['diagnosis_within_bank'] or r['final']['status']} | "+
            f"{r['verdict_EVALUATOR_ONLY']} |")
    lines+=["",
        "## Controles negativos e interpretación",
        "",
        "- En los seis controles con dos cuellos simultáneos, cada par",
        "de etapas comparte la capacidad nominal (55/h o 90/h).",
        "Ser 'dos cuellos nominales' NO significa que dos colas crezcan",
        "a la vez: la etapa anterior puede limitar lo que llega después.",
        "- En los dos mundos de cuatro etapas, el selector SOLO recibe",
        "la entrega final y las mediciones nombradas de las primeras tres.",
        "La cuarta etapa no se revela como configuración, ni existe",
        "rechazo por mirar el número real de etapas. No detectar la",
        "etapa oculta es un fallo de cobertura, no una validación del modelo.",
        "- Se distinguen certeza de clase DENTRO DEL BANCO, respuesta",
        "correcta en el mundo evaluado y diagnóstico falso de cuello único.",
        "- Si el menú bajo presupuesto no alcanza el requisito, el",
        "selector retorna REQUIREMENT_NOT_MET, no fuerza una medición.",
        "- La tolerancia ±1 es convenio determinista, no intervalo",
        "estadístico. Los costos 1-8 son ordinales ilustrativos;",
        "sin VoI económico y sin una probabilidad de modelos.",
        "- El catálogo aumentado de 24 hipótesis sigue siendo",
        "incompleto: no cubre variación estocástica, más de 3 etapas",
        "ni todos los patrones multi-cuello ni otros mecanismos físicos.",
        "- No se utilizan operadores de stock M/D; ATMS sin cambios.",
        "- Las mediciones corresponden a pruebas DES independientes",
        "con reinicio; la adaptación consiste en elegir la segunda",
        "prueba tras ver la primera, no en cambiar el proceso a mitad",
        "de una sola simulación.",
        f"- Simulaciones DES de banco: {result['bank_DES_runs']};",
        f"evaluaciones DES: {result['evaluation_DES_runs']}.",
        "",
        "## Resumen por estructura",
        "",
    ]
    for bank_name,groups in result["summary"].items():
        lines.append(f"### {bank_name}")
        for typ,values in groups.items():
            lines.append(
                f"- {typ}: {values['n']} mundos; "
                f"veredictos {values['verdicts']}; "
                f"falsos cuellos únicos {values['false_single']}; "
                f"segunda medición {values['n_second_measurement']} veces.")
    lines+=["",
        "## Veredicto de seguridad",
        "",
        "**No hay aprobación para desplegar**: incluso un resultado sin",
        "falsos positivos en este menú no demostraría generalización",
        "a mecanismos reales. La bandera de seguridad explicita si",
        "los controles negativos siguen produciendo falsos cuellos únicos.",
        f"Controles negativos sin falsos cuellos únicos en banco aumentado: "
        f"{result['negative_controls_zero_false_single_expanded']}.",
        f"Diagnósticos correctos del banco ampliado por tipo: "
        f"{result['expanded_correct_diagnoses_by_structure']}.",
        f"**Puerta de promoción:** {result['promotion_gate']}.",
        "Cero falsos positivos por abstención universal NO equivale",
        "a capacidad de identificar estructura; se exige al menos",
        "una decisión correcta por tipo para la mínima cobertura",
        "experimental, sin considerarla validación independiente.",
        "",
    ]
    return "\n".join(lines)


def run(out,source_commit):
    target=Path(out).resolve()
    need(not target.exists(),"CAF07B_OUTPUT_ALREADY_EXISTS")
    need(type(source_commit) is str and
         SOURCE_COMMIT_PATTERN.fullmatch(source_commit),
         "CAF07B_SOURCE_COMMIT_SHA_REQUIRED")
    original_policy=caf07.caf05.d.POLICY.read_bytes()
    banks={"single_only":bank(False),
           "single_plus_dual":bank(True)}
    plans={name:precompute(rows) for name,rows in banks.items()}
    worldlist=scenarios()
    target.mkdir(parents=True,exist_ok=False)
    digests={}
    def write(name,content):
        digests[name]=lab.write_new(target,name,content)
    write("00_PLAN_BANCOS_Y_CODIGO_ANTES_DE_MUNDOS.json",{
        "schema":SCHEMA,"github_source_commit_sha":source_commit,
        "source_commit_verifiable_in_workflow":True,
        "banks":banks,"precomputed_predictions":plans,
        "world_evaluator_configs":worldlist,
        "baseline":{"rate":caf07.T0_RATE,"minute":caf07.T0_MINUTE},
        "fixed_first_action":FIRST,
        "candidate_second_actions":list(ACTIONS),
        "quality_requirement_per_surviving_class":
            MIN_GUARANTEED_PER_SURVIVING_CLASS,
        "tolerance_orders":TOLERANCE,
        "cumulative_budget_units":BUDGET,
        "stage_count_or_truth_not_passed_to_selector":True,
        "public_exploratory_not_independent":True,
        "CAF02_policy_sha256":lab.sha(original_policy),
        "evaluation_world_DES_calls_before_plan":0,
        "no_external_custody":True,
    })
    write("00B_CHECKPOINT_PRE_EVALUACION.json",{
        "plan_sha256":digests["00_PLAN_BANCOS_Y_CODIGO_ANTES_DE_MUNDOS.json"],
        "source_commit":source_commit,
        "evaluation_DES_calls":0,"second_action_selection_not_yet_run":True,
    })
    outputs=[]
    for bank_name,rows in banks.items():
        for world in worldlist:
            outputs.append(evaluate_case(
                world,rows,plans[bank_name],bank_name,target))
    need(caf07.caf05.d.POLICY.read_bytes()==original_policy,
         "CAF07B_LEGACY_POLICY_MUTATED")
    summary=summarize(outputs)
    negative_clean=all(summary["single_plus_dual"][typ][
        "false_single"]==0 for typ in ("double","unknown-extra"))
    expanded_diagnoses_by_structure={
        typ:summary["single_plus_dual"][typ]["verdicts"].get(
            "CORRECT_WITHIN_SIMULATED_WORLD",0)
        for typ in ("single","double")
    }
    expanded_has_minimum_diagnostic_coverage=all(
        n>=1 for n in expanded_diagnoses_by_structure.values())
    promotion_gate=(
        "BLOCKED_NO_DIAGNOSTIC_COVERAGE"
        if not expanded_has_minimum_diagnostic_coverage else
        "BLOCKED_NOT_INDEPENDENTLY_VALIDATED"
    )
    final={
        "schema":SCHEMA,
        "status":"CAF07B_DECISION_THRESHOLD_AND_CONDITIONAL_SECOND_EXECUTED",
        "source_commit":source_commit,
        "bank_DES_runs":sum(
            len(rows)*(1+len(ACTIONS)) for rows in banks.values()),
        "evaluation_DES_runs":sum(x["evaluation_DES_runs"]
                                   for x in outputs),
        "n_scenarios":len(worldlist),"n_evaluations":len(outputs),
        "quality_threshold_per_class":
            MIN_GUARANTEED_PER_SURVIVING_CLASS,
        "budget_is_cumulative":True,
        "costs_are_illustrative":True,
        "evaluator_truth_used_in_policy":False,
        "hidden_extra_stage_rejected_using_known_topology":False,
        "M_D_observation_operators_modified":False,
        "negative_controls_zero_false_single_expanded":negative_clean,
        "expanded_correct_diagnoses_by_structure":
            expanded_diagnoses_by_structure,
        "expanded_has_minimum_diagnostic_coverage":
            expanded_has_minimum_diagnostic_coverage,
        "promotion_gate":promotion_gate,
        "zero_false_singles_can_be_vacuous_when_no_diagnoses":True,
        "deployment_validated":False,
        "summary":summary,"evaluations":outputs,
    }
    write("01_RESULTADOS.json",final)
    write("02_INFORME.md",markdown(final))
    write("03_MANIFIESTO.json",{
        "schema":SCHEMA,"files_sha256":digests,
        "source_commit":source_commit,
        "plan_saved_before_all_new_world_DES":True,
        "choices_saved_before_each_followup_DES":True,
        "external_custody":False,"exploratory_only":True,
        "scientific_performance_guaranteed":False,
    })
    return final


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--source-commit",required=True)
    args=parser.parse_args()
    report=run(args.out,args.source_commit)
    print(json.dumps({
        "status":report["status"],
        "commit":report["source_commit"],
        "summary":report["summary"],
        "evaluation_DES_runs":report["evaluation_DES_runs"],
        "negative_controls_zero_false_single_expanded":
            report["negative_controls_zero_false_single_expanded"],
        "deployment_validated":report["deployment_validated"],
    },sort_keys=True))


if __name__=="__main__":
    main()
