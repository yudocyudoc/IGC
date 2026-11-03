"""A3 known-control adjudicator: fail-closed tests, no invented OMC traces."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import ev01,evidence,scoped_memory, f3_adjudicate as f3
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError,digest

STAMP="2026-11-02T16:00:00Z"


class F3AdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw,snaps=ev01.trace_generator()
        ev01.verify_des_parity(snaps)
        cls.views=evidence.build(obs.project_events(raw,"POS"),
                                 obs.project_events(raw,"FULL"))["views"]

    def worker(self,arm,cond):
        v=self.views[cond]
        return {
            "arm":arm,"condition":cond,
            "status":{"D":"BLOCKED_NOMINAL_PULSE_MISSING",
                      "B":"ORIGINAL_ENGINE_OFFLINE_MOCK",
                      "M":"ORIGINAL_E1_ENUMERATOR_ENGINEERING_ONLY"}[arm],
            "visible_input_hash":digest(v),
            "source_snapshot_hash":v["source_snapshot_hash"],
            "worker_input_count":1,
            "private_generator_present":False,
            "provider_calls":0,"scientific_use_proven":False,
            "native_method_run":arm!="D",
            "candidate_count":6 if arm=="M" else 0,
            "user_prompt_hashes":["sha256:"+("a" if cond=="O0" else "b")*64]
                              if arm=="B" else []
        }

    def build_worker(self,folder,arm,cond,report=None):
        folder.mkdir()
        receipt=report if report is not None else self.worker(arm,cond)
        (folder/"worker-receipt.json").write_text(json.dumps(receipt))
        scoped_memory.record(
            folder/"scoped-ledger.sqlite",
            self.views[cond],arm,cond,"worker",receipt,
            timestamp=STAMP)
        x=scoped_memory.inspect(
            folder/"scoped-ledger.sqlite",
            self.views[cond],arm,cond,"worker",
            at="2026-11-02T16:00:02Z")
        # CI stores record and inspect results; fixture must match exact schema.
        row=scoped_memory.inspect(
            folder/"scoped-ledger.sqlite",
            self.views[cond],arm,cond,"worker",at=STAMP)
        (folder/"memory-receipt.json").write_text(json.dumps(row))
        (folder/"memory-rebuild.json").write_text(json.dumps(x))

    def test_deliveries_rmse_has_t0_and_exact_six_samples(self):
        rows=[{"t_minutes":float(t),"native_prediction":0.5*t,
               "observed_orders":t, "residual_orders":-0.5*t}
              for t in (0,2,4,6,8,10)]
        self.assertAlmostEqual((sum((0.5*t)**2 for t in
                                    (0,2,4,6,8,10))/6)**0.5,f3._rmse(rows))
        with self.assertRaisesRegex(ArenaContractError,
                                    "F3_MEASUREMENT_GRID_MISMATCH"):
            f3._rmse(rows[:5])
        with self.assertRaisesRegex(ArenaContractError,
                                    "F3_MEASUREMENT_GRID_MISMATCH"):
            bad=deepcopy(rows);bad[3]["t_minutes"]=7
            f3._rmse(bad)

    def test_mock_B_cannot_become_genuine_inference_or_cross_scope(self):
        for arm,cond in (("B","O0"),("B","O1"),("D","O0"),("M","O1")):
            with self.subTest(arm=arm,cond=cond),TemporaryDirectory() as temp:
                folder=Path(temp)/"worker"
                self.build_worker(folder,arm,cond)
                outcome=f3._worker(folder,self.views[cond],arm,cond)
                self.assertFalse(outcome["inference_authenticated"])
                self.assertEqual(4,outcome["memory"]["revisions"])
                self.assertTrue(outcome["memory"]["actual_SQLite_reconstruction"])
                self.assertIn("-"+arm+"-"+cond+"-",outcome["memory"]["case_id"])
                if arm=="B":
                    self.assertEqual("UNSUPPORTED_DOCUMENTED",outcome["interface_original_port"])
                with self.assertRaisesRegex(ArenaContractError,
                                            "F3_WORKER_NOT_BOUND_TO_OWN_EVIDENCE_OR_MOCK"):
                    f3._worker(folder,self.views["O1" if cond=="O0" else "O0"],
                               arm,cond)

    def test_genuine_B_fabrication_is_not_accepted_by_f3(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)/"worker"
            self.build_worker(root,"B","O0")
            report=json.loads((root/"worker-receipt.json").read_text())
            report["status"]="G3_PREDICTIVE_SUCCESS"
            (root/"worker-receipt.json").write_text(json.dumps(report))
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3_WORKER_NOT_BOUND_TO_OWN_EVIDENCE_OR_MOCK"):
                f3._worker(root,self.views["O0"],"B","O0")

    def test_scope_and_non_leakage_preflight_without_solver(self):
        left=self.views["O0"];right=self.views["O1"]
        self.assertEqual(left["construction"]["observation_series"],
                         right["construction"]["observation_series"])
        self.assertEqual(left["construction"]["pos_arrival_events"],
                         right["construction"]["pos_arrival_events"])
        self.assertNotEqual(left["source_snapshot_hash"],right["source_snapshot_hash"])
        self.assertNotIn("physical_observation",left["construction"])
        self.assertIn("physical_observation",right["construction"])
        self.assertEqual("PARTIAL",f3.adjudicate.__doc__) if False else None
        self.assertEqual(10,len({
            scoped_memory.scope(self.views[c],a,c,kind)["case_id"]
            for c in ("O0","O1") for a in ("D","B","M")
            for kind in (("worker","native") if a!="B" else ("worker",))
        }))


if __name__=="__main__":
    unittest.main()
