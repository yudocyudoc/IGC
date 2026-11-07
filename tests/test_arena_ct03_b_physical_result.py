"""B physical result on synthetic CSV/log only, never OMC or provider."""
import csv
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_b_own_feedback import build
from scripts.arena_cafe.ct03_b_physical_prepare import prepare
from scripts.arena_cafe.ct03_b_physical_result import check
from test_arena_ct03_b_own_feedback import fixture,public,TIME

def setup(root,broken_mass=False):
    native,receipt=fixture()
    fb=build(original=native,receipt=receipt,construction=public(),
             recorded_at=TIME,out=root/"feedback")
    plan=prepare(native,receipt,public(),fb,root/"physical")
    with (root/"physical/b-original_res.csv").open(
            "w",encoding="utf-8",newline="") as stream:
        w=csv.writer(stream)
        w.writerow(["time","delivered_work","pending_work"])
        for i in range(65):
            t=i/8
            delivered=.1*t
            remain=0 if broken_mass else 1.7*min(t,2)-delivered
            w.writerow([t,delivered,remain])
    (root/"physical/b-original-omc.log").write_text(
        "OpenModelica 1.26.5\nCheck of "+
        plan["translated_model_name"]+
        " completed successfully.\nLOG_SUCCESS FAKE_TEST_NOT_OMC\n"
        "b-original_res.csv\n")
    return native,receipt,plan


class BPhysicalResultTests(unittest.TestCase):
    def test_one_original_B_success_shape_not_a_live_result(self):
        with TemporaryDirectory(dir=".") as t:
            root=Path(t).relative_to(Path.cwd())
            native,receipt,plan=setup(root)
            result=check(native=native,receipt=receipt,plan=plan,
                         root=root/"physical",
                         github_run_id="12345",github_sha="a"*40)
            self.assertEqual(result["forecast"][0]["time"],6)
            self.assertAlmostEqual(result["forecast"][0]["delivered"],.6)
            self.assertEqual(result["forecast"][1]["time"],8)
            self.assertAlmostEqual(result["forecast"][1]["delivered"],.8)
            self.assertLess(result["max_abs_material_residual"],1e-10)
            self.assertEqual(result["parent_native_sha256"],receipt["result_sha256"])
            self.assertTrue(result["not_a_scientific_G3_score"])

    def test_bad_mass_or_wrong_operator_must_fail(self):
        with TemporaryDirectory(dir=".") as t:
            root=Path(t).relative_to(Path.cwd())
            native,receipt,plan=setup(root,broken_mass=True)
            with self.assertRaisesRegex(ValueError,"MATERIAL_MASS_BALANCE_FAILED"):
                check(native=native,receipt=receipt,plan=plan,
                      root=root/"physical",
                      github_run_id="12345",github_sha="a"*40)
            plan["observation_operator"]["modelica_csv_column"]="pending_work"
            with self.assertRaisesRegex(ValueError,"NATIVE_PORT_OR_PARENT_DRIFT"):
                check(native=native,receipt=receipt,plan=plan,
                      root=root/"physical",
                      github_run_id="12345",github_sha="a"*40)

if __name__=="__main__":
    unittest.main()
