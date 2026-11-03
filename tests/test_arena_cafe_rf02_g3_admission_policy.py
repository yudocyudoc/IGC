"""RF-02P: prospectively scoped admission/abstention, never silent G3."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import r2_g3_admission_policy as p
from scripts.arena_cafe import r2_hj_parameter_gate as hj
from scripts.arena_v0_contract import ArenaContractError,digest


class ProspectiveG3Admission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths=(os.environ.get("RF02_PUBLIC_DIR"),
               os.environ.get("RF02_HJ_REPORT"),
               os.environ.get("RF02_D_G2_DIR"),
               os.environ.get("RF02_M_G2_DIR"))
        if not all(paths):
            raise unittest.SkipTest("Use pinned original A1, H_j, six D and six M trace artifacts")
        cls.visible=json.loads((Path(paths[0])/"O0_VISIBLE.json").read_text())
        cls.h=json.loads(Path(paths[1]).read_text())
        cls.d_root,cls.m_root=map(Path,paths[2:])
        # Independent, repeated source verification BEFORE the policy uses H_j.
        independently_reconstructed=hj.build(cls.visible,cls.d_root,cls.m_root)
        assert digest(cls.h)==digest(independently_reconstructed),(
            "RF02P_HJ_ARTIFACT_DIFFERS_FROM_INDEPENDENT_REAUDIT")
        cls.r=p.build(cls.h,cls.visible)

    def test_00_original_twelve_candidate_provenance_and_immutability(self):
        r=self.r
        self.assertEqual(p.SCHEMA,r["schema"])
        self.assertEqual(12,sum(a["candidate_count"] for a in r["arms"].values()))
        self.assertEqual((6,6,0),
            tuple(r["arms"][a]["candidate_count"] for a in ("D","M","B")))
        self.assertEqual({k:r["source_artifact_runs"][k] for k in (
                         "A1_public_run_id","D_G2_engineering_run_id",
                         "M_G2_engineering_run_id")},
                         { "A1_public_run_id":p.hj.A1_ORIGIN_RUN,
                           "D_G2_engineering_run_id":p.hj.D_ORIGIN_RUN,
                           "M_G2_engineering_run_id":p.hj.M_ORIGIN_RUN })
        self.assertEqual(digest(self.h),r["source_hj_report_sha256"])
        self.assertEqual(self.h["public_view_sha256"],r["public_view_sha256"])
        self.assertEqual(self.h["public_source_snapshot_hash"],
                         r["public_source_snapshot_hash"])
        for arm in ("D","M"):
            self.assertEqual(6,len({x["candidate_id"] for x in
                                    r["arms"][arm]["candidates"]}))
            for row in r["arms"][arm]["candidates"]:
                self.assertFalse(row["scored"])
                self.assertTrue(row["native_G2_trace_sha256"].startswith("sha256:"))
        self.assertEqual(0,r["omc_invocations"])
        self.assertEqual(0,r["provider_calls"])

    def test_01_fair_arm_specific_responses_and_no_illusory_calibration(self):
        a=self.r["arms"]
        self.assertEqual("ABSTAIN_NO_AUTHORIZED_G3_INPUTS",a["D"]["admission"])
        self.assertEqual("DOES_NOT_EXIST_IN_ORIGINAL_D",
                         a["D"]["method_native_parameter_fit"])
        self.assertEqual("NON_EMPIRICAL_CONFORMANCE_FIXTURE_NOT_EV01_MEASUREMENT",
                         a["D"]["parameter_state"])
        self.assertEqual("ABSTAIN_G3_BUT_NATIVE_ENUMERATOR_COMPLETE",
                         a["M"]["admission"])
        self.assertEqual("NOT_REQUIRED_BY_SHORT_E1_ENUMERATOR",
                         a["M"]["method_native_parameter_fit"])
        self.assertEqual("NO_CALIBRATION_IMPOSED_ON_ORIGINAL_METHOD",
                         a["M"]["calibration_option"])
        self.assertEqual("ORIGINAL_E1_BASE_SIX_FULL_AST_ENUMERATED",
                         a["M"]["native_component_state"])
        self.assertEqual("NOT_RUN",a["B"]["G2"])
        self.assertEqual("NOT_AUTHORIZED_TO_CALL_PROVIDER",
                         a["B"]["calibration_option"])
        self.assertEqual("LIVE_EV01_NATIVE_INFERENCE_NOT_RUN",
                         a["B"]["native_component_state"])
        self.assertEqual(0,a["B"]["candidate_count"])
        for arm in a.values():
            self.assertEqual("NONE",arm["selection_actor"])
            self.assertGreater(len(arm["reasons"]),1)

    def test_02_science_not_promoted_by_green_engineering(self):
        r=self.r
        self.assertEqual("ABSTAIN_G3_WITH_ARM_SPECIFIC_REASONS",r["result"])
        self.assertEqual("NOT_RUN",r["G3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("PARTIAL_CONTRACTS_ENGINEERING_ONLY",r["R2"])
        self.assertTrue(r["no_scores"])
        self.assertTrue(r["no_parameter_fits"])
        self.assertTrue(r["no_native_model_selection"])
        self.assertTrue(r["no_private_data_access"])
        self.assertFalse(r["syntactically_valid_future_metadata_is_G3_authorization"])
        self.assertEqual([],r["unregistered_g3_actions_permitted"])
        self.assertFalse(r["proposed_G3_new_world_available"])
        self.assertIsNone(r["prospective_evidence_metadata"])
        self.assertEqual("PENDING",r["independent_scientific_adjudication"])

    def test_03_protocol_distinguishes_conditional_replay_from_forecasting(self):
        proto=self.r["preregistration_candidate"]
        self.assertEqual(p.CANDIDATE_PROTOCOL_SCHEMA,proto["schema"])
        self.assertEqual("OFFLINE_CONDITIONAL_REPLAY_WITH_EXOGENOUS_ARRIVALS_KNOWN",
                         proto["task"])
        self.assertFalse(proto["development_O0_is_a_blind_holdout"])
        self.assertEqual("ALREADY_EXAMINED_FOR_ENGINEERING_DO_NOT_REUSE_AS_SEALED_EVALUATION",
                         proto["development_O0_status"])
        self.assertEqual(["2","4","6","8","10"],
                         proto["proposed_primary_observable"]["times_minutes_exact"])
        self.assertEqual("MAE_CUMULATIVE_DELIVERY_COUNTS",
                         proto["proposed_primary_observable"]["candidate_statistic"])
        self.assertEqual("NOT_GRANTED",
                         proto["proposed_primary_observable"]["scientific_approval"])
        self.assertFalse(proto["construction_input_policy"]["rate_instrument_measured"])
        self.assertTrue(proto["training_and_evaluation"][
            "construction_and_evaluation_must_be_distinct_worlds"])
        self.assertEqual("NONE",proto["selected_winner_before_evaluation"])
        self.assertEqual("NOT_RUN",proto["metric_application"])

    def test_04_hj_mutations_are_rejected_individually(self):
        cases={
            "g3_promoted":lambda h: h["gates"].update({"G3":"PASS"}),
            "d_params":lambda h: h["parameters"]["D"].update({"eligible_for_G3":True}),
            "m_params":lambda h: h["parameters"]["M"].update({"eligible_for_G3":True}),
            "b_params":lambda h: h["parameters"]["B"].update({"eligible_for_G3":True}),
            "fabricated_13th":lambda h: h["candidates"].append(deepcopy(h["candidates"][0])),
            "missing_candidates":lambda h: h.update({"candidates":[]}),
            "ranked_candidate":lambda h: h["candidates"][0].update({"G3":"PASS"}),
            "g2_absent":lambda h: h["candidates"][0].update({"G2":"NOT_RUN"}),
            "different_signal":lambda h: h["candidates"][1].update({
                "input_signal_sha256":"sha256:"+"0"*64}),
            "false_hj":lambda h: h["observables"]["delivery_cumulative"].update({
                "G3_ADMISSIBLE":True}),
            "wrong_view":lambda h: h.update({
                "public_source_snapshot_hash":"sha256:"+"f"*64}),
        }
        for name,mutate in cases.items():
            with self.subTest(case=name):
                forged=deepcopy(self.h)
                mutate(forged)
                with self.assertRaises(ArenaContractError):
                    p.build(forged,self.visible)

    @staticmethod
    def future_template():
        return {
            "schema":p.FUTURE_SCHEMA,
            "task":"OFFLINE_CONDITIONAL_REPLAY_WITH_EXOGENOUS_ARRIVALS_KNOWN",
            "construction":{
                "dataset_id":"dev-future-001",
                "world_id":"independent-world-dev-001",
                "snapshot_sha256":"sha256:"+"1"*64,
                "source_kind":"NON_RESERVED_PUBLIC_OPERATIONAL_INPUTS",
                "observed_outcomes_access":"VISIBLE_TO_METHOD_FOR_CONSTRUCTION",
                "role":"CONSTRUCTION",
                "data_availability":"FUTURE_CREATED",
                "source_independence_attested_by":"PENDING_EXTERNAL_AUDIT",
            },
            "evaluation":{
                "dataset_id":"eval-future-002",
                "world_id":"independent-world-test-002",
                "snapshot_sha256":"sha256:"+"2"*64,
                "source_kind":"PROSPECTIVE_SEALED_INDEPENDENT_WORLD",
                "observed_outcomes_access":"SEALED_NOT_ACCESSIBLE_TO_ARMS_OR_CALIBRATOR",
                "role":"EVALUATION",
                "data_availability":"FUTURE_CREATED",
                "source_independence_attested_by":"PENDING_EXTERNAL_AUDIT",
            },
            "registration":{
                "protocol_sha256":"sha256:"+"3"*64,
                "candidate_register_sha256":"sha256:"+"4"*64,
                "declared_prior_to_evaluation_outcomes":True,
                "measurement_equivalence_review":"NOT_RUN",
                "access_isolation_review":"NOT_RUN",
                "cost_authorization_state":"NOT_AUTHORIZED",
                "external_review_reference":"audit-future-pending",
            },
            "evaluation_outcomes_became_visible_before_registration":False,
            "any_candidate_or_parameter_selected_from_evaluation_outcomes":False,
        }

    def test_05_valid_metadata_never_grants_scientific_admission(self):
        proposed=self.future_template()
        result=p.build(self.h,self.visible,proposed)
        self.assertEqual("PASS_ONLY_UNVERIFIED_SELF_ATTESTATION",
                         result["prospective_evidence_metadata"]["metadata_shape"])
        self.assertEqual("NOT_EXTERNALLY_AUTHENTICATED",
                         result["prospective_evidence_metadata"]["independent_provenance"])
        self.assertFalse(result["prospective_evidence_metadata"]["execution_authorized"])
        self.assertEqual("NOT_RUN",result["G3"])
        self.assertFalse(result["proposed_G3_new_world_available"])
        self.assertEqual("ABSTAIN_G3_WITH_ARM_SPECIFIC_REASONS",result["result"])

    def test_06_forbidden_future_metadata_variants_rejected(self):
        variants={
            "same_world":lambda s: s["evaluation"].update({
                "world_id":s["construction"]["world_id"]}),
            "same_data":lambda s: s["evaluation"].update({
                "dataset_id":s["construction"]["dataset_id"]}),
            "same_sha":lambda s: s["evaluation"].update({
                "snapshot_sha256":s["construction"]["snapshot_sha256"]}),
            "existing_dev_source":lambda s: s["evaluation"].update({
                "snapshot_sha256":self.h["public_source_snapshot_hash"]}),
            "existing_current_world":lambda s: s["evaluation"].update({
                "world_id":self.visible["observability"]["world_public_id"]}),
            "unsealed":lambda s: s["evaluation"].update({
                "observed_outcomes_access":"VISIBLE_TO_METHOD_FOR_CONSTRUCTION"}),
            "wrong_dataset_role":lambda s: s["evaluation"].update({
                "role":"CONSTRUCTION"}),
            "seen_outcomes":lambda s: s.update({
                "evaluation_outcomes_became_visible_before_registration":True}),
            "score_selected_by_holdout":lambda s: s.update({
                "any_candidate_or_parameter_selected_from_evaluation_outcomes":True}),
            "pretend_forecast":lambda s: s.update({
                "task":"REAL_TIME_FORECAST"}),
            "false_registration":lambda s: s["registration"].update({
                "declared_prior_to_evaluation_outcomes":False}),
            "missing_protocol":lambda s: s["registration"].pop(
                "protocol_sha256"),
            "extra_scientific_approval":lambda s: s.update({
                "G3":"PASS"}),
        }
        for key,mutate in variants.items():
            with self.subTest(case=key):
                proposal=self.future_template()
                mutate(proposal)
                with self.assertRaises(ArenaContractError):
                    p.build(self.h,self.visible,proposal)

    def test_07_privileged_actions_are_application_denied(self):
        for action in p.METHODOLOGICAL_ACTIONS:
            with self.subTest(action=action):
                with self.assertRaisesRegex(ArenaContractError,
                        "RF02P_ACTION_DENIED_G3_NOT_AUTHORIZED"):
                    p.deny_privileged_action(action,self.r)
        for invalid in ("", "SCORE_G2", "ALLOW_CLOUDFLARE"):
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02P_UNKNOWN_PRIVILEGED_ACTION"):
                p.deny_privileged_action(invalid,self.r)
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF02P_ADMISSION_REPORT_REQUIRED"):
            p.deny_privileged_action("SCORE_G3",{})


if __name__=="__main__":
    unittest.main()
