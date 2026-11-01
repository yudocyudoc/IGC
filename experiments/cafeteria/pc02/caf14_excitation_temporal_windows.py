#!/usr/bin/env python3
"""CAF-14: precommitted factorial excitation and temporal windows.

Exact rational max-plus inversion in a narrowly specified deterministic
three-stage FIFO tandem with one shared continuous capacity parameter.
No selector, calibrated noise model, external validation, or capacity policy.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
import caf12_continuous_observability as v12
import caf13_structural_distinguishability as v13
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA = "igc-caf14-factorial-excitation-temporal-window/0.1"
PROTO_COMMIT = "153e4e18de83c35609b64abd98f958c796ecd11a"
GATE = "BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION"

FULL_CHANNELS = v13.FULL
RATES = (("R15","3/2"),("R18","9/5"),("R25","5/2"))
TIMES = (10,15,20,25,40)
BASE = (v12.K0,v12.K1)
PROGRAM_NAMES = ("BASE",) + tuple(
    f"F_{name}_T{minute}" for name,rate in RATES for minute in TIMES
) + ("W_R25_T10_T20","W_R25_T15_T20")


def need(ok,code):
    if not ok:
        raise ValueError(code)


def make_probe(pid,rate,minute):
    need(type(minute) is int and minute in TIMES,
         "CAF14_UNDECLARED_TIME")
    need(rate in ("3/2","9/5","5/2"),"CAF14_UNDECLARED_RATE")
    return {"id":pid,"rate":rate,"minute":minute,
            "channels":FULL_CHANNELS}


def frozen_programs():
    result={"BASE":BASE}
    for name,rate in RATES:
        for t in TIMES:
            result[f"F_{name}_T{t}"]=BASE+(make_probe("T",rate,t),)
    result["W_R25_T10_T20"]=BASE+(
        make_probe("T1","5/2",10),make_probe("T2","5/2",20))
    result["W_R25_T15_T20"]=BASE+(
        make_probe("T1","5/2",15),make_probe("T2","5/2",20))
    need(tuple(result)==PROGRAM_NAMES and len(result)==18,
         "CAF14_FROZEN_PROGRAMSET_CHANGED")
    return result


def signature_flat(reading,probes):
    return v13.flattened(reading,probes)


def rational_witness(atom):
    return atom["left"] if atom["kind"]=="point" else (
        atom["left"]+atom["right"])/2


def clocks_for_model(model):
    """One calendar per rate; pulse always 20 minutes even for read t40."""
    return {
        rate:v12.build_parametric_calendar(model["stages"],rate)
        for rate in ("6/5","3/2","9/5","5/2")
    }


def family_program_catalog(model,program,calendars):
    probes=frozen_programs()[program]
    atoms=v12.exact_atomic_regimes(calendars,probes)
    uniq={}
    for atom in atoms:
        sig=signature_flat(atom["pred"],probes)
        d=rational_witness(atom)
        need(v11.D_LOW<=d<=v11.D_HIGH,
             "CAF14_SIGNATURE_WITNESS_OUTSIDE_DOMAIN")
        if sig not in uniq:
            prediction={p["id"]:v12.predict_channels(
                calendars[p["rate"]],p["channels"],p["minute"],d)
                for p in probes}
            need(signature_flat(prediction,probes)==sig,
                 "CAF14_SIGNATURE_NOT_REPRODUCIBLE")
            uniq[sig]={
                "signature":sig,"witness_duration":d,
                "witness_capacity":Fraction(60)/d,
                "representative_atom_type":atom["kind"],
            }
    return {"atoms":atoms,"signatures":tuple(uniq.values()),
            "n_atomic_regimes":len(atoms)}


def make_catalog():
    models=v11.models()
    p=frozen_programs()
    all_rows={}
    for model in models:
        calendars=clocks_for_model(model)
        for pid in p:
            all_rows[(pid,model["id"])]=family_program_catalog(
                model,pid,calendars)
    need(len(all_rows)==18*6,"CAF14_WRONG_CATALOG_SIZE")
    return all_rows


def serialize_catalog(catalog):
    result={}
    for pid in PROGRAM_NAMES:
        result[pid]={}
        for model in v11.models():
            row=catalog[(pid,model["id"])]
            probes=frozen_programs()[pid]
            result[pid][model["id"]]={
                "class":model["label"],
                "n_atomic_regimes":row["n_atomic_regimes"],
                "n_distinct_signatures":len(row["signatures"]),
                "signatures":[{
                    "signature":list(r["signature"]),
                    "witness_capacity":str(r["witness_capacity"]),
                    "witness_duration":str(r["witness_duration"]),
                    "representative_atom_type":r["representative_atom_type"],
                } for r in row["signatures"]],
                "atoms":[{
                    "kind":a["kind"],"d_low":str(a["left"]),
                    "d_high":str(a["right"]),
                    "low_included":a["include_left"],
                    "high_included":a["include_right"],
                    "signature":list(signature_flat(a["pred"],probes)),
                } for a in row["atoms"]],
            }
    return result


def pair_graph(catalog):
    models=v11.models()
    output={}
    for pid in PROGRAM_NAMES:
        pairs=[]
        for a,z in combinations(models,2):
            first=[{
                "signature":r["signature"],
                "witness_c":r["witness_capacity"]
            } for r in catalog[(pid,a["id"])]["signatures"]]
            second=[{
                "signature":r["signature"],
                "witness_c":r["witness_capacity"]
            } for r in catalog[(pid,z["id"])]["signatures"]]
            witness=v13.sign_pair_witness(first,second)
            tp=("double_double" if len(a["stages"])==len(z["stages"])==2
                else "single_single" if len(a["stages"])==len(z["stages"])==1
                else "single_double")
            pairs.append({
                "class_a":a["label"],"class_b":z["label"],
                "type":tp,"confusable_exists":witness is not None,
                "globally_robustly_separable":witness is None,
                "witness":witness,
            })
        need(len(pairs)==15,"CAF14_INVALID_PAIR_COUNT")
        output[pid]={
            "n_pairs":15,
            "n_confusable":sum(p["confusable_exists"] for p in pairs),
            "n_separable":sum(p["globally_robustly_separable"] for p in pairs),
            "confusable_double_double":sum(
                p["confusable_exists"] and p["type"]=="double_double"
                for p in pairs),
            "confusable_single_double":sum(
                p["confusable_exists"] and p["type"]=="single_double"
                for p in pairs),
            "pairs":pairs,
        }
    return output


def physical_snapshot(config,rate,minute):
    """Native DES prefix experiment, no future arrivals for t<20."""
    need(minute in TIMES or minute==20,"CAF14_INVALID_SNAPSHOT_TIME")
    arrivals=des.half_open_arrivals(rate,20)
    if minute<20:
        arrivals=tuple(t for t in arrivals if t<=minute)
    snapshots=des.run_toy_engine(
        config,arrivals,(Fraction(0),Fraction(minute)))
    snap=snapshots[-1]
    allstocks=[a+z for a,z in zip(
        snap.stage_waiting,snap.stage_in_service)]
    need(snap.accepted_cum_orders==
         snap.delivered_cum_orders+sum(allstocks),
         "CAF14_MASS_BALANCE_FAILED")
    need(snap.pending_orders==sum(allstocks),
         "CAF14_PENDING_STOCK_MISMATCH")
    return snap


def physical_fields(snap,channels):
    out=[]
    allstocks=[w+u for w,u in zip(
        snap.stage_waiting,snap.stage_in_service)]
    for field,stage in channels:
        if field=="delivered" and stage is None:
            val=snap.delivered_cum_orders
        else:
            need(stage in b.STAGES,"CAF14_BAD_PHYSICAL_STAGE")
            idx=b.STAGES.index(stage)
            if field=="waiting":
                val=snap.stage_waiting[idx]
            elif field=="stage_stock":
                val=allstocks[idx]
            else:
                raise ValueError("CAF14_UNKNOWN_PHYSICAL_CHANNEL")
        need(type(val) is int and val>=0,"CAF14_NEGATIVE_OBSERVATION")
        out.append(val)
    return out


def physical_probes_cached(config,probe_cache):
    """One snapshot per unique rate/time: two T windows share one trajectory."""
    return {
        p["id"]:physical_fields(
            probe_cache[(p["rate"],p["minute"])],p["channels"])
        for p in config
    }


def matches_obs(reading,signature,probes):
    return v13.compatible_exact(signature_flat(reading,probes),signature)


def world_inference(reading,pid,catalog):
    """The analyst sees ONLY readings, fixed programs and abstract catalog."""
    probes=frozen_programs()[pid]
    observed=signature_flat(reading,probes)
    surviving=[]
    for model in v11.models():
        if any(v13.compatible_exact(observed,row["signature"])
               for row in catalog[(pid,model["id"])]["signatures"]):
            surviving.append(model["label"])
    return sorted(surviving)


def robust_true_singleton(reading,pid,true_class,catalog):
    """EVALUATOR only, compare all alternative family signatures within 2."""
    sig=signature_flat(reading,frozen_programs()[pid])
    for m in v11.models():
        if m["label"]==true_class:
            continue
        if any(v13.compatible_signatures(sig,r["signature"])
               for r in catalog[(pid,m["id"])]["signatures"]):
            return False
    return True


def true_d_in_atom(reading,pid,catalog,class_label,d):
    """Stronger than class survives: exact true capacity belongs to its atom."""
    probes=frozen_programs()[pid]
    sig=signature_flat(reading,probes)
    model=next(m for m in v11.models() if m["label"]==class_label)
    return any(
        (signature_flat(a["pred"],probes)==sig)
        and (a["left"]<d<a["right"]
             or (a["left"]==d and a["include_left"])
             or (a["right"]==d and a["include_right"]))
        for a in catalog[(pid,model["id"])]["atoms"]
    )


def read_cache(world,all_programs):
    physical={}
    for probes in all_programs.values():
        for p in probes:
            k=(p["rate"],p["minute"])
            if k not in physical:
                physical[k]=physical_snapshot(
                    world["config"],p["rate"],p["minute"])
    return physical


def run(out,checkout_sha,head_sha):
    need(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha)
         and b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha),
         "CAF14_SHA_REQUIRED")
    root=Path(out).resolve()
    need(not root.exists(),"CAF14_REFUSE_OVERWRITE")
    programs=frozen_programs()
    catalog=make_catalog()
    graphs=pair_graph(catalog)
    worlds=v12.worlds()
    need(len(worlds)==32,"CAF14_WORLD_COUNT_CHANGED")
    root.mkdir(parents=True,exist_ok=False)
    def save(name,val):
        b.lab.write_new(root,name,val)
    save("00B_EXACT_SIGNATURES_BEFORE_EVAL.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "no_world_evaluator_DES_called":True,
        "family_program_catalog":serialize_catalog(catalog),
    })
    digest=sha256(
        (root/"00B_EXACT_SIGNATURES_BEFORE_EVAL.json").read_bytes()).hexdigest()
    save("00_PLAN_BEFORE_EVAL.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "families":v11.models(),
        "fixed_programs":[{"id":pid,"probes":probes}
                          for pid,probes in programs.items()],
        "worlds_EVALUATOR_ONLY":worlds,
        "catalog_sha256":"sha256:"+digest,
        "n_models":6,"n_programs":18,"n_worlds":32,
        "n_frozen_comparisons":18*15,
        "n_frozen_inversions":18*32*6,
        "duration_range":[str(v11.D_LOW),str(v11.D_HIGH)],
        "capacity_range":[str(v11.CAPACITY_LOW),str(v11.CAPACITY_HIGH)],
        "tolerance_orders":v13.TOLERANCE,
        "pulse_end_minute":20,
        "all_catalog_predictions_precede_real_world_evaluation":True,
        "new_world_DES_calls_before_plan":0,
        "measurement_error_not_calibrated":True,
    })
    save("00C_GLOBAL_GRAPH_BEFORE_EVAL.json",{
        "schema":SCHEMA,"pair_graphs":graphs,
        "does_not_use_world_truth":True,
    })
    evaluated=[]
    for world in worlds:
        snapshots=read_cache(world,programs)
        for pid,probes in programs.items():
            observations=physical_probes_cached(probes,snapshots)
            inferred=world_inference(observations,pid,catalog)
            truth=world["truth_class"]
            if truth is not None:
                d=Fraction(60,world["capacity"])
                need(true_d_in_atom(
                    observations,pid,catalog,truth,d),
                    "CAF14_TRUE_CAPACITY_EXCLUDED")
                need(truth in inferred,"CAF14_TRUE_CLASS_EXCLUDED")
            windows=[p for p in probes if p["id"] not in ("K0","K1")]
            active_windows=sum(
                any(observations[p["id"]][i]!=0
                    for i in range(len(v13.WAIT)))
                for p in windows)
            full_stock_windows=sum(
                any(observations[p["id"]][i]!=0
                    for i in range(len(v13.WAIT),len(v13.FULL)))
                for p in windows)
            rateloads={
                p["id"]:str(Fraction(p["rate"])*60/world["capacity"])
                for p in windows
            }
            exact_single=(inferred[0] if len(inferred)==1 else None)
            evaluated.append({
                "world":world["id"],"cohort":world["cohort"],"program":pid,
                "type_EVALUATOR_ONLY":world["truth_type"],
                "truth_class_EVALUATOR_ONLY":truth,
                "truth_capacity_EVALUATOR_ONLY":world["capacity"],
                "demand_capacity_ratios_EVALUATOR_ONLY":rateloads,
                "observed":observations,
                "active_queue_windows":active_windows,
                "nonzero_stock_windows":full_stock_windows,
                "compatible_classes":inferred,
                "n_classes":len(inferred),
                "unique_class":exact_single,
                "robust_true_singleton_EVALUATOR_ONLY":(
                    robust_true_singleton(observations,pid,truth,catalog)
                    if truth is not None else None),
                "truth_parameter_contained_EVALUATOR_ONLY":
                    True if truth is not None else None,
            })
    need(len(evaluated)==32*18,
         "CAF14_EVALUATIONS_WRONG")
    for world in worlds:
        rows=[r for r in evaluated if r["world"]==world["id"]]
        base=set(next(r for r in rows if r["program"]=="BASE")["compatible_classes"])
        need(all(set(r["compatible_classes"]).issubset(base) for r in rows),
             "CAF14_NON_MONOTONIC_CLASS_FILTER")
    summary={}
    for pid in PROGRAM_NAMES:
        subset=[r for r in evaluated if r["program"]==pid]
        within=[r for r in subset if r["truth_class_EVALUATOR_ONLY"] is not None]
        extra=[r for r in subset if r["truth_class_EVALUATOR_ONLY"] is None]
        need(len(within)==27 and len(extra)==5,
             "CAF14_BAD_DENOMINATORS")
        double=[r for r in within if r["type_EVALUATOR_ONLY"]=="double"]
        single=[r for r in within if r["type_EVALUATOR_ONLY"]=="single"]
        need(len(double)==18 and len(single)==9,
             "CAF14_BAD_STRUCTURE_DENOMINATORS")
        summary[pid]={
            "n_within":27,"n_unknown_extra":5,
            "n_channels":sum(len(p["channels"]) for p in programs[pid]),
            "global_confusable_pairs":graphs[pid]["n_confusable"],
            "global_separable_pairs":graphs[pid]["n_separable"],
            "confusable_double_double":graphs[pid]["confusable_double_double"],
            "confusable_single_double":graphs[pid]["confusable_single_double"],
            "true_class_coverage":sum(
                r["truth_class_EVALUATOR_ONLY"] in r["compatible_classes"]
                for r in within),
            "true_parameter_coverage":sum(
                r["truth_parameter_contained_EVALUATOR_ONLY"] for r in within),
            "unique_correct":sum(
                r["unique_class"]==r["truth_class_EVALUATOR_ONLY"]
                for r in within),
            "robust_unique_true":sum(
                r["robust_true_singleton_EVALUATOR_ONLY"] for r in within),
            "double_unique":sum(r["unique_class"]==r["truth_class_EVALUATOR_ONLY"]
                                for r in double),
            "double_robust":sum(r["robust_true_singleton_EVALUATOR_ONLY"]
                                for r in double),
            "single_unique":sum(r["unique_class"]==r["truth_class_EVALUATOR_ONLY"]
                                for r in single),
            "unknown_false_unique":sum(r["unique_class"] is not None for r in extra),
            "unknown_no_compatible_family":sum(r["n_classes"]==0 for r in extra),
            "unknown_compatible_as_known":sum(r["n_classes"]>0 for r in extra),
            "n_all_six_within":sum(r["n_classes"]==6 for r in within),
            "avg_class_count_within":round(
                sum(r["n_classes"] for r in within)/27,4),
            "worlds_any_nonzero_queue":sum(r["active_queue_windows"]>0
                                            for r in subset),
            "worlds_any_nonzero_stock":sum(r["nonzero_stock_windows"]>0
                                            for r in subset),
        }
    report={
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_worlds":32,"n_programs":18,
        "n_global_pair_comparisons":18*15,
        "n_structural_parameter_filters":18*32*6,
        "n_exact_family_program_catalogs":18*6,
        "fully_precomputed_before_world_evaluation":True,
        "truth_never_passed_to_inverse":True,
        "no_new_selector":True,"no_external_validation":True,
        "summary":summary,"graphs":graphs,
        "evaluations":evaluated,
        "promotion_gate":GATE,
    }
    save("01_RESULTADOS.json",report)
    lines=[
        "# CAF-14 — Excitación de demanda y ventanas temporales",
        "",
        "**No validación externa.** Familias deterministas compartidas;",
        "capacidad continua exacta c∈[55,110], ±1 no calibrado.",
        "Comparar esquemas de tasa y tiempo NO identifica una política óptima.",
        "",
        "| Programa | Canales | Confundibles /15 | Dobles vs dobles confundibles /3 | Únicos correctos /27 | Robustamente únicos /27 | Dobles únicos /18 | Controles 4ª etapa únicos falsos /5 | Controles fuera de todas las familias /5 | Mundos con cola no nula /32 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pid in PROGRAM_NAMES:
        s=summary[pid]
        lines.append("| "+" | ".join(map(str,(
            pid,s["n_channels"],s["global_confusable_pairs"],
            s["confusable_double_double"],s["unique_correct"],
            s["robust_unique_true"],s["double_unique"],
            s["unknown_false_unique"],s["unknown_no_compatible_family"],
            s["worlds_any_nonzero_queue"]
        )))+" |")
    lines+=["",
        "## Auditoría de casos individuales",
        "",
        "| Mundo | Programa | K0/K1, T/T1/T2 | Clases compatibles | Clase única | Robusto verdadero | Razón llegada/capacidad |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in evaluated:
        lines.append("| "+" | ".join((
            r["world"],r["program"],str(r["observed"]),
            ", ".join(r["compatible_classes"]) or "∅",
            r["unique_class"] or "N/A",
            (str(r["robust_true_singleton_EVALUATOR_ONLY"])
             if r["truth_class_EVALUATOR_ONLY"] is not None else "N/A"),
            str(r["demand_capacity_ratios_EVALUATOR_ONLY"]),
        ))+" |")
    lines+=["",
        "## Interpretación condicionada",
        "",
        "- La misma c debe satisfacer conjuntamente TODAS las lecturas.",
        "- Firmas separables globalmente solo lo son en estos programas,",
        "  sensores, dominio paramétrico y banda ±1; par confundible no",
        "  implica equivalencia universal de dinámicas.",
        "- Dos ventanas pertenecen a una sola trayectoria T a misma tasa;",
        "  K0/K1 y trayectoria T son resets independientes pero misma c.",
        "- Medir en el pulso puede revelar colas que desaparecen tras drenar;",
        "  medir al t40 no garantiza que el sistema siga saturado.",
        "- La cuarta etapa real no está en el catálogo. Clasificación única",
        "  en sus controles es falsa, no certificación física.",
        "- La tasa 150/h sobrepasa capacidad nominal de 55..110/h y solo",
        "  se usa como excitación sintética de laboratorio.",
        "- Los costos monetarios, riesgo real, ruido y distribuciones de",
        "  servicio/llegadas permanecen fuera de alcance.",
        "",
        "**Gate:** "+GATE,
        ""]
    save("02_INFORME.md","\n".join(lines))
    artifacts=sorted(p for p in root.iterdir() if p.is_file())
    save("03_MANIFIESTO.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "files_sha256":{p.name:"sha256:"+sha256(p.read_bytes()).hexdigest()
                        for p in artifacts},
        "catalog_and_graph_saved_before_evaluator":True,
        "no_external_custody":True,
    })
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--checkout-sha",required=True)
    parser.add_argument("--head-sha",required=True)
    a=parser.parse_args()
    result=run(a.out,a.checkout_sha,a.head_sha)
    print(json.dumps({
        "n_worlds":result["n_worlds"],"n_programs":result["n_programs"],
        "filters":result["n_structural_parameter_filters"],
        "summary":result["summary"],"gate":result["promotion_gate"]
    },ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
