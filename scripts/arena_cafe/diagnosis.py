# F0-HIST promoted copy: source Git blob a3b900db0993af8246e6f64a5f7e05833b50bc46; import-only changes, see manifest.
#!/usr/bin/env python3
"""Arena Café: practical diagnosis from the ACTUAL instrumented cafe events.

No banks of 24/720 hypotheses. No external datasets. Three source views of
the *same* physical cafe are respected. A physical stage diagnosis is made
only on FULL instrumented events; POS/KDS remain partial observations.
Counterfactuals are computed with the existing CAF-01 DES, not a new engine.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_cafe import ev01
from scripts import arena_event_observability as observable
from scripts.arena_physical import des_engine as des

SCHEMA="igc-arena-cafe-operational-diagnosis/0.1"
STAGE_FIELD_TYPES=("etapa_entrada","servicio_inicio","servicio_fin")
CHECKPOINTS=(Q(0),Q(2),Q(4),Q(6),Q(8),Q(10))
FIXED_MEAL="15 orders, 0-6 minutes, 150/hour synthetic arrivals"


def need(p,tag):
    if not p:
        raise ValueError(tag)


def as_fraction(r):
    try: return Q(r)
    except (TypeError,ValueError,ZeroDivisionError) as ex:
        raise ValueError("CAFE_BAD_EXACT_TIME") from ex


def read_full_csv(filename):
    """Consume an EV-01 FULL export, *never* silently upgrade POS/KDS."""
    path=Path(filename)
    need(path.is_file(),"CAFE_EVENT_FILE_NOT_FOUND")
    with path.open(encoding="utf-8",newline="") as fh:
        r=csv.DictReader(fh)
        expected={"case_id","event_seq","activity","event_type",
                  "t_minutes_exact","source","stage","resource_id"}
        need(set(r.fieldnames or ())==expected,
             "CAFE_FULL_INSTRUMENTATION_REQUIRED")
        rows=[]
        for line in r:
            need(set(line)==expected and all(v is not None for v in line.values()),
                 "CAFE_MALFORMED_CSV_ROW")
            try:
                seq=int(line["event_seq"])
            except (TypeError,ValueError) as ex:
                raise ValueError("CAFE_BAD_EVENT_SEQUENCE") from ex
            need(str(seq)==line["event_seq"] and seq>=0,
                 "CAFE_BAD_EVENT_SEQUENCE")
            row={**line,"event_seq":seq}
            if row["stage"]=="": row.pop("stage")
            if row["resource_id"]=="": row.pop("resource_id")
            rows.append(row)
    need(rows and [e["event_seq"] for e in rows]==list(range(len(rows))),
         "CAFE_NONCONTIGUOUS_EVENTS")
    return rows


def infer_stage_order(full):
    """Stage order from explicitly observed entrances, not a fixed catalog."""
    groups=observable.group_by_case(full)
    need(groups,"CAFE_NO_CASES")
    paths=[]
    for case,events in groups.items():
        entrances=[e["stage"] for e in events
                   if e["event_type"]=="etapa_entrada"]
        need(len(entrances)==len(set(entrances)) and entrances,
             "CAFE_INCOMPLETE_STAGE_ENTRANCES")
        paths.append(tuple(entrances))
    need(all(path==paths[0] for path in paths),
         "CAFE_BRANCHING_NOT_SUPPORTED_IN_TANDEM_DIAGNOSIS")
    return paths[0]


def average(nums):
    need(bool(nums),"CAFE_EMPTY_STAT")
    return str(sum(nums,Q(0))/len(nums))


def percent_share(numer,denom):
    need(denom>0,"CAFE_BAD_DENOMINATOR")
    return round(float(100*numer/denom),3)


def queue_peaks(full,stages):
    """At *event-time boundaries*, waiting=#entered-#service-started.

    Group all simultaneous events before evaluating to avoid artificial peaks
    produced by arbitrary processing order of ties.
    """
    ledger={s:defaultdict(lambda:0) for s in stages}
    for e in full:
        stage=e.get("stage")
        if stage not in ledger: continue
        t=as_fraction(e["t_minutes_exact"])
        if e["event_type"]=="etapa_entrada":
            ledger[stage][t]+=1
        elif e["event_type"]=="servicio_inicio":
            ledger[stage][t]-=1
    peak={}
    for stage,changes in ledger.items():
        q=maximum=0
        for time in sorted(changes):
            q+=changes[time]
            need(q>=0,"CAFE_NEGATIVE_QUEUE_FROM_EVENTS")
            maximum=max(maximum,q)
        need(q==0,"CAFE_UNDRAINED_QUEUE")
        peak[stage]=maximum
    return peak


def diagnosis(full,declared_servers):
    stages=infer_stage_order(full)
    need(tuple(declared_servers)==stages,
         "CAFE_SERVER_SCHEMA_NOT_MATCH_STAGE_OBSERVATION")
    need(all(type(n) is int and n>=1 for n in declared_servers.values()),
         "CAFE_INVALID_SERVER_CAPACITY")
    # Existing EV-01 layer checks every recorded entrance/start/finish,
    # order closure and resource collisions.
    checked=observable.analyze_view(full,"FULL",stages)
    case_measures=checked["cases"]
    n=len(case_measures)
    created=[as_fraction(r["t_minutes_exact"]) for r in full
             if r["event_type"]=="pedido_creado"]
    delivered=[as_fraction(r["t_minutes_exact"]) for r in full
               if r["event_type"]=="pedido_entregado"]
    need(len(created)==len(delivered)==n,"CAFE_LIFECYCLE_INCOMPLETE")
    span=max(delivered)-min(created)
    need(span>0,"CAFE_ZERO_OBSERVATION_WINDOW")
    waiting_totals={}
    busy_totals={}
    details={}
    peaks=queue_peaks(full,stages)
    for stage in stages:
        waits=[Q(case["per_stage_observed"][stage]["wait_minutes_exact"])
               for case in case_measures]
        services=[Q(case["per_stage_observed"][stage]["service_minutes_exact"])
                  for case in case_measures]
        waits_total=sum(waits,Q(0))
        services_total=sum(services,Q(0))
        waiting_totals[stage]=waits_total
        busy_totals[stage]=services_total
        occupied={e["resource_id"] for e in full
                  if e["event_type"]=="servicio_inicio" and e.get("stage")==stage}
        need(len(occupied)<=declared_servers[stage],
             "CAFE_OBSERVED_RESOURCE_EXCEEDS_CAPACITY")
        details[stage]={
            "n_orders":n,
            "servers_declared":declared_servers[stage],
            "servers_seen_in_trace":len(occupied),
            "mean_wait_minutes_exact":average(waits),
            "mean_service_minutes_exact":average(services),
            "total_wait_minutes_exact":str(waits_total),
            "total_busy_minutes_exact":str(services_total),
            "max_waiting_at_event_boundaries":peaks[stage],
            "orders_that_waited":sum(w>0 for w in waits),
            "share_total_wait_percent":0,
            "utilization_percent_over_full_cycle_window":percent_share(
                services_total,span*declared_servers[stage]),
        }
    total_wait=sum(waiting_totals.values(),Q(0))
    need(total_wait>0,"CAFE_NO_WAIT_OBSERVED_NOT_DIAGNOSTIC")
    for stage in stages:
        details[stage]["share_total_wait_percent"]=percent_share(
            waiting_totals[stage],total_wait)
    # Tie-break deterministically by stage order; evidence is measured waiting
    # time, NOT a declaration of universal causal capacity bottleneck.
    ranked=sorted(stages,key=lambda stage:(
        -waiting_totals[stage],stages.index(stage)))
    cycles=[Q(case["cycle_minutes_exact"]) for case in case_measures]
    return {
        "n_orders":n,
        "n_stages_actually_instrumented":len(stages),
        "stage_order_directly_observed":list(stages),
        "window_minutes_exact":str(span),
        "mean_cycle_minutes_exact":average(cycles),
        "total_wait_all_orders_minutes_exact":str(total_wait),
        "mean_wait_all_stages_minutes_exact":str(total_wait/n),
        "ranked_waiting_pressure":ranked,
        "top_waiting_stage":ranked[0],
        "stage_metrics":details,
        "cycle_balances_passed":n,
        "rank_is_observed_queue_pressure_not_causal_intervention_proof":True,
        "not_trained_on_a_parameter_grid":True,
    }


def compare_capacity_scenarios(config,arrivals,checkpoints,proposals):
    """Reuse CAF-01 DES for simple, feasible-to-discuss *simulations*."""
    base=des.run_toy_engine(config,arrivals,checkpoints)
    def compact(snap):
        return {
            "t_min":str(snap.t_min),
            "delivered":snap.delivered_cum_orders,
            "pending":snap.pending_orders,
            "waiting_by_stage":list(snap.stage_waiting),
            "in_service_by_stage":list(snap.stage_in_service),
        }
    ref={str(s.t_min):compact(s) for s in base}
    alternatives={}
    for label,index in proposals.items():
        need(type(index) is int and 0<=index<len(config["stages"]),
             "CAFE_BAD_PROPOSAL_STAGE")
        candidate={
            **config,
            "stages":[dict(stage) for stage in config["stages"]],
        }
        candidate["stages"][index]["servers"]+=1
        des.validate_private_config(candidate)
        simulation=des.run_toy_engine(candidate,arrivals,checkpoints)
        series={str(s.t_min):compact(s) for s in simulation}
        alternatives[label]={
            "extra_worker_stage":index,
            "snapshots":series,
            "delta_delivered_vs_baseline":{
                t:series[t]["delivered"]-ref[t]["delivered"]
                for t in ref},
            "delta_pending_vs_baseline":{
                t:series[t]["pending"]-ref[t]["pending"]
                for t in ref},
            "not_a_real_world_intervention":True,
            "assumes_extra_physical_workstation_capacity":True,
        }
    return {
        "baseline_snapshots":ref,
        "alternatives":alternatives,
        "model":"CAF01_DETERMINISTIC_DES",
        "counterfactuals_do_not_measure_cost_or_workstation_feasibility":True,
    }


def run(out,checkout_sha,head_sha):
    need(len(checkout_sha)==len(head_sha)==40 and
         all(c in "0123456789abcdef" for c in checkout_sha+head_sha),
         "CAFE_REAL_GIT_SHAS_REQUIRED")
    root=Path(out)
    need(not root.exists(),"CAFE_REFUSE_OVERWRITE")
    root.mkdir(parents=True)
    original,snapshots=ev01.trace_generator()
    ev01.verify_des_parity(snapshots)
    event_log=observable.project_events(original,"FULL")
    stage_servers=dict(zip(ev01.STAGES,(x[0] for x in ev01.SPEC)))
    outcome=diagnosis(event_log,stage_servers)
    counter=compare_capacity_scenarios(
        ev01.config(),ev01.ARRIVALS,CHECKPOINTS,
        {"extra_preparation":1,"extra_cashier":0})
    evidence={
        "schema":SCHEMA,
        "checkout_sha":checkout_sha,
        "pr_head_sha":head_sha,
        "physical_source":"EV01_SYNTHETIC_CAFE_15_ORDERS",
        "uses_only_full_instrumentation_for_internal_waits":True,
        "full_operational_diagnosis":outcome,
        "counterfactuals":counter,
        "measured_demand_rate_per_hour":150,
        "real_business_validated":False,
        "recommendation":"SIMULATE_EXTRA_PREPARATION_CAPACITY_FIRST"
            if max(counter["alternatives"]["extra_preparation"]["delta_delivered_vs_baseline"].values())>
               max(counter["alternatives"]["extra_cashier"]["delta_delivered_vs_baseline"].values())
            else "NO_UNIQUE_ACTION_FROM_THIS_SIMULATION",
        "physical_feasibility_and_cost_not_verified":True,
    }
    # Source views are never converted into privileged FULL observations.
    pos=observable.analyze_view(
        observable.project_events(original,"POS"),"POS")
    kds=observable.analyze_view(
        observable.project_events(original,"POS_KDS"),"POS_KDS")
    need(all("per_stage_observed" not in case for view in (pos,kds)
             for case in view["cases"]),"CAFE_PARTIAL_VIEW_LEAK")
    evidence["observability"]={
        "POS":pos["observability_claim"],
        "POS_KDS":kds["observability_claim"],
        "FULL":"STAGE_WAITS_MEASURED_NOT_INFERRED",
    }
    def put(name,body):
        p=root/name
        if not isinstance(body,str):
            body=json.dumps(body,indent=2,sort_keys=True,
                            ensure_ascii=False)+"\n"
        p.write_text(body,encoding="utf-8")
    put("01_RESULT.json",evidence)
    table=[
        "# Diagnóstico operativo · Cafetería simulada",
        "",
        "**Una misma cafetería, 15 pedidos, registro físico completo.**",
        "",
        "| Etapa | Pedidos que esperaron | Espera media (min) | Espera máxima en cola (pedidos) | % de toda la espera | Ocupación observada |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for stage in ev01.STAGES:
        s=outcome["stage_metrics"][stage]
        table.append(
            f"| {stage} | {s['orders_that_waited']} | "
            f"{float(Q(s['mean_wait_minutes_exact'])):.3f} | "
            f"{s['max_waiting_at_event_boundaries']} | "
            f"{s['share_total_wait_percent']:.1f}% | "
            f"{s['utilization_percent_over_full_cycle_window']:.1f}% |")
    table.extend([
        "",
        "**Mayor concentración de espera observada:** "+outcome["top_waiting_stage"]+".",
        "",
        "## Contrafactual con el motor CAF-01 existente",
        "",
        "| Minuto | Entregas base | +1 preparación | +1 caja | Pedidos pendientes base |",
        "|---|---:|---:|---:|---:|",
    ])
    base=counter["baseline_snapshots"]
    cprep=counter["alternatives"]["extra_preparation"]["snapshots"]
    ccaja=counter["alternatives"]["extra_cashier"]["snapshots"]
    for t in base:
        table.append(
            f"| {t} | {base[t]['delivered']} | {cprep[t]['delivered']} | "
            f"{ccaja[t]['delivered']} | {base[t]['pending']} |")
    table.extend([
        "",
        "La comparación muestra el comportamiento del **mismo DES determinista**",
        "al añadir capacidad en una etapa. No equivale a un efecto causal",
        "validado en una cafetería real; no hay costos, espacio ni nuevas",
        "distribuciones de servicio verificadas.",
        "",
        "**Datos POS/KDS no habilitan este diagnóstico interno.** Solo el",
        "registro FULL contiene entrada, inicio y fin de servicio de cada",
        "pedido por etapa. Ningún residuo demuestra estaciones ocultas.",
        "",
        "**Siguiente decisión tangible:** revisar si preparación dispone de",
        "infraestructura física para una segunda estación; si se dispone,",
        "comparar con medidas reales de colas y servicio antes de contratar.",
        "",
    ])
    put("02_DIAGNOSTICO.md","\n".join(table))
    hashes={p.name:"sha256:"+sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.iterdir()) if p.is_file()}
    put("03_MANIFEST.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,
        "pr_head_sha":head_sha,"files_sha256":hashes})
    return evidence


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    a=p.parse_args()
    res=run(a.out,a.checkout_sha,a.head_sha)
    print(json.dumps({
        "n_orders":res["full_operational_diagnosis"]["n_orders"],
        "top_waiting_stage":res["full_operational_diagnosis"]["top_waiting_stage"],
        "recommendation":res["recommendation"],
        "real_business_validated":False,
    },sort_keys=True))
