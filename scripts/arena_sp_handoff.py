"""Arena independent S/P handoff: seal provider drafts before molecular execution.

Never attribute mock suggestions to real inference. ATMS admission precedes solver;
P is a typed judgement only, not a causal or numerical prediction. The handoff
contains NO D submissions, D trajectories or hidden-world outputs.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

from .arena_round import (SCHEMA as ROUND_SCHEMA, COST_UNITS, RoundError,
                          hash_obj, no_hidden, validate_submission, exclusive_json)
from .arena_sp_producers import (SCHEMA as PROVIDER_SCHEMA, ProviderError,
                                 _validate_schedule)
from .fm_b2_atms_candidate_reasoning import apply_supports

SCHEMA = "igc-arena-sp-handoff/0.1"
ORIGINS = {"MOCK_SYNTHETIC", "CLOUDFLARE_VERIFIED_RUN"}


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ProviderError(message)


def verify_draft(draft: dict, package: dict, catalog: dict,
                 views: dict, *, origin: str, provenance: dict | None) -> None:
    _validate_schedule(package)
    ensure(origin in ORIGINS, "unknown S/P inference provenance")
    ensure(draft.get("schema") == PROVIDER_SCHEMA and
           draft.get("status") == "PROVIDER_DRAFTS_NOT_LANE_SUBMISSIONS",
           "only normalized provider drafts accepted")
    clone = dict(draft)
    provided_hash = clone.pop("output_hash", None)
    ensure(provided_hash == hash_obj(clone), "tampered provider draft")
    manifest = package["manifest"]
    ensure(draft.get("round_id") == manifest["round_id"], "wrong round")
    ensure(draft.get("requests_hash") == manifest["requests_hash"],
           "draft is unrelated to frozen provider requests")
    ensure(draft.get("claims_of_truth") is False and
           draft.get("predictions_generated") is False,
           "provider draft cannot declare truth or numeric trajectory")
    ensure(hash_obj(catalog) == manifest["catalog_hash"], "catalog mismatch")
    ensure(set(views) >= {"S", "P"}, "missing lane view")
    for lane in ("S","P"):
        ensure(views[lane].get("view_hash") == manifest["view_hashes"][lane],
               "draft not linked to same lane snapshot")
        ensure(draft.get(lane,{}).get("lane") == lane,
               "cross-lane provider result")
    no_hidden(draft)
    if origin == "CLOUDFLARE_VERIFIED_RUN":
        ensure(isinstance(provenance, dict) and
               provenance.get("schema") == "igc-arena-provider-receipt/0.1" and
               provenance.get("requests_hash") == manifest["requests_hash"] and
               provenance.get("response_hashes") == draft["response_hashes"] and
               provenance.get("calls_completed") == 3 and
               provenance.get("mock") is False,
               "real provider run requires independently sealed response receipt")
    else:
        ensure(provenance is None, "mock fixture cannot present a provider receipt")


def seal_handoff(draft: dict, package: dict, catalog: dict, views: dict,
                 composed: dict, support_plan: dict,
                 *, origin: str = "MOCK_SYNTHETIC",
                 provenance: dict | None = None) -> dict:
    """Admit S selections through existing FM-B2 ATMS; seal P with source links."""
    verify_draft(draft, package, catalog, views, origin=origin, provenance=provenance)
    selected_catalog = {x["candidate_id"] for x in catalog["candidates"]}
    composed_ids = {x["id"] for x in composed["candidates"]}
    ensure(selected_catalog == composed_ids,
           "catalog must match independently composed candidate universe")
    selection = apply_supports(composed, support_plan)
    admitted = {x["candidate_id"]: x for x in selection["selected"]}
    rejected = {x["candidate_id"]: x for x in selection["rejected"]}
    chosen = draft["S"].get("selected_candidate_ids")
    ensure(isinstance(chosen,list) and len(chosen)==len(set(chosen)),
           "invalid S candidate list")
    ensure(set(chosen) <= selected_catalog, "S introduced candidate not in catalog")
    # Never quietly convert a logically inconsistent candidate into a runnable one.
    forbidden = sorted(set(chosen) & set(rejected))
    ensure(not forbidden, "ATMS_REJECTED_CANDIDATE:" + ",".join(forbidden))
    frozen = {
        "schema": SCHEMA, "round_id": draft["round_id"], "origin": origin,
        "synthetic": True, "eligible_for_empirical_scoring": False,
        "provider_draft_hash": draft["output_hash"],
        "provider_package_hash": hash_obj(package),
        "catalog_hash": hash_obj(catalog),
        "atms_support_plan_hash": hash_obj(support_plan),
        "composed_candidates_hash": hash_obj(composed),
        "atms_selection_hash": hash_obj(selection),
        "views": {x:views[x]["view_hash"] for x in ("S","P")},
        "S": {"selection": list(chosen),
              "admitted": [admitted[x] for x in chosen],
              "rejected_by_atms": sorted(rejected),
              "rationale": draft["S"]["rationale"],
              "falsifier": draft["S"]["falsifier"],
              "next_test": draft["S"]["next_test"],
              "unknowns": draft["S"]["unknowns"],
              "state": "STRUCTURE_SELECTED_NOT_SIMULATED" if chosen else
                       "ABSTAINED_NO_STRUCTURE"},
        "P": {"assessment": draft["P"]["support_assessment"],
              "confidence": draft["P"]["confidence"],
              "numeric_crosscheck": draft["P"]["numeric_crosscheck"],
              "state": "JUDGEMENT_NOT_TOPOLOGY"},
        "provenance": provenance
    }
    no_hidden(frozen)
    frozen["handoff_hash"] = hash_obj(frozen)
    return frozen


def verify_handoff(seal: dict, draft: dict, package: dict, catalog: dict, views: dict,
                   composed: dict, support_plan: dict) -> None:
    copy = dict(seal)
    integrity = copy.pop("handoff_hash", None)
    ensure(integrity == hash_obj(copy), "HANDOFF_TAMPERED")
    expect = seal_handoff(draft,package,catalog,views,composed,support_plan,
                          origin=seal["origin"],provenance=seal.get("provenance"))
    ensure(expect == seal, "HANDOFF_DEPENDENCY_MISMATCH")


def p_submission(seal: dict, view: dict, *,
                 tokens: int = 0, human_minutes: float = 0,
                 actual_provider_evidence: bool = False) -> dict:
    """Type P assessment; no topologies, no numeric trajectory or fake token usage."""
    ensure(view["lane"] == "P" and view["view_hash"] == seal["views"]["P"],
           "P cross-lane handoff")
    ensure((seal["origin"] == "CLOUDFLARE_VERIFIED_RUN") == actual_provider_evidence,
           "P cannot impersonate real provider inference")
    ensure(type(tokens) is int and tokens >= 0 and
           type(human_minutes) in (int,float) and human_minutes >= 0,
           "P cost values must be explicitly measured non-negative")
    # Mock is only for contract testing, not for a real Arena evaluation.
    cost = {key: 0 for key in COST_UNITS}
    cost.update(llm_calls=2, tokens=tokens, human_minutes=human_minutes)
    proposal = {
        "candidate_id": "P-CLEF-CLAIRIC-V0", "kind": "assessment",
        "judgement": seal["P"]["assessment"],
        "confidence": seal["P"]["confidence"],
        "arithmetic_crosscheck": seal["P"]["numeric_crosscheck"],
        "qualifier": "Conditional assessment; cannot establish causal truth.",
        "handoff_hash": seal["handoff_hash"]
    }
    response = {"schema": ROUND_SCHEMA, "round_id": view["round_id"],
                "lane": "P", "view_hash": view["view_hash"],
                "status": "SUBMITTED" if actual_provider_evidence else "ABSTAINED",
                "producer": "clef-clairic-typed-gate",
                "proposals": [proposal] if actual_provider_evidence else [],
                "unknowns": ["MOCK_ONLY_NOT_A_PROVIDER_SUBMISSION"] if not actual_provider_evidence else
                            ["Causal mechanism not proven; parameter identifiability unresolved"],
                "objections": ["Clairic arithmetic discrepancy"] if not
                              seal["P"]["numeric_crosscheck"]["valid_arithmetic"] else [],
                "cost": cost if actual_provider_evidence else {key:0 for key in COST_UNITS}}
    validate_submission(response,view)
    return response


def simulation_selection(seal:dict, composed:dict, support_plan:dict) -> dict:
    """Read sealed S structure only; never read D simulation output."""
    source = apply_supports(composed,support_plan)
    ensure(seal.get("atms_selection_hash")==hash_obj(source) and
           seal.get("composed_candidates_hash")==hash_obj(composed) and
           seal.get("atms_support_plan_hash")==hash_obj(support_plan),
           "S simulation inputs changed after selection")
    allowed = {x["candidate_id"]:x for x in source["selected"]}
    chosen = seal["S"]["selection"]
    ensure(set(chosen)<=set(allowed), "ATMS admission changed after handoff")
    if not chosen:
        return {"status":"ABSTAINED_NO_SIMULATION", "selected":[],
                "rejected":source["rejected"], "candidate_ids":source["candidate_ids"]}
    return {"status":"ADMITTED_FOR_INDEPENDENT_SIMULATION",
            "selected":[allowed[x] for x in chosen],
            "rejected":source["rejected"],
            "candidate_ids":source["candidate_ids"]}


def main() -> int:
    p=argparse.ArgumentParser(description="S/P ATMS handoff from sealed provider drafts")
    for key in ("draft","package","catalog","views-dir","composed","support-plan","out"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--origin",choices=sorted(ORIGINS),default="MOCK_SYNTHETIC")
    p.add_argument("--receipt",type=Path)
    args=p.parse_args()
    read=lambda path: json.loads(path.read_text(encoding="utf-8"))
    seal=seal_handoff(read(args.draft),read(args.package),read(args.catalog),
                      {l:read(args.views_dir/(l+".json")) for l in ("S","P")},
                      read(args.composed),read(args.support_plan),
                      origin=args.origin,provenance=read(args.receipt) if args.receipt else None)
    exclusive_json(args.out,seal)
    print(json.dumps({"status":"S_P_HANDOFF_LOCKED_NOT_EVALUATED",
                      "origin":seal["origin"],"s_candidates":len(seal["S"]["admitted"]),
                      "hash":seal["handoff_hash"]}))


if __name__=="__main__":
    main()
