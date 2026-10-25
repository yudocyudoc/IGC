"""No-network audit of genuine S/P capture code with controlled fake HTTP sender."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_sp_capture import (usage_of, build_receipt, check_receipt,
                                      run_capture)
from scripts.arena_sp_producers import AUTHORIZATION,ProviderError,ORDER
from scripts.arena_sp_verify_capture import verify_archive
from test_arena_sp_producers import bundle,raw_results,MockResponse
from scripts.arena_sp_producers import build_requests

ENV={"CLOUDFLARE_ACCOUNT_ID":"a"*32,"CLOUDFLARE_API_TOKEN":"synthetic"}


class ProviderCaptureTests(unittest.TestCase):
    def setUp(self):
        self.spec,self.views,self.catalog=bundle()
        self.package=build_requests(self.views,self.spec,self.catalog)
        self.results=raw_results(self.package)
        self.tmp=tempfile.TemporaryDirectory()
        self.directory=Path(self.tmp.name)/"campaign"
    def tearDown(self):
        self.tmp.cleanup()

    def fake(self,observed,*,fail_after=None):
        def sender(request,timeout=150):
            idx=len(observed)
            observed.append((request.full_url,timeout))
            if fail_after is not None and idx==fail_after:
                raise TimeoutError("injected")
            return MockResponse(self.results[ORDER[idx]])
        return sender

    def run_campaign_test(self,observed):
        clock_count=[0]
        def clock():
            clock_count[0]+=1
            return float(clock_count[0])
        return run_capture(self.package,self.catalog,
            authorization=AUTHORIZATION,output_dir=self.directory,
            run_ref="synthetic-test-run",sender=self.fake(observed),
            capture_method="INJECTED_TEST_SENDER",env=ENV,clock=clock)

    def test_three_calls_journaled_without_guessing_tokens(self):
        called=[]
        receipt=self.run_campaign_test(called)
        self.assertEqual(len(called),3)
        self.assertEqual(receipt["calls_completed"],3)
        self.assertIsNone(receipt["tokens"])
        self.assertEqual(receipt["tokens_status"],"PARTIAL_OR_UNAVAILABLE")
        self.assertTrue(receipt["mock"])
        self.assertFalse(receipt["independent_attestation"])
        for i in (1,2,3):
            self.assertTrue((self.directory/f"call-{i}.json").exists())
        self.assertTrue((self.directory/"provider-drafts.json").exists())
        self.assertTrue((self.directory/"completed.json").exists())
        check_receipt(receipt,self.package,self.results)
        with self.assertRaisesRegex(ProviderError,"MOCK_IS_NOT_LIVE"):
            check_receipt(receipt,self.package,self.results,require_live=True)

    def test_offline_archive_replays_all_hashed_journal_entries(self):
        observed=[]
        receipt=self.run_campaign_test(observed)
        result=verify_archive(self.package,self.catalog,self.directory)
        self.assertEqual(result["status"],
                         "ARCHIVE_CONSISTENT_NOT_INDEPENDENTLY_ATTESTED")
        self.assertEqual(result["receipt_hash"],receipt["receipt_hash"])
        self.assertFalse(result["external_attestation"])

    def test_offline_verifier_rejects_changed_call_journal(self):
        self.run_campaign_test([])
        first=self.directory/"call-1.json"
        data=json.loads(first.read_text(encoding="utf-8"))
        data["response"]["result"]["response"]="replaced"
        first.write_text(json.dumps(data))
        with self.assertRaisesRegex(ProviderError,"CALL_JOURNAL_TAMPERED"):
            verify_archive(self.package,self.catalog,self.directory)

    def test_concurrent_or_accidental_replay_of_directory_is_rejected(self):
        seen=[]
        self.run_campaign_test(seen)
        with self.assertRaises(FileExistsError):
            self.run_campaign_test(seen)
        self.assertEqual(len(seen),3)

    def test_failed_second_call_stops_and_never_marks_complete(self):
        observed=[]
        with self.assertRaisesRegex(ProviderError,"FAILED_NO_RETRY"):
            run_capture(self.package,self.catalog,authorization=AUTHORIZATION,
                        output_dir=self.directory,run_ref="synthetic-test-run",
                        sender=self.fake(observed,fail_after=1),
                        capture_method="INJECTED_TEST_SENDER",env=ENV)
        self.assertEqual(len(observed),2)
        self.assertTrue((self.directory/"call-1.json").exists())
        self.assertFalse((self.directory/"call-2.json").exists())
        self.assertFalse((self.directory/"completed.json").exists())
        with self.assertRaises(FileExistsError):
            self.run_campaign_test(observed)
        self.assertEqual(len(observed),2)

    def test_no_authorization_no_call_no_directory(self):
        observed=[]
        with self.assertRaisesRegex(ProviderError,"NO_INFERENCE"):
            run_capture(self.package,self.catalog,authorization="NONE",
                        output_dir=self.directory,run_ref="synthetic",
                        sender=self.fake(observed),
                        capture_method="INJECTED_TEST_SENDER",env=ENV)
        self.assertFalse(self.directory.exists())
        self.assertEqual(observed,[])

    def test_usage_neurons_not_misrepresented_as_token_count(self):
        response={"result":{"usage":{"neurons":2.32}}}
        x=usage_of(response)
        self.assertEqual(x["provider_reported"]["neurons"],2.32)
        self.assertEqual(x["token_status"],"UNAVAILABLE")
        self.assertIsNone(x["token_total"])

    def test_usage_tokens_only_if_provider_reports_them(self):
        self.results["S_GLM"]["result"]["usage"]={"prompt_tokens":24,"completion_tokens":8}
        self.results["P_CLEF"]["result"]["usage"]={"input_tokens":13,"output_tokens":11}
        self.results["P_CLAIRIC"]["result"]["usage"]={"total_tokens":6}
        seen=[]
        receipt=self.run_campaign_test(seen)
        self.assertEqual(receipt["tokens"],62)
        self.assertEqual(receipt["tokens_status"],"REPORTED_ALL")
        self.assertEqual(receipt["cost_status"],"PROVIDER_CURRENCY_NOT_VERIFIED")
        check_receipt(receipt,self.package,self.results)

    def test_receipt_tampering_invalidates_integrity(self):
        called=[]
        receipt=self.run_campaign_test(called)
        changed=copy.deepcopy(receipt)
        changed["observations"][0]["duration_ms"]+=2
        with self.assertRaisesRegex(ProviderError,"TAMPERED"):
            check_receipt(changed,self.package,self.results)

    def test_response_hash_mismatch_rejected(self):
        called=[]
        receipt=self.run_campaign_test(called)
        responses=copy.deepcopy(self.results)
        responses["S_GLM"]["result"]["response"]="changed after sealed"
        with self.assertRaisesRegex(ProviderError,"CAPTURE_MISMATCH"):
            check_receipt(receipt,self.package,responses)

if __name__=="__main__":
    unittest.main()
