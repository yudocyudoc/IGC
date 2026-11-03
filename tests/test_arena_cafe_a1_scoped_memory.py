"""A1 real ledger/ATMS scope tests; no claim of OS or GitHub ACL."""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import unittest

from scripts.arena_cafe import ev01,evidence,scoped_memory as memory
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError,digest
from scripts.ledger import Ledger,IdempotencyConflict

STAMP="2026-11-02T16:00:00Z"
FUTURE="2026-11-02T16:01:00Z"


class ScopedMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw,checkpoints=ev01.trace_generator()
        ev01.verify_des_parity(checkpoints)
        cls.views=evidence.build(obs.project_events(raw,"POS"),
                                 obs.project_events(raw,"FULL"))["views"]

    def receipt(self,arm,condition):
        visible=self.views[condition]
        return {"schema":"igc-a1-isolated-worker-receipt/0.1",
                "arm":arm,"condition":condition,"status":{
                    "D":"BLOCKED_NOMINAL_PULSE_MISSING",
                    "B":"ORIGINAL_ENGINE_OFFLINE_MOCK",
                    "M":"ORIGINAL_E1_ENUMERATOR_ENGINEERING_ONLY"}[arm],
                "visible_input_hash":digest(visible),
                "source_snapshot_hash":visible["source_snapshot_hash"],
                "scientific_use_proven":False,"provider_calls":0}

    def test_real_sqlite_append_atms_and_condition_arm_boundary(self):
        with TemporaryDirectory() as temp:
            db=Path(temp)/"source-ledger.sqlite"
            expected={}
            for condition,arm in [("O0","D"),("O1","D"),("O0","M"),("O1","B")]:
                out=memory.record(db,self.views[condition],arm,condition,"worker",
                                  self.receipt(arm,condition),timestamp=STAMP)
                expected[(condition,arm)]=out
                self.assertEqual(4,out["revisions"])
                self.assertTrue(out["ledger_integrity_verified"])
                self.assertEqual(1,out["retrieval_count"])
                self.assertTrue(out["atms_outcome"]["supported"])
                self.assertEqual("NOT_ESTABLISHED",out["empirical_truth_from_ATMS"])
                self.assertEqual("PARTIAL_APP_LEVEL_NO_FORMAL_OS_OR_API_ACL",
                                 out["memory_gate"])
            one=memory.inspect(db,self.views["O0"],"D","O0","worker",at=FUTURE)
            self.assertEqual(one["context"]["case_id"],expected[("O0","D")][
                "context"]["case_id"])
            self.assertNotEqual(one["context"]["case_id"],expected[("O1","D")][
                "context"]["case_id"])
            self.assertNotEqual(one["atms_projection_hash"],expected[("O0","M")][
                "atms_projection_hash"])
            with sqlite3.connect(db) as connection:
                self.assertEqual(16,connection.execute(
                    "SELECT count(*) FROM entity_revisions").fetchone()[0])
            # Public API explicitly scopes the SQL snapshot before projection.
            case=memory.scope(self.views["O0"],"D","O0","worker")["case_id"]
            own=Ledger(db,memory.MIGRATION).snapshot(case_id=case,as_known_at=FUTURE)
            self.assertEqual(4,len(own))
            self.assertTrue(all("O1" not in r.entity_id and "M-O0" not in r.entity_id
                                and r.case_id==case for r in own))

    def test_early_cutoff_and_unowned_scope_fail_closed(self):
        with TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.sqlite"
            memory.record(db,self.views["O0"],"D","O0","worker",
                          self.receipt("D","O0"),timestamp=STAMP)
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_MISSING_OR_UNAUTHORIZED_SCOPE"):
                memory.inspect(db,self.views["O0"],"D","O0","worker",
                               at="2026-11-02T15:59:59Z")
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_MISSING_OR_UNAUTHORIZED_SCOPE"):
                memory.inspect(db,self.views["O1"],"D","O1","worker",at=FUTURE)
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_MISSING_OR_UNAUTHORIZED_SCOPE"):
                memory.inspect(db,self.views["O0"],"M","O0","worker",at=FUTURE)

    def test_receipt_swapping_and_fabricated_scientific_result_rejected(self):
        with TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.sqlite"
            o0=self.views["O0"]
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_WORKER_SOURCE_OR_SCOPE_MISMATCH"):
                memory.record(db,o0,"D","O0","worker",
                              self.receipt("D","O1"),timestamp=STAMP)
            falsified=self.receipt("D","O0")
            falsified["scientific_use_proven"]=True
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_WORKER_SOURCE_OR_SCOPE_MISMATCH"):
                memory.record(db,o0,"D","O0","worker",falsified,timestamp=STAMP)
            bogus=self.receipt("D","O0")
            bogus["status"]="NATIVE_G2_MATERIAL_BALANCE_PASS_ENGINEERING_ONLY"
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_STATUS_NOT_ORIGINAL_METHOD"):
                memory.record(db,o0,"D","O0","worker",bogus,timestamp=STAMP)

    def test_idempotent_replay_but_changed_receipt_is_conflict(self):
        with TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.sqlite"
            receipt=self.receipt("M","O1")
            first=memory.record(db,self.views["O1"],"M","O1","worker",
                                receipt,timestamp=STAMP)
            second=memory.record(db,self.views["O1"],"M","O1","worker",
                                 receipt,timestamp=STAMP)
            self.assertEqual(first["atms_projection_hash"],second["atms_projection_hash"])
            self.assertEqual(4,second["revisions"])
            mutated={**receipt,"candidate_count":1000}
            with self.assertRaises(IdempotencyConflict):
                memory.record(db,self.views["O1"],"M","O1","worker",
                              mutated,timestamp=STAMP)

    def test_native_manifest_receipt_and_hj_must_be_bound(self):
        from scripts.arena_cafe import native_pos_scenario
        visible=self.views["O0"]
        _,_,manifest=native_pos_scenario.build(visible,"D","O0")
        result={"arm_id":"D","condition_id":"O0",
                "status":"NATIVE_G2_MATERIAL_BALANCE_PASS_ENGINEERING_ONLY",
                "nominal_parameters_are_assumptions":True,
                "candidate_full_hash":digest(manifest["candidate"])}
        hj={"arm_id":"D","condition_id":"O0",
            "visible_input_hash":digest(visible),
            "status":"DESCRIPTIVE_HJ_PROBE_ONLY_UNVERIFIED_TRACE",
            "scientific_status":"NOT_ESTABLISHED"}
        with TemporaryDirectory() as temp:
            db=Path(temp)/"db.sqlite"
            good=memory.record(db,visible,"D","O0","native",result,
                               manifest=manifest,hj=hj,timestamp=STAMP)
            self.assertEqual(4,good["revisions"])
            altered=deepcopy(manifest)
            altered["candidate"]["nominal_parameters"]["capacity"]=999
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_CANDIDATE_CROSS_LINK_MISMATCH"):
                memory.record(db,visible,"D","O0","native",result,
                              manifest=altered,hj=hj,timestamp=STAMP)
            swapped={**hj,"condition_id":"O1"}
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_MEMORY_HJ_SCOPE_OR_CLAIM_MISMATCH"):
                memory.record(db,visible,"D","O0","native",result,
                              manifest=manifest,hj=swapped,timestamp=STAMP)


if __name__=="__main__":
    unittest.main()
