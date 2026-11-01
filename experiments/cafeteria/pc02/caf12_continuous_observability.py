#!/usr/bin/env python3
"""CAF-12: exact-rational continuous parameter inversion with queue/stock sensors.

NO selector, optimizer, guessed continuous interpolation, or new DES.
All K0/K1/K2 observations share ONE c=60/d across a family's predictions.
Only the specified deterministic FIFO tandem with homogeneous service times
is amenable to the max-plus clocks used here; no claim beyond that family.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA = "igc-caf12-continuous-sensor-observability/0.1"
PROTOCOL_COMMIT = "c99fd8d8167b13062d573be721cff8f21b437d4d"
GATE = "BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION"

K0 = {"id":"K0", "rate":b.caf07.T0_RATE,"minute":b.caf07.T0_MINUTE,
      "channels":(("delivered",None),)}
K1 = {"id":"K1", "rate":b.FIRST["rate"],"minute":b.FIRST["minute"],
      "channels":tuple(tuple(c) for c in b.FIRST["channels"])}
SCHEMES = (
    ("BASE", None),
    ("PREP_Q", "prep_queue_15_t20"),
    ("DISPATCH_Q", "dispatch_queue_15_t20"),
    ("DELIVERY_Q", "delivery_queue_15_t20"),
    ("DISPATCH_STOCK", "dispatch_stock_15_t20"),
    ("PREP_DISPATCH_Q", "prep_dispatch_15_t20"),
    ("ALL_QUEUES", "all_queues_15_t20"),
    ("STRESS_PREP_DISPATCH", "prep_dispatch_18_t20"),
)
SCHEME_NAMES=tuple(name for name,_ in SCHEMES)
SCHEME_MAP=dict(SCHEMES)


def need(condition,code):
    if not condition:
        raise ValueError(code)


def probe(action):
    return {"id":"K2","rate":action["rate"],"minute":action["minute"],
            "channels":tuple(tuple(channel) for channel in action["channels"])}


def scheme_probes(name):
    need(name in SCHEME_MAP, "CAF12_UNKNOWN_SCHEME")
    action_id=SCHEME_MAP[name]
    out=[K0,K1]
    if action_id is not None:
        a=b.ACTION_BY_ID[action_id]
        need(a["cost"]+b.FIRST["cost"]<=b.BUDGET,
             "CAF12_BUDGET_OVERFLOW")
        out.append(probe(a))
    return tuple(out)


def build_parametric_calendar(stage_indices,rate):
    """Ordered per-stage FCFS start/end clocks by order index.

    With homogeneous duration and identical parallel servers in a stage,
    departure order is nondecreasing, and job i starts no earlier than job
    i-m(s) finishes. Recursive max-plus construction is exact in this scope.
    """
    need(tuple(stage_indices) in v11.STAGE_SETS,
         "CAF12_UNDECLARED_STRUCTURE")
    arrivals=des.half_open_arrivals(rate,20)
    zero=v11.Clock.line()
    variable=v11.Clock.line(1,0)
    fixed=v11.Clock.line(0,1)
    inputs=[]
    starts=[]
    ends=[]
    for s in range(3):
        nservers=1 if s in stage_indices else 2
        duration=variable if s in stage_indices else fixed
        stage_inputs=[]
        stage_starts=[]
        stage_ends=[]
        for i,arr in enumerate(arrivals):
            incoming=(v11.Clock.line(0,arr) if s==0
                      else ends[s-1][i])
            free=(stage_ends[i-nservers]
                  if i>=nservers else zero)
            begin=incoming.vmax(free)
            finish=begin.add(duration)
            stage_inputs.append(incoming)
            stage_starts.append(begin)
            stage_ends.append(finish)
        inputs.append(stage_inputs)
        starts.append(stage_starts)
        ends.append(stage_ends)
    return {"stage_indices":tuple(stage_indices),
            "rate":rate,
            "arrivals":arrivals,
            "inputs":inputs,
            "starts":starts,
            "ends":ends}


def relevant_clocks(calendar,channel):
    field,stage=channel
    if field=="delivered":
        need(stage is None,"CAF12_BAD_DELIVERY_STAGE")
        return [calendar["ends"][-1]]
    need(stage in b.STAGES,"CAF12_BAD_STAGE")
    ix=b.STAGES.index(stage)
    if field=="waiting":
        return [calendar["inputs"][ix],calendar["starts"][ix]]
    if field=="stage_stock":
        return [calendar["inputs"][ix],calendar["ends"][ix]]
    raise ValueError("CAF12_UNSUPPORTED_CHANNEL")


def count_completed(clocks,d,t):
    return sum(c.at(d)<=t for c in clocks)


def predict_channels(calendar, channels, minute, d):
    """Snapshot at t inclusive of all complete, accept and start events."""
    out=[]
    for channel in channels:
        field,stage=channel
        if field=="delivered":
            need(stage is None,"CAF12_WRONG_DELIVERY_CHANNEL")
            result=count_completed(calendar["ends"][-1],d,minute)
        else:
            ix=b.STAGES.index(stage)
            input_count=count_completed(calendar["inputs"][ix],d,minute)
            if field=="waiting":
                result=input_count-count_completed(
                    calendar["starts"][ix],d,minute)
            elif field=="stage_stock":
                result=input_count-count_completed(
                    calendar["ends"][ix],d,minute)
            else:
                raise ValueError("CAF12_UNSUPPORTED_FIELD")
        need(type(result) is int and result>=0,
             "CAF12_NEGATIVE_PHYSICAL_STOCK")
        out.append(result)
    return out


def all_clocks_for_probes(calendars,probes):
    for p in probes:
        key=p["rate"]
        cal=calendars[key]
        for channel in p["channels"]:
            for clock_list in relevant_clocks(cal,channel):
                for clock in clock_list:
                    yield clock,p["minute"]


def exact_atomic_regimes(calendars,probes):
    """Partition entire rational interval at ALL potentially changing events.

    K0,K1,K2 predictions are identical on each open interval between adjacent
    roots. Evaluate singleton boundaries separately to preserve <= semantics.
    """
    bounds={v11.D_LOW,v11.D_HIGH}
    for clock,time in all_clocks_for_probes(calendars,probes):
        bounds.update(clock.roots_at(time))
    cuts=sorted(bounds)
    need(cuts[0]==v11.D_LOW and cuts[-1]==v11.D_HIGH,
         "CAF12_INCOMPLETE_PARAM_DOMAIN")
    def pred(d):
        return {p["id"]:predict_channels(
            calendars[p["rate"]],p["channels"],p["minute"],d)
            for p in probes}
    atoms=[]
    for i,d in enumerate(cuts):
        atoms.append({
            "kind":"point","left":d,"right":d,
            "include_left":True,"include_right":True,
            "pred":pred(d)
        })
        if i+1<len(cuts):
            r=cuts[i+1]
            atoms.append({
                "kind":"open","left":d,"right":r,
                "include_left":False,"include_right":False,
                "pred":pred((d+r)/2)
            })
    need(len(atoms)==2*len(cuts)-1,
         "CAF12_ATOMIC_PARTITION_BROKEN")
    return atoms


def compatible(pred,measured):
    need(set(pred)==set(measured),"CAF12_CHANNEL_SCHEMA_MISMATCH")
    return all(len(pred[k])==len(measured[k])
               and all(abs(x-y)<=b.TOLERANCE
                       for x,y in zip(pred[k],measured[k]))
               for k in measured)


def merge_compatible(atoms,readings):
    comps=[]
    for at in atoms:
        if not compatible(at["pred"],readings):
            continue
        new={
            "left":at["left"],"right":at["right"],
            "include_left":at["include_left"],
            "include_right":at["include_right"],
        }
        if (comps and comps[-1]["right"]==new["left"]
                and (comps[-1]["include_right"] or new["include_left"])):
            comps[-1]["right"]=new["right"]
            comps[-1]["include_right"]=new["include_right"]
        else:
            comps.append(new)
    return comps


def region_serialization(comps):
    return v11.capacity_regions(comps)


def models():
    return v11.models()


def worlds():
    # Reuse ALL previously exposed CAF-11 worlds without pretending they are new.
    existing=[
        {**w,"cohort":"H_CAF11_EXPOSED_20"}
        for w in v11.worlds()
    ]
    fresh=[]
    for cap in (61,79,107):
        for i,j in ((0,1),(0,2),(1,2)):
            fresh.append({
                "id":f"N_DUAL_{cap}_{i}{j}",
                "cohort":"N_ADDITIONAL_DOUBLE_9",
                "truth_type":"double",
                "truth_class":b.klass([b.STAGES[i],b.STAGES[j]]),
                "capacity":cap,
                "config":b.make_physical_config((i,j),cap),
            })
    for cap in (62,78,106):
        fresh.append({
            "id":f"N_EXTRA_{cap}",
            "cohort":"N_ADDITIONAL_EXTRA_3",
            "truth_type":"unknown-extra",
            "truth_class":None,
            "capacity":cap,
            "config":b.make_physical_config((),cap,extra=True),
        })
    out=existing+fresh
    need(len(out)==32 and len({x["id"] for x in out})==32,
         "CAF12_BAD_WORLDSET")
    need(sum(x["truth_class"] is not None for x in out)==27,
         "CAF12_BAD_IN_FAMILY_COUNT")
    need(sum(x["truth_class"] is None for x in out)==5,
         "CAF12_BAD_UNKNOWN_COUNT")
    return out


def read_world(config,all_probes):
    """Never use truth here for diagnosis, only physical configuration to DES."""
    return {
        p["id"]:b.read_physical(config,p["rate"],p["minute"],
                               p["channels"])
        for p in all_probes
    }


def get_scheme_families():
    """Precompute exact parametric regimes; no evaluator DES worlds yet."""
    result={}
    for m in models():
        rates={p["rate"] for s in SCHEME_NAMES for p in scheme_probes(s)}
        calendars={
            rate:build_parametric_calendar(m["stages"],rate)
            for rate in sorted(rates)
        }
        for scheme in SCHEME_NAMES:
            key=(m["id"],scheme)
            result[key]={
                "id":m["id"],"label":m["label"],
                "scheme":scheme,
                "atoms":exact_atomic_regimes(
                    calendars,scheme_probes(scheme))
            }
    need(len(result)==48,"CAF12_WRONG_FAMILY_SCHEME_COUNT")
    return result


def evaluated_scheme(readings, scheme, family_map):
    """Inference interface: receives observations + abstract precomputed models."""
    ids=[p["id"] for p in scheme_probes(scheme)]
    need(set(readings)==set(ids),"CAF12_INVALID_OBSERVATION_SET")
    out=[]
    for m in models():
        family=family_map[(m["id"],scheme)]
        comps=merge_compatible(family["atoms"],readings)
        out.append({
            "id":m["id"],"class":m["label"],
            "nonempty":bool(comps),
            "n_regions":len(comps),
            "capacity_regions":region_serialization(comps),
            "_d_components":comps,
        })
    return out


def format_atom(at):
    return {
        "kind":at["kind"],
        "duration_low":str(at["left"]),
        "duration_high":str(at["right"]),
        "low_included":at["include_left"],
        "high_included":at["include_right"],
        "pred":at["pred"],
    }


def canonical_bytes(value):
    return json.dumps(value,ensure_ascii=False,
                      sort_keys=True,separators=(",",":"),
                      allow_nan=False).encode("utf-8")


def run(dest,checkout_sha,head_sha):
    need(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha) is not None
         and b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha) is not None,
         "CAF12_SHA_REQUIRED")
    dest=Path(dest).resolve()
    need(not dest.exists(),"CAF12_DO_NOT_OVERWRITE")
    families=get_scheme_families()
    wlist=worlds()
    dest.mkdir(parents=True,exist_ok=False)
    def save(name,body):
        b.lab.write_new(dest,name,body)
    family_regimes=[
        {"id":m["id"],"class":m["label"],"scheme":scheme,
         "atoms":[format_atom(at) for at in families[(m["id"],scheme)]["atoms"]]}
        for m in models() for scheme in SCHEME_NAMES
    ]
    # Largest evidence file still written before a single evaluation-world DES.
    save("00B_EXACT_REGIMES_PRE_EVALUACION.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTOCOL_COMMIT,
        "precomputed_48_family_scheme_regimes":family_regimes,
        "NO_EVALUATION_WORLD_DES_CALLS":True,
    })
    source_hash=hashlib.sha256(
        (dest/"00B_EXACT_REGIMES_PRE_EVALUACION.json").read_bytes()).hexdigest()
    save("00_PLAN_PRE_EVALUACION.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTOCOL_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "parameter_domain_capacity":[str(v11.CAPACITY_LOW),str(v11.CAPACITY_HIGH)],
        "duration_domain":[str(v11.D_LOW),str(v11.D_HIGH)],
        "tolerance_counts":b.TOLERANCE,
        "family_count":len(models()),"scheme_names":SCHEME_NAMES,
        "schemes":[{"id":s,"probes":scheme_probes(s),
                    "total_ordinal_cost":
                      b.FIRST["cost"]+(
                        b.ACTION_BY_ID[SCHEME_MAP[s]]["cost"]
                        if SCHEME_MAP[s] is not None else 0)}
                   for s in SCHEME_NAMES],
        "evaluator_worlds_EVALUATOR_ONLY":wlist,
        "regimes_sha256":"sha256:"+source_hash,
        "event_time_ties_inclusive":True,
        "single_parameter_shared_across_independent_resets":True,
        "new_evaluation_world_DES_calls_before_plan":0,
        "native_DES_not_modified":True,
        "not_external_validation":True,
    })
    # Only now evaluate real synthetic worlds using native DES reader.
    all_probes=[]
    seen=set()
    for s in SCHEME_NAMES:
        for p in scheme_probes(s):
            k=(p["rate"],p["minute"],p["channels"])
            if k not in seen:
                seen.add(k)
                all_probes.append(p)
    evaluations=[]
    for world in wlist:
        # Sensor map is generated from the truth config ONLY here.
        raw={}
        for p in all_probes:
            # Collision of K2 IDs across schemes is harmless if scoped by scheme;
            # physical reading keyed by declared rate/time/channels.
            key=(p["rate"],p["minute"],p["channels"])
            raw[key]=b.read_physical(
                world["config"],p["rate"],p["minute"],p["channels"])
        for scheme in SCHEME_NAMES:
            probes=scheme_probes(scheme)
            obs={p["id"]:raw[(p["rate"],p["minute"],p["channels"])]
                 for p in probes}
            classes=evaluated_scheme(obs,scheme,families)
            surviving=sorted(f["class"] for f in classes if f["nonempty"])
            true=world["truth_class"]
            true_family=next((f for f in classes if f["class"]==true),None)
            parameter_covered=(
                v11.contains_duration(
                    true_family["_d_components"],
                    Fraction(60,world["capacity"]))
                if true_family is not None else None)
            evaluations.append({
                "case":world["id"],"cohort":world["cohort"],
                "scheme":scheme,
                "ordinal_cost":b.FIRST["cost"]+(
                    b.ACTION_BY_ID[SCHEME_MAP[scheme]]["cost"]
                    if SCHEME_MAP[scheme] is not None else 0),
                "world_type_EVALUATOR_ONLY":world["truth_type"],
                "truth_class_EVALUATOR_ONLY":true,
                "truth_capacity_EVALUATOR_ONLY":world["capacity"],
                "observations":obs,
                "n_classes":len(surviving),
                "compatible_classes":surviving,
                "one_class_within_family":surviving[0] if len(surviving)==1 else None,
                "coverage_class_EVALUATOR_ONLY":
                    (true in surviving if true is not None else None),
                "coverage_parameter_EVALUATOR_ONLY":parameter_covered,
                "families":[{
                    k:v for k,v in f.items() if k!="_d_components"
                } for f in classes],
            })
    need(len(evaluations)==32*8,
         "CAF12_EVALUATIONS_WRONG")
    for x in evaluations:
        if x["truth_class_EVALUATOR_ONLY"] is not None:
            need(x["coverage_class_EVALUATOR_ONLY"]
                 and x["coverage_parameter_EVALUATOR_ONLY"],
                 "CAF12_FALSE_EXCLUSION_OF_REAL_IN_FAMILY_PARAMETER")
    for world in wlist:
        seq=[e for e in evaluations if e["case"]==world["id"]]
        baseline=set(next(x for x in seq if x["scheme"]=="BASE")["compatible_classes"])
        for item in seq:
            need(set(item["compatible_classes"]).issubset(baseline),
                 "CAF12_NONMONOTONIC_FEASIBLE_CLASS_SET")
    for x in evaluations:
        need(x["ordinal_cost"]<=b.BUDGET,
             "CAF12_COST_EXCEEDS_FROZEN_BUDGET")
    summary={}
    for scheme in SCHEME_NAMES:
        all_rows=[x for x in evaluations if x["scheme"]==scheme]
        inside=[x for x in all_rows if x["truth_class_EVALUATOR_ONLY"] is not None]
        unknown=[x for x in all_rows if x["truth_class_EVALUATOR_ONLY"] is None]
        summary[scheme]={
            "n_total":len(all_rows),
            "in_family":len(inside),
            "unknown_extra":len(unknown),
            "cost_units":all_rows[0]["ordinal_cost"],
            "class_coverage":sum(x["coverage_class_EVALUATOR_ONLY"] for x in inside),
            "parameter_coverage":sum(x["coverage_parameter_EVALUATOR_ONLY"] for x in inside),
            "unique_correct_in_family":sum(
                x["one_class_within_family"]==x["truth_class_EVALUATOR_ONLY"]
                for x in inside),
            "in_family_ambiguous":sum(x["n_classes"]>1 for x in inside),
            "in_family_all_six":sum(x["n_classes"]==6 for x in inside),
            "in_family_incompatible":sum(x["n_classes"]==0 for x in inside),
            "unknown_unique_false_certifications":sum(
                x["one_class_within_family"] is not None for x in unknown),
            "unknown_compatible_as_known":sum(
                x["n_classes"]>0 for x in unknown),
            "unknown_incompatible":sum(x["n_classes"]==0 for x in unknown),
            "cardinality_histogram_in_family":dict(sorted(Counter(
                x["n_classes"] for x in inside).items())),
            "cardinality_histogram_unknown":dict(sorted(Counter(
                x["n_classes"] for x in unknown).items())),
            "sum_final_classes_in_family":sum(x["n_classes"] for x in inside),
        }
    result={
        "schema":SCHEMA,"protocol_first_commit":PROTOCOL_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_worlds":len(wlist),"n_inversions":len(evaluations)*len(models()),
        "n_scheme_evaluations":len(evaluations),
        "n_precomputed_family_scheme_regimes":len(family_regimes),
        "all_in_family_truth_capacity_covered":True,
        "truth_never_passed_to_inverse":True,
        "no_policy_selection":True,
        "no_external_validity_proven":True,
        "summary":summary,"evaluations":evaluations,
        "promotion_gate":GATE,
    }
    save("01_RESULTADOS.json",result)
    lines=[
        "# CAF-12 — Observabilidad de sensores con inversión exacta continua",
        "",
        "Lab DES determinista compartido; no validación externa.",
        "Ningún esquema fue elegido tras observar los resultados.",
        "±1 es tolerancia declarada no calibrada; los costos son ordinales.",
        "",
        "| Esquema | Costo | Clases únicas correctas (27) | Ambiguos (27) | Seis clases (27) | Cobertura clase/parámetro | Unknowns con única clase falsa (5) | Unknowns compatibles (5) |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for s in SCHEME_NAMES:
        r=summary[s]
        lines.append("| "+" | ".join(map(str,(
            s,r["cost_units"],r["unique_correct_in_family"],
            r["in_family_ambiguous"],r["in_family_all_six"],
            f'{r["class_coverage"]}/27 y {r["parameter_coverage"]}/27',
            r["unknown_unique_false_certifications"],
            r["unknown_compatible_as_known"]
        )))+" |")
    lines+=["",
        "## Auditoría por mundo y esquema",
        "",
        "| Mundo | Esquema | Lectura K0/K1/K2 | Clases compatibles | n | Clase verdadera cubierta |",
        "|---|---|---|---|---:|---|",
    ]
    for x in evaluations:
        lines.append("| "+" | ".join((
            x["case"],x["scheme"],
            str(x["observations"]),
            ",".join(x["compatible_classes"]) or "∅",
            str(x["n_classes"]),
            "N/A" if x["coverage_class_EVALUATOR_ONLY"] is None
            else str(x["coverage_class_EVALUATOR_ONLY"]),
        ))+" |")
    lines +=["",
        "## Reglas de interpretación",
        "",
        "- Una clase única no prueba que la topología sea completa; los cinco",
        "  mundos con cuarta etapa son controles fuera de familia.",
        "- Cobertura 27/27 es control algebraico esperado por compartir DES.",
        "- La reducción de clases depende de sensores, error ±1, y funciones",
        "  exactas de tiempos de servicio deterministas.",
        "- Comparar calidad/costo no implica óptimo de información, porque",
        "  la función objetivo no fue calibrada económicamente.",
        "- Una prueba nueva a distinto rate es un reinicio independiente; las",
        "  sondas a mismo rate/tiempo que K1 comparten el mismo snapshot",
        "  determinista y NO aportan independencia estadística.",
        "- El inversor exacto solo certifica regiones en el submodelo",
        "  de tres etapas FIFO, capacidad continua común, servicio homogéneo.",
        "- Las raíces de eventos y extremos de regiones son fracciones exactas.",
        "- Prohibido promocionar a diagnóstico de sistemas reales.",
        "",
        "Gate: "+GATE,
        ""]
    save("02_INFORME.md","\n".join(lines))
    saved=[p for p in dest.iterdir() if p.is_file()]
    save("03_MANIFIESTO.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,
        "pr_head_sha":head_sha,
        "file_sha256":{p.name:"sha256:"+hashlib.sha256(
            p.read_bytes()).hexdigest() for p in sorted(saved)},
        "no_external_independent_evaluation":True,
        "plan_precedes_evaluation_DES":True,
    })
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    args=p.parse_args()
    results=run(args.out,args.checkout_sha,args.head_sha)
    print(json.dumps({
        "n_worlds":results["n_worlds"],
        "n_scheme_evaluations":results["n_scheme_evaluations"],
        "n_inversions":results["n_inversions"],
        "summary":results["summary"],
        "gate":results["promotion_gate"],
    },ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
