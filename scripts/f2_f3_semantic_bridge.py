"""Build candidate support proposals from a provenance-linked RDF/CRMinf graph."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, URIRef


BASE = "https://example.invalid/igc/"
OA = Namespace("http://www.w3.org/ns/oa#")
PROV = Namespace("http://www.w3.org/ns/prov#")
CRMINF = Namespace("http://www.cidoc-crm.org/extensions/crminf/")
IGC = Namespace("https://example.invalid/igc/vocab/")


class SemanticBridgeError(ValueError):
    """The source claim or RDF-to-candidate mapping is incomplete."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive_candidate_proposals(
    annotation: dict[str, Any],
    claim: dict[str, Any],
    source_bytes: bytes,
    proposal_set: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Query supported candidate mappings from a synthetic PROV/CRMinf graph.

    The CRMinf graph records an explicit software formalization of a ClaimOccurrence.
    It does not assert an empirical inference or causal truth.
    """
    if claim.get("synthetic") is not True or claim.get("entity_type") != "ClaimOccurrence":
        raise SemanticBridgeError("only a synthetic ClaimOccurrence is accepted")
    if proposal_set.get("claim_id") != claim.get("claim_id"):
        raise SemanticBridgeError("candidate proposals must cite the source claim")
    if not annotation.get("id") or not annotation.get("body", {}).get("id"):
        raise SemanticBridgeError("source annotation is incomplete")
    if claim.get("quote") != annotation["body"].get("value"):
        raise SemanticBridgeError("annotation text does not match the claim quote")
    source_text = source_bytes.decode("utf-8")
    if source_text.count(claim["quote"]) != 1:
        raise SemanticBridgeError("claim quote must resolve exactly once in the source")

    graph = Graph()
    graph.parse(data=json.dumps(annotation), format="json-ld")
    annotation_id = URIRef(annotation["id"])
    body_id = URIRef(annotation["body"]["id"])
    source_id = URIRef(annotation["target"]["source"])
    claim_id = URIRef(BASE + claim["claim_id"])
    anchor_activity = URIRef(BASE + "activity-anchor-001")
    reasoning_activity = URIRef(BASE + "activity-formalize-claim-001")
    belief_id = URIRef(BASE + "belief-synthetic-001")
    proposition_id = URIRef(BASE + "proposition-set-synthetic-001")

    graph.add((annotation_id, RDF.type, OA.Annotation))
    graph.add((body_id, IGC.representsClaim, claim_id))
    graph.add((claim_id, RDF.type, IGC.ClaimOccurrence))
    graph.add((source_id, RDF.type, PROV.Entity))
    graph.add((annotation_id, RDF.type, PROV.Entity))
    graph.add((anchor_activity, RDF.type, PROV.Activity))
    graph.add((anchor_activity, PROV.used, source_id))
    graph.add((anchor_activity, PROV.generated, annotation_id))
    graph.add((annotation_id, PROV.wasGeneratedBy, anchor_activity))

    graph.add((reasoning_activity, RDF.type, CRMINF.I1_Argumentation))
    graph.add((reasoning_activity, RDF.type, PROV.Activity))
    graph.add((reasoning_activity, PROV.used, source_id))
    graph.add((reasoning_activity, PROV.used, annotation_id))
    graph.add((reasoning_activity, PROV.generated, belief_id))
    graph.add((reasoning_activity, PROV.generated, proposition_id))
    graph.add((belief_id, RDF.type, CRMINF.I2_Belief))
    graph.add((belief_id, CRMINF.J4_that, proposition_id))
    graph.add((reasoning_activity, CRMINF.J2_concluded_that, belief_id))
    graph.add((proposition_id, RDF.type, CRMINF.I4_Proposition_Set))
    graph.add((proposition_id, IGC.containsClaim, claim_id))
    graph.add((proposition_id, PROV.wasGeneratedBy, reasoning_activity))

    for proposal in proposal_set.get("proposals", []):
        if proposal.get("claim_id") != claim.get("claim_id"):
            continue
        candidate = URIRef(BASE + "candidate/" + proposal["candidate_id"])
        mechanism = URIRef(BASE + proposal["mechanism_hypothesis_id"])
        graph.add((candidate, RDF.type, IGC.SystemModelCandidate))
        graph.add((candidate, IGC.basedOnClaim, claim_id))
        graph.add((candidate, IGC.mechanismHypothesis, mechanism))
        graph.add((candidate, IGC.candidateId, Literal(proposal["candidate_id"])))
        graph.add((mechanism, IGC.mechanismId, Literal(proposal["mechanism_hypothesis_id"])))
        graph.add((mechanism, IGC.mechanismStatement, Literal(proposal["mechanism_statement"])))
        graph.add((candidate, IGC.parameterOverrides,
                   Literal(json.dumps(proposal.get("parameter_values", {}), sort_keys=True))))
        for assumption_id in proposal.get("assumption_ids", []):
            graph.add((candidate, IGC.requiresAssumption, URIRef(BASE + assumption_id)))

    query = """
        PREFIX oa: <http://www.w3.org/ns/oa#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX crminf: <http://www.cidoc-crm.org/extensions/crminf/>
        PREFIX igc: <https://example.invalid/igc/vocab/>
        SELECT DISTINCT ?candidate_id ?mechanism_id ?statement ?assumption ?parameters
               ?claim ?source ?annotation ?reasoning ?proposition
        WHERE {
          ?annotation a oa:Annotation ;
                      oa:hasBody ?body ;
                      oa:hasTarget ?target ;
                      prov:wasGeneratedBy ?anchor .
          ?body igc:representsClaim ?claim .
          ?target oa:hasSource ?source .
          ?anchor prov:used ?source ; prov:generated ?annotation .
          ?reasoning a crminf:I1_Argumentation ;
                     crminf:J2_concluded_that ?belief ;
                     prov:used ?source, ?annotation ;
                     prov:generated ?proposition .
          ?belief a crminf:I2_Belief ; crminf:J4_that ?proposition .
          ?proposition a crminf:I4_Proposition_Set ; igc:containsClaim ?claim .
          ?candidate a igc:SystemModelCandidate ;
                     igc:basedOnClaim ?claim ;
                     igc:candidateId ?candidate_id ;
                     igc:mechanismHypothesis ?mechanism ;
                     igc:requiresAssumption ?assumption ;
                     igc:parameterOverrides ?parameters .
          ?mechanism igc:mechanismId ?mechanism_id ;
                     igc:mechanismStatement ?statement .
        }
    """
    grouped: dict[str, dict[str, Any]] = {}
    for row in graph.query(query):
        candidate_id = str(row.candidate_id)
        entry = grouped.setdefault(candidate_id, {
            "candidate_id": candidate_id,
            "mechanism_hypothesis_id": str(row.mechanism_id),
            "mechanism_statement": str(row.statement),
            "assumption_ids": set(),
            "parameter_values": json.loads(str(row.parameters)),
        })
        entry["assumption_ids"].add(str(row.assumption).removeprefix(BASE))
    proposals = []
    for item in grouped.values():
        item["assumption_ids"] = sorted(item["assumption_ids"])
        proposals.append(item)
    proposals.sort(key=lambda item: item["candidate_id"])
    if not proposals:
        raise SemanticBridgeError("SPARQL found no candidate supported by the source proposition")

    graph_bytes = graph.serialize(format="turtle").encode("utf-8")
    evidence = {
        "schema": "igc-semantic-candidate-evidence/0.1",
        "synthetic": True,
        "query_name": "claim-to-candidate-support/0.1",
        "claim_id": claim["claim_id"],
        "source_annotation_id": str(annotation_id),
        "source_id": str(source_id),
        "reasoning_activity_id": str(reasoning_activity),
        "proposition_set_id": str(proposition_id),
        "source_sha256": _sha256(source_bytes),
        "claim_sha256": _sha256(json.dumps(claim, sort_keys=True).encode("utf-8")),
        "rdf_graph_sha256": _sha256(graph_bytes),
        "candidate_catalog_sha256": _sha256(json.dumps(proposal_set, sort_keys=True).encode("utf-8")),
        "query_sha256": _sha256(query.encode("utf-8")),
        "semantic_bridge_sha256": _sha256(Path(__file__).read_bytes()),
        "rdf_triple_count": len(graph),
        "crminf_terms": ["I1_Argumentation", "I2_Belief", "I4_Proposition_Set", "J2_concluded_that", "J4_that"],
        "empirical_inference_asserted": False,
        "causal_claim_asserted": False,
        "matching_candidate_ids": [item["candidate_id"] for item in proposals],
        "interpretation": "Synthetic mapping query only; no empirical or causal inference.",
    }
    return {"assumptions": proposal_set["assumptions"],
            "nogoods": proposal_set["nogoods"],
            "proposals": proposals,
            "semantic_evidence": evidence}, graph_bytes.decode("utf-8")
