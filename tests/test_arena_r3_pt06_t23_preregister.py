"""PT06 STR-03 cases frozen before observations, simulations or selection."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r3_pt06_t23_preregister import (
    CASES,ORIGINAL_GRID_SHA,WORLD_PACKAGE,freeze,emit,make_world_graph)
from scripts.arena_r3_pt06_t23_worlds import commands,prepare
from scripts.arena_r3_pt06_t23_evaluate import (
    validate_case,archived_candidates,evaluate,CASE_SCHEMA)
from scripts.arena_r3_pt06_t23_extract import extract
from scripts.arena_r3_pt06_parametric import plan
from scripts.arena_v0_contract import digest

ORIGINAL=os.environ.get("ARENA_R3_T1_ORIGINAL_DIR")


class PT06T23Predeclared(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol,cls.worlds,cls.sealed=freeze()

    def test_no_posthoc_grids_or_new_molecules(self):
        m,pkg=plan()
        self.assertEqual(digest(m),ORIGINAL_GRID_SHA)
        self.assertEqual(len(m["candidates"]),27)
        self.assertEqual(self.protocol["threshold_items"],.020)
        self.assertEqual(self.protocol["new_candidate_simulations"],0)
        self.assertEqual(self.protocol["total_new_simulations_executed"],0)
        self.assertEqual(self.protocol["new_world_simulations_requested_later"],2)
        self.assertEqual(self.protocol["archived_candidate_run_id"],40578550337)
        self.assertEqual(self.protocol["archived_candidate_artifact_id"],12769310740)
        self.assertEqual(len(self.protocol["case_protocols"]),2)
        self.assertEqual(len(self.sealed["sealed"]),2)
        self.assertNotIn("world_material_class",json.dumps(self.protocol))
        self.assertNotIn("source_parameters",json.dumps(self.protocol))
        self.assertNotIn("C01",json.dumps(self.protocol))
        self.assertNotIn("C02",json.dumps(self.protocol))
        for spec in CASES:
            cfg,classes,graph,key=make_world_graph(spec)
            self.assertEqual(spec["public_observation_times_hours"] if
                             "public_observation_times_hours" in spec else len(spec["times_hours"]),4)
            self.assertEqual(len(spec["declared_noise_items"]),4)
        self.assertEqual(self.worlds.count("  model R3T"),2)
        self.assertNotIn("der(",self.worlds)
        self.assertNotIn(" when ",self.worlds)

    def test_early_ambiguity_is_negative_control_not_assumed_result(self):
        early,later=self.protocol["case_protocols"]
        self.assertEqual(early["public_observation_times_hours"],[0,.05,.1,.15])
        self.assertEqual(early["declared_noise_items"],[0,0,0,0])
        self.assertEqual(early["new_world_simulation_interval"],[0,.15])
        self.assertIn("NOT_GUARANTEED",
                      early["anticipated_outcome_NOT_AN_ASSUMED_RESULT"])
        self.assertEqual(later["public_observation_times_hours"],[0,1,2,3])
        self.assertEqual(later["new_world_simulation_interval"],[0,3])
        self.assertIn("NOT_GUARANTEED",
                      later["anticipated_outcome_NOT_AN_ASSUMED_RESULT"])

    def test_exact_two_world_simulation_budget_and_absent_csv_failure(self):
        Path("artifacts").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir="artifacts") as temp:
            folder=Path(temp)
            # tempfile path is absolute /repo/artifacts..., use relative path.
            folder=Path("artifacts")/folder.name/"t23"
            receipt=prepare(folder)
            self.assertEqual(receipt["world_simulations_max"],2)
            self.assertEqual(receipt["candidate_simulations_max"],0)
            self.assertEqual(receipt["new_solver_calls_now"],0)
            cmd=commands(folder)
            self.assertEqual(cmd.count("simulate("),2)
            self.assertEqual(cmd.count("checkModel("),2)
            self.assertEqual(cmd.count("fileNamePrefix="),2)
            self.assertNotIn("R3C00P",cmd)
            self.assertEqual((folder/"two-worlds-NOT-RUN.mos").read_text(),cmd)
            with self.assertRaisesRegex(ValueError,"R3_T23_REAL_GENERATOR_CSV_MISSING"):
                extract(folder,json.loads(Path("experiments/e0/catalog.json").read_text()))
            with self.assertRaisesRegex(ValueError,"R3_T23_PREFLIGHT_OUTPUT_EXISTS"):
                emit(folder)

    def test_never_allow_truth_labels_or_unregistered_observation_schedule(self):
        p=self.protocol
        first=p["case_protocols"][0]
        case={
          "schema":CASE_SCHEMA,"case_id":first["case_id"],
          "observability":"deliveredTotal","public_stimulus":{
              "kind":"pulse","rate":1.7,"duration":2.0},
          "construction_observations":[{"t":t,"delivered":0.0}
                                       for t in first["public_observation_times_hours"]],
          "measurement_bound_status":"NO_INSTRUMENT_BOUND",
          "synthetic_case":True,
        }
        case["source_snapshot_hash"]=digest(case["construction_observations"])
        self.assertEqual(validate_case(case,p),case["construction_observations"])
        for kind in ("truth","timing","hash","profile"):
            x=copy.deepcopy(case)
            if kind=="truth":x["generating_topology"]="C01"
            if kind=="timing":x["construction_observations"][-1]["t"]=1.0
            if kind=="hash":x["source_snapshot_hash"]="sha256:"+"f"*64
            if kind=="profile":x["public_stimulus"]["rate"]=2.0
            with self.assertRaises(ValueError):
                validate_case(x,p)


@unittest.skipUnless(ORIGINAL,"Real R3-T1 archive required, never mock physical candidate data")
class OriginalT1CandidateReuse(unittest.TestCase):
    def test_real_G2_verified_27_candidate_csv_unchanged(self):
        import hashlib
        root=Path(ORIGINAL)
        before={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
                for f in (root/"candidates").glob("*_res.csv")}
        manifest,rows,index=archived_candidates(
            root,freeze()[0],json.loads(Path("experiments/e0/catalog.json").read_text()))
        self.assertEqual(len(rows),27)
        self.assertEqual(len(index),27)
        self.assertEqual({x["id"] for x in index},
                         {x["id"] for x in manifest["candidates"]})
        for x in rows.values():
            self.assertGreaterEqual(len(x),70)
        self.assertEqual(before,{f.name:hashlib.sha256(f.read_bytes()).hexdigest()
                for f in (root/"candidates").glob("*_res.csv")})

if __name__=="__main__":
    unittest.main()
