#!/usr/bin/env python3
"""Five predeclared PUBLIC DES worlds. Exploratory, never a blinded holdout.

A repeats the original; B/C/D relocate the single 60/h bottleneck;
E removes saturation with 120/h everywhere. Identical K0, K1 design,
M/D model families, filtering, scoring and K2 pulse in every world.
"""
import argparse
import csv
from fractions import Fraction
from hashlib import sha256
import io
import json
from pathlib import Path

import caf02_lab_exploratorio as lab
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf02-exploratory-five-world-matrix/0.1"
NAMES=("A","B","C","D","E")
# Fixed ex-ante BEFORE observing this matrix's results.
STAGES={
    "A":((2,"3/2"),(1,"3/4"),(2,"3/2")),
    "B":((1,"1"),(2,"1"),(2,"1")),
    "C":((2,"1"),(1,"1"),(2,"1")),
    "D":((2,"1"),(2,"1"),(1,"1")),
    "E":((2,"1"),(2,"1"),(2,"1")),
}
LABELS={
    "A":"balanceada (mundo anterior)",
    "B":"cuello en preparación",
    "C":"cuello en despacho",
    "D":"cuello en entrega",
    "E":"capacidad holgada",
}
CAPS={"A":80,"B":60,"C":60,"D":60,"E":120}


def need(condition,code):
    if not condition:raise ValueError(code)


def spec(name):
    need(name in NAMES,"MATRIX_WORLD_NOT_DECLARED")
    config={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
            "stages":[{"servers":n,"service_minutes":t}
                      for n,t in STAGES[name]]}
    stages=des.validate_private_config(config)
    capacity=min(Fraction(servers,1)/time*60 for servers,time in stages)
    need(capacity==CAPS[name],"MATRIX_CAPACITY_CHANGED")
    return {"id":name,"world_name":f"CAF02_LAB_WORLD_{name}_v1",
            "label":LABELS[name],"config":config,
            "capacity_orders_per_hour":float(capacity)}


def fixed_specs():
    need(tuple(STAGES)==NAMES and tuple(LABELS)==NAMES and
         tuple(CAPS)==NAMES,"MATRIX_WORLD_LIST_CHANGED")
    result=[spec(name) for name in NAMES]
    need(result[0]["config"]==lab.WORLD and
         result[0]["world_name"]==lab.VERSION,
         "MATRIX_ORIGINAL_A_CHANGED")
    return result


def family_count(families):
    return sum(n or 0 for n in families.values())


def arm_metrics(result,arm):
    a=result["G4a_summary"][arm]
    b=result["G4b_summary"][arm]
    row=result["scores"][arm]
    k0=row["K0"]["set_loss_mean"]
    k1=row["K1"]["set_loss_mean"]
    gain=row["paired_set_loss_gain_orders"]
    scale=result["scores"]["M"]["REF_SCALE"]["set_loss_mean"]
    return {
        "family_K0":a,"family_K1":b,
        "n0":family_count(a),"n1":family_count(b),
        "loss0":k0,"loss1":k1,"gain":gain,
        "paired":row["status"]=="PAIRED",
        "abstention_K1":k1 is None,
        "improved_at_least_0_25":row["revision_predictive_improvement_pass"],
        "worse_than_K0":gain<0 if gain is not None else None,
        "beats_REF_SCALE_only_K0":(
            k1<scale if k1 is not None and scale is not None else None),
        "K1_point_eligible":row["K1"]["status"]=="POINT_ELIGIBLE",
        "K1_coverage_count":row["K1"].get("coverage_count"),
    }


def summarize(specification,result):
    selected=result["K1"]["measurement"] if result["K1"] else None
    return {
        "id":specification["id"],"label":specification["label"],
        "world_name":specification["world_name"],
        "capacity_orders_per_hour":specification["capacity_orders_per_hour"],
        "K0_D5":result["K0"]["delivered_t5"],
        "K0_D10":result["K0"]["delivered_t10"],
        "K1_selected":selected,
        "K1_observed":result["K1"]["delivered"] if result["K1"] else None,
        "K2_des":result["K2"]["delivered"],
        "REF_SCALE_K0_only":result["scores"]["M"]["REF_SCALE"]["set_loss_mean"],
        "REF_CAF_K0_only":result["scores"]["M"]["REF_CAF"]["set_loss_mean"],
        "M":arm_metrics(result,"M"),"D":arm_metrics(result,"D"),
        "DES_lab_runs":result["exploratory_DES_runs"],
        "confirmatory_DES_runs":result["confirmatory_DES_runs"],
        "forecast_file_sha256":result["predictions_file_sha256"],
        "checkpoint_sha256":result["checkpoint_sha256"],
    }


def fmt(x):
    if x is None:return "—"
    if type(x) is bool:return "sí" if x else "no"
    if isinstance(x,(float,int)):return f"{x:.3f}"
    return str(x)


def markdown(data):
    lines=[
        "# CAF-02 — Cinco mundos DES: resultados exploratorios",
        "",
        "Cinco configuraciones públicas y fijas antes de leer K2 de la matriz.",
        "A repite el mundo ya explorado. B, C, D comparten tres tiempos",
        "de servicio de 1 minuto; solo cambia la posición del servidor",
        "limitante de 60 pedidos/hora. E tiene 120 pedidos/hora en las",
        "tres estaciones. No es validación independiente ni cafetería real.",
        "",
        "## Entregas observadas del DES y K1 elegida por M+D",
        "",
        "| Mundo | Cuello | K0 D5,D10 | K1 seleccionada | K2 DES t5,10,15,20,30,40 |",
        "|---|---:|---|---|---|",
    ]
    for r in data["worlds"]:
        k=r["K1_selected"]
        choice=(f"{k['rate_per_minute']}/min, t={k['t_min']}, "+
                f"D={r['K1_observed']}" if k else "ninguna")
        lines.append(
            f"| {r['id']} ({r['label']}) | {fmt(r['capacity_orders_per_hour'])}/h | "+
            f"({r['K0_D5']},{r['K0_D10']}) | {choice} | {r['K2_des']} |")
    lines.extend(["",
        "## Hipótesis y pérdida L_set (menor es mejor)",
        "",
        "| Mundo | M n0→n1 | M L0→L1 | Mejora M | D n0→n1 | D L0→L1 | Mejora D | REF_SCALE (solo K0) |",
        "|---|---:|---|---:|---:|---|---:|---:|",
    ])
    for r in data["worlds"]:
        m,d=r["M"],r["D"]
        lines.append(
            f"| {r['id']} | {m['n0']}→{m['n1']} | "+
            f"{fmt(m['loss0'])}→{fmt(m['loss1'])} | {fmt(m['gain'])} | "+
            f"{d['n0']}→{d['n1']} | {fmt(d['loss0'])}→{fmt(d['loss1'])} | "+
            f"{fmt(d['gain'])} | {fmt(r['REF_SCALE_K0_only'])} |")
    lines.extend(["",
        "Abstención aparece como —, nunca como pérdida cero. Una mejora",
        "es L(K0) menos L(K1). La referencia REF_SCALE recibe solo K0,",
        "por lo que no representa una comparación a igualdad de información.",
        "",
        "## Diagnóstico de comportamiento",
    ])
    for arm in ("M","D"):
        paired=[r[arm] for r in data["worlds"] if r[arm]["paired"]]
        lines.append(
            f"- {arm}: {len(paired)}/5 casos pareados; "+
            f"{sum(x['improved_at_least_0_25'] is True for x in paired)} "+
            "con mejora >=0.25; "+
            f"{sum(x['worse_than_K0'] is True for x in paired)} empeoran; "+
            f"{sum(r[arm]['abstention_K1'] for r in data['worlds'])} abstienen; "+
            f"{sum(r[arm]['beats_REF_SCALE_only_K0'] is True for r in data['worlds'])} "+
            "superan REF_SCALE K0-only.")
    lines+=["",
        "## Analogía estructural y límites",
        "",
        "El generador DES tiene tres etapas en los cinco mundos, pero las",
        "familias continuas C01 y D3 no son su misma estructura matemática.",
    ]
    for r in data["worlds"]:
        lines.append(
            f"- {r['id']}: M-C01 K1={r['M']['family_K1'].get('C01') or 0}; "+
            f"D-D3 K1={r['D']['family_K1'].get('D3') or 0}.")
    lines+=["",
        f"- Total DES exploratorios: {data['DES_lab_runs']}; confirmatorios: 0.",
        "- Cada mundo posee archivos de pronósticos K2 y checkpoint fsync",
        "antes de su primera llamada DES K2. No hay firma externa.",
        "- No se modificaron M, D, política K1, catálogo, umbral 0.77",
        "ni pérdida en función de lo observado.",
        "- No se extrapolan frecuencias de éxito a cafeterías reales:",
        "cinco mundos deterministas deliberados NO son muestra estadística.",
        "- G2 nativo completado previamente en otra campaña, 0 OMC aquí;",
        "- ATMS persistida no demostrada; proveedores: 0.",
        "",
    ]
    return "\n".join(lines)


def csv_summary(data):
    buf=io.StringIO(newline="")
    w=csv.writer(buf)
    w.writerow(["world","scenario","capacity_per_hour","K0_D5","K0_D10",
                "K1_rate_per_min","K1_t_min","K1_delivered","K2",
                "M_n0","M_n1","M_loss0","M_loss1","M_gain","M_abstain",
                "M_beats_REF_SCALE","D_n0","D_n1","D_loss0","D_loss1",
                "D_gain","D_abstain","D_beats_REF_SCALE",
                "REF_SCALE_K0_loss","DES_lab_runs"])
    for r in data["worlds"]:
        m,d=r["M"],r["D"]
        k=r["K1_selected"] or {}
        w.writerow([r["id"],r["label"],r["capacity_orders_per_hour"],
                    r["K0_D5"],r["K0_D10"],k.get("rate_per_minute"),
                    k.get("t_min"),r["K1_observed"],
                    "|".join(str(x) for x in r["K2_des"]),
                    m["n0"],m["n1"],m["loss0"],m["loss1"],m["gain"],
                    m["abstention_K1"],m["beats_REF_SCALE_only_K0"],
                    d["n0"],d["n1"],d["loss0"],d["loss1"],d["gain"],
                    d["abstention_K1"],d["beats_REF_SCALE_only_K0"],
                    r["REF_SCALE_K0_only"],r["DES_lab_runs"]])
    return buf.getvalue()


def run_matrix(out):
    folder=Path(out).resolve()
    need(not folder.exists(),"MATRIX_OUTPUT_ALREADY_EXISTS")
    specs=fixed_specs()
    folder.mkdir(parents=True,exist_ok=False)
    lab.write_new(folder,"00_PLAN_FIJO.json",{
        "schema":"igc-caf02-five-worlds-fixed-before-matrix/0.1",
        "worlds":specs,"K2_observed_before_plan":False,
        "worlds_executed_before_plan":0,
        "classification":"EXPLORATORY_NOT_CONFIRMATORY",
        "policy_sha256":lab.sha(lab.d.POLICY.read_bytes()),
        "no_outcome_based_world_choice":True,
    })
    rows=[]
    for scenario in specs:
        world_folder=folder/("mundo_"+scenario["id"])
        result=lab.run_lab(world_folder,
                           world_config=scenario["config"],
                           world_version=scenario["world_name"])
        need(result["world_name"]==scenario["world_name"] and
             result["world_parameters"]==scenario["config"] and
             result["confirmatory_DES_runs"]==0 and
             result["exploratory_DES_runs"] in (2,3),
             "MATRIX_WRONG_WORLD_OR_RUN_BUDGET")
        manifest=json.loads((world_folder/"11_MANIFIESTO.json").read_bytes())
        for filename,expected in manifest["files_sha256"].items():
            need(lab.sha((world_folder/filename).read_bytes())==expected,
                 "MATRIX_WORLD_FILE_INTEGRITY_CHANGED")
        need(manifest["K2_priors_written_before_K2"] and
             manifest["external_custody_verified"] is False,
             "MATRIX_PRE_K2_OR_EXTERNAL_CUSTODY_CHANGED")
        rows.append(summarize(scenario,result))
    data={
        "schema":SCHEMA,"status":"FIVE_PUBLIC_DES_EXPLORATORY_WORLDS_EXECUTED",
        "world_count":len(rows),"worlds":rows,
        "DES_lab_runs":sum(r["DES_lab_runs"] for r in rows),
        "DES_confirmatory_runs":0,"new_OpenModelica_calls":0,
        "provider_calls":0,"external_custody_verified":False,
        "M_D_policy_unchanged":True,
    }
    lab.write_new(folder,"01_RESULTADOS.json",data)
    lab.write_new(folder,"02_COMPARACION.csv",csv_summary(data))
    lab.write_new(folder,"03_INFORME.md",markdown(data))
    file_hashes={p.relative_to(folder).as_posix():lab.sha(p.read_bytes())
                 for p in folder.rglob("*") if p.is_file()}
    lab.write_new(folder,"04_ARCHIVOS_SHA256.json",{
        "schema":"igc-caf02-five-worlds-local-digests/0.1",
        "files":file_hashes,"external_custody_verified":False,
    })
    return data


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    x=ap.parse_args()
    result=run_matrix(x.out)
    print(json.dumps({
        "status":result["status"],"worlds":result["world_count"],
        "lab_DES_runs":result["DES_lab_runs"],
        "comparison":[{
            "world":r["id"],"K0":[r["K0_D5"],r["K0_D10"]],
            "K1_selected":r["K1_selected"],"K2":r["K2_des"],
            "M_gain":r["M"]["gain"],"D_gain":r["D"]["gain"],
            "REF_SCALE":r["REF_SCALE_K0_only"],
        } for r in result["worlds"]],
    },sort_keys=True))


if __name__=="__main__":
    main()
