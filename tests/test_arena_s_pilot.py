"""Pilot preparation and B0/D/S lock; no holdout and no provider calls."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_round import prepare,hash_obj
from scripts.arena_s_calibration import calibrate
from scripts.arena_s_pilot_enumeration import prepare_enumeration
from scripts.arena_s_pilot_lock import build_lock
from scripts.arena_sp_producers import ProviderError
from scripts.compose_molecular_candidates import compose
from scripts.fm_b5_parameter_identifiability import sample_times,simulate

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/name).read_text(encoding="utf-8"))


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.plan=read("data/synthetic/fm_b3_dynamic_plan.json")
        self.plan["candidates"]=self.plan["candidates"][:2]
        self.composed=compose(self.plan,read("data/synthetic/fm_a_structural_candidates.json"))
        self.fit=read("data/synthetic/arena_s_pilot_fit_config.json")
        # Reduce the synthetic fitting grid for unit tests only.
        self.fit["parameter_ranges"]["maxThroughput"]={
            "minimum":1.6,"maximum":1.8,"step":0.2}
        self.fit["parameter_ranges"]["responseTime"]={
            "minimum":0.8,"maximum":1.0,"step":0.2}
        cal=self.fit["calibration"]
        spec=read("data/synthetic/arena_s_pilot_round_spec.json")
        self.primary={
            "investigation_id":spec["investigation_id"],
            "observable_id":"delivered","unit":"units",
            "times":sample_times(cal["stop_time"],cal["observation_interval"]),
            "values":simulate(2,1.8,0.8,cal["input_amplitude"],
                cal["input_duration"],cal["stop_time"],
                cal["observation_interval"],self.fit["numerics"]["integration_step"]),
            "sources":["synthetic-construction-only-fixture"],
            "input_profile":{"kind":"pulse","amplitude":cal["input_amplitude"],
                "duration":cal["input_duration"],"initial_stocks_zero":True}}
        self.spec=spec
        self.views=prepare(self.spec,self.primary)

    def test_independent_d_enumeration_generates_both_models(self):
        calibrated,eval_plan,receipt=calibrate(
            self.composed,self.plan,self.fit,self.primary)
        supports=read("data/synthetic/arena_s_pilot_supports.json")
        with TemporaryDirectory() as folder:
            out=Path(folder)/"D"
            manifest=prepare_enumeration(self.composed,calibrated,
                self.plan,eval_plan,supports,self.fit,self.primary,receipt,out)
            self.assertEqual(manifest["candidate_ids"],[
                "urn:igc:candidate:CS-01","urn:igc:candidate:CS-02"])
            script=(out/"run-enumeration.mos").read_text()
            self.assertEqual(script.count("simulate("),2)
            self.assertEqual(manifest["status"],"ENUMERATION_PREPARED_NOT_EXECUTED")

    def test_locally_fabricated_s_capture_prepares_real_origin_modelica(self):
        # Deliberately forge the local receipt: tests the real-origin CODE PATH,
        # not a provider invocation or independently attested provenance.
        from scripts.arena_sp_producers import build_requests,parse_s_response
        from scripts.arena_sp_capture import usage_of
        from scripts.arena_s_real import seal_s_only
        from scripts.arena_sp_simulation import prepare_s
        calibrated,eval_plan,cal_receipt=calibrate(
            self.composed,self.plan,self.fit,self.primary)
        supports=read("data/synthetic/arena_s_pilot_supports.json")
        catalog=read("data/synthetic/arena_s_pilot_catalog.json")
        package=build_requests(self.views,self.spec,catalog)
        response={"success":True,"result":{
            "response":json.dumps({
                "selected_candidate_ids":["urn:igc:candidate:CS-02"],
                "rationale":"Two-stage model remains plausible",
                "falsifier":"New pulse could reject proposed structure",
                "unknowns":["Capacity uncertain"],
                "next_test":"Predeclared pulse"}),
            "usage":{"prompt_tokens":100,"completion_tokens":50}}}
        draft=parse_s_response(package,response,catalog)
        receipt={
            "schema":"igc-arena-s-single-capture/0.1",
            "run_ref":"test-only-locally-fabricated-not-attested",
            "capture_method":"PYTHON_URLLIB","mock":False,
            "requests_hash":package["manifest"]["requests_hash"],
            "catalog_hash":hash_obj(catalog),
            "view_hash":self.views["S"]["view_hash"],
            "request_body_hash":package["requests"][0]["body_hash"],
            "response_hash":hash_obj(response),
            "parsed_s_hash":hash_obj(draft),
            "calls_completed":1,"retries":0,"duration_ms":1.0,
            "usage":usage_of(response),"independent_attestation":False,
            "empirical_causality":"NOT_PROVEN"}
        receipt["receipt_hash"]=hash_obj(receipt)
        seal=seal_s_only(package,catalog,{"S":self.views["S"]},
            calibrated,supports,response,draft,receipt,
            calibration=cal_receipt)
        self.assertFalse(seal["eligible_for_empirical_scoring"])
        with TemporaryDirectory() as folder:
            report=prepare_s(seal,draft,package,catalog,
                {"S":self.views["S"]},calibrated,supports,eval_plan,
                Path(folder)/"S",
                s_capture={"response":response,"draft":draft,"receipt":receipt},
                calibration=cal_receipt)
            self.assertEqual(report["status"],
                "S_SIMULATION_PREPARED_CAPTURED_NOT_SCORED")
            modelica=(Path(folder)/"S"/"ArenaSProposalDynamics.mo").read_text()
            self.assertIn("Evaluate_CS_02",modelica)
            self.assertNotIn("Evaluate_CS_01",modelica)
            self.assertEqual(report["simulated_ids"],
                ["urn:igc:candidate:CS-02"])

    def test_b0_d_s_lock_with_p_skipped(self):
        v=self.views
        mk=lambda cid:{"candidate_id":cid,"kind":"modelica_calibrated",
                        "mechanism":"Synthetic queue model",
                        "predictions":[1.,2.,3.]}
        s={"schema":self.spec["schema"],"round_id":self.spec["round_id"],
           "lane":"S","view_hash":v["S"]["view_hash"],"status":"SUBMITTED",
           "producer":"test-only","proposals":[mk("urn:igc:candidate:CS-02")],
           "unknowns":["not proof"],"objections":[],
           "capture_receipt_hash":"test-receipt",
           "calibration_receipt_hash":"test-fit",
           "cost":{"llm_calls":1,"tokens":55,"simulations":1,
                   "human_minutes":0,"retries":0}}
        d={"schema":self.spec["schema"],"round_id":self.spec["round_id"],
           "lane":"D","view_hash":v["D"]["view_hash"],"status":"SUBMITTED",
           "producer":"test-only","proposals":[mk("urn:igc:candidate:CS-01"),
                                                mk("urn:igc:candidate:CS-02")],
           "unknowns":["not proof"],"objections":[],
           "source_manifest_hash":"test-manifest",
           "openmodelica_log_sha256":"test-log",
           "cost":{"llm_calls":0,"tokens":0,"simulations":2,
                   "human_minutes":0,"retries":0}}
        views,submissions,lock=build_lock(self.spec,self.primary,s,d,run_ref="test:dry")
        self.assertEqual(submissions["P"]["status"],"NOT_IMPLEMENTED")
        self.assertEqual(submissions["B0"]["status"],"SUBMITTED")
        self.assertEqual(lock["evaluation_status"],"LOCKED_NOT_EVALUATED")
        bad=dict(s); bad.pop("capture_receipt_hash")
        with self.assertRaisesRegex(ProviderError,"PILOT_S_MUST"):
            build_lock(self.spec,self.primary,bad,d,run_ref="test:dry")


if __name__=="__main__":
    unittest.main()
