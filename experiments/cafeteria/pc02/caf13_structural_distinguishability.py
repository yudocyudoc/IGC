#!/usr/bin/env python3
"""CAF-13: exhaustive global distinguishability of continuous-parameter
deterministic FIFO tandem families across fixed observation programs.

Existential confusability: there exist parameters c_M, c_N (possibly different)
and compatible integer measurements +/-1 in EVERY declared channel.
No sampling, optimization, stochastic calibration or selector.
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

SCHEMA="igc-caf13-global-family-distinguishability/0.1"
PROTO_COMMIT="1267f8ffc3583b04619ceb8607a189c78c12a643"
GATE="BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION"
TOLERANCE=1

WAIT=tuple(("waiting",s) for s in b.STAGES)
STOCK=tuple(("stage_stock",s) for s in b.STAGES)
FULL=WAIT+STOCK

PROGRAMS=(
    ("BASE",None),
    ("Q20_15",("3/2",20,WAIT)),
    ("STOCK20_15",("3/2",20,STOCK)),
    ("FULL20_15",("3/2",20,FULL)),
    ("Q40_15",("3/2",40,WAIT)),
    ("FULL40_15",("3/2",40,FULL)),
    ("Q20_18",("9/5",20,WAIT)),
    ("FULL40_18",("9/5",40,FULL)),
)
IDS=tuple(p[0] for p in PROGRAMS)
PROGRAM_MAP=dict(PROGRAMS)
P0=v12.K0
P1=v12.K1


def need(ok,code):
    if not ok: raise ValueError(code)


def program_probes(pid):
    need(pid in PROGRAM_MAP,"CAF13_UNDECLARED_PROGRAM")
    t=PROGRAM_MAP[pid]
    base=[P0,P1]
    if t is not None:
        rate,minute,channels=t
        base.append({"id":"T","rate":rate,"minute":minute,"channels":channels})
    return tuple(base)


def flattened(readings,probes):
    """All components in stable order, preserving K0/K1/T and channel order."""
    need(set(readings)=={p["id"] for p in probes},
         "CAF13_MISMATCHED_PROBES")
    return tuple(v for p in probes for v in readings[p["id"]])


def label_family(m):
    return m["label"]


def witness_d(atom):
    if atom["kind"]=="point":
        return atom["left"]
    return (atom["left"]+atom["right"])/2


def family_signatures(stage_indices,program):
    probes=program_probes(program)
    rates=sorted({p["rate"] for p in probes})
    calendars={
        rate:v12.build_parametric_calendar(stage_indices,rate)
        for rate in rates
    }
    atoms=v12.exact_atomic_regimes(calendars,probes)
    by_sig={}
    for atom in atoms:
        sig=flattened(atom["pred"],probes)
        d=witness_d(atom)
        need(v11.D_LOW<=d<=v11.D_HIGH,
             "CAF13_WITNESS_OUT_OF_DOMAIN")
        # One exact rational representative per distinct integer output.
        # Need not compress all components: original atoms kept in archive.
        if sig not in by_sig:
            predicted={
                p["id"]:v12.predict_channels(
                    calendars[p["rate"]],p["channels"],p["minute"],d)
                for p in probes
            }
            need(flattened(predicted,probes)==sig,
                 "CAF13_WITNESS_NOT_REPRODUCIBLE")
            by_sig[sig]={"signature":sig,"witness_d":d,
                         "witness_c":Fraction(60)/d,
                         "atom_kind":atom["kind"],
                         "atom_duration_left":atom["left"],
                         "atom_duration_right":atom["right"]}
    need(by_sig,"CAF13_NO_SIGNATURES")
    return {"n_atomic_regimes":len(atoms),
            "signatures":list(by_sig.values()),
            "atoms":atoms}


def compatible_signatures(a,z,tol=TOLERANCE):
    need(len(a)==len(z) and type(tol) is int and tol>=0,
         "CAF13_BAD_SIGNATURE_LENGTH_OR_TOLERANCE")
    return all(abs(u-v)<=2*tol for u,v in zip(a,z))


def compatible_exact(observed,forecast,tol=TOLERANCE):
    need(len(observed)==len(forecast),
         "CAF13_BAD_SIGNATURE_LENGTH")
    return all(abs(u-v)<=tol for u,v in zip(observed,forecast))


def canonical_signature_row(row):
    return {
        "vector":list(row["signature"]),
        "witness_duration":str(row["witness_d"]),
        "witness_capacity":str(row["witness_c"]),
        "atom_type":row["atom_kind"],
        "atom_duration_left":str(row["atom_duration_left"]),
        "atom_duration_right":str(row["atom_duration_right"]),
    }


def sign_pair_witness(rows_a,rows_b):
    """Exact enumeration over all signatures. First witness is sufficient."""
    # Bucket adjacent baseline counts to prune many impossible cases.
    prefix_index={}
    for z in rows_b:
        s=z["signature"]
        prefix_index.setdefault(s[:2],[]).append(z)
    for a in rows_a:
        sa=a["signature"]
        for k0 in range(max(0,sa[0]-2*TOLERANCE),sa[0]+2*TOLERANCE+1):
            for k1 in range(max(0,sa[1]-2*TOLERANCE),sa[1]+2*TOLERANCE+1):
                for z in prefix_index.get((k0,k1),()):
                    if compatible_signatures(sa,z["signature"]):
                        return {
                            "first_signature":list(sa),
                            "second_signature":list(z["signature"]),
                            "first_capacity":str(a["witness_c"]),
                            "second_capacity":str(z["witness_c"]),
                            "common_integer_observation_example":[
                                max(u-TOLERANCE,v-TOLERANCE)
                                for u,v in zip(sa,z["signature"])
                            ],
                        }
    return None


def build_catalog():
    """All 48 family/program exhaustive signatures, no evaluator worlds."""
    out={}
    for program in IDS:
        for m in v11.models():
            out[(program,m["id"])]=family_signatures(m["stages"],program)
    need(len(out)==len(IDS)*6,"CAF13_CATALOG_INCOMPLETE")
    return out


def global_graph(catalog):
    """One undirected edge per confusable PAIR, never a partition."""
    out={}
    models=v11.models()
    for pid in IDS:
        pairs=[]
        for a,z in combinations(models,2):
            found=sign_pair_witness(
                catalog[(pid,a["id"])]["signatures"],
                catalog[(pid,z["id"])]["signatures"])
            pairs.append({
                "class_a":a["label"],"class_b":z["label"],
                "type_pair":(
                    "single_vs_double"
                    if (len(a["stages"])==1)!=(len(z["stages"])==1)
                    else "single_vs_single" if len(a["stages"])==1
                    else "double_vs_double"
                ),
                "confusable_existential":found is not None,
                "robust_separable_all_parameter_pairs":found is None,
                "witness":found,
            })
        need(len(pairs)==15,"CAF13_PAIR_GRAPH_NOT_COMPLETE")
        out[pid]={
            "n_families":6,
            "n_pairs":15,
            "n_existentially_confusable":sum(
                x["confusable_existential"] for x in pairs),
            "n_robustly_separable_global":sum(
                x["robust_separable_all_parameter_pairs"] for x in pairs),
            "confusable_single_double":sum(
                x["confusable_existential"]
                for x in pairs if x["type_pair"]=="single_vs_double"),
            "confusable_double_double":sum(
                x["confusable_existential"]
                for x in pairs if x["type_pair"]=="double_vs_double"),
            "pairs":pairs,
            "not_an_equivalence_partition":True,
        }
    return out


def evaluate_observation(readings,program,cat):
    """Does not know the true class, topology, capacity or physical config."""
    probes=program_probes(program)
    sig=flattened(readings,probes)
    feasible=[]
    for m in v11.models():
        rows=cat[(program,m["id"])]["signatures"]
        if any(compatible_exact(sig,z["signature"]) for z in rows):
            feasible.append(m["label"])
    return sorted(feasible)


def is_robust_true_state_singleton(readings,program,real_class,cat):
    """Evaluator ONLY: all +/-1 errors around true exact prediction exclude
    every other class at every c, requiring a channel gap >2.
    """
    probes=program_probes(program)
    true_sig=flattened(readings,probes)
    for m in v11.models():
        if m["label"]==real_class:
            continue
        if any(compatible_signatures(true_sig,row["signature"])
               for row in cat[(program,m["id"])]["signatures"]):
            return False
    return True


def physical_observe(config,program):
    return {
        p["id"]:b.read_physical(config,p["rate"],p["minute"],
                               p["channels"])
        for p in program_probes(program)
    }


def run(out,checkout_sha,head_sha):
    need(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha) is not None
         and b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha) is not None,
         "CAF13_SHA_REQUIRED")
    out=Path(out).resolve()
    need(not out.exists(),"CAF13_REFUSE_OVERWRITE")
    cat=build_catalog()
    graph=global_graph(cat)
    worlds=v12.worlds()
    out.mkdir(parents=True,exist_ok=False)
    def save(name,obj):
        b.lab.write_new(out,name,obj)
    catalog_json={
        pid:{
            m["id"]:{
                "class":m["label"],"n_atomic_regimes":cat[(pid,m["id"])]["n_atomic_regimes"],
                "n_distinct_signatures":len(cat[(pid,m["id"])]["signatures"]),
                "signatures":[canonical_signature_row(z)
                              for z in cat[(pid,m["id"])]["signatures"]],
                "atoms":[{
                    "kind":atom["kind"],
                    "duration_left":str(atom["left"]),
                    "duration_right":str(atom["right"]),
                    "include_left":atom["include_left"],
                    "include_right":atom["include_right"],
                    "signature":list(flattened(
                        atom["pred"],program_probes(pid))),
                } for atom in cat[(pid,m["id"])]["atoms"]],
            }
            for m in v11.models()
        }
        for pid in IDS
    }
    save("00B_CATALOGO_FIRMAS_ANTES_MUNDOS.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "no_evaluator_DES_calls_before_catalog":True,
        "exact_48_family_program_signature_sets":catalog_json,
    })
    sign_digest=sha256(
        (out/"00B_CATALOGO_FIRMAS_ANTES_MUNDOS.json").read_bytes()).hexdigest()
    save("00_PLAN_ANTES_MUNDOS.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "K0_K1":(P0,P1),
        "programs":[{"id":pid,"probes":program_probes(pid)}
                    for pid in IDS],
        "model_families":v11.models(),
        "continuous_capacity_range":[str(v11.CAPACITY_LOW),str(v11.CAPACITY_HIGH)],
        "tolerance_orders":TOLERANCE,
        "worlds_for_evaluator_only":worlds,
        "catalog_sha256":"sha256:"+sign_digest,
        "true_world_DES_calls_before_plan":0,
        "all_signatures_precomputed_before_evaluator":True,
        "no_probability_no_cost_comparison":True,
        "all_programs_frozen_before_any_world_DES":True,
    })
    # Pure structural graph computed with catalog before world evaluation.
    save("00C_GRAFO_GLOBAL_PRE_EVALUACION.json",{
        "schema":SCHEMA,"provenance":"ONLY_EXACT_SIGNATURES_NOT_WORLD_TRUTH",
        "graphs":graph,
    })
    evaluations=[]
    for world in worlds:
        for pid in IDS:
            observed=physical_observe(world["config"],pid)
            feasible=evaluate_observation(observed,pid,cat)
            truth=world["truth_class"]
            robust=(
                is_robust_true_state_singleton(observed,pid,truth,cat)
                if truth is not None else None
            )
            # Verify true d and structure are preserved with ALL probes,
            # not simply the existence of some capacity of same class.
            if truth is not None:
                m=next(x for x in v11.models() if x["label"]==truth)
                d=Fraction(60,world["capacity"])
                predicted=family_signatures(m["stages"],pid)
                true_sig=flattened(observed,program_probes(pid))
                need(any(
                    row["signature"]==true_sig and
                    (atom["left"]<=d<=atom["right"]) and (
                        atom["left"]<d<atom["right"] or
                        atom["left"]==d and atom["include_left"] or
                        atom["right"]==d and atom["include_right"])
                    for atom in predicted["atoms"]
                    for row in [{"signature":flattened(
                        atom["pred"],program_probes(pid))}]
                ),"CAF13_TRUE_CAPACITY_EXCLUDED")
                need(truth in feasible,"CAF13_TRUE_CLASS_EXCLUDED")
            evaluations.append({
                "world":world["id"],"cohort":world["cohort"],
                "program":pid,
                "world_type_EVALUATOR_ONLY":world["truth_type"],
                "truth_class_EVALUATOR_ONLY":truth,
                "truth_capacity_EVALUATOR_ONLY":world["capacity"],
                "observed":observed,
                "compatible_classes":feasible,
                "n_classes":len(feasible),
                "singleton_at_exact_reading":len(feasible)==1,
                "singleton_class":feasible[0] if len(feasible)==1 else None,
                "robustly_singleton_true_state_EVALUATOR_ONLY":robust,
                "true_class_covered_EVALUATOR_ONLY":
                    (truth in feasible if truth is not None else None),
            })
    need(len(evaluations)==len(worlds)*len(IDS)==256,
         "CAF13_WRONG_EVALUATION_COUNT")
    for w in worlds:
        rows=[z for z in evaluations if z["world"]==w["id"]]
        base=set(next(x for x in rows if x["program"]=="BASE")["compatible_classes"])
        need(all(set(x["compatible_classes"]).issubset(base)
                 for x in rows),"CAF13_NEW_PROBE_ADDS_CLASS")
    summary={}
    for pid in IDS:
        rows=[z for z in evaluations if z["program"]==pid]
        inside=[x for x in rows if x["truth_class_EVALUATOR_ONLY"] is not None]
        extra=[x for x in rows if x["truth_class_EVALUATOR_ONLY"] is None]
        need(len(inside)==27 and len(extra)==5,"CAF13_WRONG_DENOMINATORS")
        summary[pid]={
            "n_in_family":27,"n_unknown":5,
            "in_family_covered":sum(x["true_class_covered_EVALUATOR_ONLY"]
                                    for x in inside),
            "in_family_singleton_exact_correct":sum(
                x["singleton_class"]==x["truth_class_EVALUATOR_ONLY"]
                for x in inside),
            "in_family_robust_singleton_true":sum(
                x["robustly_singleton_true_state_EVALUATOR_ONLY"]
                for x in inside),
            "double_in_family_unique_exact":sum(
                x["singleton_class"]==x["truth_class_EVALUATOR_ONLY"]
                for x in inside if x["world_type_EVALUATOR_ONLY"]=="double"),
            "double_in_family_robust_singleton":sum(
                x["robustly_singleton_true_state_EVALUATOR_ONLY"]
                for x in inside if x["world_type_EVALUATOR_ONLY"]=="double"),
            "unknown_false_singleton":sum(
                x["singleton_at_exact_reading"] for x in extra),
            "unknown_outside_all_families":sum(
                x["n_classes"]==0 for x in extra),
            "n_all_six_in_family":sum(x["n_classes"]==6 for x in inside),
            "avg_class_count_in_family":round(
                sum(x["n_classes"] for x in inside)/27,4),
            "global_confusable_pairs":graph[pid]["n_existentially_confusable"],
            "global_robust_separable_pairs":graph[pid]["n_robustly_separable_global"],
        }
    results={
        "schema":SCHEMA,"protocol_first_commit":PROTO_COMMIT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_programs":len(IDS),"n_worlds":len(worlds),
        "n_family_world_program_filters":len(evaluations)*6,
        "n_pair_comparisons":len(IDS)*15,
        "distinct_family_program_signature_catalog":48,
        "summary":summary,
        "global_graph":graph,"evaluations":evaluations,
        "truth_never_given_to_inference":True,
        "not_real_world_validated":True,
        "promotion_gate":GATE,
    }
    save("01_RESULTADOS.json",results)
    lines=[
        "# CAF-13 — Distinguibilidad estructural global de familias continuas",
        "",
        "Misma física DES determinista CAF-01; ±1 artificial, sin incertidumbre",
        "de sensor calibrada, sin costos, sin inferencia de mecanismos reales.",
        "Un par CONFUSABLE significa que EXISTEN dos capacidades que permiten",
        "lecturas comunes. NO significa que el par sea inidentificable siempre.",
        "",
        "| Programa | Aristas confundibles /15 | Pares separables robustos /15 | Únicos correctos /27 | Únicos robustos /27 | Dobles únicos /18 | Dobles robustos /18 | Falsos únicos unknown /5 | Controles sin familia /5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pid in IDS:
        s=summary[pid]
        lines.append("| "+" | ".join(map(str,(
            pid,s["global_confusable_pairs"],s["global_robust_separable_pairs"],
            s["in_family_singleton_exact_correct"],
            s["in_family_robust_singleton_true"],
            s["double_in_family_unique_exact"],
            s["double_in_family_robust_singleton"],
            s["unknown_false_singleton"],s["unknown_outside_all_families"]
        )))+" |")
    lines+=["",
        "## Pares globalmente confundibles o separables por programa",
        "",
        "| Programa | Familia A | Familia B | Confundible para algún par de capacidades | Capacidades testigo (si existe) |",
        "|---|---|---|---|---|",
    ]
    for pid in IDS:
        for pair in graph[pid]["pairs"]:
            w=pair["witness"]
            cap=(w["first_capacity"]+", "+w["second_capacity"]) if w else "N/A"
            lines.append("| "+" | ".join((
                pid,pair["class_a"],pair["class_b"],
                str(pair["confusable_existential"]),cap))+" |")
    lines+=["",
        "## Resultados mundiales con doble cuello",
        "",
        "| Mundo | Programa | Lecturas | Clases compatibles | Única exacta | Única robusta bajo ±1 |",
        "|---|---|---|---|---|---|",
    ]
    for row in evaluations:
        if row["world_type_EVALUATOR_ONLY"]!="double":
            continue
        lines.append("| "+" | ".join((
            row["world"],row["program"],str(row["observed"]),
            ",".join(row["compatible_classes"]) or "∅",
            str(row["singleton_at_exact_reading"]),
            str(row["robustly_singleton_true_state_EVALUATOR_ONLY"]),
        ))+" |")
    lines+=["",
        "## Límites de las afirmaciones",
        "",
        "- Todos los mundos con estructura representada proceden del mismo",
        "  DES y familia; recuperación no equivale a validación independiente.",
        "- Un par separable globalmente lo es solo bajo el programa y las",
        "  bandas indicadas, con la familia restringida y horizonte finito.",
        "- Un testigo de confusibilidad usa dos capacidades que pueden ser",
        "  DIFERENTES; la misma capacidad no es una condición necesaria.",
        "- Los nuevos operadores FULL20/FULL40 no pertenecen al menú original",
        "  CAF-07B ni tienen costo económico calibrado.",
        "- Los conteos en t40 siguen al pulso de llegadas t en [0,20);",
        "  no se incrementa artificialmente la demanda después de t20.",
        "- Un único conocido ante un control de cuarta etapa es falso único,",
        "  no un diagnóstico real. Una familia incompatible tampoco prueba",
        "  que exista precisamente una cuarta etapa.",
        "- El informe no entrena un selector ni afirma optimalidad.",
        "",
        "Gate: "+GATE,
        ""]
    save("02_INFORME.md","\n".join(lines))
    saved=sorted(p for p in out.iterdir() if p.is_file())
    save("03_MANIFIESTO.json",{
        "schema":SCHEMA,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "files_sha256":{
            p.name:"sha256:"+sha256(p.read_bytes()).hexdigest()
            for p in saved
        },
        "plan_written_before_evaluator_worlds":True,
        "same_simulator_not_blinded":True,
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
        "n_worlds":result["n_worlds"],
        "n_programs":result["n_programs"],
        "n_pair_comparisons":result["n_pair_comparisons"],
        "summary":result["summary"],"gate":result["promotion_gate"]
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
