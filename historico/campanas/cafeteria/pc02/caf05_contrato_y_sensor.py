#!/usr/bin/env python3
"""CAF-05: an explicit physical-observation contract and fixed-sensor transfer.

Prior sensor choice is computed ONLY from a CAF-04 frozen *known-world*
training excerpt; three NEW public 75/h worlds (I/J/K) are fixed separately.
A pressure-matched t10 / 1.5/min trial and an out-of-domain 0.8/min control
run once each: 6 DES calls total. The selection and classifier prototypes
are written and fsynced BEFORE the first new-world DES execution.

M has named E1 preparation/dispatch material stocks but no validated
measurement mapping to DES discrete stage stock counts; D stocks are generic
chain positions. Neither is allowed to consume internal DES stage states as
if it possessed a valid observation operator. This experiment measures
sensor transfer descriptively; it is NOT M/D topology recovery or custody.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import io
import json
from pathlib import Path

import caf02_lab_exploratorio as lab
import caf02_structural_k0k1k2 as m
import caf02_d_k0k1k2_adapter as d
import caf04_observabilidad_bcd as cf
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf05-stock-observation-contract-sensor-transfer/0.1"
HERE=Path(__file__).resolve().parent
REF_PATH=HERE/"caf05_referencia_caf04_congelada.json"
NEW_WORLDS=("I","J","K")
KNOWN_WORLD_LABELS=("B","C","D")
STAGES=("preparacion","despacho","entrega")
# Declared NEW capacity 75/h, compared against prior training 60/h.
SERVICE="4/5"
EVALUATION=(("MATCHED","3/2"),("LOW_OOD","4/5"))
MINUTE=10
M_FAMILIES=("C00","C01")
D_FAMILIES=("D1","D2","D3")
OBSERVABLES=("delivered","pending_total","waiting","in_service","stage_stock")
STATUS_SUPPORTED="SUPPORTED_DIRECT_MODEL_OUTPUT"
STATUS_DERIVED="DERIVED_FROM_DELIVERED_NOT_INDEPENDENT"
STATUS_CONDITIONAL="CONDITIONAL_ROLE_MATCH_NO_DES_OPERATOR"
STATUS_UNSUPPORTED="UNSUPPORTED_NO_VALID_OPERATOR"


def need(condition,reason):
    if not condition:
        raise ValueError(reason)


def observation_contract():
    """Supported outputs vs candidates for an explicit future physical map.

    The E1 role name does not certify continuous stock equals integer WIP.
    Only cumulative delivered is actually scored/observed by existing M/D.
    """
    repertoire=m.verify_existing_repertoire()
    need(repertoire["C00"]==["preparation","dispatch"]
         and repertoire["C01"]==["preparation","dispatch","transit"],
         "CAF05_M_ROLE_REPERTOIRE_DRIFT")
    contract={}
    for arm,families in (("M",M_FAMILIES),("D",D_FAMILIES)):
        contract[arm]={}
        for family in families:
            fields={}
            for field in OBSERVABLES:
                names=STAGES if field in ("waiting","in_service",
                                          "stage_stock") else (None,)
                for stage in names:
                    key=field if stage is None else f"{field}:{stage}"
                    if field=="delivered":
                        status=STATUS_SUPPORTED
                        reason="M/D existing cumulative delivery prediction"
                    elif field=="pending_total":
                        status=STATUS_DERIVED
                        reason=("accepted minus delivered under a known "
                                "arrival schedule; not stage localization")
                    elif field=="stage_stock" and arm=="M" and stage in (
                        "preparacion","despacho"):
                        status=STATUS_CONDITIONAL
                        reason=("E1 contains the named role but no verified "
                                "continuous-stock to DES integer-WIP "
                                "observation operator or error calibration")
                    else:
                        status=STATUS_UNSUPPORTED
                        reason=("No justified physical decomposition or "
                                "named-stage mapping in the existing grammar")
                    fields[key]={
                        "status":status,
                        "reason":reason,
                        "eligible_for_direct_stage_scoring":
                            status==STATUS_SUPPORTED,
                    }
            contract[arm][family]=fields
    return {
        "schema":"igc-caf05-observation-operators/0.1",
        "M_repertoire":repertoire,
        "D_grammar":"generic D1/D2/D3 chain positions, not named stages",
        "observable_units":{
            "delivered":"cumulative orders",
            "pending_total":"orders at t",
            "waiting":"orders waiting by named physical stage",
            "in_service":"orders currently in service by named stage",
            "stage_stock":"waiting + in_service by named stage",
        },
        "semantics":"CONDITIONAL_ROLE_MATCH_IS_NOT_A_VALIDATED_MEASUREMENT",
        "by_arm_family":contract,
        "no_automatic_DES_stage_M_D_stock_correspondence":True,
    }


def require_scoring_support(contract,arm,family,observable,stage=None):
    key=observable if stage is None else observable+":"+stage
    item=contract["by_arm_family"][arm][family][key]
    if item["status"]!=STATUS_SUPPORTED:
        raise ValueError("CAF05_NO_VALID_MODEL_OBSERVATION_OPERATOR")
    return item


def known_reference():
    r=json.loads(REF_PATH.read_text(encoding="utf-8"))
    source=r["source"]
    need(source["artifact_id"]==13028087089
         and source["source_file_sha256"]==
          "sha256:d8a2cee6fbeb1e1a88cf4abe7a343a0b8a20ee8a38d89e4aa3e638384549902c",
         "CAF05_PRIOR_REFERENCE_OR_SOURCE_CHANGED")
    o=r["training_observation"]
    need(o["arrival_rate_per_minute"]=="3/2"
         and o["minute"]==MINUTE
         and tuple(o["known_worlds"])==KNOWN_WORLD_LABELS
         and r["sensor_selection"]==
             "MIN_CHANNEL_COUNT_BCD_UNIQUE_SIGNATURE_THEN_LEXICAL_TIEBREAK"
         and r["frozen_classifier"]==
             "NEAREST_SINGLE_SENSOR_KNOWN_BCD_PROTOTYPE_ABSOLUTE_DIFFERENCE_TIE_ABSTAIN"
         and tuple(r["stages"])==STAGES
         and tuple(r["allowed_sensor_fields"])==cf.FIELDS,
         "CAF05_TRAINING_MENU_DRIFT")
    for w in KNOWN_WORLD_LABELS:
        need(o["known_bottleneck_stage"][w]==
             STAGES[KNOWN_WORLD_LABELS.index(w)] and
             o["delivered"][w]==7 and
             all(len(o[f][w])==3 and all(type(x) is int and x>=0
                     for x in o[f][w]) for f in cf.FIELDS) and
             sum(o["stage_stock"][w])==15-o["delivered"][w] and
             all(o["waiting"][w][i]+o["in_service"][w][i]==
                 o["stage_stock"][w][i] for i in range(3)),
             "CAF05_REFERENCE_KNOWN_PHYSICAL_FACTS_INVALID")
    return r


def select_from_previous_only(reference):
    observations=reference["training_observation"]
    rows={world:{field:observations[field][world] for field in cf.FIELDS}
          for world in KNOWN_WORLD_LABELS}
    choice=cf.separating_sets(rows,cf.FIELDS)
    need(choice["separable"] and
         choice["minimal_sensor_count"]==1 and
         choice["total_minimal_equivalent_solutions"]>=1,
         "CAF05_NO_UNIQUE_SINGLE_SENSOR_ON_PRIOR_WORLDS")
    all_choice=choice["minimal_sensors"]
    # Sorting is declared ex ante; do not use new-world outcomes.
    selected=min(all_choice,key=lambda subset:tuple(
        (item["field"],item["stage"]) for item in subset))
    need(len(selected)==1,"CAF05_SENSOR_COUNT_NOT_ONE")
    one=selected[0]
    need(one["field"]=="stage_stock" and one["stage"]=="despacho",
         "CAF05_CAF04_SENSOR_PROVENANCE_NOT_DISPATCH_STOCK")
    i=STAGES.index(one["stage"])
    prototypes={observations["known_bottleneck_stage"][w]:
                observations[one["field"]][w][i]
                for w in KNOWN_WORLD_LABELS}
    need(prototypes=={"preparacion":1,"despacho":6,"entrega":2},
         "CAF05_CAF04_SENSOR_PROTOTYPES_CHANGED")
    return {
        "measurement":{
            "field":one["field"],"stage":one["stage"],"stage_index":i,
            "minute":MINUTE,"arrival_rate_per_minute":"3/2",
            "unit":"orders (waiting + in_service)",
        },
        "classifier":{
            "method":"NEAREST_ABSOLUTE_DISTANCE_TIES_ABSTAIN",
            "prototypes":prototypes,
            "classes":list(STAGES),
            "abstain_on_ties":True,
            "no_prototype_update_on_new_worlds":True,
        },
        "prior_CAF04_training_signatures":{
            w:observations[one["field"]][w][i]
            for w in KNOWN_WORLD_LABELS
        },
        "selected_from_known_worlds_only":True,
        "predeclared_before_new_DES":True,
        "previous_minimal_sensor_count":choice["minimal_sensor_count"],
    }


def predict_one(value,selector):
    need(type(value) is int and value>=0,"CAF05_INVALID_MEASURED_STOCK")
    prototypes=selector["classifier"]["prototypes"]
    distances={stage:abs(value-x) for stage,x in prototypes.items()}
    smallest=min(distances.values())
    best=[stage for stage,err in distances.items() if err==smallest]
    return {
        "prediction":best[0] if len(best)==1 else None,
        "status":"PREDICTED" if len(best)==1 else "ABSTAIN_TIED_PROTOTYPES",
        "distance_by_class":distances,
        "distance_to_nearest":smallest,
        "trained_at_capacity_h":60,
        "no_new_world_refitting":True,
    }


def world_spec(name):
    need(name in NEW_WORLDS,"CAF05_UNDECLARED_WORLD")
    bottleneck=NEW_WORLDS.index(name)
    stages=[
        {"servers":1 if i==bottleneck else 2,
         "service_minutes":SERVICE if i==bottleneck else "1"}
        for i in range(3)]
    cfg={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
         "stages":stages}
    validated=des.validate_private_config(cfg)
    capacity=min(Fraction(n,1)/t*60 for n,t in validated)
    need(capacity==75 and sum(n==1 for n,t in validated)==1,
         "CAF05_NEW_PHYSICAL_CAPACITY_NOT_75")
    return {
        "name":name,"actual_bottleneck":STAGES[bottleneck],
        "config":cfg,"nominal_capacity_h":75,
        "independent_of_CAF04_in_parameters":True,
        "public_world_not_blinded":True,
    }


def all_worlds():
    return [world_spec(name) for name in NEW_WORLDS]


def measure_world(world,rate_name,rate,selector):
    arrivals=des.half_open_arrivals(rate,20)
    need(rate_name in dict(EVALUATION),"CAF05_UNDECLARED_PRESSURE")
    snapshots=des.run_toy_engine(world["config"],arrivals,(0,MINUTE,40))
    need(len(snapshots)==3 and
         snapshots[0].accepted_cum_orders==0 and
         snapshots[0].pending_orders==0,"CAF05_WORLD_NOT_EMPTY_AT_RESET")
    snap=snapshots[1]
    need(snap.accepted_cum_orders==
         snap.delivered_cum_orders+snap.pending_orders and
         snap.pending_orders==sum(snap.stage_waiting)+sum(
             snap.stage_in_service),"CAF05_DES_MASS_VIOLATION")
    idx=selector["measurement"]["stage_index"]
    measured=snap.stage_waiting[idx]+snap.stage_in_service[idx]
    other=[a+b for a,b in zip(snap.stage_waiting,snap.stage_in_service)]
    need(measured==other[idx],"CAF05_OBSERVATION_CONTRACT_VIOLATED")
    base={
        "world":world["name"],
        "true_physical_bottleneck":world["actual_bottleneck"],
        "rate_name":rate_name,
        "rate_per_minute":rate,
        "t_min":MINUTE,
        "accepted":snap.accepted_cum_orders,
        "delivered":snap.delivered_cum_orders,
        "pending_total":snap.pending_orders,
        "selected_sensor_reading":measured,
        "selected_sensor_only_measured_stage":selector["measurement"]["stage"],
        "all_stage_stock_in_evaluator_diagnostics_only":other,
        "all_stage_waiting_in_evaluator_diagnostics_only":
            list(snap.stage_waiting),
        "all_stage_in_service_in_evaluator_diagnostics_only":
            list(snap.stage_in_service),
    }
    if rate_name!="MATCHED":
        base["classification"]={
            "status":"OUT_OF_DOMAIN_PRESSURE_NO_CLASSIFICATION",
            "prediction":None,
            "trained_rate_per_minute":"3/2",
            "why":"Frozen classifier is conditioned on the CAF04 training input",
        }
    else:
        base["classification"]=predict_one(measured,selector)
    return base


def summarize(rows):
    eval_matched=[r for r in rows if r["rate_name"]=="MATCHED"]
    eval_low=[r for r in rows if r["rate_name"]=="LOW_OOD"]
    need(len(eval_matched)==len(eval_low)==3,"CAF05_MISSING_EVALUATIONS")
    measured={r["selected_sensor_reading"] for r in eval_matched}
    deliveries={r["delivered"] for r in eval_matched}
    low_sensor={r["selected_sensor_reading"] for r in eval_low}
    return {
        "matched": {
            "n_worlds":3,
            "n_unique_deliveries":len(deliveries),
            "n_unique_sensor_readings":len(measured),
            "delivery_observation_distinguishes_all":len(deliveries)==3,
            "selected_sensor_distinguishes_all":len(measured)==3,
            "classifier_correct":sum(
                x["classification"]["prediction"]==
                x["true_physical_bottleneck"]
                for x in eval_matched),
            "classifier_abstentions":sum(
                x["classification"]["prediction"] is None
                for x in eval_matched),
            "classifier_wrong":sum(
                x["classification"]["prediction"] is not None and
                x["classification"]["prediction"]!=x["true_physical_bottleneck"]
                for x in eval_matched),
        },
        "low_out_of_domain":{
            "n_worlds":3,
            "n_unique_deliveries":len({r["delivered"] for r in eval_low}),
            "n_unique_sensor_readings":len(low_sensor),
            "selected_sensor_distinguishes_all":len(low_sensor)==3,
            "classifier_run":False,
        },
    }


def csv_rows(rows):
    output=io.StringIO(newline="")
    w=csv.writer(output)
    w.writerow(["world","true_bottleneck","rate_name","rate","t_min",
                "delivered","pending_total","selected_dispatch_stock",
                "classification_status","predicted_bottleneck","all_stock"])
    for r in rows:
        w.writerow([r["world"],r["true_physical_bottleneck"],
                    r["rate_name"],r["rate_per_minute"],r["t_min"],
                    r["delivered"],r["pending_total"],
                    r["selected_sensor_reading"],
                    r["classification"]["status"],
                    r["classification"]["prediction"] or "",
                    "|".join(map(str,r[
                        "all_stage_stock_in_evaluator_diagnostics_only"]))])
    return output.getvalue()


def markdown(report):
    rows=report["observations"]
    s=report["selector"]
    lines=[
        "# CAF-05 — Contrato de observación y transferencia de un sensor",
        "",
        "**Exploración sintética, sin inferencia M/D de stocks internos.**",
        "La elección del sensor y los prototipos se tomaron SOLO de los",
        "mundos B/C/D de CAF-04 (60/h). Las cafeterías nuevas I/J/K",
        "tienen 75/h, con cuello respectivamente en preparación, despacho",
        "y entrega. Se mantuvieron las otras dos etapas a 120/h.",
        "",
        f"Sensor seleccionado ANTES de nuevos DES: **{s['measurement']['field']}**",
        f"en **{s['measurement']['stage']}**, minuto {MINUTE}, tasa 1.5/min.",
        "Prototipos congelados: preparación=1, despacho=6, entrega=2.",
        "Clasificador: mínima distancia absoluta al prototipo; empate",
        "significa abstención. No hay ajuste con los mundos I/J/K.",
        "",
        "## Resultados DES de mundos NUEVOS",
        "",
        "| Mundo | Cuello real | Entrada | Entregas t10 | Stock despacho t10 | Predicción congelada |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in rows:
        p=r["classification"]["prediction"]
        lines.append(
            f"| {r['world']} | {r['true_physical_bottleneck']} | "+
            f"{float(Fraction(r['rate_per_minute'])):.2f}/min | "+
            f"{r['delivered']} | {r['selected_sensor_reading']} | "+
            f"{p or r['classification']['status']} |")
    v=report["summary"]
    lines+=["",
        "## Alcance de la prueba",
        "",
        f"- A presión coincidente: el sensor distingue los tres mundos: "
        f"**{v['matched']['selected_sensor_distinguishes_all']}**; "
        f"entregas por sí solas distinguen los tres: "
        f"**{v['matched']['delivery_observation_distinguishes_all']}**.",
        f"- Clasificación por prototipos heredados: "
        f"{v['matched']['classifier_correct']}/3 correctos, "
        f"{v['matched']['classifier_wrong']} erróneos, "
        f"{v['matched']['classifier_abstentions']} abstenciones.",
        f"- Baja presión (0.8/min): el sensor tiene "
        f"{v['low_out_of_domain']['n_unique_sensor_readings']} "
        "valores distintos entre los tres mundos; **no ejecutamos el",
        "clasificador fuera de la entrada para la que fue elegido**.",
        "",
        "## Contrato de observabilidad para M y D",
        "",
        "- M-C00/C01: predicen entregas. Sus E1 bounded-queue",
        "nombran preparación y despacho, pero no se ha validado",
        "un operador que convierta el stock continuo en stock entero DES.",
        "- D-D1/D2/D3: predicen entregas y sus stocks son posiciones",
        "genéricas de cadena; no se puede renombrar D3 como preparación,",
        "despacho o entrega sin evidencia adicional.",
        "- Ni M ni D desagregan stock en espera frente a servicio en",
        "estos adaptadores. No se ha asignado una pérdida nueva ni",
        "se han infiltrado sensores internos en K0/K1/K2 anteriores.",
        "- Pendientes totales = aceptados − entregados, si sabemos",
        "las llegadas. No identifica dónde se acumulan los pedidos.",
        "",
        "## Límites",
        "",
        "- La fuente anterior CAF-04 es pública, y los nuevos mundos",
        "también están declarados en el código; la prueba es exploratoria",
        "fuera de la muestra previa, pero NO independiente ni ciega.",
        "- Se eligió una única presión y t10 por diseño de la prueba;",
        "no se optimizaron nuevas tasas con resultados I/J/K.",
        "- La búsqueda del sensor fue realizada sobre mundos previos",
        "con el cuello conocido. Los resultados no demuestran que el",
        "mismo canal permita localizar cuellos generales ni que un",
        "observador real conozca la escala de valores y sus prototipos.",
        f"- Corridas DES nuevas: {report['DES_runs']}; "
        "confirmatorias: 0; M/D reentrenados o cambiados: NO.",
        "- El próximo paso de inferencia M/D exigiría implementar y",
        "verificar operadores observacionales con unidades, papel de",
        "etapa, supuestos y errores; queda fuera de CAF-05.",
        "",
    ]
    return "\n".join(lines)


def run(out):
    folder=Path(out).resolve()
    need(not folder.exists(),"CAF05_OUTPUT_ALREADY_EXISTS")
    r=known_reference()
    selector=select_from_previous_only(r)
    contract=observation_contract()
    worlds=all_worlds()
    original_policy=d.POLICY.read_bytes()
    source_engine=lab.sha((lab.ROOT/
                            "experiments/cafeteria/pc01/caf01_des_engine.py").read_bytes())
    folder.mkdir(parents=True,exist_ok=False)
    writes={}
    def write(filename,data):
        writes[filename]=lab.write_new(folder,filename,data)
    write("00_SENSOR_Y_MUNDOS_PREDECLARADOS.json",{
        "schema":SCHEMA,
        "prior_reference_sha256":lab.sha(REF_PATH.read_bytes()),
        "prior_reference_source":r["source"],
        "source_DES_engine_sha256":source_engine,
        "CAF02_original_policy_sha256":lab.sha(original_policy),
        "sensor_selector":selector,
        "three_new_public_75h_worlds":worlds,
        "evaluation_rates":dict(EVALUATION),
        "observation_minute":MINUTE,
        "worlds_run_before_plan":0,
        "new_world_outcomes_seen":False,
        "M_D_existing_grids_and_policies_unchanged":True,
        "formal_confirmatory_trial":False,
    })
    write("01_CONTRATO_OBSERVABILIDAD.json",contract)
    write("01B_CHECKPOINT_ANTES_DE_DES.json",{
        "prior_model_and_sensor_frozen":True,
        "source_plan_sha256":writes["00_SENSOR_Y_MUNDOS_PREDECLARADOS.json"],
        "contract_sha256":writes["01_CONTRATO_OBSERVABILIDAD.json"],
        "DES_runs_so_far":0,
        "no_external_custody":True,
    })
    rows=[]
    for world in worlds:
        for rate_name,rate in EVALUATION:
            rows.append(measure_world(world,rate_name,rate,selector))
    need(d.POLICY.read_bytes()==original_policy,
         "CAF05_ORIGINAL_POLICY_CHANGED")
    summary=summarize(rows)
    report={
        "schema":SCHEMA,
        "status":"CAF05_OBSERVATION_CONTRACT_AND_SENSOR_TRANSFER_EXECUTED",
        "source_training":"CAF04_BCD_60_PER_H_K1_T10",
        "new_worlds":list(NEW_WORLDS),
        "selector":selector,
        "observations":rows,
        "summary":summary,
        "contract_cannot_score_M_D_with_DES_stage_stocks":True,
        "new_cafeteria_configs_public":True,
        "new_worlds_not_random_or_blinded":True,
        "DES_runs":len(rows),
        "DES_confirmatory_runs":0,
        "M_D_policy_or_grammar_modified":False,
        "external_custody":False,
    }
    need(report["DES_runs"]==6,"CAF05_NEW_WORLD_RUN_BUDGET")
    write("02_RESULTADOS.json",report)
    write("03_OBSERVACIONES.csv",csv_rows(rows))
    write("04_INFORME.md",markdown(report))
    write("05_MANIFIESTO.json",{
        "schema":SCHEMA,"files_sha256":dict(writes),
        "sensor_chosen_before_first_new_DES":True,
        "model_observation_contract_chosen_before_first_new_DES":True,
        "M_D_not_fitted_to_internal_states":True,
        "external_custody":False,
    })
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    value=run(args.out)
    print(json.dumps({
        "status":value["status"],"DES_runs":value["DES_runs"],
        "sensor":value["selector"]["measurement"],
        "observations":[{
            "world":r["world"],"rate":r["rate_name"],
            "delivered":r["delivered"],"selected_stock":
                r["selected_sensor_reading"],
            "prediction":r["classification"]["prediction"],
        } for r in value["observations"]],
        "summary":value["summary"],
    },sort_keys=True))


if __name__=="__main__":
    main()
