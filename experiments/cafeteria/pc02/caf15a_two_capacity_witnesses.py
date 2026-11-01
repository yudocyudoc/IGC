#!/usr/bin/env python3
"""CAF-15A: exact, positive-only falsification of diagonal capacity assumptions.

A fixed rational lattice in independent (c1,c2) can PROVIDE witnesses
in the full continuous model. Failure to find a witness on this finite
lattice NEVER certifies global separation or model incompatibility.
No selector, no estocastic calibration, no hidden topology inference.
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
import caf13_structural_distinguishability as v13
import caf14_excitation_temporal_windows as v14
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf15a-two-free-capacity-lattice-counterexamples/0.1"
PRECOMMIT="af837c9d2e716ffc5a2b7e3f99c579e46be0e301"
PRECODE_AMENDMENT="7f66df735e0909433542a6d2e9cc21d8f232c932"
GATE="BLOCKED_LATTICE_WITNESSES_ONLY_NO_2D_GLOBAL_CERTIFICATION_NO_EXTERNAL_VALIDATION"
C_GRID=(55,60,65,68,70,75,80,83,86,90,95,97,100,105,110)
PIDS=("BASE","F_R18_T20","F_R25_T20","F_R25_T25")
CHANNELS=v13.FULL

def need(ok,code):
    if not ok: raise ValueError(code)

def programs():
    original=v14.frozen_programs()
    return {pid:original[pid] for pid in PIDS}

def config_for(stages,caps):
    """One independent exact Fraction service time for each limited stage."""
    need(tuple(stages) in v11.STAGE_SETS,"CAF15A_NOT_A_KNOWN_FAMILY")
    need(len(caps)==len(stages) and all(
        type(c) is int and c in C_GRID for c in caps),
        "CAF15A_CAPACITY_NOT_ON_FROZEN_LATTICE")
    by_stage=dict(zip(stages,caps))
    arr=[{
        "servers":1 if i in by_stage else 2,
        "service_minutes":str(Fraction(60,by_stage[i]))
            if i in by_stage else "1",
    } for i in range(3)]
    config={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,"stages":arr}
    des.validate_private_config(config)
    return config

def extra_config(cap):
    """Fourth stage fast controls are outside CAF07B's legacy cap<120 guard."""
    need(cap in (64,86,106,160,220),"CAF15A_UNDECLARED_EXTRA")
    config={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
            "stages":[{"servers":2,"service_minutes":"1"} for _ in range(3)]
            +[{"servers":1,"service_minutes":str(Fraction(60,cap))}]}
    des.validate_private_config(config)
    return config

def rows():
    results=[]
    for model in v11.models():
        stage=tuple(model["stages"])
        capsets=((c,) for c in C_GRID) if len(stage)==1 else (
            (c1,c2) for c1 in C_GRID for c2 in C_GRID)
        for capacities in capsets:
            serial="_".join(map(str,capacities))
            results.append({
                "id":model["id"]+"__"+serial,
                "model":model["id"],"class":model["label"],
                "stages":stage,"capacity_by_stage":capacities,
                "diagonal":len(set(capacities))==1,
                "config":config_for(stage,capacities),
            })
    need(len(results)==720,"CAF15A_WRONG_BANK_CARDINALITY")
    need(sum(x["diagonal"] for x in results)==90,
         "CAF15A_WRONG_DIAGONAL_CARDINALITY")
    need(sum(not x["diagonal"] for x in results)==630,
         "CAF15A_WRONG_OFF_DIAGONAL_CARDINALITY")
    need(len(set(x["id"] for x in results))==len(results),
         "CAF15A_DUPLICATE_ROW")
    return results

def native_readings(config):
    """Exactly 4 DES runs per configuration; retain common stage physics."""
    k0=v14.physical_snapshot(config,"6/5",10)
    k1=v14.physical_snapshot(config,"3/2",20)
    r18=v14.physical_snapshot(config,"9/5",20)
    arrival=des.half_open_arrivals("5/2",20)
    s20,s25=des.run_toy_engine(config,arrival,(Fraction(0),Fraction(20),Fraction(25)))[1:]
    allrows={
        "K0":v14.physical_fields(k0,(("delivered",None),)),
        "K1":v14.physical_fields(k1,(("delivered",None),)),
        "F_R18_T20":v14.physical_fields(r18,CHANNELS),
        "F_R25_T20":v14.physical_fields(s20,CHANNELS),
        "F_R25_T25":v14.physical_fields(s25,CHANNELS),
    }
    need(all(len(allrows[k])==6 for k in PIDS if k!="BASE"),
         "CAF15A_BAD_SENSOR_VECTOR")
    need(len(allrows["K0"])==len(allrows["K1"])==1,
         "CAF15A_BAD_K0K1")
    return {
        pid:tuple(allrows["K0"]+allrows["K1"]+
                  (allrows[pid] if pid!="BASE" else []))
        for pid in PIDS
    }

def compute_bank():
    """No evaluator worlds passed; 720 exact sensor signatures per program."""
    allrows=rows()
    for row in allrows:
        row["signatures"]=native_readings(row["config"])
        del row["config"] # prevent inference functions reading physical config
    need(len(allrows)==720,"CAF15A_BAD_SIGNATURE_BANK")
    return allrows

def candidate_with_witness(first,second):
    """Exact integer observation-box overlap +/-1 in each fixed channel."""
    need(len(first)==len(second),"CAF15A_SENSOR_SIZE_MISMATCH")
    if any(abs(x-y)>2 for x,y in zip(first,second)):
        return None
    obs=tuple(max(0,x-1,y-1) for x,y in zip(first,second))
    need(all(abs(o-x)<=1 and abs(o-y)<=1
             for o,x,y in zip(obs,first,second)),
         "CAF15A_BAD_COMMON_OBSERVATION")
    return obs

def witness_for(rows_a,rows_b,pid):
    """Frozen lexicographic search; successful witness is independently checkable."""
    index={}
    for z in rows_b:
        sig=z["signatures"][pid]
        index.setdefault(sig[:2],[]).append(z)
    for a in rows_a:
        sig=a["signatures"][pid]
        for k0 in range(max(0,sig[0]-2),sig[0]+3):
            for k1 in range(max(0,sig[1]-2),sig[1]+3):
                for z in index.get((k0,k1),()):
                    target=z["signatures"][pid]
                    common=candidate_with_witness(sig,target)
                    if common is not None:
                        return {
                            "first_row_id":a["id"],
                            "second_row_id":z["id"],
                            "first_capacity_by_stage":list(a["capacity_by_stage"]),
                            "second_capacity_by_stage":list(z["capacity_by_stage"]),
                            "first_signature":list(sig),
                            "second_signature":list(target),
                            "common_integer_reading":list(common),
                            "at_least_one_off_diagonal":not(a["diagonal"] and z["diagonal"]),
                        }
    return None

def graph(bank):
    all_models=v11.models()
    result={}
    for pid in PIDS:
        edges=[]
        for ma,mb in combinations(all_models,2):
            ra=[x for x in bank if x["model"]==ma["id"]]
            rb=[x for x in bank if x["model"]==mb["id"]]
            old=witness_for(
                [r for r in ra if r["diagonal"]],
                [r for r in rb if r["diagonal"]],pid)
            new=witness_for(ra,rb,pid)
            need(old is None or new is not None,
                 "CAF15A_DIAGONAL_NOT_SUBSET_OF_EXPANDED_MODEL")
            edges.append({
                "class_a":ma["label"],"class_b":mb["label"],
                "type":"double_double" if len(ma["stages"])==len(mb["stages"])==2
                       else "single_single" if len(ma["stages"])==len(mb["stages"])==1
                       else "single_double",
                "diag_status":"WITNESS_FOUND_IN_LATTICE" if old else "NO_WITNESS_ON_FIXED_LATTICE",
                "expanded_status":"WITNESS_FOUND_IN_LATTICE" if new else "NO_WITNESS_ON_FIXED_LATTICE",
                "new_edge_created_by_two_free_capacities":old is None and new is not None,
                "diagonal_witness":old,
                "expanded_witness":new,
            })
        need(len(edges)==15,"CAF15A_BAD_GRAPH")
        result[pid]={
            "pairs":edges,
            "edges_diagonal_lattice":sum(x["diagonal_witness"] is not None for x in edges),
            "edges_expanded_lattice":sum(x["expanded_witness"] is not None for x in edges),
            "new_edges_from_capacity_freedom":sum(
                x["new_edge_created_by_two_free_capacities"] for x in edges),
            "positive_witness_does_not_require_global_inversion":True,
            "absent_witness_does_not_certify_separability":True,
        }
    return result

def worlds():
    result=[]
    for stage in ((0,1),(0,2),(1,2)):
        m=next(z for z in v11.models() if tuple(z["stages"])==stage)
        for cap in ((68,70),(70,68),(83,86),(86,83),
                    (95,100),(100,95),(60,100),(100,60)):
            result.append({
                "id":"DUAL_FREE_"+''.join(map(str,stage))+"_"+'_'.join(map(str,cap)),
                "type":"in_family_off_diagonal","true_class":m["label"],
                "truth_capacity_by_stage":cap,
                "config":config_for(stage,cap),
            })
    for cap in (64,86,106,160,220):
        result.append({
            "id":"EXTRA_"+str(cap),"type":"extra_fourth_stage",
            "true_class":None,"truth_capacity_by_stage":(cap,),
            "config":extra_config(cap),
        })
    need(len(result)==29 and len(set(x["id"] for x in result))==29,
         "CAF15A_WRONG_FROZEN_WORLDSET")
    return result

def compatible_classes(observed,pid,bank,only_diagonal):
    # Truth-free read interface; a selector has no access to world configs.
    available=sorted({
        r["class"] for r in bank
        if (r["diagonal"] or not only_diagonal)
        and candidate_with_witness(observed,r["signatures"][pid]) is not None
        # This candidate overlap is ±1 on BOTH sides (<=2) and is NOT the
        # same as comparing a fixed observation to predicted +/-1.
    })
    return available

def compatible_with_fixed_reading(observed,predicted):
    """Actual observed fixed integer y, candidate x compatible iff |y-x|<=1."""
    need(len(observed)==len(predicted),"CAF15A_FIXED_READING_MISMATCH")
    return all(abs(x-y)<=1 for x,y in zip(observed,predicted))

def infer(observed,pid,bank,diagonal):
    return sorted({
        row["class"] for row in bank
        if (row["diagonal"] or not diagonal)
        and compatible_with_fixed_reading(observed,row["signatures"][pid])
    })

def save_json(labroot,name,value):
    return b.lab.write_new(labroot,name,value)

def run(out,checkout_sha,head_sha):
    need(bool(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha)) and
         bool(b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha)),
         "CAF15A_INVALID_SHA")
    out=Path(out).resolve()
    need(not out.exists(),"CAF15A_REFUSE_OVERWRITE")
    bank=compute_bank()
    graphs=graph(bank)
    ww=worlds()
    out.mkdir(parents=True,exist_ok=False)

    def serialize_row(r):
        return {
            "id":r["id"],"model":r["model"],"class":r["class"],
            "stages":list(r["stages"]),
            "capacities":list(r["capacity_by_stage"]),
            "diagonal":r["diagonal"],
            "signatures":{k:list(v) for k,v in r["signatures"].items()},
        }
    save_json(out,"00B_CATALOGO_TESTIGOS_PRE_MUNDOS.json",{
        "schema":SCHEMA,"protocol_first_commit":PRECOMMIT,
        "precode_amendment":PRECODE_AMENDMENT,
        "bank":[serialize_row(x) for x in bank],
        "no_evaluator_world_DES_called":True,
    })
    digest=sha256((out/"00B_CATALOGO_TESTIGOS_PRE_MUNDOS.json").read_bytes()).hexdigest()
    save_json(out,"00_PLAN_PRE_MUNDOS.json",{
        "schema":SCHEMA,"protocol_first_commit":PRECOMMIT,
        "precode_amendment":PRECODE_AMENDMENT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "frozen_lattice_capacities":C_GRID,
        "programs":programs(),
        "worlds_EVALUATOR_ONLY":ww,
        "n_diagonal_rows":90,"n_off_diagonal_rows":630,
        "n_total_rows":720,"n_frozen_worlds":29,
        "tolerance_integer_count":1,
        "no_world_evaluator_called_before_bank_and_plan":True,
        "catalog_sha256":"sha256:"+digest,
        "never_claim_global_2D_separation_from_absence":True,
    })
    save_json(out,"00C_GRAFO_TESTIGOS_PRE_MUNDOS.json",{
        "schema":SCHEMA,"graph":graphs,
        "from_bank_only_no_world_truth":True,
    })
    evaluated=[]
    for w in ww:
        observed=native_readings(w["config"])
        for pid in PIDS:
            true=w["true_class"]
            diag=infer(observed[pid],pid,bank,True)
            full=infer(observed[pid],pid,bank,False)
            need(set(diag).issubset(full),
                 "CAF15A_FIXED_OBSERVATION_NONMONOTONIC")
            if true is not None:
                need(true in full,
                     "CAF15A_IN_FAMILY_TRUE_CLASS_EXCLUDED")
                correct=next(x for x in bank if
                    x["class"]==true and
                    tuple(x["capacity_by_stage"])==tuple(w["truth_capacity_by_stage"]))
                need(compatible_with_fixed_reading(
                    observed[pid],correct["signatures"][pid]),
                    "CAF15A_TRUE_CAPACITY_NOT_REPRODUCED")
            evaluated.append({
                "world":w["id"],"world_type_EVALUATOR_ONLY":w["type"],
                "true_class_EVALUATOR_ONLY":true,
                "true_capacities_EVALUATOR_ONLY":list(w["truth_capacity_by_stage"]),
                "program":pid,"observed_signature":list(observed[pid]),
                "diagonal_compatible_classes":diag,
                "expanded_compatible_classes":full,
                "n_diagonal_classes":len(diag),
                "n_expanded_classes":len(full),
                "diagonal_unique_class":diag[0] if len(diag)==1 else None,
                "expanded_unique_class":full[0] if len(full)==1 else None,
                "true_class_covered_on_expanded_lattice_EVALUATOR_ONLY":
                    true in full if true is not None else None,
                "true_class_covered_on_diagonal_lattice_EVALUATOR_ONLY":
                    true in diag if true is not None else None,
            })
    need(len(evaluated)==29*4,"CAF15A_BAD_EVAL_COUNT")
    summary={}
    for pid in PIDS:
        group=[x for x in evaluated if x["program"]==pid]
        inside=[x for x in group if x["true_class_EVALUATOR_ONLY"] is not None]
        unknown=[x for x in group if x["true_class_EVALUATOR_ONLY"] is None]
        need(len(inside)==24 and len(unknown)==5,"CAF15A_BAD_EVAL_DENOMINATORS")
        summary[pid]={
            "offdiag_worlds":24,"extra_worlds":5,
            "new_confusable_edges":graphs[pid]["new_edges_from_capacity_freedom"],
            "diag_witness_edges":graphs[pid]["edges_diagonal_lattice"],
            "expanded_witness_edges":graphs[pid]["edges_expanded_lattice"],
            "offdiag_true_class_covered_2D_grid":sum(
                x["true_class_covered_on_expanded_lattice_EVALUATOR_ONLY"] for x in inside),
            "offdiag_true_class_covered_diagonal_grid":sum(
                x["true_class_covered_on_diagonal_lattice_EVALUATOR_ONLY"] for x in inside),
            "offdiag_expanded_unique_correct":sum(
                x["expanded_unique_class"]==x["true_class_EVALUATOR_ONLY"] for x in inside),
            "offdiag_diag_false_unique":sum(
                x["diagonal_unique_class"] is not None
                and x["diagonal_unique_class"]!=x["true_class_EVALUATOR_ONLY"]
                for x in inside),
            "offdiag_diag_empty":sum(x["n_diagonal_classes"]==0 for x in inside),
            "offdiag_full_empty":sum(x["n_expanded_classes"]==0 for x in inside),
            "extra_diag_unique_false":sum(x["diagonal_unique_class"] is not None for x in unknown),
            "extra_full_unique_false":sum(x["expanded_unique_class"] is not None for x in unknown),
            "extra_diag_no_lattice_match":sum(x["n_diagonal_classes"]==0 for x in unknown),
            "extra_full_no_lattice_match":sum(x["n_expanded_classes"]==0 for x in unknown),
            "avg_n_diag_classes_offdiag_worlds":round(
                sum(x["n_diagonal_classes"] for x in inside)/24,4),
            "avg_n_expanded_classes_offdiag_worlds":round(
                sum(x["n_expanded_classes"] for x in inside)/24,4),
        }
    report={
        "schema":SCHEMA,"protocol_first_commit":PRECOMMIT,
        "precode_amendment":PRECODE_AMENDMENT,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_hypothesis_rows":len(bank),"n_programs":len(PIDS),
        "n_worlds":len(ww),"n_world_program_evaluations":len(evaluated),
        "n_global_lattice_pair_comparisons":4*15,
        "all_24_true_two_capacities_recovered_on_lattice":all(
            x["true_class_covered_on_expanded_lattice_EVALUATOR_ONLY"]
            for x in evaluated if x["true_class_EVALUATOR_ONLY"] is not None),
        "no_global_2d_certificate":True,
        "no_external_validation":True,
        "truth_not_passed_to_infer":True,
        "summary":summary,"graphs":graphs,"evaluations":evaluated,
        "promotion_gate":GATE,
    }
    save_json(out,"01_RESULTADOS.json",report)
    lines=[
        "# CAF-15A — Dos capacidades libres: testigos positivos, sin certificado 2D",
        "",
        "**Todos los resultados de no coincidencia son únicamente sobre la",
        "malla fija de 15 capacidades. NO representan incompatibilidad global.**",
        "Familia DES FIFO determinista compartida, tolerancia ±1 no calibrada.",
        "",
        "| Programa | Parejas con testigo diagonal /15 | Con testigo 2D /15 | Nuevas parejas confundibles | Verdades offdiag cubiertas por diagonal /24 | Verdades offdiag cubiertas por 2D /24 | Offdiag únicos correctos 2D /24 | Extra 4ª etapa falsos únicos diagonal /5 | Extra falsos únicos 2D /5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pid in PIDS:
        m=summary[pid]
        lines.append("| "+" | ".join(map(str,(
            pid,m["diag_witness_edges"],m["expanded_witness_edges"],
            m["new_confusable_edges"],m["offdiag_true_class_covered_diagonal_grid"],
            m["offdiag_true_class_covered_2D_grid"],
            m["offdiag_expanded_unique_correct"],
            m["extra_diag_unique_false"],m["extra_full_unique_false"],
        )))+" |")
    lines +=["","## Pares estructurales con y sin testigos"]
    lines+=["",
      "| Programa | Clase A | Clase B | Testigo diagonal | Testigo con dos capacidades | Arista nueva |",
      "|---|---|---|---|---|---|"]
    for pid in PIDS:
        for e in graphs[pid]["pairs"]:
            lines.append("| "+" | ".join((
                pid,e["class_a"],e["class_b"],
                str(e["diagonal_witness"] is not None),
                str(e["expanded_witness"] is not None),
                str(e["new_edge_created_by_two_free_capacities"]),
            ))+" |")
    lines +=["","## Mundos in-family y fuera de familia, sin diagnóstico global",
      "",
      "| Mundo | Programa | Verdad evaluador | Clases con diagonal | Clases con dos capacidades |",
      "|---|---|---|---|---|"]
    for r in evaluated:
        lines.append("| "+" | ".join((
            r["world"],r["program"],r["true_class_EVALUATOR_ONLY"] or "4ª etapa",
            ", ".join(r["diagonal_compatible_classes"]) or "∅",
            ", ".join(r["expanded_compatible_classes"]) or "∅",
        ))+" |")
    lines+=["",
        "## Reglas de interpretación",
        "",
        "- Cada testigo es un contraejemplo matemático contra una separación",
        "  global, porque sus capacidades racionales pertenecen a [55,110]².",
        "- Una pareja sin testigo en este catálogo no está certificada como",
        "  globalmente separable; el continuo fuera de la malla queda sin resolver.",
        "- La extensión exacta c1=c2 ⊂ (c1,c2) significa que la inferencia",
        "  nunca puede recuperar separabilidad global perdida por ampliar modelo.",
        "- Recuperar la verdad off-diagonal en 24/24 es autoconsistencia",
        "  esperada (cada capacidad real se colocó en la malla del evaluador).",
        "- El control de cuarta etapa rápida >150/h puede seguir dejando",
        "  tiempos de tránsito y stock; invisibilidad no está garantizada.",
        "- No inferir frecuencia, probabilidad, precisión de sensores ni costo",
        "  de intervención, a partir de testigos de malla sintéticos.",
        "",
        "Gate permanente: "+GATE,
        ""]
    save_json(out,"02_INFORME.md","\n".join(lines))
    files=sorted(f for f in out.iterdir() if f.is_file())
    save_json(out,"03_MANIFIESTO.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "sha256":{f.name:"sha256:"+sha256(f.read_bytes()).hexdigest()
                  for f in files},
        "catalog_graph_plan_created_before_world_des":True,
        "no_external_custody":True,
    })
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    x=p.parse_args()
    r=run(x.out,x.checkout_sha,x.head_sha)
    print(json.dumps({
        "n_hypotheses":r["n_hypothesis_rows"],
        "n_worlds":r["n_worlds"],
        "summary":r["summary"],"gate":r["promotion_gate"],
    },sort_keys=True))

if __name__=="__main__":
    main()
