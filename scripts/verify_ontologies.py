"""Verify versioned official ontology snapshots and one bounded entailment path."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from rdflib import Graph, RDF, RDFS, URIRef
from owlrl import DeductiveClosure, OWLRL_Semantics


def fetch(source: str) -> bytes:
    request = Request(source, headers={"User-Agent": "IGC-ontology-inventory/0.1"})
    with urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"{source}: HTTP {response.status}")
        return response.read()


def parse_graph(raw: bytes, syntax: str) -> Graph:
    graph = Graph()
    graph.parse(data=raw, format=syntax)
    if len(graph) == 0:
        raise ValueError("ontology graph parsed as empty")
    return graph


def verify(manifest_path: Path) -> tuple[dict, list[dict]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    merged = Graph()
    reports = []
    packages = []
    for entry in manifest["ontologies"]:
        raw = fetch(entry["source"])
        digest = hashlib.sha256(raw).hexdigest()
        expected = entry.get("sha256")
        if expected and digest != expected:
            raise ValueError(
                f"{entry['name']} {entry['version']} SHA-256 mismatch: "
                f"expected {expected}, got {digest}"
            )
        graph = parse_graph(raw, entry["format"])
        missing = [
            term for term in entry["required_terms"]
            if not any(URIRef(term) in triple for triple in graph)
        ]
        if missing:
            raise ValueError(f"{entry['name']}: required terms missing: {missing}")
        merged += graph
        reports.append({
            "name": entry["name"],
            "version": entry["version"],
            "source": entry["source"],
            "sha256": digest,
            "triples": len(graph),
            "required_terms": len(entry["required_terms"]),
            "status": "PARSE_AND_TERM_CHECK_PASS",
        })
        packages.append({
            "name": entry["name"],
            "version": entry["version"],
            "scope": "official-ontology-graph",
            "purl": f"pkg:generic/{entry['name'].lower().replace(' ', '-') }@{entry['version']}",
            "downloadLocation": entry["source"],
            "checksums": [{"algorithm": "SHA256", "checksumValue": digest}],
            "comment": "Official versioned graph downloaded in CI; full import closure and license review are not asserted.",
        })

    # CRMsci's published mapping says CRM E16 Measurement is a CRMsci S4
    # Single Observation. Test that the pinned graphs entail this class typing.
    sample = URIRef("https://igc.example/ontology-check/sample")
    crm_measurement = URIRef("http://www.cidoc-crm.org/cidoc-crm/E16_Measurement")
    crmsci_observation = URIRef(
        "http://www.cidoc-crm.org/extensions/crmsci/S4_Single_Observation"
    )
    merged.add((sample, RDF.type, crm_measurement))
    DeductiveClosure(OWLRL_Semantics).expand(merged)
    inferred = (sample, RDF.type, crmsci_observation) in merged
    if not inferred:
        raise ValueError("bounded entailment failed: E16 Measurement did not entail S4 Single Observation")
    report = {
        "manifest": str(manifest_path).replace("\\", "/"),
        "graphs": reports,
        "combined_triples_after_owl_rl": len(merged),
        "entailment": {
            "input_type": str(crm_measurement),
            "inferred_type": str(crmsci_observation),
            "status": "PASS",
        },
        "scope_limitations": [
            "Only the four manifest graphs are downloaded; owl:imports closure is not expanded.",
            "OWL-RL closure and one declared cross-model mapping do not imply empirical validity.",
            "License review remains deferred to the final inventory step.",
        ],
    }
    return report, packages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--packages", type=Path, required=True)
    args = parser.parse_args()
    report, packages = verify(args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.packages.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.packages.write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
