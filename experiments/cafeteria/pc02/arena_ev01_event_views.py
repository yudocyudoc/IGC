#!/usr/bin/env python3
"""ARENA EV01: ONE physically conserved event trace, THREE disclosure views.

No topology inversion, no capacity grid and no latent-stage assertions.
The privately instrumented fourth station is visible only in FULL; the
analyst of POS/KDS never receives its identity or hidden-event ordinals.
"""
from __future__ import annotations
import argparse
from collections import deque
import csv
from fractions import Fraction as Q
from hashlib import sha256
from heapq import heappush, heappop
import json
from pathlib import Path

import caf07b_umbral_secuencial as b
from experiments.cafeteria.pc01 import caf01_des_engine as des
from scripts import arena_event_observability as obs

SCHEMA="igc-arena-eventlog-three-views/0.1"
PRECOMMIT="6bd6c224578fa90af6e9a2ce348981839bfd7f5e"
GATE=obs.GATE
STAGES=("caja","preparacion","despacho","transferencia_final")
SPEC=((2,Q(1)),(1,Q(60,68)),(1,Q(60,86)),(1,Q(60,220)))
CHECKPOINTS=tuple(map(Q,(0,2,4,6,8,10,14,20,30)))
ARRIVALS=des.half_open_arrivals("5/2",6)
VIEWS=obs.VIEWS


def need(ok,code):
    if not ok: raise ValueError(code)


def config():
    cfg={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
         "stages":[{"servers":n,"service_minutes":str(t)} for n,t in SPEC]}
    need(des.validate_private_config(cfg)==SPEC,"EV01_DES_CONFIG_DRIFT")
    return cfg


def trace_generator():
    """Separately implemented FCFS scheduler, with FULL event timestamps."""
    waiting=[deque() for _ in SPEC]
    busy=[{} for _ in SPEC] # physical server index -> case id
    heap=[]
    serial=0
    accepted=delivered=0
    completed=set()
    for i,time in enumerate(ARRIVALS):
        heappush(heap,(time,1,serial,"accept",-1,i,-1));serial+=1
    trace=[]
    snapshots=[]

    def emit(kind,time,order,stage=None,resource=None):
        stage_name=STAGES[stage] if stage is not None else None
        event={
            "event_seq":len(trace),
            "case_id":f"O{order:03d}",
            "event_type":kind,
            "activity":f"{kind}::{stage_name}" if stage is not None else kind,
            "t_minutes_exact":str(time),
            "stage":stage_name,
            "resource_id":f"{stage_name}-r{resource+1}" if resource is not None else None,
            "provenance_EVALUATOR_ONLY":"PHYSICAL_SYNTHETIC_EVENT_ENGINE",
        }
        trace.append(event)

    def check():
        material=sum(len(q)+len(active) for q,active in zip(waiting,busy))
        need(accepted==delivered+material,"EV01_MASS_BALANCE")
        need(all(len(active)<=SPEC[s][0] for s,active in enumerate(busy)),
             "EV01_SERVER_CAPACITY")
        ids=[x for q in waiting for x in q]+[
            x for a in busy for x in a.values()]
        need(len(ids)==len(set(ids)) and not (set(ids)&completed),
             "EV01_DUPLICATE_ORDER")
        need(len(completed)==delivered,"EV01_DELIVERED_ACCOUNTING")
        return material

    for target in CHECKPOINTS:
        while heap and heap[0][0]<=target:
            now=heap[0][0]
            batch=[]
            while heap and heap[0][0]==now:
                batch.append(heappop(heap))
            # Complete first, accept second, then all starts downstream-first.
            for _,_,_,kind,stage,order,resource in batch:
                if kind!="complete": continue
                need(busy[stage].get(resource)==order,
                     "EV01_UNSCHEDULED_COMPLETION")
                del busy[stage][resource]
                emit("servicio_fin",now,order,stage,resource)
                if stage+1<len(SPEC):
                    waiting[stage+1].append(order)
                    emit("etapa_entrada",now,order,stage+1)
                else:
                    need(order not in completed,"EV01_DOUBLE_DELIVERY")
                    completed.add(order)
                    delivered+=1
                    emit("pedido_entregado",now,order)
            for _,_,_,kind,stage,order,resource in batch:
                if kind!="accept": continue
                accepted+=1
                waiting[0].append(order)
                emit("pedido_creado",now,order)
                emit("pago_confirmado",now,order)
                emit("etapa_entrada",now,order,0)
            for stage in reversed(range(len(SPEC))):
                max_servers,service_time=SPEC[stage]
                while waiting[stage] and len(busy[stage])<max_servers:
                    order=waiting[stage].popleft()
                    available=min(set(range(max_servers))-set(busy[stage]))
                    busy[stage][available]=order
                    emit("servicio_inicio",now,order,stage,available)
                    heappush(heap,(now+service_time,0,serial,
                                   "complete",stage,order,available))
                    serial+=1
            check()
        pending=check()
        snapshots.append({
            "time":str(target),"accepted":accepted,
            "delivered":delivered,"pending":pending,
            "waiting":[len(q) for q in waiting],
            "in_service":[len(a) for a in busy],
        })
    need(accepted==delivered==len(ARRIVALS)==15 and not heap,
         "EV01_ORDERS_NOT_COMPLETELY_DRAINED")
    need(len(trace)==15*(3+3*4),"EV01_EVENT_COUNT_DRIFT")
    return trace,snapshots


def verify_des_parity(snapshots):
    native=des.run_toy_engine(config(),ARRIVALS,CHECKPOINTS)
    need(len(native)==len(snapshots),"EV01_PARITY_SIZE")
    for n,record in zip(native,snapshots):
        need(record=={
            "time":str(n.t_min),"accepted":n.accepted_cum_orders,
            "delivered":n.delivered_cum_orders,"pending":n.pending_orders,
            "waiting":list(n.stage_waiting),
            "in_service":list(n.stage_in_service),
        },"EV01_INDEPENDENT_DES_PARITY_FAIL")
    return {"status":"PARITY_CONFIRMED_ALL_SNAPSHOTS",
            "n_checkpoints":len(snapshots),
            "mass_balance_checked_at_every_event":True,
            "resources_checked_at_every_event":True}


def inspect_visibility(a,bb,cc,analyses):
    """All three views must represent identical order lifecycle, not worlds."""
    views={"POS":a,"POS_KDS":bb,"FULL":cc}
    need({k:len(v) for k,v in views.items()}==
         {"POS":45,"POS_KDS":75,"FULL":225},
         "EV01_VIEW_EVENT_COUNTS")
    for name,rows in views.items():
        need([r["event_seq"] for r in rows]==list(range(len(rows))),
             "EV01_HIDDEN_EVENT_SEQUENCE_LEAK")
        if name!="FULL":
            need(all("resource_id" not in row and
                     row.get("stage")!="transferencia_final"
                     for row in rows),"EV01_TRUTH_LEAK")
    need(all("stage" not in row for row in a),"EV01_POS_STAGE_LEAK")
    need({row.get("stage") for row in bb if "stage" in row}=={"preparacion"},
         "EV01_KDS_STAGE_LEAK")
    def shared(rows):
        return {(r["case_id"],r["activity"],r["t_minutes_exact"]) for r in rows}
    need(shared(a)<=shared(bb)<=shared(cc),"EV01_VIEW_NOT_NESTED")
    measures={v:{row["case_id"]:row["cycle_minutes_exact"]
                 for row in analyses[v]["cases"]} for v in VIEWS}
    need(measures["POS"]==measures["POS_KDS"]==measures["FULL"],
         "EV01_CYCLE_TIME_CHANGED_ACROSS_VIEWS")
    need(all(r["cycle_balance_exact"] for r in analyses["FULL"]["cases"]),
         "EV01_PHYSICAL_CYCLE_BALANCE")
    need(all("per_stage_observed" not in r
             for v in ("POS","POS_KDS") for r in analyses[v]["cases"]),
         "EV01_ANALYST_TRUTH_LEAK")
    return {"same_cases":15,
            "shared_events_same_time":True,
            "all_view_event_sequences_locally_reindexed":True,
            "full_15_of_15_cycle_balances":True,
            "stage4_appears_only_by_direct_instrumentation":True,
            "pos_cannot_decompose_wait_vs_service":True,
            "kds_post_prep_gap_cannot_prove_hidden_stage":True}


def write_json(root,name,obj):
    return b.lab.write_new(root,name,obj)


def write_csv(root,name,events,view):
    fields=["case_id","event_seq","activity","event_type",
            "t_minutes_exact","source"]
    if view!="POS": fields.append("stage")
    if view=="FULL": fields.append("resource_id")
    out=root/name
    need(not out.exists(),"EV01_REFUSE_OVERWRITE_CSV")
    with out.open("w",encoding="utf-8",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields,extrasaction="raise")
        w.writeheader()
        w.writerows(events)
    return out


def run(root,checkout_sha,head_sha):
    need(bool(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha))
         and bool(b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha)),
         "EV01_GIT_SHAS_REQUIRED")
    root=Path(root).resolve()
    need(not root.exists(),"EV01_REFUSE_OVERWRITE")
    root.mkdir(parents=True,exist_ok=False)
    write_json(root,"00_PLAN_BEFORE_TRACE.json",{
        "schema":SCHEMA,"precommit":PRECOMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "arrival_rate_per_minute":"5/2","arrival_window":"[0,6)",
        "n_order_entities":len(ARRIVALS),
        "frozen_stages":[{"stage":name,"servers":n,
            "service_minutes_exact":str(t)}
            for name,(n,t) in zip(STAGES,SPEC)],
        "checkpoint_minutes":[str(t) for t in CHECKPOINTS],
        "three_observability_views":list(VIEWS),
        "pos_kds_service_timestamps_are_idealized":True,
        "unknown_stage_detection_not_an_objective":True,
        "pm4py_version_pinned_in_CI":"2.7.23.11",
        "pm4py_dependency_license":"AGPL-3.0, review for commercial use",
        "no_parameter_grid":True,
        "scientific_gate":GATE,
    })
    full,snaps=trace_generator()
    parity=verify_des_parity(snaps)
    views={v:obs.project_events(full,v) for v in VIEWS}
    analyses={v:obs.analyze_view(views[v],v,STAGES) for v in VIEWS}
    disclosure=inspect_visibility(*(views[v] for v in VIEWS),analyses)
    discovery={v:obs.pm4py_dfg(views[v]) for v in VIEWS}
    need(all(discovery[v]["n_cases"]==15 for v in VIEWS),
         "EV01_PM4PY_LOST_CASES")
    need(all("transferencia_final" not in str(discovery[v])
             for v in ("POS","POS_KDS")),"EV01_MINING_LEAKED_STAGE")
    need("transferencia_final" in str(discovery["FULL"]),
         "EV01_INSTRUMENTED_STAGE_NOT_IN_DFG")
    # Auditors get separately tagged full truth; the POS/KDS inference
    # functions were already run on projected allowlisted input only.
    write_json(root,"00B_EVALUATOR_ONLY_PHYSICAL_TRACE.json",{
        "schema":SCHEMA,"NOT_ANALYST_INPUT":True,
        "full_physical_truth":full,"checkpoints":snaps,
        "independent_DES_parity":parity})
    for v in VIEWS:
        write_csv(root,"01_"+v+"_PUBLIC_EVENTS.csv",views[v],v)
    result={
        "schema":SCHEMA,"precommit":PRECOMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "same_world_three_views":True,
        "n_orders":15,"n_internal_stages_EVALUATOR_ONLY":4,
        "n_event_rows_by_view":{v:len(views[v]) for v in VIEWS},
        "parity":parity,
        "visibility_audit":disclosure,
        "analyses":analyses,
        "pm4py_discovery":discovery,
        "no_inference_of_unknown_stage_from_residual":True,
        "process_DFG_does_not_identify_causal_mechanisms":True,
        "no_grid_or_catalog":True,
        "no_external_real_data":True,
        "promotion_gate":GATE,
    }
    write_json(root,"02_RESULTS.json",result)
    lines=[
        "# ARENA EV01 — Mismo mundo, tres niveles de evidencia",
        "",
        "**No es un detector de estaciones ocultas.** El nivel C observa directamente",
        "las cuatro etapas, mientras A y B solamente reciben sus eventos autorizados.",
        "",
        "| Vista | Eventos observados | Casos | ¿Ciclo observado? | ¿Servicio preparación? | ¿Espera/servicio de todas las etapas? | ¿Se ve etapa 4? |",
        "|---|---:|---:|---|---|---|---|",
        "| POS | 45 | 15 | Sí | No | No | No |",
        "| POS+KDS idealizado | 75 | 15 | Sí | Sí, si timestamps son físicos | No | No |",
        "| Instrumentación completa | 225 | 15 | Sí | Sí | Sí, observado directamente | Sí |",
        "",
        "## Qué aprendimos",
        "",
        "- **POS:** un tiempo total positivo admite varias asignaciones temporales",
        "  distintas entre servicio y espera. El sistema **no** infiere reparto ni",
        "  determina número de etapas a partir de la duración total.",
        "- **POS+KDS idealizado:** inicio y fin de preparación revelan duración de",
        "  ese servicio, pero no cuándo entró el pedido a su cola ni cómo se",
        "  descompone el lapso preparación-fin a entrega. Este residual NO prueba",
        "  una transferencia o estación adicional.",
        "- **FULL:** se registran los límites de las cuatro etapas, se miden",
        "  esperas y servicios por pedido y 15/15 balances temporales cierran.",
        "  La transferencia final es **observada**, NO inferida.",
        "- **PM4Py:** los tres DFG tienen actividades distintas porque la",
        "  observación es distinta. Una arista es sucesión observada,",
        "  no relación causal o prueba de la topología física.",
        "- **Paridad:** motor de eventos local y CAF-01 concuerdan en las",
        "  nueve observaciones físicas de conteo, WIP y servidores.",
        "- **Dependencia:** PM4Py 2.7.23.11 (AGPL-3.0); revisar licencia",
        "  antes de integrarlo en software comercial.",
        "",
        "## Descubrimiento PM4Py por vista",
        "",
        "| Vista | Actividades distintas | Aristas DFG | Versión |",
        "|---|---:|---:|---|",
    ]
    for v in VIEWS:
        d=discovery[v]
        lines.append(f"| {v} | {d['n_activities']} | {len(d['edges'])} | {d['pm4py_version']} |")
    lines.extend(["",
        "## Límites y siguiente trabajo",
        "",
        "- Operación sintética determinista de 15 pedidos; cero datos POS/KDS",
        "  reales, cero distribución calibrada y sin variación de recursos.",
        "- El plan no infiere capacidades con un banco de parámetros.",
        "- El ejemplo de dos descomposiciones temporales no es una prueba de",
        "  factibilidad de dos redes completas bajo los mismos recursos; sí",
        "  demuestra que los endpoints por sí solos no fijan espera y servicio.",
        "- Un proceso observado no equivale a una estructura causal completa.",
        "- No se conecta todavía D/B/M ni se escribe al ledger o ATMS.",
        "- La siguiente tarea es leer un log externo con semántica de hitos",
        "  verificada, después analizar modelos de incertidumbre y colas.",
        "",
        "Gate: "+GATE,
    ])
    write_json(root,"03_REPORT.md","\n".join(lines))
    manifest={p.name:"sha256:"+sha256(p.read_bytes()).hexdigest()
              for p in sorted(root.iterdir()) if p.is_file()}
    write_json(root,"04_MANIFEST.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "files_sha256":manifest,"all_public_views_redacted":True,
        "no_actual_business_data":True,
    })
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    a=p.parse_args()
    report=run(a.out,a.checkout_sha,a.head_sha)
    print(json.dumps({
        "n_cases":report["n_orders"],
        "n_event_rows_by_view":report["n_event_rows_by_view"],
        "physical_parity":report["parity"]["status"],
        "gate":report["promotion_gate"]},sort_keys=True))
