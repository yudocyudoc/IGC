"""E06 / Arena: source-first video2 fitness for one material boundary, two fixed windows.

Read-only, offline evaluation of the investigator-supplied archived annotations.
Never extracts video, performs tracking, equates local IDs with physical objects,
infers capacities, fits service times, executes PM or reuses physical DES truth.
Output is a bounded aggregate evidence packet safe to commit without raw rows.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

SCHEMA = "igc-arena-e06-video2-observational-fitness/0.1"
ZIP_SHA256 = "eb1c619de072a5790182cd7eb060f9d8b0c6a163acdfd6c18e0af3986fec23e8"
VIDEO_DECLARED_SHA256 = "bdf725f004a0d39929a2a0f4fdc6d7d3d066e225cdcb14b81b82384eec34169e"
V1_SHA256 = "2ab597aea3b381cccdd8b7bc06bb696c518977847130daf444b8aedb4866f958"
V2_SHA256 = "1e81b5464d871cb621e18dd8880a99ccb33be714e458785e25cb345099336d72"
L001_EVENTS_SHA256 = "4bcbeeaa732dcb6f6d3f217e1f2ce3efe9bdba98079f79e02a1bde197a1b7165"
L001_METRICS_SHA256 = "f45e12578813f75ae6f201e5390f93e39bf115aed2849edd704072f09544fc28"
MASTER_V2 = "video2/maestro_15m_v2/eventos_maestro.csv"
MASTER_V1 = "video2/maestro_15m_v1/eventos_maestro.csv"
L001 = "video2/lote_L001_v2/eventos_detallados.csv"
METRICS = "video2/lote_L001_v2/metricas.csv"
EVENTS = "video2/eventos_15m_v1/eventos.csv"
COVERAGE = "video2/eventos_15m_v1/cobertura_eventos.csv"
REQUESTS = "video2/eventos_15m_v1/solicitudes.csv"
WINDOWS = ((Decimal(0), Decimal(300)), (Decimal(300), Decimal(600)))


def _require(yes, reason):
    if not yes:
        raise ValueError("E06_" + reason)


def _sha(raw):
    return sha256(raw).hexdigest()


def _csv(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))


def _num(value):
    try:
        d = Decimal(str(value))
        _require(d.is_finite(), "NONFINITE_TIMESTAMP")
        return d
    except (InvalidOperation, TypeError):
        raise ValueError("E06_INVALID_TIMESTAMP") from None


def verified_members(archive_path, *, expected_sha=ZIP_SHA256):
    """Require exactly inventoried bytes, no duplicate members or path traversal."""
    p = Path(archive_path)
    _require(_sha(p.read_bytes()) == expected_sha, "ZIP_SHA256_MISMATCH")
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        _require(len(set(names)) == len(names), "DUPLICATE_ZIP_MEMBER")
        _require(all(not n.startswith(("/", "\\")) and ".." not in Path(n).parts
                     and "\\" not in n for n in names), "UNSAFE_ZIP_MEMBER")
        _require("VIDEO2_SOURCE_INVENTORY.json" in names, "INVENTORY_ABSENT")
        manifest_bytes = z.read("VIDEO2_SOURCE_INVENTORY.json")
        inventory = json.loads(manifest_bytes)
        _require(inventory["planned_windows_video_seconds"] == [[0,300],[300,600]]
                 and inventory["window_convention"] == "left_closed_right_open"
                 and inventory["video_declared_sha256"] == VIDEO_DECLARED_SHA256
                 and inventory["video_bytes_rehashed_in_this_review"] is False,
                 "INVENTORY_SCOPING_CHANGED")
        items = inventory["files"]
        declared = [i["path"] for i in items]
        _require(len(declared) == 20 and len(set(declared)) == 20
                 and set(names) == set(declared) | {"VIDEO2_SOURCE_INVENTORY.json"},
                 "INVENTORY_MEMBERS_CHANGED")
        members = {}
        for item in items:
            b = z.read(item["path"])
            _require(len(b) == item["size_bytes"] and _sha(b) == item["sha256"],
                     "MEMBER_BYTES_CHANGED:" + item["path"])
            members[item["path"]] = b
    for path, expected in ((MASTER_V1,V1_SHA256), (MASTER_V2,V2_SHA256),
                           (L001,L001_EVENTS_SHA256),(METRICS,L001_METRICS_SHA256)):
        _require(_sha(members[path]) == expected, "PINNED_SOURCE_MISMATCH:" + path)
    return members, _sha(manifest_bytes)


def _interval_overlap(row, lo, hi):
    """Evidence span, not event time; never replace by midpoint."""
    start = _num(row["observado_desde_video_s"])
    end = _num(row["observado_hasta_video_s"])
    _require(start <= end, "EVIDENCE_SPAN_REVERSED")
    return start < hi and end >= lo  # right boundary belongs to NEXT window


def audit_members(members, inventory_sha):
    old, rows = _csv(members[MASTER_V1]), _csv(members[MASTER_V2])
    events, coverage, requests = (_csv(members[p]) for p in (EVENTS, COVERAGE, REQUESTS))
    hits, metrics = _csv(members[L001]), _csv(members[METRICS])
    summary = json.loads(members["video2/maestro_15m_v2/resumen.json"])
    summary_v1 = json.loads(members["video2/eventos_15m_v1/resumen.json"])
    dictionary = _csv(members["video2/maestro_15m_v2/diccionario_columnas.csv"])
    _require(len(rows) == 288 and len(rows[0]) == 58 and len(old) == 280
             and len(events) == 199 and len(coverage) == 13 and len(requests) == 14
             and len(hits) == 7 and len(metrics) == 9 and len(dictionary) == 58,
             "EXPECTED_SOURCE_SHAPES_CHANGED")
    _require(set(row["columna"] for row in dictionary) == set(rows[0]), "DICTIONARY_MISMATCH")
    _require(summary["version"] == "2.0-revision-L001"
             and summary["base_sha256"] == V1_SHA256
             and summary["fuente_sha256"] == VIDEO_DECLARED_SHA256
             and summary["nueva_fuente_empirica"] is False
             and summary["recepciones_confirmadas"] == 2
             and summary["total_bebidas_unicas_despachadas"] is None
             and summary_v1["source_video_sha256"] == VIDEO_DECLARED_SHA256
             and summary_v1["exhaustive_event_detection"] is False
             and summary_v1["physical_clock_verified"] is False
             and summary_v1["continuous_recording_verified"] is False,
             "SOURCE_SEMANTICS_CHANGED")
    for row in rows:
        _require(row["fuente_sha256"] == VIDEO_DECLARED_SHA256
                 and row["base_tiempo"] == "segundos_video"
                 and row["continuidad_verificada"] == "false"
                 and row["velocidad_real_verificada"] == "false"
                 and row["apto_parametro_servicio_arena"] == "false",
                 "SOURCE_CLOCK_OR_SERVICE_ATTESTATION_CHANGED")
    old_ids = {x["registro_id"]: x for x in old}
    new_ids = {x["registro_id"]: x for x in rows}
    _require(len(old_ids)==len(old) and len(new_ids)==len(rows)
             and set(old_ids) <= set(new_ids), "MASTER_IDENTITY_CHANGED")
    changed=[]
    for ident, before in old_ids.items():
        if any(after_val != before[k] for k, after_val in new_ids[ident].items()
               if k in before):
            changed.append(ident)
    newly = set(new_ids)-set(old_ids)
    _require(set(changed) == set(summary["filas_actualizadas"])
             and newly == ({summary["evento_nuevo"]} | {
                 "MD-L001-F02","MD-L001-F03","MD-L001-F04","MD-L001-F05",
                 "MD-L001-F06","MD-L001-F07","MD-L001-F09"})
             and summary["metricas_nuevas"] == 7,
             "UNDECLARED_V1_V2_REVISION")

    # A local candidate Vxxx / Lxxx / person is NOT a stable physical cup or order.
    orders = [x for x in rows if x["pedido_id"]]
    cups = [x for x in rows if x["recipiente_id"]]
    service = [x for x in rows if x["duracion_servicio_min_s"] or x["duracion_servicio_max_s"]]
    _require(not orders and not cups and not service,
             "CURRENT_SOURCE_HAS_NEW_UNADJUDICATED_ID_OR_SERVICE")
    _require(not any(x["complete_count_identifiable"].lower() == "true" for x in coverage),
             "SOURCE_COMPLETENESS_CLAIM_CHANGED")
    _require(all(x["tracking_status"] != "enlace_individual_validado" for x in requests),
             "REQUEST_LINK_SEMANTICS_CHANGED")
    receptions = [r for r in rows if r["recepcion_cliente_confirmada"] == "true"]
    _require(len(receptions) == 2 and all(r["lote_id"] == "L001" and
             r["tipo_evento"] == "entrega_receptor" and r["tipo_registro"] == "evento"
             for r in receptions), "RECEPTION_EVIDENCE_CHANGED")
    bounds = sorted([[str(_num(r["inicio_min_video_s"])), str(_num(r["inicio_max_video_s"]))]
                     for r in receptions])
    _require(all(_num(a) <= _num(b) for a,b in bounds)
             and all(_num(a) < 300 and _num(b) < 300 for a,b in bounds),
             "RECEPTION_INTERVAL_OR_WINDOW_CHANGED")

    window_results=[]
    for lo,hi in WINDOWS:
        included = [r for r in rows if _interval_overlap(r,lo,hi)]
        by_type = {k:sum(r["tipo_registro"] == k for r in included)
                   for k in ("evento","medicion_temporizador","conteo_visual","intervalo_derivado")}
        # Only clearly delimited transitions are potential evidence, not all activity windows.
        possible_inputs = sum(r["tipo_evento"] == "colocacion_solicitud"
                              and r["tipo_registro"] == "evento" for r in included)
        possible_exits = sum(r["recepcion_cliente_confirmada"] == "true" for r in included)
        window_results.append({
            "video_seconds_left_closed_right_open":[int(lo),int(hi)],
            "master_records_with_evidence_span_intersecting_window":len(included),
            "record_types_overlapping":by_type,
            "observed_placement_transitions_not_linked_to_deliveries":possible_inputs,
            "confirmed_L001_receptions_not_linked_to_placements":possible_exits,
            "complete_per_unit_input_output_pairs_validated":0,
            "coverage_interpretation":"NONEXHAUSTIVE_OVERLAPPING_RECORDS_NOT_EVENT_COUNTS_OR_ARRIVAL_RATES"
        })
    crossings = {str(int(x)):
                 sum(_num(r["observado_desde_video_s"]) < x < _num(r["observado_hasta_video_s"])
                     for r in rows) for x in (Decimal(300), Decimal(600))}
    # A row overlapping 300 occurs in BOTH windows, never double-count it as a new event.
    return {
        "schema":SCHEMA, "experiment":"E06",
        "question":"Can a validated material unit cross the same request-cup-placement to physical-reception boundary in both 5-minute windows, with known censoring?",
        "status":"SOURCE_NOT_FIT_FOR_THIS_QUESTION",
        "scope":"VIDEO2_EXISTING_ANNOTATIONS_DEVELOPMENT_ONLY_NO_NEW_OBSERVATIONS",
        "source":{
            "archive_sha256":"sha256:"+ZIP_SHA256,
            "manifest_sha256":"sha256:"+inventory_sha,
            "video_hd_sha256_declared_not_rehashed":"sha256:"+VIDEO_DECLARED_SHA256,
            "master_v1_sha256":"sha256:"+V1_SHA256,
            "master_v2_sha256":"sha256:"+V2_SHA256,
            "l001_hitos_sha256":"sha256:"+L001_EVENTS_SHA256,
            "video_original_present_in_archive":False,
            "physical_clock_verified":False,"recording_continuity_verified":False,
            "source_family":"ONE_VIDEO_HD_NO_INDEPENDENT_REPLICATION"
        },
        "unit_boundary":{
            "candidate_unit":"individual solicitud-associated vessel/beverage; order equivalence NOT established",
            "start_observable":"colocacion_solicitud at machine (not customer arrival)",
            "end_observable":"confirmed physical entrega_receptor of same unit",
            "same_unit_identity":"NOT_VALIDATED",
            "known_initial_population":"UNKNOWN_WITH_LEFT_CENSORING",
            "complete_input_output_pairs":0,
            "video_seconds_are_physical_seconds":False
        },
        "version_reconciliation":{
            "master_v1_rows":len(old),"master_v2_rows":len(rows),
            "v2_existing_rows_revised":len(changed),
            "v2_added_event_rows":1,"v2_added_derived_interval_rows":7,
            "v1_v2_same_video_source":True,
            "l001_derivatives_are_not_independent_observations":True
        },
        "windows":window_results,
        "evidence_spans_crossing_fixed_cuts":crossings,
        "l001_evidence":{
            "confirmed_receptions_in_first_window":len(receptions),
            "reception_transition_intervals_video_s":bounds,
            "two_receptions_not_four":True,
            "contextual_lot_not_individual_request_to_delivery_link":True,
            "pickup_and_pass_not_service_start_or_customer_arrival":True
        },
        "censoring":{
            "entry_of_first_observed_removed_request":"LEFT_CENSORED_BEFORE_VIDEO_START",
            "unobserved_transitions":"UNKNOWN_NOT_ZERO",
            "window_end_with_missing_unit_identity":"RIGHT_CENSORED_OR_UNKNOWN_NEVER_IMPUTED",
            "time_intervals":"BOUNDED_NOT_MIDPOINTS",
            "derived_integral_F09":"SHARED_SOURCE_NOT_NEW_SAMPLE"
        },
        "secondary_observation":"TWO_CONTEXTUAL_LOT_RECEPTIONS_IN_VIDEO_TIME_ONLY",
        "missing_measurements":[
            "SAME_PHYSICAL_UNIT_IDENTIFIER_ACROSS_PLACEMENT_PREPARATION_AND_RECEPTION",
            "OBSERVED_INPUT_AND_OUTPUT_AT_ONE_DECLARED_BOUNDARY_FOR_THE_SAME_UNIT",
            "INITIAL_WIP_AND_CENSORSHIP_FOR_EACH_5_MINUTE_WINDOW",
            "VALIDATED_SEGMENT_CONTINUITY_AND_PHYSICAL_CLOCK_FOR_RATES_OR_SERVICE_TIME",
            "COMPLETE_SERVICE_START_AND_FINISH_EVENTS_IF_SERVICE_DURATION_IS_ASKED"
        ],
        "E07":"NOT_TRIGGERED_NO_NEW_OBSERVED_INCREMENTAL_PROCESS_REGULARITY",
        "no_new_pm_des_omc_provider":True,
        "models_D_B_M_not_run_on_video2":True,
        "physical_capacity_or_productivity_not_inferred":True,
        "raw_annotations_or_person_records_embedded":False
    }


def audit_zip(path, *, expected_sha=ZIP_SHA256):
    members, inventory_sha=verified_members(path,expected_sha=expected_sha)
    return audit_members(members,inventory_sha)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():
        raise ValueError("E06_REFUSE_TO_OVERWRITE")
    r=audit_zip(a.source_zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"E06":r["status"],"windows":[w["master_records_with_evidence_span_intersecting_window"] for w in r["windows"]],"E07":r["E07"],"new_model_calls":0}))

if __name__=="__main__":
    main()