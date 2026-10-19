"""Run the synthetic F0 vertical wiring probe without hiding missing engines."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "synthetic" / "source.txt"
CLAIM_PATH = ROOT / "data" / "synthetic" / "claim.json"
MODEL_PATH = ROOT / "spike" / "f0_vertical" / "F0ToyStock.mo"
CANDIDATE_PATH = ROOT / "spike" / "f0_vertical" / "candidate-stub.json"
SHAPES_PATH = ROOT / "spike" / "f0_vertical" / "f0_shapes.ttl"
OUTPUT_DIR = ROOT / "artifacts" / "f0"
SYNTHETIC_BASE = "https://example.invalid/igc/"


def overall_status(stages: list[dict]) -> str:
    states = {stage["status"] for stage in stages}
    if "FAIL" in states:
        return "FAIL"
    if states & {"PENDING", "STUB", "NOT_RUN"}:
        return "BLOCKED"
    return "PASS"


def source_and_annotation() -> tuple[list[dict], dict]:
    source_bytes = SOURCE_PATH.read_bytes()
    source_text = source_bytes.decode("utf-8")
    claim = json.loads(CLAIM_PATH.read_text(encoding="utf-8"))
    quote = claim["quote"]
    offset = source_text.find(quote)
    if offset < 0:
        return ([{"stage": "source_ingest_and_anchor", "status": "FAIL",
                  "reason": "claim quote is not present in source"}], {})

    source_hash = hashlib.sha256(source_bytes).hexdigest()
    source_stage = {
        "stage": "source_ingest_and_anchor",
        "status": "PASS",
        "source_id": SYNTHETIC_BASE + claim["source_id"],
        "source_sha256": source_hash,
        "quote_start": offset,
        "quote_end": offset + len(quote),
        "synthetic": bool(claim.get("synthetic")),
    }
    annotation = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": SYNTHETIC_BASE + "annotation-001",
        "type": "Annotation",
        "motivation": "assessing",
        "body": {
            "id": SYNTHETIC_BASE + claim["claim_id"],
            "type": "TextualBody",
            "value": quote,
            "purpose": "tagging",
        },
        "target": {
            "source": SYNTHETIC_BASE + claim["source_id"],
            "selector": {"type": "TextQuoteSelector", "exact": quote},
        },
    }
    return [source_stage], annotation


def _pending_semantic_stages(reason: str) -> list[dict]:
    return [
        {"stage": "web_annotation_jsonld_roundtrip", "status": "PENDING", "reason": reason},
        {"stage": "rdf_prov_mapping", "status": "PENDING", "reason": reason},
        {"stage": "shacl_positive_and_negative", "status": "PENDING", "reason": reason},
        {"stage": "sparql_query", "status": "PENDING", "reason": reason},
    ]


def run_semantic_pipeline(annotation: dict) -> list[dict]:
    """Parse Web Annotation JSON-LD, add PROV-O links, validate SHACL, and query RDF."""
    try:
        from pyshacl import validate
        from rdflib import Graph, Namespace, RDF, URIRef
        from rdflib.compare import isomorphic
    except ImportError as exc:
        return _pending_semantic_stages(f"semantic dependency unavailable: {exc.name}")

    try:
        import json as json_module
        from rdflib import Literal

        graph = Graph()
        graph.parse(data=json_module.dumps(annotation), format="json-ld")
        annotation_id = URIRef(annotation["id"])
        body_id = URIRef(annotation["body"]["id"])
        source_id = URIRef(annotation["target"]["source"])
        activity_id = URIRef(SYNTHETIC_BASE + "activity-anchor-001")
        oa = Namespace("http://www.w3.org/ns/oa#")
        prov = Namespace("http://www.w3.org/ns/prov#")

        graph.add((annotation_id, RDF.type, oa.Annotation))
        graph.add((source_id, RDF.type, prov.Entity))
        graph.add((annotation_id, RDF.type, prov.Entity))
        graph.add((activity_id, RDF.type, prov.Activity))
        graph.add((activity_id, prov.used, source_id))
        graph.add((activity_id, prov.generated, annotation_id))
        graph.add((annotation_id, prov.wasGeneratedBy, activity_id))

        roundtrip = Graph()
        roundtrip.parse(data=graph.serialize(format="turtle"), format="turtle")
        roundtrip_ok = isomorphic(graph, roundtrip)
        prov_ok = (
            (activity_id, prov.used, source_id) in graph
            and (activity_id, prov.generated, annotation_id) in graph
            and (annotation_id, prov.wasGeneratedBy, activity_id) in graph
        )

        # Minimal, fixture-scoped CRMinf profile. The source explicitly says it
        # contains no real measurement, inference, or causal evidence, so CRMsci
        # observation and CRMinf inference classes must not be asserted here.
        crminf = Namespace("http://www.cidoc-crm.org/extensions/crminf/")
        belief_id = URIRef(SYNTHETIC_BASE + "belief-synthetic-001")
        proposition_id = URIRef(SYNTHETIC_BASE + "proposition-set-synthetic-001")
        graph.add((activity_id, RDF.type, crminf.I1_Argumentation))
        graph.add((belief_id, RDF.type, crminf.I2_Belief))
        graph.add((proposition_id, RDF.type, crminf.I4_Proposition_Set))
        graph.add((activity_id, crminf.J2_concluded_that, belief_id))
        graph.add((belief_id, crminf.J4_that, proposition_id))
        crminf_mapping_ok = all((
            (activity_id, RDF.type, crminf.I1_Argumentation) in graph,
            (belief_id, RDF.type, crminf.I2_Belief) in graph,
            (proposition_id, RDF.type, crminf.I4_Proposition_Set) in graph,
            (activity_id, crminf.J2_concluded_that, belief_id) in graph,
            (belief_id, crminf.J4_that, proposition_id) in graph,
            (activity_id, RDF.type, crminf.I5_Inference_Making) not in graph,
        ))
        (OUTPUT_DIR / "annotation-graph.ttl").write_text(
            graph.serialize(format="turtle"), encoding="utf-8"
        )

        shapes = Graph().parse(str(SHAPES_PATH), format="turtle")
        conforms, report_graph, report_text = validate(
            data_graph=graph,
            shacl_graph=shapes,
            inference="none",
            abort_on_first=False,
            allow_infos=False,
            allow_warnings=False,
        )
        (OUTPUT_DIR / "shacl-report.ttl").write_text(
            report_graph.serialize(format="turtle"), encoding="utf-8"
        )
        body_nodes = list(graph.objects(annotation_id, oa.hasBody))
        negative_graph = Graph()
        for triple in graph:
            negative_graph.add(triple)
        if body_nodes:
            negative_graph.remove((annotation_id, oa.hasBody, body_nodes[0]))
        negative_conforms, _, negative_report = validate(
            data_graph=negative_graph,
            shacl_graph=shapes,
            inference="none",
            abort_on_first=False,
            allow_infos=False,
            allow_warnings=False,
        )
        shacl_ok = bool(conforms) and not bool(negative_conforms)
        (OUTPUT_DIR / "shacl-negative-report.txt").write_text(
            str(negative_report), encoding="utf-8"
        )

        query = """
            PREFIX oa: <http://www.w3.org/ns/oa#>
            PREFIX prov: <http://www.w3.org/ns/prov#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?annotation ?source ?activity
            WHERE {
              ?annotation a oa:Annotation ;
                          oa:hasBody ?body ;
                          oa:hasTarget ?target ;
                          oa:motivatedBy oa:assessing ;
                          prov:wasGeneratedBy ?activity .
              ?body a oa:TextualBody ; rdf:value ?quote .
              ?target oa:hasSource ?source ; oa:hasSelector ?selector .
              ?selector a oa:TextQuoteSelector ; oa:exact ?quote .
              ?activity prov:used ?source ; prov:generated ?annotation .
            }
        """
        query_rows = list(graph.query(query))
        sparql_ok = any(str(row.annotation) == str(annotation_id) for row in query_rows)

        stages = [
            {"stage": "web_annotation_jsonld_roundtrip",
             "status": "PASS" if roundtrip_ok else "FAIL",
             "triples": len(graph),
             "artifact": "annotation-graph.ttl"},
            {"stage": "rdf_prov_mapping",
             "status": "PASS" if prov_ok else "FAIL",
             "activity": str(activity_id),
             "source": str(source_id),
             "annotation": str(annotation_id)},
            {"stage": "shacl_positive_and_negative",
             "status": "PASS" if shacl_ok else "FAIL",
             "positive_conforms": bool(conforms),
             "negative_conforms": bool(negative_conforms),
             "report": "shacl-report.ttl",
             "negative_report": "shacl-negative-report.txt",
             "details": str(report_text)},
            {"stage": "sparql_query",
             "status": "PASS" if sparql_ok else "FAIL",
             "matching_rows": len(query_rows)},
            {"stage": "crminf_crmsci_mapping",
             "status": "PASS" if crminf_mapping_ok else "FAIL",
             "profile": "igc-f0-crminf-minimal/0.1",
             "crminf_version": "1.2.1",
             "crmsci_version": "3.2",
             "crm_compatible_version": "7.1.3",
             "crminf_terms": ["I1", "I2", "I4", "J2", "J4"],
             "crminf_inference_asserted": False,
             "crmsci_observation_applicable": False,
             "reason": "fixture explicitly contains no measurement or causal evidence"},
        ]
        return stages
    except Exception as exc:
        return [
            {"stage": "web_annotation_jsonld_roundtrip", "status": "FAIL",
             "reason": f"{type(exc).__name__}: {exc}"},
            {"stage": "rdf_prov_mapping", "status": "PENDING",
             "reason": "semantic pipeline stopped before provenance checks"},
            {"stage": "shacl_positive_and_negative", "status": "PENDING",
             "reason": "semantic pipeline stopped before SHACL checks"},
            {"stage": "sparql_query", "status": "PENDING",
             "reason": "semantic pipeline stopped before SPARQL query"},
        ]


def run_openmodelica() -> dict:
    omc = shutil.which("omc")
    docker = shutil.which("docker")
    docker_image = os.environ.get("IGC_OMC_DOCKER_IMAGE")
    use_docker = bool(docker_image)

    if use_docker and not docker:
        return {"stage": "openmodelica_compile_and_simulate", "status": "PENDING",
                "reason": "IGC_OMC_DOCKER_IMAGE is configured but docker is unavailable"}
    if not use_docker and not omc:
        return {"stage": "openmodelica_compile_and_simulate", "status": "PENDING",
                "reason": "omc was not found on PATH and no Docker image was configured"}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prefix = "f0_toy_stock"
    mos_path = OUTPUT_DIR / "simulate.mos"
    if use_docker:
        model_path = "/workspace/" + MODEL_PATH.relative_to(ROOT).as_posix()
        mos_container_path = "/workspace/" + mos_path.relative_to(ROOT).as_posix()
    else:
        model_path = MODEL_PATH.as_posix()
        mos_container_path = str(mos_path)

    mos_path.write_text(
        f"loadFile({json.dumps(model_path)});\n"
        "getErrorString();\n"
        f"simulate(F0ToyStock, startTime=0.0, stopTime=10.0, numberOfIntervals=100, outputFormat=\"csv\", fileNamePrefix=\"{prefix}\");\n"
        "getErrorString();\n",
        encoding="utf-8",
    )
    if use_docker:
        relative_cwd = OUTPUT_DIR.relative_to(ROOT).as_posix()
        command = [
            docker, "run", "--rm", "--volume", f"{ROOT}:/workspace",
            "--workdir", f"/workspace/{relative_cwd}", docker_image,
            "omc", mos_container_path,
        ]
    else:
        command = [omc, str(mos_path)]

    try:
        completed = subprocess.run(
            command, cwd=OUTPUT_DIR, capture_output=True, text=True,
            timeout=600 if use_docker else 120, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        (OUTPUT_DIR / "omc.log").write_text(str(exc), encoding="utf-8")
        return {"stage": "openmodelica_compile_and_simulate", "status": "FAIL",
                "reason": "OpenModelica compilation/simulation timed out"}
    except OSError as exc:
        (OUTPUT_DIR / "omc.log").write_text(str(exc), encoding="utf-8")
        return {"stage": "openmodelica_compile_and_simulate", "status": "FAIL",
                "reason": "failed to launch OpenModelica command"}

    log = completed.stdout + "\n--- STDERR ---\n" + completed.stderr
    (OUTPUT_DIR / "omc.log").write_text(log, encoding="utf-8")
    csv_path = OUTPUT_DIR / f"{prefix}_res.csv"
    errors = "Error:" in log
    if completed.returncode != 0 or errors or not csv_path.is_file():
        return {"stage": "openmodelica_compile_and_simulate", "status": "FAIL",
                "reason": "omc did not produce a successful result CSV",
                "return_code": completed.returncode, "log": "omc.log"}
    return {"stage": "openmodelica_compile_and_simulate", "status": "PASS",
            "engine": "Docker image" if use_docker else "PATH executable",
            "engine_version": docker_image if use_docker else None,
            "model": str(MODEL_PATH.relative_to(ROOT)), "log": "omc.log",
            "csv": str(csv_path.relative_to(ROOT))}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stages, annotation = source_and_annotation()
    if annotation:
        (OUTPUT_DIR / "annotation-draft.json").write_text(
            json.dumps(annotation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        stages.extend(run_semantic_pipeline(annotation))
    else:
        stages.extend(_pending_semantic_stages("synthetic annotation could not be created"))

    stages.extend([
        {"stage": "atms_reasoning", "status": "PENDING",
         "reason": "no ATMS implementation selected or installed"},
        {"stage": "system_model_candidate_and_handoff", "status": "STUB",
         "reason": "candidate is a labeled contract stub; no candidate is promoted",
         "stub_artifact": str(CANDIDATE_PATH.relative_to(ROOT))},
        run_openmodelica(),
        {"stage": "cloudflare_d1_r2_persistence", "status": "NOT_RUN",
         "reason": "cloud resources are out of scope for this synthetic spike"},
    ])
    report = {
        "schema": "igc-f0-spike-report/0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status(stages),
        "claim": "Synthetic wiring probe only; not evidence about a real system.",
        "stages": stages,
    }
    report_path = OUTPUT_DIR / "run.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "report": str(report_path),
                      "stages": stages}, ensure_ascii=False, indent=2))
    return 0 if report["overall_status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
