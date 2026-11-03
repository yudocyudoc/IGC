"""F3 / F6 admission probe: does observed PM add process structure beyond B1/B2?

NO new process-mining method, no grid, no DES run. Reuses original EV-01
PM4Py DFG and independently checks it against the exact FULL event log and
evaluator-side B1/B2 physical reports. O0/O1 remain strictly public and
cannot gain FULL-stage sequence information through this evaluator diagnostic.

Negative result applies only to the known deterministic EV-01 control, not
to PM in general or the later F6 ablation on independent reserve data.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import csv
import json
from pathlib import Path

from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_v0_contract import canonical, digest
from scripts import arena_event_observability as obs

SCHEMA="igc-arena-f3-process-information-increment/0.1"
TYPES={"pedido_creado","pago_confirmado","pedido_entregado",
       "etapa_entrada","servicio_inicio","servicio_fin"}


def read_full(filename):
    with Path(filename).open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        cols={"case_id","event_seq","activity","event_type",
              "t_minutes_exact","source","stage","resource_id"}
        need(set(reader.fieldnames or [])==cols,
             "F3P_FULL_SOURCE_REQUIRED")
        rows=[]
        for row in reader:
            need(set(row)==cols,"F3P_MALFORMED_FULL_ROW")
            need(str(int(row["event_seq"]))==row["event_seq"],
                 "F3P_INVALID_EVENT_SEQ")
            row["event_seq"]=int(row["event_seq"])
            for key in ("stage","resource_id"):
                if row[key]=="":
                    row.pop(key)
            rows.append(row)
    need(bool(rows) and [x["event_seq"] for x in rows]==list(range(len(rows))),
         "F3P_FULL_NOT_CONTIGUOUS")
    return rows


def _per_case(full):
    groups=defaultdict(list)
    for row in full:
        need(row["event_type"] in TYPES and
             row["activity"]==(
               row["event_type"]+"::"+row["stage"] if row.get("stage")
               else row["event_type"]),
             "F3P_EVENT_ACTIVITY_MISMATCH")
        if row["event_type"] in {"etapa_entrada","servicio_inicio","servicio_fin"}:
            need(row["source"]=="instrumentacion_fisica" and
                 bool(row.get("stage")),"F3P_UNINSTRUMENTED_SERVICE")
        groups[row["case_id"]].append(row)
    return {key:sorted(rows,key=lambda e:(
            Fraction(e["t_minutes_exact"]),e["event_seq"]))
            for key,rows in groups.items()}


def _counts(groups):
    arcs=Counter()
    starts=Counter()
    ends=Counter()
    for rows in groups.values():
        activities=[r["activity"] for r in rows]
        arcs.update(zip(activities,activities[1:]))
        starts[activities[0]]+=1
        ends[activities[-1]]+=1
    return arcs,starts,ends


def audit(ev01,full,f2,o0,o1):
    validate_a1_visible(o0,"O0")
    validate_a1_visible(o1,"O1")
    need(ev01.get("schema")=="igc-arena-eventlog-three-views/0.1" and
         ev01.get("same_world_three_views") is True and
         ev01.get("n_orders")==15 and
         ev01.get("n_event_rows_by_view")=={
             "POS":45,"POS_KDS":75,"FULL":225} and
         ev01.get("process_DFG_does_not_identify_causal_mechanisms") is True and
         ev01.get("no_grid_or_catalog") is True,
         "F3P_ORIGINAL_EV01_REPORT_INVALID")
    need(f2.get("schema")=="igc-cafe-f2-b0-b1-b2-physical-controls/0.1" and
         f2.get("case")=="EV01_KNOWN_SYNTHETIC_CONTROL" and
         f2["B0"]["status"]=="B0_POS_MATERIAL_BALANCE_PASS" and
         f2["B1"]["status"]=="B1_DIRECT_FULL_INSTRUMENTATION_PASS" and
         f2["B2"]["status"]=="B2_EXACT_RESOURCE_PERIODS_PASS" and
         f2.get("causal_bottleneck_discovery")=="NOT_ESTABLISHED" and
         f2["B1"]["ranked_waiting_is_not_causal_bottleneck"] is True,
         "F3P_ORIGINAL_B0_B1_B2_REPORT_INVALID")
    need(o0["observability"]["world_public_id"]==
         o1["observability"]["world_public_id"] and
         o0["observability"]["cutoff_minutes_exact"]==
         o1["observability"]["cutoff_minutes_exact"]=="10" and
         o0["construction"]["observation_series"]==
         o1["construction"]["observation_series"] and
         o0["construction"]["pos_arrival_events"]==
         o1["construction"]["pos_arrival_events"],
         "F3P_O0_O1_NOT_SAME_PHYSICAL_OBSERVATIONS")
    need("physical_observation" not in o0["construction"] and
         "physical_observation" in o1["construction"] and
         o1["construction"]["physical_observation"]["stage_disclosed"]==
            "preparacion",
         "F3P_O1_NOT_JUST_PREP_AGGREGATE")
    for visible in (o0,o1):
        need("resource_id" not in json.dumps(visible) and
             "transferencia_final" not in json.dumps(visible) and
             "despacho" not in json.dumps(visible) and
             len(visible["construction"]["pos_arrival_events"])==15 and
             all(set(x)=={"case_id","t_minutes_exact"} for x in
                 visible["construction"]["pos_arrival_events"]),
             "F3P_HIDDEN_STAGE_OR_PATH_LEAK_TO_PRODUCER")
    stage_order=f2["B1"]["operational_diagnosis"]["stage_order_directly_observed"]
    need(len(stage_order)==4 and len(set(stage_order))==4 and
         f2["B1"]["operational_diagnosis"]["n_stages_actually_instrumented"]==4 and
         set(stage_order)==set(f2["B1"]["stage_event_balances"]),
         "F3P_B1_STAGE_ORDER_NOT_PHYSICALLY_OBSERVED")
    need(len(full)==225, "F3P_FULL_225_REQUIRED")
    # Independently invoke existing FULL time/resource consistency checks,
    # rather than trusting historical PM edges as truth.
    checked=obs.analyze_view(full,"FULL",tuple(stage_order))
    need(len(checked["cases"])==15,"F3P_FULL_VALIDATION_NOT_FIFTEEN")
    groups=_per_case(full)
    need(len(groups)==15 and all(len(r)==15 for r in groups.values()),
         "F3P_INCOMPLETE_FULL_CASE_TRACES")
    arcs,starts,ends=_counts(groups)
    for view,expected in (("POS",(3,2)),("POS_KDS",(5,4)),
                          ("FULL",(15,14))):
        mined=ev01["pm4py_discovery"][view]
        need(mined["method"]=="PM4Py.discover_dfg" and
             mined["dfg_is_observed_succession_not_causal_proof"] is True and
             (mined["n_activities"],len(mined["edges"]))==expected and
             mined["n_cases"]==15,
             "F3P_PRIOR_PM4PY_WITNESS_INVALID")
    full_dfg=ev01["pm4py_discovery"]["FULL"]
    reported_arcs=Counter({
        (x["from"],x["to"]):x["count"] for x in full_dfg["edges"]})
    need(len(reported_arcs)==len(full_dfg["edges"])==14 and
         reported_arcs==arcs and
         full_dfg["start_activities"]==dict(starts) and
         full_dfg["end_activities"]==dict(ends),
         "F3P_PM_DFG_NOT_REPRODUCIBLE_FROM_FULL_CASE_EVENTS")
    routes=[
        tuple(x["stage"] for x in rows if x["event_type"]=="etapa_entrada")
        for rows in groups.values()
    ]
    variants=Counter(routes)
    need(all(path[0]==stage_order[0] and
             set(path)==set(stage_order) for path in variants),
         "F3P_B1_AND_DIRECT_EVENT_PATH_DISAGREE")
    repeated_stage_cases=sum(len(path)!=len(set(path)) for path in routes)
    need(all(set(v.values())=={15} for v in
             f2["B1"]["stage_event_balances"].values()),
         "F3P_B1_STAGE_MASS_DRIFT")
    no_variation=len(variants)==1 and repeated_stage_cases==0
    if no_variation:
        need(tuple(stage_order)==next(iter(variants)),
             "F3P_B1_ALREADY_OBSERVED_SAME_ROUTE")
    if no_variation:
        verdict="NO_INCREMENTAL_ROUTE_VARIATION_OVER_B1_IN_KNOWN_EV01"
    else:
        verdict="VARIATION_FOUND_REQUIRES_SAME_INFORMATION_ABLATION"
    # B1 already infers/validates the full physical path; original PM4Py
    # cannot establish a bottleneck cause or previously hidden stage.
    return {
        "schema":SCHEMA,
        "scope":"EVALUATOR_ONLY_KNOWN_SYNTHETIC_EV01",
        "original_pm_engine":"PM4Py.discover_dfg",
        "original_pm4py_version":full_dfg["pm4py_version"],
        "original_pm4py_report_sha256":digest(ev01),
        "original_f2_b1_b2_report_sha256":digest(f2),
        "public_O0_sha256":digest(o0),
        "public_O1_sha256":digest(o1),
        "same_world":True,
        "n_cases":len(groups),
        "view_information":{
            "O0":"PUBLIC_POS_ARRIVALS_AND_CUMULATIVE_DELIVERIES_NOT_CASE_STAGE_PATHS",
            "O1":"O0_PLUS_CENSORED_PREPARATION_SUMMARY_NOT_CASE_STAGE_PATHS",
            "FULL":"EVALUATOR_ONLY_COMPLETE_FOUR_STAGE_CASE_PATHS",
        },
        "pm4py_event_views":{
            view:{"activities":p["n_activities"],
                  "dfg_edges":len(p["edges"])}
            for view,p in ev01["pm4py_discovery"].items()},
        "full_case_route_variants":len(variants),
        "full_case_route_counts":[{
            "route":list(route),"cases":count}
            for route,count in sorted(variants.items())],
        "repeated_stage_cases":repeated_stage_cases,
        "full_dfg_14_edges_count_15_each":(
            len(arcs)==14 and all(v==15 for v in arcs.values())),
        "B1_already_observes_order_and_per_stage_physics":True,
        "B2_already_observes_per_resource_service_periods":True,
        "PM_reveals_additional_structural_requirement_over_B1":(
            "NOT_OBSERVED_IN_THIS_EV01" if no_variation else
            "NOT_YET_ATTRIBUTED"),
        "incremental_process_information_verdict":verdict,
        "same_evidence_P_ablation_per_D_B_M":"NOT_RUN",
        "PM_14":"NOT_TRIGGERED_FOR_THIS_KNOWN_CONTROL",
        "global_F6":"NOT_ADJUDICATED",
        "causal_bottleneck_location_from_DFG":"NOT_IDENTIFIED",
        "known_evaluator_stages_are_not_inferred_from_POS_O0_O1":True,
        "no_model_or_sensor_advice_from_PM_alone":True,
        "no_new_PM_or_DES_or_provider_execution":True,
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ev01-report",required=True,type=Path)
    p.add_argument("--full",required=True,type=Path)
    p.add_argument("--f2-report",required=True,type=Path)
    p.add_argument("--o0",required=True,type=Path)
    p.add_argument("--o1",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    need(not a.out.exists(),"F3P_REFUSE_OVERWRITE")
    load=lambda path:json.loads(path.read_text(encoding="utf-8"))
    report=audit(load(a.ev01_report),read_full(a.full),load(a.f2_report),
                 load(a.o0),load(a.o1))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "verdict":report["incremental_process_information_verdict"],
        "route_variants":report["full_case_route_variants"],
        "A3":report["A3"],"G4":report["G4"],"G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
