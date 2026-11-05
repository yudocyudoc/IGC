#!/usr/bin/env python3
"""Valida observaciones de video para Arena v0.1: esquema e invariantes.

NO valida interpretación visual, reloj físico, cobertura ni tasas/capacidad.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2] / "data" / "arena" / "video_barista_v0_1" / "contrato"


def load_contracts():
    schema = json.loads((ROOT / "schema_anotacion_v0_1.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "catalogo_eventos_v0_1.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema), {e["code"]: e for e in catalog["entries"]}, catalog


def validate_record(row, validator, entries, catalog):
    errors = sorted("JSON Schema: " + e.message for e in validator.iter_errors(row))
    if errors:
        return errors
    code = row["event_code"]
    if row["kind"] != entries[code]["kind"]:
        errors.append(f"event_code={code} requiere kind={entries[code]['kind']}")
    provenance = row["provenance"]
    if provenance["source_video_sha256"] != catalog["source_video_sha256"]:
        errors.append("SHA-256 de video no coincide con el corpus")
    if provenance["physical_clock_verified"] or provenance["continuous_recording_verified"]:
        errors.append("El corpus v0.1 no verifica tiempo físico ni continuidad")
    if row.get("batch_context") and row.get("batch_link") == "none":
        errors.append("batch_context exige un vínculo no nulo")
    if row.get("batch_link") == "object_trace_verified" and not row.get("object_track_id"):
        errors.append("object_trace_verified requiere traza de objeto")
    time = row["time"]
    mode = time["mode"]
    expected = {"estado": "sample", "accion": "sample", "transicion": "transition", "episodio": "episode"}
    if mode != expected[row["kind"]]:
        errors.append(f"{row['kind']} requiere time.mode={expected[row['kind']]}")
    if mode == "sample":
        samples = time["samples_video_s"]
        if samples != sorted(set(samples)):
            errors.append("Muestras desordenadas o repetidas")
        evidence_seconds = {round(e["frame_video_s"], 6) for e in row["evidence"]}
        if any(round(s, 6) not in evidence_seconds for s in samples):
            errors.append("Toda muestra necesita fotograma de evidencia")
    elif mode == "transition":
        older, newer = time["last_state_video_s"], time["first_new_state_video_s"]
        if older >= newer:
            errors.append("Transición exige t_antiguo < t_nuevo")
        frames = {round(e["frame_video_s"], 6) for e in row["evidence"]}
        if round(older, 6) not in frames or round(newer, 6) not in frames:
            errors.append("Transición exige evidencia antes y después")
    elif mode == "episode":
        start, end, censoring = time["start_video_s"], time["end_video_s"], time["censoring"]
        if censoring == "bounded" and (start is None or end is None):
            errors.append("bounded exige ambos extremos")
        if censoring == "left_censored" and start is not None:
            errors.append("left_censored exige inicio null")
        if censoring == "right_censored" and end is not None:
            errors.append("right_censored exige fin null")
        if censoring == "both_censored" and (start is not None or end is not None):
            errors.append("both_censored exige inicio y fin null")
        if start is not None and start[0] > start[1]:
            errors.append("Inicio invertido")
        if end is not None and end[0] > end[1]:
            errors.append("Fin invertido")
        if start is not None and end is not None and (start[0] > end[1] or start[1] > end[1]):
            errors.append("Inicio posterior al fin")
        if len(row["evidence"]) < 2:
            errors.append("Episodio exige al menos dos fotogramas")
    if code == "minimo_recipientes_con_contenido":
        if row.get("count_lower_bound", -1) < 1:
            errors.append("Falta count_lower_bound positivo")
        if row.get("quantity_unit") != "recipientes_visibles":
            errors.append("Unidad debe ser recipientes_visibles")
    if code in ("montaje_completo_verificado", "ultimo_vertido_visible", "vapor_activo_verificado", "extraccion_activa_verificada"):
        if not row.get("evidence_criterion"):
            errors.append(f"{code} requiere evidence_criterion")
    if code == "montaje_completo_verificado" and not row.get("object_track_id"):
        errors.append("Montaje completo requiere traza de objeto")
    return errors


def validate_file(path):
    validator, entries, catalog = load_contracts()
    errors = []
    count = 0
    ids = set()
    with Path(path).open(encoding="utf-8-sig") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"línea {line_no}: JSON inválido: {exc}")
                continue
            count += 1
            event_id = record.get("event_id")
            if event_id in ids:
                errors.append(f"línea {line_no}: id duplicado {event_id!r}")
            ids.add(event_id)
            for problem in validate_record(record, validator, entries, catalog):
                errors.append(f"línea {line_no} ({event_id}): {problem}")
    return count, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()
    count, errors = validate_file(args.jsonl)
    for error in errors:
        print("ERROR:", error)
    if errors:
        print(f"FAIL: {len(errors)} problemas, {count} registros")
        return 1
    print(f"PASS: {count} anotaciones estructuralmente válidas; evidencia visual NO certificada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
