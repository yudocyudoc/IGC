"""S-only provider path: no P dependency and no accidental proof claims."""
import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_round import hash_obj, prepare
from scripts.arena_sp_producers import ProviderError, build_requests
from scripts.arena_s_real import (
    AUTHORIZATION, capture_s, seal_s_only, verify_s_capture,
    verify_s_only_seal, TEST_ORIGIN
)

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/name).read_text(encoding="utf-8"))
CID=lambda n: f"urn:igc:candidate:CS-0{n}"


class MockResponse:
    def __init__(self, body): self.body=body
    def __enter__(self): return io.BytesIO(json.dumps(self.body).encode())
    def __exit__(self, *args): return False


def fixture():
    spec=read("data/synthetic/arena_v0_b3_round_spec.json")
    primary=read("data/synthetic/arena_v0_b3_primary.json")
    catalog=read("data/synthetic/arena_sp_public_catalog.json")
    supports=read("data/synthetic/fm_b3_dynamic_supports.json")
    views=prepare(spec,primary)
    package=build_requests(views,spec,catalog)
    structures=[{"id":f"urn:igc:structure:CS-0{n}@0.2",
                 "structural_hash":"sha256:"+str(n)*64} for n in (1,2,3)]
    composed={"structures":structures,"candidates":[
        {"id":CID(n),"structure_revision_id":structures[n-1]["id"]}
        for n in (1,2,3)]}
    response={"success":True,"result":{"response":json.dumps({
        "selected_candidate_ids":[CID(2)],
        "rationale":"Cannot establish causal truth",
        "falsifier":"Discriminating input pulse",
        "unknowns":["Parameter uncertainty"],
        "next_test":"Perform a controlled pulse"}),
        "usage":{"prompt_tokens":40,"completion_tokens":15}}}
    return package,catalog,views,supports,composed,response


class SingleProviderTests(unittest.TestCase):
    def setUp(self):
        (self.package,self.catalog,self.views,self.supports,
         self.composed,self.response)=fixture()
        self.env={"CLOUDFLARE_ACCOUNT_ID":"a"*32,
                  "CLOUDFLARE_API_TOKEN":"TEST_SECRET"}

    def captured(self, out):
        called=[]
        def sender(request,timeout):
            called.append(json.loads(request.data))
            return MockResponse(self.response)
        receipt=capture_s(
            self.package,self.catalog,authorization=AUTHORIZATION,
            out_dir=out,run_ref="test:mock",env=self.env,
            sender=sender,capture_method="INJECTED_TEST_SENDER")
        self.assertEqual(len(called),1)
        self.assertEqual(called[0],self.package["requests"][0]["body"])
        self.assertEqual(receipt["calls_completed"],1)
        self.assertTrue(receipt["mock"])
        self.assertEqual(receipt["usage"]["token_total"],55)
        response=json.loads((out/"response.json").read_text())
        draft=json.loads((out/"s-draft.json").read_text())
        verify_s_capture(self.package,self.catalog,response,draft,receipt)
        return response,draft,receipt

    def test_one_s_no_clef_or_clairic_and_seal(self):
        with TemporaryDirectory() as tmp:
            response,draft,receipt=self.captured(Path(tmp)/"run")
            seal=seal_s_only(self.package,self.catalog,
                {"S":self.views["S"]},self.composed,self.supports,
                response,draft,receipt)
            self.assertEqual(seal["origin"],TEST_ORIGIN)
            self.assertEqual(seal["S"]["selection"],[CID(2)])
            self.assertFalse(seal["eligible_for_empirical_scoring"])
            verify_s_only_seal(seal,self.package,self.catalog,
                {"S":self.views["S"]},self.composed,self.supports,
                response,draft,receipt)
            with self.assertRaisesRegex(ProviderError,"MOCK_IS_NOT_REAL"):
                verify_s_capture(self.package,self.catalog,
                    response,draft,receipt,require_live=True)

    def test_reject_invented_and_atms_rejected(self):
        with TemporaryDirectory() as tmp:
            r=copy.deepcopy(self.response)
            r["result"]["response"]=json.dumps({
                "selected_candidate_ids":[CID(3)],"rationale":"test",
                "falsifier":"test", "unknowns":[], "next_test":"test"})
            self.response=r
            response,draft,receipt=self.captured(Path(tmp)/"run")
            with self.assertRaisesRegex(ProviderError,"ATMS_REJECTED_CANDIDATE"):
                seal_s_only(self.package,self.catalog,{"S":self.views["S"]},
                            self.composed,self.supports,response,draft,receipt)

    def test_invalid_draft_and_receipt_rejected(self):
        with TemporaryDirectory() as tmp:
            response,draft,receipt=self.captured(Path(tmp)/"run")
            bad=copy.deepcopy(draft)
            bad["selected_candidate_ids"]=[CID(1)]
            with self.assertRaisesRegex(ProviderError,"S_RESPONSE_PROVENANCE_MISMATCH"):
                verify_s_capture(self.package,self.catalog,response,bad,receipt)
            tampered=copy.deepcopy(receipt)
            tampered["usage"]["token_total"]=0
            with self.assertRaisesRegex(ProviderError,"S_RECEIPT_TAMPERED"):
                verify_s_capture(self.package,self.catalog,response,draft,tampered)

    def test_real_claim_cannot_simulate_without_calibration(self):
        # This locally fabricated receipt illustrates why capture is NOT
        # independent attestation. The downstream fit gate must still close.
        from scripts.arena_sp_simulation import prepare_s
        with TemporaryDirectory() as tmp:
            response,draft,receipt=self.captured(Path(tmp)/"run")
            receipt["capture_method"]="PYTHON_URLLIB"
            receipt["mock"]=False
            receipt["receipt_hash"]=hash_obj({
                k:v for k,v in receipt.items() if k!="receipt_hash"})
            seal=seal_s_only(self.package,self.catalog,
                {"S":self.views["S"]},self.composed,self.supports,
                response,draft,receipt)
            plan=read("data/synthetic/fm_b3_dynamic_plan.json")
            with self.assertRaisesRegex(ProviderError,
                                       "S_REAL_REQUIRES_CALIBRATED_PARAMETERS"):
                prepare_s(seal,draft,self.package,self.catalog,
                    {"S":self.views["S"]},self.composed,self.supports,
                    plan,Path(tmp)/"solver",
                    s_capture={"response":response,"draft":draft,"receipt":receipt})

    def test_empty_selection_remains_explicit_abstention(self):
        with TemporaryDirectory() as tmp:
            response=copy.deepcopy(self.response)
            answer=json.loads(response["result"]["response"])
            answer["selected_candidate_ids"]=[]
            response["result"]["response"]=json.dumps(answer)
            self.response=response
            raw,draft,receipt=self.captured(Path(tmp)/"run")
            seal=seal_s_only(self.package,self.catalog,
                {"S":self.views["S"]},self.composed,self.supports,
                raw,draft,receipt)
            self.assertEqual(seal["S"]["state"],"ABSTAINED_NO_STRUCTURE")
            self.assertEqual(seal["S"]["selection"],[])

    def test_zero_calls_without_authorization_and_no_replay(self):
        called=[]
        def sender(request,timeout):
            called.append(1)
            return MockResponse(self.response)
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/"run"
            with self.assertRaisesRegex(ProviderError,"NO_INFERENCE"):
                capture_s(self.package,self.catalog,authorization="NO_INFERENCE",
                    out_dir=out,run_ref="x",env=self.env,
                    sender=sender,capture_method="INJECTED_TEST_SENDER")
            self.assertEqual(called,[])
            self.captured(out)
            with self.assertRaises(FileExistsError):
                capture_s(self.package,self.catalog,authorization=AUTHORIZATION,
                    out_dir=out,run_ref="x",env=self.env,
                    sender=sender,capture_method="INJECTED_TEST_SENDER")
            self.assertEqual(called,[])


if __name__ == "__main__":
    unittest.main()
