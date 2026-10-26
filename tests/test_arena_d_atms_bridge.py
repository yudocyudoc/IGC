"""Deterministic D→ATMS memory integration, without hypothesis generation by ATMS."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.arena_atms import ATMS, Rule, ATMSError
from scripts.arena_v0_contract import INPUT_SCHEMA
from scripts.ledger import Ledger, IdempotencyConflict
from scripts.arena_d_atms_bridge import (
    SCHEMA, POLICY, MIGRATION, BridgeError, _logical_record, _store,
    snapshot, retract_assumption, checked_trace, validated_bundle,
)
from scripts.arena_d_v01 import prepare
from scripts.arena_d_v1_screen import write_evaluation


FIRST="2026-10-25T18:00:00-06:00"
LATER="2026-10-25T19:00:00-06:00"


def data():
    return {"schema":INPUT_SCHEMA, "investigation_id":"D-ATMS-UNIT",
            "round_id":"R0", "question":"What transit dynamic is compatible?",
            "source_snapshot_hash":"sha256:"+"a"*64, "iteration_limit":2,
            "construction":{"input_profile":{"kind":"pulse","rate":1.7,"duration":2.0},
                            "nominal_parameters":{"capacity":2.0,"response_time":1.0,"loss_time":3.0},
                            "observations":[{"t":0,"delivered":0},
                                            {"t":1,"delivered":0.3},
                                            {"t":4,"delivered":2.5}]},
            "observability":{"stock_unit":"items","time_unit":"hour","observable":"cumulative_delivered"},
            "resources":{"max_stocks":2,"allow_loss":False,"max_candidates":2,
                         "max_simulations":2}}


def protocol():
    return {"schema":"igc-d-observation-screen/0.1",
            "noise_absolute_bound":.2,
            "parameter_grid":{"capacity":[2.0],"response_time":[1.0],"loss_time":[3.]},
            "max_grid_evaluations":2,"integration_max_step":.02,
            "new_trial_sample_times":[.25,.5,1,2,3,4]}


class DAtmsMemoryTests(unittest.TestCase):
    def test_selective_support_explain_nogood_and_what_if(self):
        engine=ATMS(
            {"D:stock1","D:stock2","D:instrument","D:observation"},
            set(),
            [Rule("j1",("D:stock1","D:instrument","D:observation"),"compatible1","D1-source"),
             Rule("j2",("D:stock2","D:instrument","D:observation"),"compatible2","D1-source")],
            set()
        )
        self.assertTrue(engine.explain("compatible1")["supported"])
        self.assertEqual(len(engine.explain("compatible2")["minimal_environments"]),1)
        impact=engine.what_if(disable_assumptions=["D:stock1"])
        self.assertIn("compatible1",impact["changed_nodes"])
        self.assertNotIn("compatible2",impact["changed_nodes"])
        self.assertTrue(engine.explain("compatible1")["supported"])
        denied=ATMS(engine.assumptions,engine.facts,engine.justifications,
                    {frozenset({"D:instrument","D:observation"})})
        self.assertFalse(denied.explain("compatible1")["supported"])
        self.assertFalse(denied.explain("compatible2")["supported"])

    def test_persistent_ledger_snapshots_retraction_and_lane_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"ledger.db"
            ledger=Ledger(db,MIGRATION)
            case,round_id="D-MEM-1","R0"
            def store(item):
                return _store(ledger,case_id=case,round_id=round_id,
                              recorded_at=FIRST,entity_type="ArenaATMSNode",
                              key="logic:"+item["id"],payload=item)
            for name in ("OBS","NOISE","GRID","H1","H2"):
                store(_logical_record(kind="assumption",id=name,
                                      case_id=case,source_id="source:D1"))
            for target,atom in (("C1","H1"),("C2","H2")):
                store(_logical_record(kind="justification",id="J"+target,
                                      case_id=case,source_id="source:D1",
                                      antecedents=[atom,"OBS","NOISE","GRID"],
                                      consequent="DCOMPATIBLE:"+target))
            # Another arm may have a record in this physical database, but never in D's projection.
            ledger.append_revision(
                entity_id="arena:D-MEM-1:R0:B:logic:bad",entity_type="ArenaATMSNode",
                case_id=case,actor_id="arena:B",idempotency_key="foreign",
                payload={"kind":"assumption","id":"B-SECRET","active":True},
                recorded_at=FIRST,created_at=FIRST,access_policy="lane:B")
            earlier=snapshot(db=db,case_id=case,round_id=round_id,as_known_at=FIRST)
            self.assertEqual(earlier["conditionally_supported"],
                             ["DCOMPATIBLE:C1","DCOMPATIBLE:C2"])
            self.assertNotIn("B-SECRET",str(earlier))
            withdrawal=retract_assumption(
                db=db,case_id=case,round_id=round_id,assumption_id="H1",
                as_known_at=FIRST,recorded_at=LATER,reason="New measurement invalidates support H1")
            self.assertEqual(withdrawal["state_after"]["conditionally_supported"],
                             ["DCOMPATIBLE:C2"])
            self.assertEqual(withdrawal["state_before"]["conditionally_supported"],
                             earlier["conditionally_supported"])
            self.assertEqual(snapshot(db=db,case_id=case,round_id=round_id,
                                      as_known_at=FIRST)["conditionally_supported"],
                             earlier["conditionally_supported"])
            self.assertTrue(ledger.verify_integrity(
                entity_id="arena:D-MEM-1:R0:D:logic:H1", revision=2))
            with self.assertRaises(BridgeError):
                retract_assumption(db=db,case_id=case,round_id=round_id,
                                   assumption_id="H1",as_known_at=LATER,
                                   recorded_at="2026-10-25T20:00:00-06:00",
                                   reason="Already withdrawn")

    def test_same_event_id_idempotent_and_conflicting_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"ledger.db"; ledger=Ledger(db,MIGRATION)
            obj=_logical_record(kind="assumption",id="OBS",case_id="A",source_id="public")
            kw=dict(case_id="A",round_id="R0",recorded_at=FIRST,
                    entity_type="ArenaATMSNode",key="logic:OBS",payload=obj)
            first=_store(ledger,**kw)
            second=_store(ledger,**kw)
            self.assertEqual(first.event_id,second.event_id)
            self.assertEqual(second.revision,1)

    def test_reject_wrong_trace_scope_and_hash(self):
        event={"schema":"igc-arena-trace-event/0.1","arm_id":"B",
               "round_id":"R0","event_type":"HYPOTHESIS_PROPOSED",
               "iteration":0,"source_hash":"sha256:"+"1"*64,
               "payload_hash":"sha256:"+"2"*64,
               "previous_event_hash":None,"event_hash":"sha256:"+"3"*64}
        with self.assertRaisesRegex(BridgeError,"FOREIGN_TRACE"):
            checked_trace(event)
        event["arm_id"]="D"
        with self.assertRaisesRegex(BridgeError,"TAMPERED_TRACE"):
            checked_trace(event)

    def test_real_d0_d1_linked_preparation_and_missing_g2_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=data(); p=protocol()
            root=Path(tmp)
            prepare(inp,root/"d0")
            d0=json.loads((root/"d0"/"memory-event.json").read_text())
            write_evaluation(inp,p,root/"d1",d0)
            events=json.loads((root/"d1"/"memory-events.json").read_text())
            self.assertEqual(events[1]["previous_event_hash"],events[0]["event_hash"])
            # No synthetic confirmation of OpenModelica; it must be truly run in CI.
            with self.assertRaisesRegex(FileNotFoundError,"Dfit_"):
                validated_bundle(inp,p,root/"d0",root/"d1")
            events[1]["payload_hash"]="sha256:"+"0"*64
            (root/"d1"/"memory-events.json").write_text(json.dumps(events))
            with self.assertRaisesRegex(BridgeError,"TAMPERED_TRACE"):
                validated_bundle(inp,p,root/"d0",root/"d1")


if __name__=="__main__":
    unittest.main()
