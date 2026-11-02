#!/usr/bin/env python3
"""CAF-04: are identical delivery histories enough to locate a bottleneck?

Reinstrument EXISTING PUBLIC B/C/D worlds, without changing their physical
configuration, over six PUBLIC arrival pressures. Compare output-only with
stage waiting, in-service and in-process stocks. No M/D fitting or CAF-02
policy changes, no real-data claim, no independent prospective validation.

Known worlds and predeclared observation menu are saved before the first DES
call. Inferring the minimal differentiating sensor subsets uses observed
internal snapshots (descriptive ORACLE), not a predictive train/test result.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
from itertools import combinations
import io
import json
from pathlib import Path

import caf02_lab_exploratorio as lab
import caf02_lab_matriz_cinco_mundos as previous
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf04-observability-existing-bcd/0.1"
WORLDS=("B","C","D")
RATES=(("LOW","4/5"),("K0","6/5"),("K2","27/20"),
       ("K1","3/2"),("HIGH","9/5"),("VERY_HIGH","12/5"))
TIMES=(5,10,15,20,30,40)
STAGES=("preparacion","despacho","entrega")
FIELDS=("waiting","in_service","stage_stock")
# Historical source outcomes with same public config and pulse, used ONLY
# as regression. Pressure sweep includes additional input rates.
HISTORICAL={("K0",5):2,("K0",10):7,("K1",20):17,
            ("K2",5):2,("K2",10):7,("K2",15):12,
            ("K2",20):17,("K2",30):27,("K2",40):27}


def need(ok,reason):
    if not ok:
        raise ValueError(reason)


def defined_worlds():
    worlds=[]
    for name in WORLDS:
        candidate=previous.spec(name)
        need(candidate["capacity_orders_per_hour"]==60,
             "CAF04_PREVIOUS_BCD_CAPACITY_CHANGED")
        stages=des.validate_private_config(candidate["config"])
        need(len(stages)==3 and sorted(n for n,_ in stages)==[1,2,2]
             and all(duration==1 for _,duration in stages),
             "CAF04_BCD_NOT_THE_PRIOR_EXACT_WORLDS")
        need(next(i for i,(n,t) in enumerate(stages) if n==1)
             ==WORLDS.index(name),"CAF04_BCD_BOTTLENECK_MOVED")
        worlds.append({"id":name,"config":candidate["config"],
                       "label":candidate["label"],"capacity_h":60})
    return worlds


def snapshot_row(world,rate_name,rate,snap):
    active=list(snap.stage_in_service)
    waiting=list(snap.stage_waiting)
    stocks=[a+b for a,b in zip(active,waiting)]
    accepted=snap.accepted_cum_orders
    delivered=snap.delivered_cum_orders
    pending=snap.pending_orders
    cfg=des.validate_private_config(world["config"])
    need(accepted==delivered+pending==delivered+sum(stocks)
         and all(0<=a<=cfg[i][0] for i,a in enumerate(active))
         and all(w>=0 for w in waiting),
         "CAF04_DES_CONSERVATION_OR_SERVER_CAPACITY_FAILED")
    return {
        "world":world["id"],"rate_name":rate_name,
        "arrivals_per_minute":str(rate),"time_minute":int(snap.t_min),
        "accepted":accepted,"delivered":delivered,"pending":pending,
        "waiting":waiting,"in_service":active,"stage_stock":stocks,
    }


def signatures(rows,channels):
    """Known-world sensor response vectors. Never fed to M/D in this lab."""
    return {
        name:tuple(
            rows[name][field][index] for field,index in channels
        ) for name in WORLDS
    }


def separating_sets(rows,allowed_fields):
    """Find minimal SENSOR CHANNEL count for B/C/D at ONE pressure and time."""
    available=tuple((field,i) for field in FIELDS
                    if field in allowed_fields for i in range(3))
    simple={}
    for count in range(1,len(available)+1):
        choices=[]
        for subset in combinations(available,count):
            sig=signatures(rows,subset)
            if len(set(sig.values()))==len(WORLDS):
                choices.append(subset)
        if choices:
            return {
                "separable":True,"minimal_sensor_count":count,
                "minimal_sensors":[[{"field":f,"stage":STAGES[i]}
                                    for f,i in subset]
                                   for subset in choices],
                "minimal_distinct_signature_count":len(WORLDS),
                "candidate_channels_considered":len(available),
                "total_minimal_equivalent_solutions":len(choices),
            }
    return {"separable":False,"minimal_sensor_count":None,
            "minimal_sensors":[],"minimal_distinct_signature_count":None,
            "candidate_channels_considered":len(available),
            "total_minimal_equivalent_solutions":0}


def analyze(all_snapshots):
    cases=[]
    for rate_name,rate in RATES:
        for t in TIMES:
            group={name:all_snapshots[name][rate_name][t]
                   for name in WORLDS}
            delivered={name:group[name]["delivered"] for name in WORLDS}
            pending={name:group[name]["pending"] for name in WORLDS}
            # Total backlog equals arrivals - deliveries, so if deliveries
            # coincide it cannot identify WHERE the bottleneck is.
            sensors={
                "waiting":separating_sets(group,("waiting",)),
                "in_service":separating_sets(group,("in_service",)),
                "stage_stock":separating_sets(group,("stage_stock",)),
                "all_nine":separating_sets(group,FIELDS),
            }
            cases.append({
                "rate_name":rate_name,"arrival_rate_per_minute":rate,
                "time_minute":t,
                "delivered_by_world":delivered,
                "pending_by_world":pending,
                "delivery_equivalent":len(set(delivered.values()))==1,
                "total_pending_equivalent":len(set(pending.values()))==1,
                "stage_waiting_by_world":{
                    name:group[name]["waiting"] for name in WORLDS},
                "in_service_by_world":{
                    name:group[name]["in_service"] for name in WORLDS},
                "stage_stock_by_world":{
                    name:group[name]["stage_stock"] for name in WORLDS},
                "sensors":sensors,
            })
    return cases


def tabular(data):
    buf=io.StringIO(newline="")
    w=csv.writer(buf)
    w.writerow(["rate","rate_per_min","minute","world","accepted",
                "delivered","total_pending",
                "prep_waiting","dispatch_waiting","delivery_waiting",
                "prep_in_service","dispatch_in_service","delivery_in_service",
                "prep_stock","dispatch_stock","delivery_stock"])
    for rate_name,rate in RATES:
        for time in TIMES:
            for world in WORLDS:
                r=data[world][rate_name][time]
                w.writerow([rate_name,rate,time,world,
                            r["accepted"],r["delivered"],r["pending"],
                            *r["waiting"],*r["in_service"],*r["stage_stock"]])
    return buf.getvalue()


def comparison_csv(cases):
    buf=io.StringIO(newline="")
    w=csv.writer(buf)
    w.writerow(["rate","minute","delivery_equivalent",
                "total_pending_equivalent",
                "minimal_waiting_sensors","minimal_in_service_sensors",
                "minimal_stage_stock_sensors","minimal_all_sensors",
                "waiting_B","waiting_C","waiting_D"])
    for c in cases:
        x=c["sensors"]
        w.writerow([c["rate_name"],c["time_minute"],
                    c["delivery_equivalent"],c["total_pending_equivalent"],
                    *[x[f]["minimal_sensor_count"]
                      for f in ("waiting","in_service",
                                "stage_stock","all_nine")],
                    *[str(c["stage_waiting_by_world"][world])
                      for world in WORLDS]])
    return buf.getvalue()


def md(data):
    cases=data["cases"]
    lines=[
        "# CAF-04 · Observabilidad de tres cuellos de botella",
        "",
        "**Laboratorio DES público, descriptivo, no prueba confirmatoria.**",
        "Se reutilizan las configuraciones B/C/D de PR #110: tres",
        "etapas con servicio 1 min; un solo servidor limitante colocado",
        "respectivamente en preparación, despacho o entrega (60 pedidos/h).",
        "",
        "Se compararon seis entradas constantes durante 20 min: 0.8, 1.2,",
        "1.35, 1.5, 1.8 y 2.4 pedidos/min, a t5,10,15,20,30,40.",
        "Conservar las colas es distinto de observar entregas totales;",
        "también se registró trabajo en servicio y stock físico por etapa.",
        "El mundo es conocido por el evaluador: esto mide",
        "**observabilidad del menú de sensores en casos conocidos**,",
        "no ajuste ni inferencia ciega de topologías M/D.",
        "",
        "## ¿Basta cambiar la presión de entrada y observar solo entregas?",
        "",
        "| Entrada (pedidos/min) | Entregas equivalentes B/C/D | Pendientes totales equivalentes |",
        "|---:|---:|---:|",
    ]
    for name,rate in RATES:
        subset=[x for x in cases if x["rate_name"]==name]
        lines.append(f"| {float(Fraction(rate)):.2f} | "+
                     f"{sum(x['delivery_equivalent'] for x in subset)}/6 tiempos | "+
                     f"{sum(x['total_pending_equivalent'] for x in subset)}/6 tiempos |")
    lines+=["",
        "## ¿Qué cambia al observar stocks y colas por etapa?",
        "",
        "Se reporta el menor número de **canales de sensor distintos** que",
        "distingue los tres mundos, a un mismo instante y misma entrada.",
        "Un canal es, por ejemplo, 'cola de despacho', no el vector completo.",
        "No es una estimación de precio de instalación del sensor.",
        "",
        "| Entrada | t | Colas B/C/D (prep, despacho, entrega) | Mín. colas | Mín. ocupación en servicio | Mín. stock etapa |",
        "|---:|---:|---|---:|---:|---:|",
    ]
    for name in ("LOW","K0","K2","K1","HIGH","VERY_HIGH"):
        for t in (10,20):
            x=next(c for c in cases if c["rate_name"]==name
                   and c["time_minute"]==t)
            q=" / ".join(str(x["stage_waiting_by_world"][w])
                         for w in WORLDS)
            def s(f):
                v=x["sensors"][f]["minimal_sensor_count"]
                return str(v) if v is not None else "no separa"
            lines.append(
                f"| {float(Fraction(x['arrival_rate_per_minute'])):.2f} | {t} | "+
                f"{q} | {s('waiting')} | {s('in_service')} | {s('stage_stock')} |")
    lines+=["",
        "## Menú de sensores y mecanismo",
        "",
        "- **Entregas acumuladas:** información externa, no localiza la",
        "etapa restringida si los mundos son observacionalmente equivalentes.",
        "- **Pedidos totales pendientes:** aceptados - entregados;",
        "no aporta ubicación interna si ambos totales son idénticos.",
        "- **Cola por etapa:** espera antes de cada estación, no incluye",
        "pedidos activos en servicio.",
        "- **Ocupación en servicio:** número de pedidos atendidos por",
        "estación, no una medición directa del número de servidores instalados.",
        "- **Stock por etapa:** espera + servicio, descomposición explícita",
        "del trabajo en proceso en la red.",
        "",
        "## Interpretación y límites",
        "",
        "- Los mínimos se encontraron *después de observar* las respuestas",
        "de los tres mundos: son descriptivos, no selección prospectiva.",
        "- La coincidencia en seis tasas y seis tiempos NO prueba igualdad",
        "para todas las trayectorias de llegada, políticas ni observables.",
        "- Cuando un canal no discrimina a una entrada concreta, no se",
        "deduce que sea inútil con otra presión, instante o tecnología.",
        "- Conocer la cola por estación NO implica que las gramáticas",
        "M y D de CAF-02 puedan asimilar esa variable; aquí no se cambió",
        "ninguno de los métodos ni se alegó recuperación estructural.",
        f"- Ejecuciones DES exploratorias de instrumentación: **{data['DES_runs']}**;",
        "corridas confirmatorias: **0**; datos de cafetería real: **0**.",
        "- Los mundos ya eran conocidos desde PR #110; esto no es",
        "un conjunto de validación independiente.",
        "",
    ]
    return "\n".join(lines)


def run(out):
    target=Path(out).resolve()
    need(not target.exists(),"CAF04_OUTPUT_ALREADY_EXISTS")
    worlds=defined_worlds()
    need(len(RATES)==6 and len(TIMES)==6 and len(WORLDS)==3,
         "CAF04_BUDGET_OR_SENSOR_MENU_CHANGED")
    target.mkdir(parents=True,exist_ok=False)
    lab.write_new(target,"00_PLAN_INSTRUMENTACION.json",{
        "schema":SCHEMA,"classification":"REUSED_KNOWN_PUBLIC_WORLDS_EXPLORATORY",
        "worlds":worlds,"rates":dict(RATES),"times":list(TIMES),
        "stage_names":list(STAGES),"sensor_fields":list(FIELDS),
        "DES_executed_before_plan":0,
        "K2_forecast_or_M_D_inference":False,
        "worlds_previously_observed_in_PR110":True,
    })
    all_snapshots={}
    runs=0
    for world in worlds:
        name=world["id"]
        all_snapshots[name]={}
        for rate_name,rate in RATES:
            arrivals=des.half_open_arrivals(rate,20)
            source=des.run_toy_engine(
                world["config"],arrivals,(0,*TIMES))
            runs+=1
            need(len(source)==len(TIMES)+1 and
                 source[0].accepted_cum_orders==0
                 and source[0].delivered_cum_orders==0,
                 "CAF04_DES_INITIAL_STATE_NOT_EMPTY")
            observed={int(s.t_min):snapshot_row(world,rate_name,rate,s)
                      for s in source[1:]}
            for t in TIMES:
                historic=HISTORICAL.get((rate_name,t))
                if historic is not None:
                    need(observed[t]["delivered"]==historic,
                         "CAF04_PREVIOUS_PUBLIC_OUTCOME_CHANGED")
            all_snapshots[name][rate_name]=observed
        lab.write_new(target,f"01_DES_MUNDO_{name}.json",{
            "world":world,"samples_by_rate":all_snapshots[name],
            "real_cafe":False,"DES_runs":len(RATES),
        })
    cases=analyze(all_snapshots)
    report={
        "schema":SCHEMA,"status":"CAF04_BCD_OBSERVABILITY_EXPLORATORY_COMPLETE",
        "worlds":list(WORLDS),"rates":dict(RATES),
        "cases":cases,
        "all_output_deliveries_equivalent":all(x["delivery_equivalent"]
                                             for x in cases),
        "all_total_backlogs_equivalent":all(x["total_pending_equivalent"]
                                           for x in cases),
        "observations_per_world":len(RATES)*len(TIMES),
        "DES_runs":runs,"DES_confirmatory_runs":0,
        "known_worlds_not_independent":True,
        "M_D_not_updated_for_new_sensors":True,
        "sensor_minima_computed_posthoc":True,
    }
    need(runs==len(WORLDS)*len(RATES),"CAF04_RUN_BUDGET_MISMATCH")
    lab.write_new(target,"02_DIAGNOSTICO_SENSORES.json",report)
    lab.write_new(target,"03_OBSERVACIONES_ETAPAS.csv",tabular(all_snapshots))
    lab.write_new(target,"04_COMPARACION_SENSORES.csv",comparison_csv(cases))
    lab.write_new(target,"05_INFORME.md",md(report))
    hashes={file.name:lab.sha(file.read_bytes())
            for file in target.iterdir() if file.is_file()}
    lab.write_new(target,"06_HASHES.json",{
        "schema":SCHEMA,"files_sha256":hashes,
        "external_custody":False,
    })
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    result=run(args.out)
    print(json.dumps({
        "status":result["status"],
        "DES_runs":result["DES_runs"],
        "all_output_equivalent":result["all_output_deliveries_equivalent"],
        "all_pending_equivalent":result["all_total_backlogs_equivalent"],
        "focus":[{
            "rate":c["rate_name"],"minute":c["time_minute"],
            "stage_waiting":c["stage_waiting_by_world"],
            "min_waiting_sensors":c["sensors"]["waiting"][
                "minimal_sensor_count"],
            "min_stage_stock_sensors":c["sensors"]["stage_stock"][
                "minimal_sensor_count"],
        } for c in result["cases"] if c["rate_name"] in ("K0","K1")
           and c["time_minute"] in (10,20)],
    },sort_keys=True))


if __name__=="__main__":
    main()
