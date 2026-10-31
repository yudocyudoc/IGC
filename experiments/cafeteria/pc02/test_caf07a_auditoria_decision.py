#!/usr/bin/env python3
"""CAF07A: catches category errors, cost arbitrariness, and audit contamination."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf07a_auditoria_decision as a
from experiments.cafeteria.pc01 import caf01_des_engine as des


class AuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank,cls.predictions=a.historical_bank()
        cls.ids=next(x["ids"] for x in a.scenario_sets(
            cls.bank,cls.predictions) if x["initial_delivery"]==9)

    def test_original_pr116_canonical_digest_and_cost_sensitivity(self):
        self.assertEqual(len(self.bank),12)
        self.assertEqual(len(self.predictions),12)
        self.assertEqual(len(self.ids),9)
        rows=a.action_metrics(self.bank,self.predictions,self.ids)
        by={r["action_id"]:r for r in rows}
        self.assertEqual(by["prep_dispatch_18_t20"]["pair_separated"],20)
        self.assertEqual(by["prep_dispatch_18_t20"]["cost_units"],7)
        self.assertEqual(by["delivered_15_t20"]["pair_separated"],12)
        self.assertEqual(by["delivered_15_t20"]["cost_units"],1)
        audit=a.lambda_audit(rows)
        winners={r["lambda"]:r["chosen"] for r in audit["sweep"]}
        self.assertEqual(winners["1"],"prep_dispatch_18_t20")
        self.assertEqual(winners["3/2"],"delivered_15_t20")
        self.assertIn("4/3",
                      audit["all_nonnegative_pairwise_crossover_lambdas"])
        self.assertTrue(audit[
            "prior_uniform_not_asserted_but_equal_pair_weights_implicit"])

    def test_guaranteed_stage_purity_differs_from_pair_separation(self):
        rows=a.action_metrics(self.bank,self.predictions,self.ids)
        by={r["action_id"]:r for r in rows}
        self.assertEqual(by["delivered_15_t20"][
            "guaranteed_hypotheses"],0)
        self.assertLess(
            by["prep_dispatch_18_t20"]["guaranteed_hypotheses"],
            len(self.ids))
        for r in rows:
            self.assertEqual(
                sum(v["total"] for v in r["per_stage"].values()),
                len(self.ids))
            self.assertEqual(
                sum(v["guaranteed"] for v in r["per_stage"].values()),
                r["guaranteed_hypotheses"])
            self.assertTrue(r["pure_over_every_plus_minus_one_observation"])
        decision=a.corrected_decision(
            self.bank,self.predictions,self.ids)
        self.assertIsNone(decision["next_action"] if decision[
            "status"]==a.MODE else None)
        front=a.pareto_frontier(rows)
        self.assertEqual(decision["pareto"],front)
        self.assertTrue(front)

    def test_model_gap_and_no_guaranteed_information_stay_different(self):
        empty=a.corrected_decision(self.bank,self.predictions,[])
        self.assertEqual(empty["status"],a.legacy.MODEL_GAP)
        only=[h["id"] for h in self.bank
              if h["bottleneck"]=="entrega"]
        self.assertEqual(a.corrected_decision(
            self.bank,self.predictions,only)["status"],
            "STOP_DECISION_ALREADY_RESOLVED")
        # Any zero-cost/counterfeit model operator must never enter the bank.
        for action in a.AFFORDABLE:
            self.assertGreater(action["cost"],0)
        self.assertEqual(
            a.measure_physical({
                "schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
                "stages":[{"servers":1,"service_minutes":"1"}]*4
            }, "3/2",20,(("waiting","preparacion"),))["status"],
            "UNSUPPORTED_TOPOLOGY_FOUR_STAGES")

    def test_two_measures_share_budget_and_cannot_be_labeled_adaptive(self):
        self.assertGreater(len(a.PAIR_MENU),0)
        for x,y in a.PAIR_MENU:
            self.assertLessEqual(x["cost"]+y["cost"],
                                 a.legacy.BUDGET_COST_UNITS)
            self.assertNotEqual(x["id"],y["id"])
        metrics=a.action_metrics(self.bank,self.predictions,self.ids)
        compared=a.fixed_two_measurement_audit(
            self.bank,self.predictions,self.ids,metrics)
        self.assertTrue(compared[
            "adaptive_second_measurement_NOT_implemented"])
        self.assertEqual(compared["n_pairs_budget_feasible"],
                         len(a.PAIR_MENU))
        self.assertLessEqual(compared["best_fixed_pair_nominal_rule"][
            "cost_units"],8)

    def test_176_cases_prespecified_before_any_new_world_DES_and_hashes(self):
        candidates=a.sweep_worlds()
        self.assertEqual(len(candidates),176)
        self.assertEqual(sum(x["type"]==
                             "one_bottleneck_in_family_topology"
                             for x in candidates),168)
        self.assertEqual(sum(x["type"]=="two_simultaneous_bottlenecks"
                             for x in candidates),6)
        self.assertEqual(sum(x["type"]==
                             "four_stages_not_in_sensor_contract"
                             for x in candidates),2)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"caf07a"
            original=des.run_toy_engine
            frozen_train_configs=[
                h["config"] for h in self.bank]
            counts={"hyp":0,"world":0}
            def wrap(config,arrivals,observations):
                if config in frozen_train_configs and not target.exists():
                    counts["hyp"]+=1
                else:
                    counts["world"]+=1
                    plan=target/"00_AUDITORIA_Y_PRECOMPROMISO.json"
                    checkpoint=target/"00B_CHECKPOINT_PRE_SWEEP.json"
                    self.assertTrue(plan.is_file())
                    self.assertTrue(checkpoint.is_file())
                    self.assertFalse((target/"01_RESULTADOS.json").exists())
                    obj=json.loads(plan.read_bytes())
                    self.assertEqual(len(obj["all_sweep_worlds_predeclared"]),
                                     176)
                    self.assertEqual(obj["evaluation_world_DES_calls_before_plan"],
                                     0)
                    self.assertEqual(obj["PR116_original_plan_SHA256"],
                                     a.PR116_PLAN_SHA)
                    self.assertEqual(obj["focus_original_K0_9"][
                        "corrected_selector"]["status"],
                        a.corrected_decision(
                            self.bank,self.predictions,self.ids)["status"])
                    cp=json.loads(checkpoint.read_bytes())
                    self.assertEqual(
                        cp["precommit_sha256"],a.lab.sha(plan.read_bytes()))
                    self.assertEqual(cp["new_world_DES_calls_so_far"],0)
                return original(config,arrivals,observations)
            with patch.object(des,"run_toy_engine",side_effect=wrap):
                result=a.run(target)
            # A new evaluator config might match a 60/75/90/105 hypothesis
            # only at an accidentally equal service time; sweep 55..110 includes
            # 60/75/90/105; all are treated as world after target exists.
            self.assertEqual(counts["hyp"],120)
            self.assertEqual(counts["world"],result["evaluation_DES_runs"])
            self.assertEqual(result["new_world_count"],176)
            self.assertEqual(result["training_hypothesis_DES_runs_recomputed"],120)
            self.assertTrue(result["no_claim_of_independence"])
            self.assertEqual(result["status"],
                "CAF07A_METHOD_CORRECTION_AUDITED_AND_SWEEP_EXECUTED")
            self.assertEqual(len(result["evaluation"]),176)
            self.assertEqual(result["summary"][
                "four_stages_not_in_sensor_contract"]["no_operator"],2)
            self.assertEqual(len((target/"02_BARRIDO_CASOS.csv").read_text().splitlines()),
                             result["evaluation_DES_runs"]-(168+6)+2+1)
            manifest=json.loads((target/"04_MANIFIESTO.json").read_bytes())
            self.assertTrue(manifest["precommit_before_all_new_worlds"])
            for file,digest in manifest["files_sha256"].items():
                self.assertEqual(digest,
                                 a.lab.sha((target/file).read_bytes()))
            with self.assertRaisesRegex(ValueError,
                                        "CAF07A_OUTPUT_ALREADY_EXISTS"):
                a.run(target)


if __name__=="__main__":
    unittest.main()
