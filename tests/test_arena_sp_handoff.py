"""Synthetic contracts for source-independent S/P handoff and ATMS gating."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest

from scripts.arena_round import prepare, hash_obj, validate_submission
from scripts.arena_sp_producers import build_requests, parse_responses, ProviderError
from scripts.arena_sp_capture import build_receipt,usage_of
from scripts.arena_sp_handoff import (seal_handoff, verify_handoff,
                                      simulation_selection, p_submission)
ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/name).read_text(encoding="utf-8"))
CID=lambda n:"urn:igc:candidate:CS-0"+str(n)


def synthetic_molecular_bundle():
    candidates=[]
    structures=[]
    for n in (1,2,3):
        sid=f"urn:igc:structure:CS-0{n}@0.2"
        candidates.append({"id":CID(n),"structure_revision_id":sid})
        structures.append({"id":sid,"structural_hash":"sha256:"+(str(n)*64)})
    return {"candidates":candidates,"structures":structures}


def fixture():
    spec=read("data/synthetic/arena_v0_b3_round_spec.json")
    primary=read("data/synthetic/arena_v0_b3_primary.json")
    catalog=read("data/synthetic/arena_sp_public_catalog.json")
    supports=read("data/synthetic/fm_b3_dynamic_supports.json")
    views=prepare(spec,primary)
    package=build_requests(views,spec,catalog)
    composed=synthetic_molecular_bundle()
    def fake(selected):
        return {"S_GLM":{"success":True,"result":{"response":json.dumps({
            "selected_candidate_ids":selected,"rationale":"Candidate is possible, not proven",
            "falsifier":"New visible experimental perturbation",
            "unknowns":["Parameter range"],"next_test":"Pulse arrivals"
        })}},
        "P_CLEF":{"success":True,"result":{"answers":{"assessment":{
            "choice":"INSUFFICIENT","probabilities":{
                "INSUFFICIENT":.85,"CS_01":.05,"CS_02":.05,"EQUIVALENT":.05}}}}},
        "P_CLAIRIC":{"success":True,"result":{"answers":{
            "observed_increment":{"value":2.0}}}}}
    return spec,views,catalog,supports,package,composed,fake


class HandoffTests(unittest.TestCase):
    def setUp(self):
        (self.spec,self.views,self.catalog,self.supports,self.pkg,
         self.composed,self.fake)=fixture()
        self.draft=parse_responses(self.pkg,self.fake([CID(2)]),self.catalog)

    def seal(self, draft=None):
        return seal_handoff(draft or self.draft,self.pkg,self.catalog,self.views,
                            self.composed,self.supports,origin="MOCK_SYNTHETIC")

    def test_seal_before_solver_contains_one_admissible_structure(self):
        s=self.seal()
        self.assertEqual(s["origin"],"MOCK_SYNTHETIC")
        self.assertFalse(s["eligible_for_empirical_scoring"])
        self.assertEqual(s["S"]["selection"],[CID(2)])
        self.assertEqual(s["S"]["admitted"][0]["candidate_id"],CID(2))
        self.assertIn(CID(3),s["S"]["rejected_by_atms"])
        self.assertEqual(simulation_selection(s,self.composed,self.supports)["status"],
                         "ADMITTED_FOR_INDEPENDENT_SIMULATION")
        self.assertEqual([x["candidate_id"] for x in
                          simulation_selection(s,self.composed,self.supports)["selected"]],
                         [CID(2)])

    def test_atms_rejected_structure_cannot_be_simulated(self):
        rejected=parse_responses(self.pkg,self.fake([CID(3)]),self.catalog)
        with self.assertRaisesRegex(ProviderError,"ATMS_REJECTED_CANDIDATE"):
            self.seal(rejected)

    def test_no_structure_is_explicit_abstention(self):
        empty=parse_responses(self.pkg,self.fake([]),self.catalog)
        s=self.seal(empty)
        self.assertEqual(s["S"]["state"],"ABSTAINED_NO_STRUCTURE")
        self.assertEqual(simulation_selection(s,self.composed,self.supports)["selected"],[])

    def test_mock_judgement_never_becomes_actual_p_submission(self):
        s=self.seal()
        response=p_submission(s,self.views["P"])
        validate_submission(response,self.views["P"])
        self.assertEqual(response["status"],"ABSTAINED")
        self.assertEqual(response["proposals"],[])

    def test_mock_origin_cannot_present_real_receipt(self):
        with self.assertRaisesRegex(ProviderError,"mock fixture"):
            seal_handoff(self.draft,self.pkg,self.catalog,self.views,
                         self.composed,self.supports,
                         origin="MOCK_SYNTHETIC",provenance={"mock":False})

    def test_real_origin_requires_provider_receipt(self):
        with self.assertRaisesRegex(ProviderError,"original raw responses and audited receipt"):
            seal_handoff(self.draft,self.pkg,self.catalog,self.views,
                         self.composed,self.supports,
                         origin="CLOUDFLARE_VERIFIED_RUN")

    def captured_fixture(self, with_usage=True):
        response=self.fake([CID(2)])
        if with_usage:
            response["S_GLM"]["result"]["usage"]={
                "prompt_tokens":60,"completion_tokens":20}
            response["P_CLEF"]["result"]["usage"]={
                "input_tokens":20,"output_tokens":10}
            response["P_CLAIRIC"]["result"]["usage"]={
                "total_tokens":5}
        observations=[]
        for i,name in enumerate(("S_GLM","P_CLEF","P_CLAIRIC")):
            observations.append({
                "sequence":i+1,"model_name":name,
                "response_hash":hash_obj(response[name]),
                "duration_ms":12.0,
                "usage":usage_of(response[name])})
        receipt=build_receipt(self.pkg,response,observations,
                              run_ref="local-synthetic-no-network",
                              capture_method="PYTHON_URLLIB")
        draft=parse_responses(self.pkg,response,self.catalog)
        return draft,response,receipt

    def test_real_handoff_requires_original_responses(self):
        draft,responses,receipt=self.captured_fixture()
        with self.assertRaisesRegex(ProviderError,"original raw responses"):
            seal_handoff(draft,self.pkg,self.catalog,self.views,
                         self.composed,self.supports,
                         origin="CLOUDFLARE_VERIFIED_RUN",provenance=receipt)

    def test_local_capture_linkage_and_p_tokens(self):
        draft,responses,receipt=self.captured_fixture()
        seal=seal_handoff(draft,self.pkg,self.catalog,self.views,
                          self.composed,self.supports,
                          origin="CLOUDFLARE_VERIFIED_RUN",
                          provenance=receipt,responses=responses)
        self.assertFalse(seal["eligible_for_empirical_scoring"])
        self.assertEqual(seal["provider_attestation"],
                         "LOCAL_CAPTURE_ONLY_NOT_INDEPENDENT")
        p=p_submission(seal,self.views["P"],actual_provider_evidence=True)
        self.assertEqual(p["status"],"SUBMITTED")
        self.assertEqual(p["cost"]["llm_calls"],2)
        self.assertEqual(p["cost"]["tokens"],35)
        with self.assertRaisesRegex(ProviderError,"differs from provider"):
            p_submission(seal,self.views["P"],actual_provider_evidence=True,
                         tokens=0)

    def test_real_p_abstains_from_submission_if_token_usage_unavailable(self):
        draft,responses,receipt=self.captured_fixture(with_usage=False)
        seal=seal_handoff(draft,self.pkg,self.catalog,self.views,
                          self.composed,self.supports,
                          origin="CLOUDFLARE_VERIFIED_RUN",
                          provenance=receipt,responses=responses)
        with self.assertRaisesRegex(ProviderError,"P_TOKEN_USAGE_NOT_OBSERVABLE"):
            p_submission(seal,self.views["P"],actual_provider_evidence=True)

    def test_provider_receipt_must_match_raw_reply_bytes(self):
        draft,responses,receipt=self.captured_fixture()
        tampered=copy.deepcopy(responses)
        tampered["P_CLAIRIC"]["result"]["answers"]["observed_increment"]["value"]=999
        with self.assertRaisesRegex(ProviderError,"CAPTURE_MISMATCH"):
            seal_handoff(draft,self.pkg,self.catalog,self.views,
                         self.composed,self.supports,
                         origin="CLOUDFLARE_VERIFIED_RUN",
                         provenance=receipt,responses=tampered)

    def test_change_in_support_plan_after_seal_fails(self):
        s=self.seal()
        supports=copy.deepcopy(self.supports)
        supports["nogoods"].append([
            "urn:igc:assumption:CS-02-mechanism",
            "urn:igc:assumption:CS-02-route-a"])
        with self.assertRaisesRegex(ProviderError,"simulation inputs changed"):
            simulation_selection(s,self.composed,supports)

    def test_handoff_tampering_rejected(self):
        s=self.seal()
        s["S"]["rationale"]="retrospective interpretation"
        with self.assertRaisesRegex(ProviderError,"HANDOFF_TAMPERED"):
            verify_handoff(s,self.draft,self.pkg,self.catalog,self.views,
                           self.composed,self.supports)

    def test_draft_tampering_rejected(self):
        corrupted=copy.deepcopy(self.draft)
        corrupted["S"]["selected_candidate_ids"]=[CID(1)]
        with self.assertRaisesRegex(ProviderError,"tampered provider draft"):
            self.seal(corrupted)

    def test_p_does_not_produce_modelica_topology_or_predicted_series(self):
        s=self.seal()
        result=p_submission(s,self.views["P"])
        self.assertNotIn("predictions",json.dumps(result))
        self.assertNotIn("modelica",json.dumps(result).lower())

    def test_candidate_catalog_must_match_actual_molecular_universe(self):
        altered=copy.deepcopy(self.composed)
        altered["candidates"].pop()
        with self.assertRaisesRegex(ProviderError,"catalog must match"):
            seal_handoff(self.draft,self.pkg,self.catalog,self.views,
                         altered,self.supports)

    def test_d_or_p_cannot_use_s_view(self):
        changed=copy.deepcopy(self.views)
        changed["P"]=copy.deepcopy(self.views["S"])
        with self.assertRaisesRegex(ProviderError,"draft not linked"):
            seal_handoff(self.draft,self.pkg,self.catalog,changed,
                         self.composed,self.supports)

    def test_rejected_only_affects_selected_candidate(self):
        s=self.seal()
        kept=simulation_selection(s,self.composed,self.supports)
        self.assertEqual(kept["selected"][0]["minimal_supporting_environments"],
                         [["urn:igc:assumption:CS-02-mechanism",
                           "urn:igc:assumption:CS-02-route-a"],
                          ["urn:igc:assumption:CS-02-mechanism",
                           "urn:igc:assumption:CS-02-route-b"]])


if __name__=="__main__":
    unittest.main()
