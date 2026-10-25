"""Unit-level G3 disposition after sealed S selection.

Only external solver/provenance verification is stubbed. The real S submission
logic, candidate filtering, cost accounting and Arena schema are exercised.
The existing OpenModelica CI covers the independent numerical/physical gates.
No provider is called.
"""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.arena_round import SCHEMA, hash_obj
from scripts.arena_s_real import ORIGIN
from scripts.arena_s_submission import (
    s_submission, s_abstention, s_g3_disposition)
from scripts.fm_b3_dynamic_evaluation import result_prefix, digest


CS1="urn:igc:candidate:CS-01"
CS2="urn:igc:candidate:CS-02"
TARGETS=[0.5, 1.0]


class G3SubmissionTests(unittest.TestCase):
    def setUp(self):
        def fit(adequate,rmse):
            return {
                "absolute_adequacy":"ADEQUATE" if adequate else "INADEQUATE",
                "best_fit":{"rmse":rmse},
                "absolute_rmse_threshold":0.24,
                "physical_input_bound_passed":True,
                "prediction_envelope_rk4":[
                    {"time":t,"minimum":1.0,"maximum":3.0}
                    for t in TARGETS]
            }
        self.calibration={
            "report_hash":"test-calibration-not-real",
            "fits":{CS1:fit(False,0.3080160251197515),CS2:fit(True,0.0)},
            "absolute_adequacy_status":"AT_LEAST_ONE_ADEQUATE"
        }
        self.view={"schema":SCHEMA,"round_id":"R-TEST", "lane":"S",
                   "view_hash":"test-view","target_times":TARGETS,
                   "primary":{},
                   "budget":{"llm_calls":1,"tokens":1000,
                             "simulations":2,"human_minutes":15,"retries":0}}
        self.receipt={"receipt_hash":"locally-stubbed","usage":{"token_total":150}}
        self.kw=dict(package={},catalog={},views={"S":self.view},
                     composed={},supports={},response={},draft={},
                     receipt=self.receipt,calibration=self.calibration,
                     base_composed={},base_plan={},evaluation_plan={},
                     fit_plan={},human_minutes=0.5)

    def seal(self,ids):
        return {"origin":ORIGIN,"S":{"selection":list(ids),
                "unknowns":["Synthetic construction not proof"]}}

    def patch_validators(self):
        return (patch("scripts.arena_s_submission.verify_s_only_seal"),
                patch("scripts.arena_s_submission.verify_calibration"))

    def test_mixed_g3_preserves_both_selected_and_two_solver_executions(self):
        seal=self.seal([CS1,CS2])
        with TemporaryDirectory() as tmp:
            out=Path(tmp)
            csv_path=out/(result_prefix(CS2)+"_res.csv")
            with csv_path.open("w",newline="",encoding="utf-8") as stream:
                wr=csv.DictWriter(stream,fieldnames=["time","delivered"])
                wr.writeheader()
                wr.writerows([{"time":0.5,"delivered":1.5},
                              {"time":1.0,"delivered":2.5}])
            verified={
                "status":"S_CAPTURED_MODEL_EXECUTION_PASS_SYNTHETIC",
                "report_hash":"solver-test-not-real",
                "simulated_ids":[CS1,CS2],
                "trace_checks":{CS2:{"csv_sha256":digest(csv_path)}}}
            manifest={"calibration_receipt_hash":hash_obj(self.calibration)}
            a,b=self.patch_validators()
            with a,b,patch("scripts.arena_s_submission.verify_s",return_value=verified):
                s=s_submission(**self.kw,seal=seal,manifest=manifest,
                               verified_report=verified,simulation_dir=out,
                               log=out/"fake.log",composer_file=out/"fake.mo")
            self.assertEqual(s["status"],"SUBMITTED")
            self.assertEqual([x["candidate_id"] for x in s["proposals"]],[CS2])
            self.assertEqual(s["proposals"][0]["predictions"],[1.5,2.5])
            self.assertEqual(s["cost"]["simulations"],2)
            self.assertEqual(s["s_g3_disposition"]["original_selected_candidate_ids"],
                             [CS1,CS2])
            rejected=s["s_g3_disposition"]["discarded_candidates"]
            self.assertEqual(len(rejected),1)
            self.assertEqual(rejected[0]["candidate_id"],CS1)
            self.assertEqual(rejected[0]["reason"],
                             "G3_ABSOLUTE_CONSTRUCTION_INADEQUACY")
            self.assertEqual(s["s_g3_disposition"]["retained_candidate_ids"],[CS2])

    def test_only_inadequate_selection_yields_abstention_even_with_other_good_candidate(self):
        seal=self.seal([CS1])
        a,b=self.patch_validators()
        with a,b:
            s=s_abstention(**self.kw,seal=seal)
        self.assertEqual(s["status"],"ABSTAINED")
        self.assertEqual(s["proposals"],[])
        self.assertEqual(s["abstention_origin"],"S_SELECTED_NO_ADEQUATE_STRUCTURE")
        self.assertEqual(s["s_g3_disposition"]["original_selected_candidate_ids"],[CS1])
        self.assertEqual(s["s_g3_disposition"]["discarded_candidates"][0]["candidate_id"],CS1)
        self.assertEqual(s["cost"]["simulations"],0)

    def test_abstention_counts_already_executed_inadequate_model(self):
        seal=self.seal([CS1])
        verified={"status":"S_CAPTURED_MODEL_EXECUTION_PASS_SYNTHETIC",
                  "simulated_ids":[CS1],"report_hash":"verified-test"}
        a,b=self.patch_validators()
        with a,b,patch("scripts.arena_s_submission.verify_s",return_value=verified):
            s=s_abstention(**self.kw,seal=seal,
                manifest={"calibration_receipt_hash":hash_obj(self.calibration)},
                verified_report=verified,simulation_dir=Path("unused"),
                log=Path("unused"),composer_file=Path("unused"))
        self.assertEqual(s["cost"]["simulations"],1)
        self.assertEqual(s["modelica_report_hash"],"verified-test")

    def test_cannot_abstain_when_a_selected_candidate_is_adequate(self):
        from scripts.arena_sp_producers import ProviderError
        seal=self.seal([CS1,CS2])
        a,b=self.patch_validators()
        with a,b,self.assertRaisesRegex(ProviderError,
                                        "S_ABSTENTION_HAS_SELECTED_ADEQUATE_CANDIDATE"):
            s_abstention(**self.kw,seal=seal)

    def test_selection_cannot_be_replaced_with_unselected_adequate_candidate(self):
        decision=s_g3_disposition(self.seal([CS1]),self.calibration)
        self.assertEqual(decision["retained_candidate_ids"],[])
        self.assertEqual(decision["original_selected_candidate_ids"],[CS1])


if __name__=="__main__":
    unittest.main()
