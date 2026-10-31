#!/usr/bin/env python3
"""CAF-07B checks that integrity does not masquerade as scientific accuracy."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf07b_umbral_secuencial as b
from experiments.cafeteria.pc01 import caf01_des_engine as des


SHA="0123456789abcdef"*2+"01234567"


class CorrectedPolicyTests(unittest.TestCase):
    def test_banks_include_simultaneous_constraints_and_hidden_extra_world(self):
        single=b.bank(False)
        mixed=b.bank(True)
        self.assertEqual(len(single),12)
        self.assertEqual(len(mixed),24)
        self.assertEqual(len({h["decision_class"] for h in single}),3)
        self.assertEqual(len({h["decision_class"] for h in mixed}),6)
        self.assertEqual(
            sum(len(h["nominal_limited_stages"])==2 for h in mixed),12)
        for hyp in mixed:
            c=des.validate_private_config(hyp["config"])
            self.assertEqual(len(c),3)
            self.assertEqual(
                sum(n==1 for n,_ in c),
                len(hyp["nominal_limited_stages"]))
        worlds=b.scenarios()
        self.assertEqual(len(worlds),11)
        self.assertEqual([v["truth_type"] for v in worlds].count("single"),3)
        self.assertEqual([v["truth_type"] for v in worlds].count("double"),6)
        self.assertEqual(
            [v["truth_type"] for v in worlds].count("unknown-extra"),2)
        self.assertEqual(
            [len(des.validate_private_config(v["config"]))
             for v in worlds[-2:]], [4,4])
        for v in worlds[-2:]:
            # No topology guard is called in the masked sensor interface.
            measured=b.read_physical(v["config"],"3/2",20,
                                     (("waiting","preparacion"),
                                      ("waiting","despacho")))
            self.assertEqual(len(measured),2)

    def test_threshold_picks_cheapest_qualifying_or_fails_closed(self):
        rows=b.bank(False)
        ids=[h["id"] for h in rows]
        preds={}
        for h in rows:
            vals={}
            for action in b.ACTIONS:
                # Distinct robust signal for each class on ALL actions
                # except cheaper delivery which is fully ambiguous.
                cls=b.STAGES.index(h["decision_class"])
                v=cls*10
                vals[action["id"]]=[0 if action["id"]==
                                   "delivered_15_t20" else v]*len(
                                       action["channels"])
            preds[h["id"]]=vals
        choice=b.choose_second(
            rows,preds,ids,remaining_budget=7,
            used_actions={b.FIRST_ACTION_ID})
        self.assertEqual(choice["status"],"MEASURE_SELECTED_AT_THRESHOLD")
        self.assertEqual(choice["action"]["cost"],2)
        self.assertNotEqual(choice["action"]["id"],b.FIRST_ACTION_ID)
        stopped=b.choose_second(
            rows,preds,ids,remaining_budget=1,
            used_actions={b.FIRST_ACTION_ID})
        self.assertEqual(stopped["status"],b.THRESHOLD_FAIL)
        self.assertIsNone(stopped["action"])
        self.assertEqual(b.choose_second(
            rows,preds,[],remaining_budget=7,
            used_actions={b.FIRST_ACTION_ID})["status"],b.MODEL_GAP)
        first_class=[h["id"] for h in rows
                     if h["decision_class"]=="preparacion"]
        self.assertEqual(b.choose_second(
            rows,preds,first_class,remaining_budget=7,
            used_actions={b.FIRST_ACTION_ID})["status"],
            "STOP_SINGLE_CLASS_WITHIN_BANK")
        with self.assertRaisesRegex(ValueError,
                                    "CAF07B_INVALID_REMAINING_BUDGET"):
            b.choose_second(rows,preds,ids,
                            remaining_budget=-1,used_actions=set())

    def test_guaranteed_resolution_checks_all_rivals_not_pairs_total(self):
        rows=b.bank(False)
        selected=[h for h in rows if h["capacity_per_hour"]==60]
        ids=[h["id"] for h in selected]
        preds={x["id"]:{"dummy":[i*4]} for i,x in enumerate(selected)}
        g=b.guarantee(rows,preds,ids,("dummy",))
        self.assertEqual(g["total_guaranteed"],3)
        self.assertTrue(g["all_classes_meet_minimum"])
        preds[ids[1]]["dummy"]=[2]
        ambiguous=b.guarantee(rows,preds,ids,("dummy",))
        self.assertEqual(ambiguous["total_guaranteed"],1)
        self.assertFalse(ambiguous["all_classes_meet_minimum"])
        self.assertEqual(ambiguous["by_class"]["entrega"]["guaranteed"],1)

    def test_24_hypothesis_forecasts_precede_every_new_world_and_followups(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"caf07b"
            original=des.run_toy_engine
            train_configs={json.dumps(h["config"],sort_keys=True)
                           for h in b.bank(False)+b.bank(True)}
            world_configs=[v["config"] for v in b.scenarios()]
            before_policy=b.caf07.caf05.d.POLICY.read_bytes()
            counts={"train":0,"evaluation":0}
            def simulate(config,arrivals,observations):
                key=json.dumps(config,sort_keys=True)
                if not out.exists():
                    self.assertIn(key,train_configs)
                    counts["train"]+=1
                else:
                    counts["evaluation"]+=1
                    self.assertTrue(
                        (out/"00_PLAN_BANCOS_Y_CODIGO_ANTES_DE_MUNDOS.json").exists())
                    plan=json.loads((out/"00_PLAN_BANCOS_Y_CODIGO_ANTES_DE_MUNDOS.json").read_bytes())
                    self.assertEqual(plan["github_source_commit_sha"],SHA)
                    self.assertTrue(plan["stage_count_or_truth_not_passed_to_selector"])
                    self.assertEqual(plan["quality_requirement_per_surviving_class"],1)
                    self.assertEqual(len(plan["world_evaluator_configs"]),11)
                    self.assertEqual(plan["evaluation_world_DES_calls_before_plan"],0)
                    check=json.loads((out/"00B_CHECKPOINT_PRE_EVALUACION.json").read_bytes())
                    self.assertEqual(check["plan_sha256"],
                                     b.lab.sha((out/"00_PLAN_BANCOS_Y_CODIGO_ANTES_DE_MUNDOS.json").read_bytes()))
                    self.assertFalse((out/"01_RESULTADOS.json").exists())
                    if len(arrivals)==36:  # 1.8/min, always second step
                        self.assertTrue(any((out/f"01_CHOICE_{w['id']}_{bank}.json").exists()
                                            for w in b.scenarios()
                                            for bank in ("single_only","single_plus_dual")))
                return original(config,arrivals,observations)
            with patch.object(des,"run_toy_engine",side_effect=simulate):
                result=b.run(out,SHA)
            self.assertEqual(counts["train"],324)
            self.assertEqual(counts["evaluation"],result["evaluation_DES_runs"])
            self.assertEqual(result["bank_DES_runs"],324)
            self.assertEqual(result["n_evaluations"],22)
            self.assertEqual(result["n_scenarios"],11)
            self.assertFalse(result["deployment_validated"])
            self.assertFalse(result["evaluator_truth_used_in_policy"])
            self.assertFalse(result[
                "hidden_extra_stage_rejected_using_known_topology"])
            self.assertTrue(result["budget_is_cumulative"])
            self.assertEqual(b.caf07.caf05.d.POLICY.read_bytes(),
                             before_policy)
            for item in result["evaluations"]:
                self.assertLessEqual(item["cost_spent"],8)
                pre=out/f"01_CHOICE_{item['case']}_{item['bank']}.json"
                self.assertTrue(pre.exists())
                doc=json.loads(pre.read_bytes())
                self.assertFalse(doc["second_observation_seen"])
                self.assertEqual(doc["selected_next_measurement"],
                                 item["selection_before_second"])
                self.assertEqual(doc["first_observation"],
                                 item["first_observation"])
                self.assertNotIn("truth_class_EVALUATOR_ONLY",doc)
                self.assertNotIn("truth_type_EVALUATOR_ONLY",doc)
                self.assertEqual(item["final"]["structural_warning"],
                                 b.STRUCTURAL_WARNING)
                self.assertFalse(item["final"]["real_world_validity_proven"])
                if item["second_observation"] is not None:
                    self.assertEqual(item["evaluation_DES_runs"],3)
                    self.assertLessEqual(
                        item["selection_before_second"]["action"]["cost"]+1,8)
                else:
                    self.assertEqual(item["evaluation_DES_runs"],2)
            assert sum(sum(v["verdicts"].values()) for g in result["summary"].values()
                       for v in g.values())==22
            m=json.loads((out/"03_MANIFIESTO.json").read_bytes())
            for name,digest in m["files_sha256"].items():
                self.assertEqual(b.lab.sha((out/name).read_bytes()),digest)
            with self.assertRaisesRegex(ValueError,"CAF07B_OUTPUT_ALREADY_EXISTS"):
                b.run(out,SHA)

    def test_invalid_sha_not_a_commit_and_no_failed_run_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"no"
            with self.assertRaisesRegex(ValueError,
                                        "CAF07B_SOURCE_COMMIT_SHA_REQUIRED"):
                b.run(p,"not-a-github-commit")
            self.assertFalse(p.exists())
            original=des.run_toy_engine
            calls=[]
            def abort(config,arrivals,observations):
                if p.exists():
                    calls.append(True)
                    raise RuntimeError("INTENTIONAL_FIRST_EVALUATION_ABORT")
                return original(config,arrivals,observations)
            with patch.object(des,"run_toy_engine",side_effect=abort):
                with self.assertRaisesRegex(RuntimeError,
                                            "INTENTIONAL_FIRST_EVALUATION_ABORT"):
                    b.run(p,SHA)
            self.assertEqual(calls,[True])
            self.assertTrue((p/"00_PLAN_BANCOS_Y_CODIGO_ANTES_DE_MUNDOS.json").exists())
            self.assertFalse((p/"01_RESULTADOS.json").exists())


if __name__=="__main__":
    unittest.main()
