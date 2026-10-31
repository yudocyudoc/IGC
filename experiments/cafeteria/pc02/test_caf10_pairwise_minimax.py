"""CAF-10: synthetic controls for exact minimax and provenance (no success assertions)."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import tempfile
import unittest

import caf07b_umbral_secuencial as b
import caf09_policy_observability as c9
import caf10_pairwise_minimax as x

SHA = "a"*40
HEAD = "b"*40


class CAF10Tests(unittest.TestCase):
    def test_frozen_worlds_and_no_historical_double_leak(self):
        w = x.worlds()
        self.assertEqual(len(w), 195)
        self.assertEqual(Counter(v["cohort"] for v in w),
                         {"H_HISTORICAL_168": 168,
                          "N_NEW_DOUBLE_24": 24,
                          "S_EXTRA_UNKNOWN_3": 3})
        self.assertEqual(len(set(v["id"] for v in w)),195)
        self.assertEqual(set(v["capacity"] for v in w
                             if v["cohort"]=="N_NEW_DOUBLE_24"),
                         set(x.DOUBLE_CAPS))
        self.assertEqual(set(x.DOUBLE_CAPS) & {55,90},set())
        self.assertEqual(x.DOUBLE_CAPS,(57,63,69,77,83,97,103,109))
        self.assertEqual(len({(v["capacity"],v["truth_class"])
                              for v in w if v["cohort"]=="H_HISTORICAL_168"}),168)
        self.assertTrue(all(v["truth_class"] is None for v in w
                            if v["cohort"]=="S_EXTRA_UNKNOWN_3"))

    def test_exhaustive_minimax_bound_and_nontransitivity(self):
        rows=[{"id":"a","decision_class":"A"},
              {"id":"b","decision_class":"B"}]
        probe=b.FIRST_ACTION_ID
        near={"a":{probe:[0]},"b":{probe:[2]}}
        far={"a":{probe:[0]},"b":{probe:[3]}}
        self.assertEqual(set(x.plausible([0])),{(0,),(1,)})
        self.assertEqual(set(x.plausible([2])),{(1,),(2,),(3,)})
        m=x.minimax_outcomes(rows,near,["a","b"],probe)
        n=x.minimax_outcomes(rows,far,["a","b"],probe)
        self.assertEqual(m["worst_surviving_classes"],2)
        self.assertEqual(n["worst_surviving_classes"],1)
        self.assertEqual((m["worst_surviving_hypotheses"],
                          n["worst_surviving_hypotheses"]),(2,1))
        self.assertEqual(n["distinct_possible_integer_observations"],5)
        self.assertTrue(n["no_probability_weights_assigned"])

    def test_minimax_gate_and_order_refuse_irrelevant_measurements(self):
        rows=[{"id":"a","decision_class":"A"},
              {"id":"b","decision_class":"B"}]
        # All actions identical within tolerance: no separated pair.
        pred={h["id"]:{a["id"]:[0]*len(a["channels"])
                       for a in b.ACTIONS} for h in rows}
        stopped=x.minimax_select(rows,pred,["a","b"])
        self.assertIsNone(stopped["action"])
        self.assertEqual(stopped["status"],
                         "NO_ROBUST_PAIR_FOR_ANY_AFFORDABLE_PROBE")
        self.assertIsNone(x.minimax_select(rows,pred,[])["action"])
        self.assertIsNone(x.minimax_select(rows,pred,["a"])["action"])
        self.assertEqual(len(x.affordable()),7)
        self.assertEqual(b.TOLERANCE,1)
        self.assertEqual(b.BUDGET,8)

    def test_source_policy_and_evaluator_parity_on_original_11(self):
        self.assertIs(x.c9.choose_relaxed,c9.choose_relaxed)
        self.assertIs(x.b.choose_second,b.choose_second)
        self.assertIs(x.b.update,b.update)
        self.assertIs(x.b.read_physical,b.read_physical)
        rows=b.bank(True)
        pred=b.precompute(rows)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for world in b.scenarios():
                legacy=b.evaluate_case(
                    world,rows,pred,"parity_"+world["id"],root)
                self.assertEqual(x.classification(legacy["final"],world),
                                 legacy["verdict_EVALUATOR_ONLY"])
                normalized=x.normalize_strict(legacy, {
                    **world,"cohort":"synthetic","capacity":world["capacity"]})
                self.assertEqual(normalized["verdict_EVALUATOR_ONLY"],
                                 legacy["verdict_EVALUATOR_ONLY"])

    def test_minimax_decision_is_actual_lexicographic_minimum(self):
        rows=b.bank(True)
        pred=b.precompute(rows)
        one=b.scenarios()[0]
        baseline=b.read_physical(one["config"],b.caf07.T0_RATE,
                                 b.caf07.T0_MINUTE,(("delivered",None),))
        k0=b.eligible(rows,pred,{"baseline":baseline})
        k1=b.read_physical(one["config"],b.FIRST["rate"],
                           b.FIRST["minute"],b.FIRST["channels"])
        ids=b.eligible(rows,pred,{b.FIRST_ACTION_ID:k1},k0)
        score=x.minimax_select(rows,pred,ids)
        self.assertIsNotNone(score["action"])
        candidates=score["candidate_metrics"]
        self.assertGreater(len(candidates),1)
        expected=min(candidates,key=lambda v:(
            v["worst_surviving_classes"],v["worst_surviving_hypotheses"],
            v["cost"],v["action_id"]))
        self.assertEqual(score["action"]["id"],expected["action_id"])
        self.assertEqual(score["worst_case_class_reduction_guaranteed"],
                         len(b.classes(rows,ids))-
                         expected["worst_surviving_classes"])

    def test_run_plan_decisions_no_late_retraining_and_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"caf10"
            r=x.run(out,SHA,HEAD)
            self.assertEqual((r["n_worlds"],r["n_evaluations"],
                              r["n_presaved_choices"]),(195,585,585))
            self.assertEqual(len(list(out.glob("01_CHOICE_*.json"))),585)
            self.assertEqual(len(r["structural_graph_per_world"]),195)
            self.assertEqual(r["promotion_gate"],x.GATE)
            self.assertFalse(r["external_validity_proven"])
            self.assertTrue(r["certification_bank_always_expanded"])
            self.assertEqual(r["pr_head_sha"],HEAD)
            plan=json.loads((out/"00_FROZEN_PLAN.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],
                             "c683d6cbdf7055b7f664b1c7fc64b7e4f0f4eea8")
            self.assertTrue(plan["new_world_DES_calls_before_plan"]==0)
            self.assertEqual(plan["pr_head_sha"],HEAD)
            self.assertTrue(all(
                v["cost_spent"]<=8 for v in r["evaluations"]))
            for c in x.POLICIES:
                self.assertEqual(sum(
                    r["summary"][co][c]["n"] for co in r["summary"]),195)
            for world in x.worlds():
                same=[e for e in r["evaluations"] if e["case"]==world["id"]]
                self.assertEqual(len(same),3)
                self.assertEqual(len({tuple(e["baseline"]) for e in same}),1)
                self.assertEqual(len({tuple(e["first"]) for e in same}),1)
                self.assertEqual(len({tuple(e["survivors_after_first"])
                                      for e in same}),1)
                if world["truth_class"] is None:
                    self.assertTrue(all(e["label_coverage_EVALUATOR_ONLY"] is None
                                        for e in same))
            manifest=json.loads((out/"04_MANIFIESTO.json").read_text())
            for filename,digest in manifest["files_sha256"].items():
                self.assertEqual(
                    digest,"sha256:"+hashlib.sha256(
                        (out/filename).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"CAF10_OUTPUT_EXISTS"):
                x.run(out,SHA,HEAD)


if __name__=="__main__":
    unittest.main(verbosity=2)
