"""ARENA-EV01: same operation, 3 observation views, no latent-stage overclaim."""
from __future__ import annotations

import csv
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import arena_ev01_event_views as e
from scripts import arena_event_observability as o


class ArenaEV01EventViewsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth,cls.snaps=e.trace_generator()
        cls.views={v:o.project_events(cls.truth,v) for v in o.VIEWS}
        cls.metrics={v:o.analyze_view(cls.views[v],v,e.STAGES) for v in o.VIEWS}

    def test_exact_physics_and_native_DES_parity_9_checkpoints(self):
        proof=e.verify_des_parity(self.snaps)
        self.assertEqual(proof["status"],"PARITY_CONFIRMED_ALL_SNAPSHOTS")
        self.assertEqual(proof["n_checkpoints"],9)
        self.assertEqual(len(e.ARRIVALS),15)
        self.assertEqual(len(self.truth),225)
        self.assertEqual(self.snaps[-1]["accepted"],15)
        self.assertEqual(self.snaps[-1]["delivered"],15)
        self.assertEqual(self.snaps[-1]["pending"],0)
        for row in self.snaps:
            self.assertEqual(row["accepted"],row["delivered"]+row["pending"])
            self.assertEqual(row["pending"],sum(row["waiting"])+sum(row["in_service"]))
            self.assertTrue(all(x<=e.SPEC[i][0] for i,x in enumerate(row["in_service"])))

    def test_only_visible_events_no_hidden_truth_or_sequence_gaps(self):
        audit=e.inspect_visibility(*(self.views[v] for v in o.VIEWS),self.metrics)
        self.assertEqual(audit["same_cases"],15)
        self.assertTrue(audit["all_view_event_sequences_locally_reindexed"])
        self.assertEqual({v:len(self.views[v]) for v in o.VIEWS},
                         {"POS":45,"POS_KDS":75,"FULL":225})
        for v in o.VIEWS:
            rows=self.views[v]
            self.assertEqual([x["event_seq"] for x in rows],
                             list(range(len(rows))))
            self.assertTrue(all("provenance_EVALUATOR_ONLY" not in x for x in rows))
            self.assertTrue(all("truth" not in key.lower()
                                for x in rows for key in x.keys()))
        for v in ("POS","POS_KDS"):
            rows=self.views[v]
            self.assertTrue(all("resource_id" not in x for x in rows))
            self.assertNotIn("transferencia_final",str(rows))
            self.assertNotIn("caja",str(rows))
            self.assertNotIn("despacho",str(rows))
        self.assertTrue(all("stage" not in x for x in self.views["POS"]))
        self.assertTrue(any(x.get("stage")=="preparacion"
                            for x in self.views["POS_KDS"]))
        self.assertTrue(any(x.get("stage")=="transferencia_final"
                            for x in self.views["FULL"]))

    def test_cycle_time_same_in_all_views_and_full_closure(self):
        def by_id(view):
            return {c["case_id"]:c for c in self.metrics[view]["cases"]}
        a,b,c=(by_id(v) for v in o.VIEWS)
        self.assertEqual(set(a),set(b))
        self.assertEqual(set(b),set(c))
        self.assertEqual(len(a),15)
        for k in a:
            self.assertEqual(a[k]["cycle_minutes_exact"],
                             b[k]["cycle_minutes_exact"])
            self.assertEqual(b[k]["cycle_minutes_exact"],
                             c[k]["cycle_minutes_exact"])
            self.assertTrue(c[k]["cycle_balance_exact"])
            self.assertEqual(set(c[k]["per_stage_observed"]),set(e.STAGES))
            self.assertEqual(Q(c[k]["sum_wait_and_service_minutes_exact"]),
                             Q(a[k]["cycle_minutes_exact"]))
            self.assertNotIn("per_stage_observed",a[k])
            self.assertNotIn("per_stage_observed",b[k])

    def test_pos_nonidentifiability_and_kds_residual_noncausal(self):
        for x in self.metrics["POS"]["cases"]:
            T=Q(x["cycle_minutes_exact"])
            self.assertGreater(T,0)
            self.assertIn("waiting_time_by_stage",x["not_identifiable_from_view"])
            w=x["timing_only_counterexamples"]
            self.assertEqual(len(w),2)
            self.assertNotEqual(w[0],w[1])
            self.assertTrue(all(Q(v["waiting"])+Q(v["service"])==T for v in w))
            self.assertFalse(self.metrics["POS"]["unknown_stage_inferred"])
        for row in self.metrics["POS_KDS"]["cases"]:
            T=Q(row["post_prep_elapsed_minutes_exact"])
            self.assertGreater(T,0)
            self.assertTrue(row["post_prep_is_not_evidence_of_hidden_stage"])
            w=row["timing_only_counterexamples_post_prep"]
            self.assertTrue(all(Q(v["unallocated_wait"])+
                                Q(v["unallocated_work"])==T for v in w))
            self.assertNotIn("per_stage_observed",row)
            self.assertIn("prep_wait_without_stage_entry",row["not_identifiable_from_view"])

    def test_error_handling_for_corrupt_or_privileged_view(self):
        bad=[dict(x) for x in self.views["POS"]]
        bad[0]["resource_id"]="hidden"
        with self.assertRaisesRegex(ValueError,"EV01_RESOURCE_LEAK"):
            o.analyze_view(bad,"POS")
        bad=[dict(x) for x in self.views["POS"]]
        bad[1]["t_minutes_exact"]="-1"
        with self.assertRaisesRegex(ValueError,"EV01_NEGATIVE_EVENT_TIME"):
            o.analyze_view(bad,"POS")
        bad=[dict(x) for x in self.views["POS"]]
        bad.pop(-1)
        with self.assertRaisesRegex(ValueError,"EV01_MISSING_OR_DUPLICATE_REQUIRED_EVENT"):
            o.analyze_view(bad,"POS")
        bad=[dict(x) for x in self.views["POS_KDS"]]
        bad[0]["stage"]="transferencia_final"
        with self.assertRaisesRegex(ValueError,"EV01_KDS_INTERNAL_EVENT_LEAK"):
            o.analyze_view(bad,"POS_KDS")
        bad=[dict(x) for x in self.views["FULL"]]
        which=next(i for i,x in enumerate(bad) if x["event_type"]=="etapa_entrada"
                   and x["stage"]=="preparacion")
        bad[which]["t_minutes_exact"]="0"
        with self.assertRaisesRegex(ValueError,"EV01_INVALID_PHYSICAL_STAGE_CHAIN"):
            o.analyze_view(bad,"FULL")

    def test_pm4py_dfg_only_mines_visible_activities_not_causality(self):
        dfg={v:o.pm4py_dfg(self.views[v]) for v in o.VIEWS}
        for v,d in dfg.items():
            self.assertEqual(d["n_cases"],15)
            self.assertTrue(d["dfg_is_observed_succession_not_causal_proof"])
            self.assertEqual(d["method"],"PM4Py.discover_dfg")
            self.assertGreater(len(d["edges"]),0)
            self.assertEqual(sum(d["start_activities"].values()),15)
            self.assertEqual(sum(d["end_activities"].values()),15)
            if v!="FULL":
                self.assertNotIn("transferencia_final",str(d))
        self.assertIn("transferencia_final",str(dfg["FULL"]))
        self.assertEqual(dfg["POS"]["n_activities"],3)
        self.assertEqual(dfg["POS_KDS"]["n_activities"],5)
        self.assertEqual(dfg["FULL"]["n_activities"],15)

    def test_full_artifact_is_reproducible_and_view_csv_is_redacted(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"ev01"
            result=e.run(path,"a"*40,"b"*40)
            self.assertEqual(result["n_orders"],15)
            self.assertEqual(result["n_event_rows_by_view"],
                             {"POS":45,"POS_KDS":75,"FULL":225})
            self.assertTrue(result["visibility_audit"]["full_15_of_15_cycle_balances"])
            self.assertTrue(result["no_grid_or_catalog"])
            self.assertTrue(result["no_inference_of_unknown_stage_from_residual"])
            self.assertEqual(result["promotion_gate"],e.GATE)
            plan=json.loads((path/"00_PLAN_BEFORE_TRACE.json").read_text())
            self.assertEqual(plan["precommit"],e.PRECOMMIT)
            self.assertEqual(plan["checkout_sha"],"a"*40)
            self.assertEqual(plan["pr_head_sha"],"b"*40)
            self.assertTrue(plan["no_parameter_grid"])
            for name,expected in (("POS",45),("POS_KDS",75),("FULL",225)):
                with (path/f"01_{name}_PUBLIC_EVENTS.csv").open(encoding="utf-8",newline="") as fh:
                    reader=csv.DictReader(fh)
                    self.assertNotIn("resource_id",reader.fieldnames) if name!="FULL" else None
                    self.assertNotIn("stage",reader.fieldnames) if name=="POS" else None
                    rows=list(reader)
                    self.assertEqual(len(rows),expected)
                    if name!="FULL":
                        self.assertNotIn("transferencia_final",str(rows))
            self.assertTrue((path/"03_REPORT.md").read_text(encoding="utf-8").startswith("# ARENA EV01"))
            manifest=json.loads((path/"04_MANIFEST.json").read_text())
            for filename,digest in manifest["files_sha256"].items():
                self.assertEqual(digest,"sha256:"+sha256(
                    (path/filename).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"EV01_REFUSE_OVERWRITE"):
                e.run(path,"a"*40,"b"*40)


if __name__=="__main__":
    unittest.main(verbosity=2)
