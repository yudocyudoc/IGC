"""Real Cloudflare request contract tests with mocked provider; zero inference cost."""
import copy
import io
import json
from pathlib import Path
import unittest

from scripts.arena_round import prepare, RoundError, hash_obj
from scripts.arena_sp_producers import (
    AUTHORIZATION, CHOICES, MODELS, ORDER, ProviderError,
    build_requests, parse_responses, run_authorized
)

ROOT = Path(__file__).resolve().parents[1]
READ = lambda path: json.loads((ROOT/path).read_text(encoding="utf-8"))


def bundle():
    spec = READ("data/synthetic/arena_v0_b3_round_spec.json")
    primary = READ("data/synthetic/arena_v0_b3_primary.json")
    catalog = READ("data/synthetic/arena_sp_public_catalog.json")
    views = prepare(spec, primary)
    return spec, views, catalog


def raw_results(pkg):
    candidate = "urn:igc:candidate:CS-02"
    s = {"selected_candidate_ids":[candidate],
         "rationale":"Two serial service stages are structurally possible, not proven",
         "falsifier":"Observed time response rejects every parameter setting",
         "unknowns":["Throughput not identified"],
         "next_test":"Perturb arrival flow and measure completion lags"}
    p = {k: 0.05 for k in CHOICES}
    p["INSUFFICIENT"] = 0.85
    return {
        "S_GLM": {"success":True, "result":{"response": json.dumps(s)}},
        "P_CLEF": {"success":True, "result":{"answers":{
            "assessment":{"choice":"INSUFFICIENT","probabilities":p}}}},
        "P_CLAIRIC": {"success":True, "result":{"answers":{
            "observed_increment":{"value":2.0}}}}
    }


class MockResponse:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return io.BytesIO(json.dumps(self.body).encode())
    def __exit__(self, *_args):
        return False


class ArenaSPTests(unittest.TestCase):
    def setUp(self):
        self.spec, self.views, self.catalog = bundle()
        self.package = build_requests(self.views, self.spec, self.catalog)

    def test_pinned_model_requests_and_no_inference_during_prepare(self):
        self.assertEqual(self.package["manifest"]["calls_made"], 0)
        self.assertEqual(self.package["manifest"]["authorization"], "NO_INFERENCE")
        self.assertEqual([r["model_name"] for r in self.package["requests"]], list(ORDER))
        self.assertEqual([r["endpoint"] for r in self.package["requests"]],
                         [MODELS[x] for x in ORDER])
        self.assertEqual([r["lane"] for r in self.package["requests"]], ["S","P","P"])

    def test_independent_prompts_never_read_other_lane_submission(self):
        s_text = json.dumps(self.package["requests"][0]["body"])
        p_text = json.dumps(self.package["requests"][1]["body"])
        self.assertNotIn("lane D", s_text)
        self.assertNotIn("D-PREDICTION-SECRET", s_text + p_text)
        self.assertNotIn("true_mechanism", s_text + p_text)
        self.assertNotIn("prediction-lock", s_text + p_text)

    def test_drafts_are_not_self_adjudicated_or_simulated(self):
        result = parse_responses(self.package, raw_results(self.package), self.catalog)
        self.assertEqual(result["S"]["selected_candidate_ids"],
                         ["urn:igc:candidate:CS-02"])
        self.assertEqual(result["P"]["support_assessment"], "INSUFFICIENT")
        self.assertTrue(result["P"]["numeric_crosscheck"]["valid_arithmetic"])
        self.assertFalse(result["predictions_generated"])
        self.assertFalse(result["claims_of_truth"])
        self.assertEqual(result["status"], "PROVIDER_DRAFTS_NOT_LANE_SUBMISSIONS")

    def test_real_glm_fenced_json_is_normalized(self):
        responses=raw_results(self.package)
        raw=responses["S_GLM"]["result"]["response"]
        responses["S_GLM"]["result"]["response"]="```json\n"+raw+"\n```"
        parsed=parse_responses(self.package,responses,self.catalog)
        self.assertEqual(parsed["S"]["selected_candidate_ids"],
                         ["urn:igc:candidate:CS-02"])

    def test_glm_invented_candidate_not_admitted(self):
        responses = raw_results(self.package)
        responses["S_GLM"]["result"]["response"] = json.dumps({
            "selected_candidate_ids": ["urn:igc:candidate:INVENTED"],
            "rationale":"invented", "falsifier":"test", "next_test":"next", "unknowns":[]})
        with self.assertRaisesRegex(ProviderError, "invented/duplicated"):
            parse_responses(self.package,responses,self.catalog)

    def test_model_or_request_tampering_rejected(self):
        pkg = copy.deepcopy(self.package)
        pkg["requests"][0]["endpoint"] = "@cf/untrusted/arbitrary"
        with self.assertRaisesRegex(ProviderError, "tampered"):
            parse_responses(pkg, raw_results(pkg), self.catalog)
        pkg = copy.deepcopy(self.package)
        pkg["requests"][0]["body"]["temperature"] = 999
        with self.assertRaisesRegex(ProviderError, "tampered"):
            parse_responses(pkg, raw_results(pkg), self.catalog)

    def test_foreign_lane_bundle_rejected(self):
        self.views["S"]["lane"] = "P"
        with self.assertRaisesRegex(ProviderError, "cross-lane"):
            build_requests(self.views,self.spec,self.catalog)

    def test_gold_or_trajectories_in_catalog_refused(self):
        for field,value in (("gold","CS-02"),("predictions",[1,2,3])):
            catalog=copy.deepcopy(self.catalog)
            catalog["candidates"][0][field]=value
            with self.assertRaises((ProviderError,RoundError)):
                build_requests(self.views,self.spec,catalog)

    def test_invalid_clairic_arithmetic_flagged_not_adopted(self):
        responses=raw_results(self.package)
        responses["P_CLAIRIC"]["result"]["answers"]["observed_increment"]["value"]=99
        output=parse_responses(self.package,responses,self.catalog)
        self.assertFalse(output["P"]["numeric_crosscheck"]["valid_arithmetic"])
        self.assertEqual(output["P"]["numeric_crosscheck"]["deterministic_expected"],2.0)

    def test_normalized_clef_probabilities_checked(self):
        responses=raw_results(self.package)
        responses["P_CLEF"]["result"]["answers"]["assessment"]["probabilities"]={"INSUFFICIENT":1.2}
        with self.assertRaisesRegex(ProviderError, "confidence"):
            parse_responses(self.package,responses,self.catalog)

    def test_billable_inference_requires_explicit_authorization(self):
        called=[]
        def fake_sender(request,timeout):
            called.append(request.full_url)
            raise AssertionError("should not make network call")
        with self.assertRaisesRegex(ProviderError,"NO_INFERENCE"):
            run_authorized(self.package,authorization="NO_INFERENCE",
                           env={"CLOUDFLARE_ACCOUNT_ID":"a"*32,"CLOUDFLARE_API_TOKEN":"tok"},
                           sender=fake_sender)
        self.assertEqual(called,[])

    def test_billable_inference_requires_credentials(self):
        with self.assertRaisesRegex(ProviderError,"credentials unavailable"):
            run_authorized(self.package,authorization=AUTHORIZATION,env={})

    def test_exactly_three_preapproved_provider_calls_with_fake_sender(self):
        outputs=raw_results(self.package)
        sent=[]
        def fake_sender(request,timeout):
            sent.append((request.full_url,json.loads(request.data)))
            return MockResponse(outputs[ORDER[len(sent)-1]])
        received=run_authorized(self.package,authorization=AUTHORIZATION,
                                env={"CLOUDFLARE_ACCOUNT_ID":"a"*32,
                                     "CLOUDFLARE_API_TOKEN":"SYNTHETIC_TOKEN"},
                                sender=fake_sender)
        self.assertEqual(len(sent),3)
        self.assertEqual(set(received),set(ORDER))
        self.assertTrue(all(x[0].startswith(
            "https://api.cloudflare.com/client/v4/accounts/") for x in sent))
        self.assertEqual(parse_responses(self.package,received,self.catalog)["P"]
                         ["numeric_crosscheck"]["valid_arithmetic"],True)

    def test_no_retries_after_provider_failure(self):
        called=[]
        def fail_sender(request,timeout):
            called.append(request.full_url)
            raise TimeoutError("synthetic timeout")
        with self.assertRaisesRegex(ProviderError,"FAILED_NO_RETRY"):
            run_authorized(self.package,authorization=AUTHORIZATION,
                           env={"CLOUDFLARE_ACCOUNT_ID":"a"*32,"CLOUDFLARE_API_TOKEN":"x"},
                           sender=fail_sender)
        self.assertEqual(len(called),1)


if __name__=="__main__":
    unittest.main()
