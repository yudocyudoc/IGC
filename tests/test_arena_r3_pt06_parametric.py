"""PT-06: test declared grid and policy WITHOUT OpenModelica or hidden worlds."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_m3_prepare import family
from scripts.arena_r3_pt06_parametric import (
    CANDIDATE_LIMIT, CASE_PLAN, PACKAGE, SCHEMA, classify, plan, write_plan,
    generate_first_case_world_modelica)
from scripts.arena_m_visible_pulse import composer
from scripts.arena_v0_contract import digest


class R3FirstCasePreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.modelica=plan()

    def test_27_candidate_grid_original_composer_and_no_new_inference(self):
        m=self.manifest
        self.assertEqual(m["search"]["topologies_count"],3)
        self.assertEqual(m["search"]["parameter_configs_per_topology"],9)
        self.assertEqual(len(m["candidates"]),CANDIDATE_LIMIT)
        self.assertEqual(sum(x["is_frozen_m3_nominal"] for x in m["candidates"]),3)
        self.assertEqual(m["candidate_solver_calls"],0)
        self.assertEqual(m["world_solver_calls"],0)
        self.assertEqual(m["method_status"],"PREFLIGHT_ONLY_NOT_SIMULATED")
        self.assertEqual(m["modelica_package_sha256"],
                         "sha256:"+sha256(self.modelica.encode()).hexdigest())
        self.assertEqual(m["test_plan"]["remaining_cases"],
                         ["AMBIGUITY_TO_DESIGN_BEFORE_SIMULATION",
                          "INCOMPATIBILITY_TO_DESIGN_BEFORE_SIMULATION"])
        self.assertEqual(self.modelica.count("  model R3C"),27)
        self.assertNotIn("der(",self.modelica)
        self.assertNotIn(" when ",self.modelica)
        self.assertNotIn("worlds/",self.modelica)
        self.assertEqual(plan(),(m,self.modelica))

    def test_original_graph_identity_and_param_bounds(self):
        cfg,classes,paths=family()
        for item in self.manifest["candidates"]:
            n=int(item["material_class"][-2:])
            base_key,base_graph=paths[n]
            graph=item["graph"]
            self.assertEqual(composer.canonical(graph),base_key)
            self.assertEqual(graph["links"],base_graph["links"])
            self.assertEqual(item["original_material_graph_sha256"],"sha256:"+base_key)
            for instance in graph["instances"]:
                before=next(x for x in base_graph["instances"] if x["id"]==instance["id"])
                self.assertEqual(instance["class_id"],before["class_id"])
                if instance["role"] in ("preparation","dispatch"):
                    self.assertEqual(instance["parameters"]["responseTime"],
                                     item["role_responseTime_hours"][instance["role"]])
                else:
                    self.assertEqual(instance,before)
        self.assertEqual(CASE_PLAN["status"],
                         "CASE_BLUEPRINT_ONLY_NO_WORLD_OR_OBSERVATIONS_GENERATED")

    def test_classification_compatible_set_and_original_frozen_baseline(self):
        m=self.manifest
        def make(default):
            return [{"id":x["id"],"rmse_items":default,
                     "csv_sha256":"sha256:"+"a"*64,
                     "g2_status":"G2_SIMULATED_CONDITIONALLY"} for x in m["candidates"]]
        a=make(0.22)
        by_id={x["id"]:x for x in a}
        by_id["C00P00"]["rmse_items"]=0.001
        r=classify(a,m)
        self.assertEqual(r["status"],"ONE_COMPATIBLE_STRUCTURE_IN_GRID_NOT_CAUSALLY_IDENTIFIED")
        self.assertEqual(r["compatible_material_classes"],["C00"])
        self.assertEqual(r["frozen_m3_original_policy"]["status"],"ABSTAIN")
        b=make(0.22)
        by_id={x["id"]:x for x in b}
        by_id["C00P00"]["rmse_items"]=0.004
        by_id["C01P08"]["rmse_items"]=0.006
        r=classify(b,m)
        self.assertEqual(r["status"],"AMBIGUOUS_MULTIPLE_COMPATIBLE_STRUCTURES")
        self.assertEqual(r["compatible_material_classes"],["C00","C01"])
        c=make(0.22)
        self.assertEqual(classify(c,m)["status"],
                         "ABSTAIN_ADMISSIBLE_GRID_HAS_NO_COMPATIBLE_STRUCTURE")
        self.assertEqual(classify(c,m)["frozen_m3_original_policy"]["status"],"ABSTAIN")

    def test_fail_closed_score_budgets_and_history(self):
        m=self.manifest
        scores=[{"id":x["id"],"rmse_items":0.3,
                 "csv_sha256":"sha256:"+"a"*64,
                 "g2_status":"G2_SIMULATED_CONDITIONALLY"} for x in m["candidates"]]
        with self.assertRaisesRegex(ValueError,"R3_MISSING_OR_EXTRA_CANDIDATE"):
            classify(scores[:-1],m)
        mutated=copy.deepcopy(m)
        mutated["new_policy"]["compatibility_threshold_items"]=0.4
        with self.assertRaisesRegex(ValueError,"R3_POSTHOC_POLICY_OR_BUDGET_CHANGE"):
            classify(scores,mutated)
        altered=copy.deepcopy(scores)
        altered[0]["g2_status"]="NOT_SIMULATED"
        with self.assertRaisesRegex(ValueError,"R3_INVALID_UNVERIFIED_CANDIDATE"):
            classify(altered,m)
        altered=copy.deepcopy(scores)
        altered[0]["rmse_items"]=-0.1
        with self.assertRaisesRegex(ValueError,"R3_INVALID_UNVERIFIED_CANDIDATE"):
            classify(altered,m)

    def test_separate_blueprint_from_selector_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"preflight"
            m=write_plan(out)
            self.assertEqual(json.loads((out/"manifest.json").read_text()),m)
            self.assertEqual((out/(PACKAGE+".mo")).read_text(),self.modelica)
            world=generate_first_case_world_modelica()
            self.assertEqual((out/"ArenaR3WorldT1-NOT-SIMULATED.mo").read_text(),world)
            self.assertIn("model R3WorldT1",world)
            self.assertIn("responseTime=0.75",world)
            self.assertIn("responseTime=0.3",world)
            self.assertNotIn("der(",world)
            self.assertEqual(json.loads((out/"researcher-case-blueprint-NOT-SELECTOR-INPUT.json").read_text()),
                             CASE_PLAN)
            self.assertNotIn(CASE_PLAN["generating_role_responseTime_hours"].__repr__(),
                             json.dumps(m))
            with self.assertRaisesRegex(ValueError,"R3_OUTPUT_EXISTS"):
                write_plan(out)

    def test_future_evaluator_rejects_truth_and_unsimulated_candidates(self):
        from scripts.arena_r3_pt06_evaluate import checked_case,evaluate_csv
        manifest=self.manifest
        case={
            "schema":"igc-arena-r3-m-construction-only/0.1",
            "case_id":"R3-T1-SHIFTED-REPRESENTABLE",
            "observability":"deliveredTotal",
            "public_stimulus":{"kind":"pulse","rate":1.7,"duration":2.0},
            "construction_observations":[
                {"t":0,"delivered":0},{"t":1,"delivered":0.2},
                {"t":2,"delivered":0.9},{"t":3,"delivered":1.5}],
            "measurement_bound_status":"NO_INSTRUMENT_BOUND",
            "source_snapshot_hash":"sha256:"+"1"*64,
            "synthetic_case":True
        }
        self.assertEqual(len(checked_case(case,manifest)),4)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/(PACKAGE+".mo")).write_text(self.modelica)
            with self.assertRaisesRegex(ValueError,"R3_CANDIDATE_CSV_MISSING"):
                evaluate_csv(manifest,case,root,{"classes":[]})
        evil=copy.deepcopy(case)
        evil["true_topology"]="C00"
        with self.assertRaisesRegex(ValueError,"R3_CASE_CONTAINS_TRUTH_OR_HOLDOUT"):
            checked_case(evil,manifest)
        evil=copy.deepcopy(case)
        evil["construction_observations"].append({"t":4,"delivered":2})
        with self.assertRaisesRegex(ValueError,"R3_CONSTRUCTION_TIMES_OR_VALUES_CHANGED"):
            checked_case(evil,manifest)


if __name__=="__main__":
    unittest.main()
