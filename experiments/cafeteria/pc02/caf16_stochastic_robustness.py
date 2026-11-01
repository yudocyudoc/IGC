#!/usr/bin/env python3
"""CAF-16: independent stochastic FCFS event engine vs frozen deterministic analyst.

Synthetic stochastic service is NOT externally calibrated or a real-world DES
validation. All results stratify physical CV and sensor perturbation separately.
"""
from __future__ import annotations

import argparse
from collections import deque, Counter
from fractions import Fraction as Q
from hashlib import sha256
from heapq import heappop, heappush
import json
from pathlib import Path
import random

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
import caf15a_two_capacity_witnesses as v15a
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA = "igc-caf16-stochastic-independent-event-engine/0.1"
PROTO_COMMIT = "5f7299dea32b9eec654b3f4a43f237b88b1f392c"
GATE = "BLOCKED_SYNTHETIC_STOCHASTIC_SERVICE_UNCALIBRATED_SENSORS_NO_EXTERNAL_VALIDATION"
MASTER_SEED = "IGC-CAF16-20261031-v1"
CVS = ("CV0", "CV25", "CV50")
MULTIPLIERS = {
    "CV0": (Q(1),),
    "CV25": (Q(3,4), Q(5,4)),
    "CV50": (Q(1,2), Q(3,2)),
}
ERRORS=("E0","E1")
PROGRAMS=("HIGH_T20","SHAPED_T14_T20")
REPS=12
SINGLES=(68,83,97)
DUALS=((68,70),(70,68),(83,86),(86,83),(95,100),(100,95))
EXTRAS=(64,106,220)
CHANNELS=v15a.CHANNELS

def need(ok,code):
    if not ok:
        raise ValueError(code)


def seed_for(*parts):
    msg="|".join([MASTER_SEED]+[str(p) for p in parts]).encode("utf-8")
    return int.from_bytes(sha256(msg).digest()[:16],"big")


def arrival_pulse(rate,duration=20,offset=0):
    return tuple(Q(offset)+t for t in des.half_open_arrivals(rate,duration))


def shaped_arrivals():
    # Each local segment has arrivals strictly before the next boundary.
    seq=(arrival_pulse("6/5",6,0)
         +arrival_pulse("5/2",8,6)
         +arrival_pulse("6/5",6,14))
    need(all(x<y for x,y in zip(seq,seq[1:])),
         "CAF16_BAD_SHAPED_ARRIVALS")
    need(len(seq)==34 and all(t<20 for t in seq),
         "CAF16_SHAPED_COUNT_DRIFT")
    return seq


def scenarios():
    return {
        "K0":(arrival_pulse("6/5",10),(Q(0),Q(10))),
        "K1":(arrival_pulse("3/2",20),(Q(0),Q(20))),
        "HIGH_T20":(arrival_pulse("5/2",20),(Q(0),Q(20))),
        "SHAPED_T14_T20":(shaped_arrivals(),(Q(0),Q(14),Q(20))),
    }


def draw_factor(cv,rng):
    choices=MULTIPLIERS[cv]
    return choices[0] if len(choices)==1 else choices[rng.randrange(2)]


def stochastic_engine(config,arrivals,times,cv,seed):
    """Independent heap/event-calendar implementation, not CAF-01 calls.

    Event ordering: COMPLETE all due, ACCEPT all due, START downstream-first;
    for strictly positive service times, starts cannot finish in same batch.
    """
    spec=des.validate_private_config(config)
    need(cv in CVS,"CAF16_UNDECLARED_CV")
    arrivals=tuple(Q(x) for x in arrivals)
    times=tuple(Q(t) for t in times)
    need(times and times[0]==0
         and all(t<u for t,u in zip(times,times[1:]))
         and all(t<u for t,u in zip(arrivals,arrivals[1:]))
         and all(t>=0 for t in arrivals)
         and (not arrivals or arrivals[-1]<=times[-1]),
         "CAF16_BAD_EVENT_SCHEDULE")
    queues=[deque() for _ in spec]
    busy=[set() for _ in spec]
    events=[]
    serial=0
    for order,when in enumerate(arrivals):
        heappush(events,(when,1,serial,"accept",-1,order))
        serial+=1
    rng=random.Random(seed)
    accepted=delivered=0
    completed=set()
    snapshots=[]

    def balance():
        pending=sum(len(q)+len(a) for q,a in zip(queues,busy))
        need(accepted==delivered+pending and len(completed)==delivered,
             "CAF16_CONSERVATION_FAILURE")
        need(all(len(busy[s])<=spec[s][0] for s in range(len(spec))),
             "CAF16_SERVER_OVERFLOW")
        active=[o for q in queues for o in q]
        active.extend(o for a in busy for o in a)
        need(len(set(active))==len(active) and not set(active)&completed,
             "CAF16_ORDER_DUPLICATION")
        return pending

    for target in times:
        while events and events[0][0]<=target:
            now=events[0][0]
            batch=[]
            while events and events[0][0]==now:
                batch.append(heappop(events))
            for _,_,_,kind,stage,order in batch:
                if kind!="complete":
                    continue
                need(order in busy[stage],"CAF16_UNSCHEDULED_COMPLETION")
                busy[stage].remove(order)
                if stage+1<len(spec):
                    queues[stage+1].append(order)
                else:
                    need(order not in completed,"CAF16_DOUBLE_DELIVERY")
                    completed.add(order)
                    delivered+=1
            for _,_,_,kind,stage,order in batch:
                if kind=="accept":
                    queues[0].append(order)
                    accepted+=1
            for stage in reversed(range(len(spec))):
                servers,base_service=spec[stage]
                while queues[stage] and len(busy[stage])<servers:
                    order=queues[stage].popleft()
                    busy[stage].add(order)
                    factor=draw_factor(cv,rng)
                    duration=base_service*factor
                    need(duration>0,"CAF16_NONPOSITIVE_SERVICE_TIME")
                    heappush(events,(now+duration,0,serial,"complete",stage,order))
                    serial+=1
            balance()
        pending=balance()
        snapshots.append({
            "time":str(target),
            "accepted":accepted,
            "delivered":delivered,
            "pending":pending,
            "waiting":tuple(map(len,queues)),
            "in_service":tuple(map(len,busy)),
        })
    return tuple(snapshots)


def native_engine_snapshots(config,arrivals,times):
    # ONLY parity oracle, never the generator for CV25/CV50 worlds.
    snap=des.run_toy_engine(config,arrivals,times)
    return tuple({
        "time":str(x.t_min),"accepted":x.accepted_cum_orders,
        "delivered":x.delivered_cum_orders,"pending":x.pending_orders,
        "waiting":x.stage_waiting,"in_service":x.stage_in_service,
    } for x in snap)


def observation(snap,channels):
    vals=[]
    for field,stage in channels:
        if field=="delivered":
            need(stage is None,"CAF16_BAD_DELIVERY")
            vals.append(snap["delivered"])
        else:
            idx=b.STAGES.index(stage)
            if field=="waiting":
                vals.append(snap["waiting"][idx])
            elif field=="stage_stock":
                vals.append(snap["waiting"][idx]+snap["in_service"][idx])
            else:
                raise ValueError("CAF16_BAD_CHANNEL")
    return tuple(vals)


def physical_worlds():
    worlds=[]
    for stage in v11.STAGE_SETS:
        capacity_vectors=((c,) for c in SINGLES) if len(stage)==1 else iter(DUALS)
        model=next(m for m in v11.models() if tuple(m["stages"])==tuple(stage))
        for caps in capacity_vectors:
            worlds.append({
                "id":"W_"+''.join(map(str,stage))+"_"+'_'.join(map(str,caps)),
                "truth_class":model["label"],"truth_type":"single" if len(stage)==1 else "double",
                "capacities":caps,"config":v15a.config_for(stage,caps),
            })
    for cap in EXTRAS:
        worlds.append({
            "id":"EXTRA_"+str(cap),"truth_class":None,
            "truth_type":"fourth_stage","capacities":(cap,),
            "config":v15a.extra_config(cap),
        })
    need(len(worlds)==30 and len({w["id"] for w in worlds})==30,
         "CAF16_WRONG_FROZEN_WORLDS")
    need(sum(w["truth_class"] is not None for w in worlds)==27,
         "CAF16_WRONG_IN_FAMILY_DENOMINATOR")
    return worlds


def physical_signatures(config,worldid,rep,cv):
    sc=scenarios()
    results={}
    for name,(arrivals,times) in sc.items():
        snap=stochastic_engine(config,arrivals,times,cv,
                               seed_for("SERVICE",worldid,rep,cv,name))
        if name=="K0" or name=="K1":
            results[name]=observation(snap[-1],(("delivered",None),))
        elif name=="HIGH_T20":
            results[name]=observation(snap[-1],CHANNELS)
        else:
            results["SHAPED_T14"]=observation(snap[1],CHANNELS)
            results["SHAPED_T20"]=observation(snap[2],CHANNELS)
    return {
        "HIGH_T20":results["K0"]+results["K1"]+results["HIGH_T20"],
        "SHAPED_T14_T20":results["K0"]+results["K1"]+
                results["SHAPED_T14"]+results["SHAPED_T20"],
    }


def with_sensor_error(raw,worldid,rep,cv,program,error):
    need(error in ERRORS,"CAF16_UNDECLARED_ERROR")
    if error=="E0":
        return tuple(raw)
    rng=random.Random(seed_for("SENSOR",worldid,rep,cv,program))
    return tuple(max(0,x+rng.choice((-1,0,1))) for x in raw)


def analyst_bank():
    """Construct deterministic bank independent of all evaluator worlds."""
    base=v15a.compute_bank()
    sc=scenarios()
    rows=[]
    for row in base:
        conf=v15a.config_for(row["stages"],tuple(row["capacity_by_stage"]))
        s=stochastic_engine(conf,*sc["SHAPED_T14_T20"],"CV0",
                            seed_for("CATALOG",row["id"]))
        shaped=(
            tuple(row["signatures"]["BASE"])
            +observation(s[1],CHANNELS)+observation(s[2],CHANNELS))
        rows.append({
            "id":row["id"],"class":row["class"],
            "stages":tuple(row["stages"]),
            "capacity_by_stage":tuple(row["capacity_by_stage"]),
            "signatures":{
                "HIGH_T20":tuple(row["signatures"]["F_R25_T20"]),
                "SHAPED_T14_T20":shaped,
            },
        })
    need(len(rows)==720,"CAF16_CATALOG_SIZE_DRIFT")
    return rows


def predict_classes(reading,program,bank):
    """Model receives ONLY fixed integer observations and deterministic bank."""
    need(program in PROGRAMS,"CAF16_UNKNOWN_PROGRAM")
    need(len(reading)==(8 if program=="HIGH_T20" else 14),
         "CAF16_BAD_SENSOR_DIMENSION")
    viable=set()
    for row in bank:
        candidate=row["signatures"][program]
        if all(abs(x-y)<=1 for x,y in zip(reading,candidate)):
            viable.add(row["class"])
    return sorted(viable)


def simplify_row(row):
    return {
        "id":row["id"],"class":row["class"],
        "stages":list(row["stages"]),
        "capacity_by_stage":list(row["capacity_by_stage"]),
        "signatures":{k:list(v) for k,v in row["signatures"].items()},
    }


def run(out,checkout_sha,head_sha):
    need(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha) and
         b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha),"CAF16_SHA_REQUIRED")
    root=Path(out).resolve()
    need(not root.exists(),"CAF16_REFUSE_OVERWRITE")
    bank=analyst_bank()
    worldset=physical_worlds()
    root.mkdir(parents=True,exist_ok=False)
    def save(filename,data):
        return b.lab.write_new(root,filename,data)
    save("00B_CATALOGO_PRE_EVALUACION.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "analyst_deterministic_configuration_count":720,
        "all_signatures_created_before_stochastic_world_evaluation":True,
        "bank":[simplify_row(r) for r in bank],
    })
    digest="sha256:"+sha256((root/"00B_CATALOGO_PRE_EVALUACION.json").read_bytes()).hexdigest()
    save("00_PLAN_PRE_EVALUACION.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "master_seed":MASTER_SEED,
        "worlds_EVALUATOR_ONLY":worldset,
        "cv_factors":{k:[str(v) for v in vals] for k,vals in MULTIPLIERS.items()},
        "service_cv_levels":CVS,"sensor_conditions":ERRORS,
        "programs":PROGRAMS,"n_replicates_per_world_condition":REPS,
        "n_worlds":30,"n_known":27,"n_unknown":3,
        "n_readings":4320,"n_known_readings":3888,
        "n_unknown_readings":432,
        "analyst_tolerance_counts":1,"catalog_sha256":digest,
        "synthetic_shaped_peak_is_not_natural_observed_demand":True,
        "no_stochastic_world_generated_before_plan":True,
        "no_independent_empirical_validation":True,
    })
    observations=[]
    n_paths=0
    for world in worldset:
        for cv in CVS:
            for replicate in range(REPS):
                phys=physical_signatures(
                    world["config"],world["id"],replicate,cv)
                n_paths+=1
                for program in PROGRAMS:
                    raw=phys[program]
                    for error in ERRORS:
                        observed=with_sensor_error(
                            raw,world["id"],replicate,cv,program,error)
                        need(all(abs(x-y)<=1 for x,y in zip(raw,observed)),
                             "CAF16_SENSOR_ERROR_EXCEEDS_DECLARED_BOUND")
                        eligible=predict_classes(observed,program,bank)
                        true=world["truth_class"]
                        if cv=="CV0" and error=="E0" and true is not None:
                            need(true in eligible,
                                 "CAF16_DETERMINISTIC_TRUE_CLASS_LOST")
                        observations.append({
                            "world":world["id"],"replicate":replicate,
                            "trajectory_id":world["id"]+"|"+cv+"|"+str(replicate),
                            "cv":cv,"sensor_error":error,
                            "program":program,
                            "truth_class_EVALUATOR_ONLY":true,
                            "truth_type_EVALUATOR_ONLY":world["truth_type"],
                            "raw_physical_signature":list(raw),
                            "observed_signature":list(observed),
                            "compatible_classes":eligible,
                            "n_classes":len(eligible),
                            "true_class_covered_EVALUATOR_ONLY":
                                true in eligible if true is not None else None,
                            "unique_class":eligible[0] if len(eligible)==1 else None,
                        })
    need(n_paths==30*3*REPS and len(observations)==4320,
         "CAF16_WRONG_FROZEN_TRIAL_COUNT")
    summary={}
    for pid in PROGRAMS:
        summary[pid]={}
        for cv in CVS:
            summary[pid][cv]={}
            for err in ERRORS:
                group=[r for r in observations if r["program"]==pid and
                       r["cv"]==cv and r["sensor_error"]==err]
                known=[r for r in group if r["truth_class_EVALUATOR_ONLY"] is not None]
                unknown=[r for r in group if r["truth_class_EVALUATOR_ONLY"] is None]
                need(len(known)==27*REPS and len(unknown)==3*REPS,
                     "CAF16_BAD_STRATUM_DENOMINATORS")
                summary[pid][cv][err]={
                    "n_known":len(known),"n_unknown":len(unknown),
                    "known_true_class_covered":sum(r["true_class_covered_EVALUATOR_ONLY"]
                                                  for r in known),
                    "known_no_lattice_match":sum(r["n_classes"]==0 for r in known),
                    "known_singleton_correct":sum(
                        r["unique_class"]==r["truth_class_EVALUATOR_ONLY"]
                        for r in known),
                    "known_singleton_false":sum(
                        r["unique_class"] is not None and
                        r["unique_class"]!=r["truth_class_EVALUATOR_ONLY"]
                        for r in known),
                    "known_avg_classes":round(
                        sum(r["n_classes"] for r in known)/len(known),4),
                    "unknown_no_lattice_match":sum(r["n_classes"]==0 for r in unknown),
                    "unknown_false_singleton":sum(r["unique_class"] is not None
                                                  for r in unknown),
                    "unknown_has_known_explanation":sum(r["n_classes"]>0 for r in unknown),
                }
    results={
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_worlds":len(worldset),"n_replicates":REPS,
        "n_trajectories_before_sensor_perturbations":n_paths,
        "n_readings":len(observations),"n_known_readings":3888,
        "n_unknown_readings":432,"n_deterministic_candidates":len(bank),
        "summary":summary,"observations":observations,
        "stochastic_generator_independent_of_legacy_DES":True,
        "natural_overload_not_observed":True,
        "no_external_calibrated_service_or_sensor":True,
        "promotion_gate":GATE,
    }
    save("01_RESULTADOS.json",results)
    lines=[
        "# CAF-16 — Robustez ante variabilidad física y error de sensor (sintético)",
        "",
        "**No es un diagnóstico empresarial ni validación estocástica externa.**",
        "Se aplica el banco DETERMINISTA CONGELADO de 720 hipótesis a un motor",
        "estocástico independiente de eventos, ambos con FIFO y sin bloqueo.",
        "Las réplicas no son mundos independientes. Un conjunto vacío indica",
        "SOLO falta de coincidencia en la malla determinista ±1.",
        "",
        "| Programa | CV | Error | Clase conocida retenida /324 | Conocidos sin ajuste /324 | Únicos correctos /324 | Únicos falsos /324 | Clases medias | Unknown sin ajuste /36 | Unknown falso único /36 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pid in PROGRAMS:
        for cv in CVS:
            for err in ERRORS:
                s=summary[pid][cv][err]
                lines.append("| "+" | ".join(map(str,(
                    pid,cv,err,s["known_true_class_covered"],
                    s["known_no_lattice_match"],s["known_singleton_correct"],
                    s["known_singleton_false"],s["known_avg_classes"],
                    s["unknown_no_lattice_match"],s["unknown_false_singleton"],
                )))+" |")
    lines+=["",
        "## Límites y lectura física",
        "",
        "- CV25 y CV50 son distribuciones sintéticas de dos puntos equiprobables",
        "  y CV0 es control de servicio determinista.",
        "- E1 es perturbación independiente del conteo de ±1 (con truncamiento",
        "  a cero); E0 no incorpora perturbación instrumental.",
        "- Los escenarios K0/K1 y T se reinician; dos lecturas del mismo",
        "  ensayo SHAPED comparten la misma trayectoria y capacidad.",
        "- HIGH es sobrecarga artificial constante; SHAPED es demanda",
        "  modulada sintética, NO una ventana de sobrecarga natural medida.",
        "- Los certificados de separabilidad de CAF-15B no aplican a",
        "  servicio variable; esta prueba no puede refutarlos matemáticamente",
        "  porque su enunciado original era condicional.",
        "- La inferencia solo ve lecturas y banco; nunca recibe la etiqueta",
        "  de topología ni el mecanismo de servicio del evaluador.",
        "- Los 27 mundos tienen parámetros nominales en la malla por diseño.",
        "  El caso CV0/E0 27/27 recuperado es autoconsistencia, no accuracy",
        "  predictiva fuera del mismo modelo.",
        "- No son estimaciones de prevalencia o probabilidad de error real.",
        "",
        "Gate permanente: "+GATE,
        ""]
    save("02_INFORME.md","\n".join(lines))
    manifest={p.name:"sha256:"+sha256(p.read_bytes()).hexdigest()
              for p in sorted(root.iterdir()) if p.is_file()}
    save("03_MANIFIESTO.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "files_sha256":manifest,
        "catalog_saved_before_world_simulation":True,
        "worlds_used_only_for_posthoc_evaluation":True,
    })
    return results


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    a=p.parse_args()
    result=run(a.out,a.checkout_sha,a.head_sha)
    print(json.dumps({
        "n_readings":result["n_readings"],"summary":result["summary"],
        "promotion_gate":result["promotion_gate"],
    },sort_keys=True))


if __name__=="__main__":
    main()
