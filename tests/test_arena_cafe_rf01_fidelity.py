"""RF-01 adversarial fidelity tests. Real original module identities; no provider/solver."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import method_fidelity_manifest as rf
from scripts.arena_v0_contract import ArenaContractError,digest


ROOT=Path(__file__).resolve().parents[1]
BASELINE=ROOT/"docs/arena_cafe/fidelity/F0_FIDELITY_BASELINE.json"


class RF01FidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=json.loads(BASELINE.read_text())
        # RF-01 must NEVER generate a new DES world even in tests.
        # Fixture inputs come only from the prior frozen A1 run, via artifact.
        source=os.environ.get("RF01_PUBLIC_DIR")
        if not source:
            raise unittest.SkipTest(
                "Supply RF01_PUBLIC_DIR with immutable existing A1 O0/O1 artifacts")
        root=Path(source)
        cls.views={c:json.loads((root/(c+"_VISIBLE.json")).read_text())
                   for c in ("O0","O1")}

    def source(self,arm,condition):
        visible=self.views[condition]
        status=rf.WORKER_STATES[arm][0]
        report={
            "arm":arm,"condition":condition,
            "status":status,
            "visible_input_hash":digest(visible),
            "source_snapshot_hash":visible["source_snapshot_hash"],
            "provider_calls":0,"scientific_use_proven":False,
            "native_method_run":arm!="D",
        }
        if arm=="B":
            report["user_prompt_hashes"]=["sha256:"+("a" if condition=="O0" else "b")*64]
        if arm=="M":
            from scripts.arena_m_short_e1 import E1,get_composer
            c=get_composer()
            cfg,classes,_=c.load_registry(E1/"registry.base.json")
            graphs=[{"canonical_sha256":k,"ast":g}
                    for k,g in c.enumerate_graphs(cfg,classes)]
            report["candidate_count"]=len(graphs)
            report["candidate_graphs_hash"]=digest(graphs)
        verified={"status":status,
                  "memory":{"case_id":"test-"+arm+"-"+condition,
                            "actual_SQLite_reconstruction":True}}
        return report,verified

    def method(self,arm,condition):
        raw,verified=self.source(arm,condition)
        return rf.classify_worker(
            self.views[condition],arm,condition,raw,verified,self.baseline)

    def test_T24_original_blobs_exact_never_move_hash_to_make_ci_pass(self):
        self.assertTrue(rf.verify_original_sources(self.baseline))
        forged=deepcopy(self.baseline)
        forged["original_source_git_blobs"]["scripts/arena_d_v01.py"]="f"*40
        with self.assertRaisesRegex(ArenaContractError,"RF01_FROZEN_SOURCE_MUTATED"):
            rf.verify_original_sources(forged)

    def test_six_native_lanes_have_no_false_full_execution(self):
        methods=[self.method(a,c) for c in ("O0","O1") for a in ("D","B","M")]
        self.assertEqual(6,len(methods))
        for x in methods:
            self.assertTrue(rf.verify_manifest(x))
            self.assertFalse(x["method_complete"])
            self.assertFalse(x["method_route_complete"])
            self.assertEqual("NOT_RUN_NATIVE_METHOD",x["g3"])
            self.assertEqual("NONE",x["selection_decision_owner"])
        self.assertEqual(2,sum(m["execution_state"]=="METHOD_ABSTAINED" for m in methods))
        self.assertEqual(4,sum(m["execution_state"]=="BLOCKED_BEFORE_RUN" for m in methods))

    def test_T01_D2_CSV_cannot_become_D_generate(self):
        d=self.method("D","O0")
        self.assertIsNone(d["original_candidate_universe"]["count"])
        self.assertEqual([],d["native_candidate_ids"])
        for key,val in (("method_complete",True),
                        ("method_route_complete",True),
                        ("execution_state","COMPLETED_METHOD")):
            broken=deepcopy(d);broken[key]=val
            with self.subTest(key=key),self.assertRaises(ArenaContractError):
                rf.verify_manifest(broken)

    def test_T02_cross_arm_prior_not_allowed_in_native_lane(self):
        d=self.method("D","O0")
        d["cross_arm_prior_imports"]=["E1_PREPARATION_CAPACITY"]
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_NATIVE_METHOD_FALSE_GATES_OR_SELECTION"):
            rf.verify_manifest(d)

    def test_T03_T04_M_universe_six_and_no_Arena_silent_selection(self):
        m=self.method("M","O1")
        self.assertEqual(6,m["original_candidate_universe"]["count"])
        self.assertEqual(6,len(m["native_candidate_hashes"]))
        self.assertEqual("ARENA_M0_BRIDGE_UNRESOLVED_SELECTION",m["abstention_origin"])
        self.assertEqual("METHOD_ABSTAINED",m["execution_state"])
        x=deepcopy(m);x["selection_decision_owner"]="NATIVE_METHOD"
        x["native_candidate_ids"]=x["native_candidate_ids"][:1]
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_NATIVE_METHOD_FALSE_GATES_OR_SELECTION"):
            rf.verify_manifest(x)
        original,verified=self.source("M","O1")
        original["candidate_count"]=1
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_M_ENUMERATED_ORIGINAL_UNIVERSE_DRIFT"):
            rf.classify_worker(self.views["O1"],"M","O1",original,verified,self.baseline)

    def test_T05_T06_B_offline_mock_not_live_or_this_scientific_run(self):
        b=self.method("B","O0")
        self.assertTrue(b["historical_B_live_not_this_EV01"])
        self.assertEqual("BLOCKED_BEFORE_RUN",b["execution_state"])
        fake=deepcopy(b);fake["provider_calls"]=1
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_NATIVE_METHOD_FALSE_GATES_OR_SELECTION"):
            rf.verify_manifest(fake)
        fake=deepcopy(b);fake["historical_B_live_not_this_EV01"]=False
        with self.assertRaisesRegex(ArenaContractError,"RF01_COMPONENT_OR_HISTORICAL_STATE_FALSE"):
            rf.verify_manifest(fake)
        raw,verified=self.source("B","O0")
        raw["status"]="REAL_CLOUDFLARE_WORKERS_AI"
        with self.assertRaisesRegex(ArenaContractError,"RF01_WORKER_PROVENANCE_MISMATCH"):
            rf.classify_worker(self.views["O0"],"B","O0",raw,verified,self.baseline)

    def test_T07_O0_can_never_advertise_O1_physical_read(self):
        d=self.method("D","O0")
        d["native_fields_read"].append("construction.physical_observation")
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_FIELD_ACTOR_OR_CONSUMPTION_FALSIFIED"):
            rf.verify_manifest(d)

    def test_T12_T16_CSV_G2_and_good_RMSE_do_not_grant_scientific_G3(self):
        m=self.method("M","O0")
        m["g3"]="G3_PASS_AFTER_COMPILATION"
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_NATIVE_METHOD_FALSE_GATES_OR_SELECTION"):
            rf.verify_manifest(m)
        m=self.method("M","O0")
        m["gates_by_candidate"]=[{"id":"C00","G3":"PASS"}]
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_NATIVE_METHOD_FALSE_GATES_OR_SELECTION"):
            rf.verify_manifest(m)

    def test_parity_owns_candidates_and_D_imports_E1_prior_explicitly(self):
        common={
            "G2":"PASS_REAL_OMC_MATERIAL_BALANCE_ENGINEERING",
            "G3":"CONSTRUCTION_DESCRIPTIVE_ONLY_NO_ADMISSIBILITY_THRESHOLD",
            "no_structure_selection":True,
            "parameters_nominal_unfitted":True,
            "independent_forecast":"NOT_RUN",
            "native_model_sha256":"sha256:"+"1"*64,
            "trace_sha256":"sha256:"+"2"*64,
            "full_candidate_hash":"sha256:"+"3"*64,
            "source_snapshot_hash":self.views["O0"]["source_snapshot_hash"],
            "native_model":"NativeTest",
            "metrics":{"comparison_semantics":"SAME_PUBLIC_POS_DELIVERED_COUNTS_AND_HJ",
                       "delivery_rmse_orders":4.3202}
        }
        for arm in ("D","M"):
            p=rf.classify_parity(common,arm,"O0",self.baseline)
            self.assertTrue(rf.verify_manifest(p))
            self.assertEqual("ARENA_POLICY",p["selection_decision_owner"])
            self.assertFalse(p["independent_method_convergence"])
            bad=deepcopy(p);bad["selection_decision_owner"]="NATIVE_METHOD"
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF01_PARITY_LAUNDERED_AS_NATIVE_METHOD"):
                rf.verify_manifest(bad)
            if arm=="D":
                self.assertEqual(["E1_PARAMETER_PRIOR_IN_D_PARITY"],
                                 p["cross_arm_prior_imports"])
                hidden=deepcopy(p);hidden["cross_arm_prior_imports"]=[]
                with self.assertRaisesRegex(ArenaContractError,
                                            "RF01_CROSS_ARM_PRIOR_HIDDEN"):
                    rf.verify_manifest(hidden)

    def test_astra_six_pure_validator_reproductions_now_fail_individually(self):
        base=self.method("M","O1")
        def mutate(x, mode):
            if mode=="entrypoint":
                x["original_entrypoint"]="fake_pos_native_fit_and_select"
            elif mode=="source_sha":
                x["original_source_sha"]="gitblob:"+"f"*40
            elif mode=="candidate_id_cropped":
                x["native_candidate_ids"]=x["native_candidate_ids"][:1]
            elif mode=="duplicate_six_candidate_hashes":
                x["native_candidate_hashes"]=[x["native_candidate_hashes"][0]]*6
            elif mode=="physical_consumption_promoted":
                x["input_fields_used_or_rejected"][-1]["status"]="SUPPORTED_AND_CONSUMED"
            elif mode=="entrypoint_deleted":
                del x["original_entrypoint"]
            else:
                raise AssertionError(mode)
        for mode in ("entrypoint","source_sha","candidate_id_cropped",
                     "duplicate_six_candidate_hashes",
                     "physical_consumption_promoted","entrypoint_deleted"):
            with self.subTest(astra_probe=mode):
                forged=deepcopy(base)
                mutate(forged,mode)
                with self.assertRaises(ArenaContractError):
                    rf.verify_manifest(forged)

    def test_strict_variant_rejects_undeclared_fields_or_false_consumption(self):
        m=self.method("M","O0")
        self.assertEqual("igc-arena-method-fidelity/1.1",m["schema"])
        self.assertTrue(rf.verify_manifest(m))
        self.assertTrue(m["native_component_execution_complete"])
        self.assertFalse(m["arena_task_complete"])
        self.assertEqual(["construction.observation_series"],
                         m["adapter_fields_read"])
        self.assertEqual([],m["native_fields_read"])
        self.assertEqual([],m["transport_fields_submitted"])
        self.assertFalse(any(x["status"]=="SUPPORTED_AND_CONSUMED"
                             for x in m["input_fields_used_or_rejected"]))
        for key,val in (
            ("input_fields_used_or_rejected",[]),
            ("native_fields_read",["construction.observation_series"]),
            ("transport_fields_submitted",["construction.observation_series"]),
            ("native_component_execution_complete",False),
            ("method_capabilities_in_scope",["PREDICTIVE_CAFETERIA_MODEL"]),
        ):
            with self.subTest(edited_field=key):
                forged=deepcopy(m)
                forged[key]=val
                with self.assertRaises(ArenaContractError):
                    rf.verify_manifest(forged)
        x=deepcopy(m);x["new_pass_field"]="METHOD_COMPLETE"
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_MANIFEST_REQUIRED_FIELDS_OR_EXTRA"):
            rf.verify_manifest(x)

    def test_original_D_rejects_before_native_read_but_adapter_reads_series(self):
        d=self.method("D","O0")
        self.assertEqual(["construction.observation_series"],
                         d["adapter_fields_read"])
        self.assertEqual([],d["native_fields_read"])
        self.assertEqual([],d["transport_fields_submitted"])
        self.assertTrue(all(x["actor"].startswith("ARENA_") for x in
                            d["input_fields_used_or_rejected"]))
        bad=deepcopy(d)
        bad["input_fields_used_or_rejected"][1]["actor"]="D_GENERATE"
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_FIELD_ACTOR_OR_CONSUMPTION_FALSIFIED"):
            rf.verify_manifest(bad)

    def test_m_own_enumerator_complete_but_arena_task_not_complete(self):
        m=self.method("M","O1")
        self.assertTrue(m["native_component_execution_complete"])
        self.assertFalse(m["arena_task_complete"])
        self.assertFalse(m["method_complete"])
        self.assertEqual("METHOD_ABSTAINED",m["execution_state"])
        self.assertEqual("ARENA_M0_BRIDGE_UNRESOLVED_SELECTION",m["abstention_origin"])

    def test_native_manifest_binds_to_raw_worker_receipt_and_view(self):
        m=self.method("M","O1")
        receipt,verified=self.source("M","O1")
        self.assertTrue(rf.verify_manifest(
            m,baseline=self.baseline,receipt=receipt,worker=verified,
            visible=self.views["O1"]))
        forged=deepcopy(m)
        forged["worker_receipt_sha"]="sha256:"+"a"*64
        with self.assertRaisesRegex(ArenaContractError,
                                    "RF01_NOT_BOUND_TO_ORIGINAL_RECEIPT"):
            rf.verify_manifest(forged,baseline=self.baseline,receipt=receipt,
                               worker=verified,visible=self.views["O1"])

    def test_malformed_public_scope_rejected_before_method(self):
        bad=deepcopy(self.views["O0"])
        bad["construction"]["physical_observation"]={
            "stage_disclosed":"preparacion"}
        raw,verified=self.source("D","O0")
        with self.assertRaisesRegex(ArenaContractError,
                                    "A1_CONSTRUCTION_SHAPE"):
            rf.classify_worker(bad,"D","O0",raw,verified,self.baseline)


if __name__=="__main__":
    unittest.main()
