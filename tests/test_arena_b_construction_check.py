import copy
import math
import unittest
from scripts.arena_b_construction_check import assess

VISIBLE={
    "schema":"igc-arena-visible-input/0.1",
    "construction":{"observations":[
        {"t":0,"delivered":0},{"t":1,"delivered":0.35},
        {"t":2,"delivered":1.1},{"t":4,"delivered":2.5},
    ]}
}


def fixture():
    rows=[]
    # Exact discrete Euler mass balance, 0 .. 8h, 0.125h step.
    for i in range(65):
        t=i*.125
        pending=1.7*min(t,2.0)
        rows.append({"time":str(t),"pending_work":str(pending),
                     "delivered_work":"0","arrivals":str(1.7 if t<2 else 0),
                     "completions":"0"})
    return rows


class BuffaloConstructionCheck(unittest.TestCase):
    def test_denom_and_heldout_distinct(self):
        result=assess(fixture(),VISIBLE)
        self.assertLess(result["balance_residual_max_items"],1e-12)
        self.assertEqual(result["rmse_denominators"],{
            "all_observations":4,"noninitial_observations":3})
        self.assertAlmostEqual(result["rmse_all_observations_items"],
                               result["rmse_noninitial_observations_items"]*math.sqrt(3/4),places=12)
        self.assertEqual(result["g3_construction_status"],"DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND")
        self.assertEqual(result["heldout_evaluation_status"],"NOT_RUN")

    def test_violated_material_balance_blocked(self):
        bad=fixture();bad[13]["pending_work"]="100"
        with self.assertRaisesRegex(ValueError,"BUFFALO_MATERIAL_BALANCE_FAILED"):
            assess(bad,VISIBLE)

    def test_missing_or_nonfinite_series_blocked(self):
        bad=fixture()
        del bad[25]["arrivals"]
        with self.assertRaisesRegex(ValueError,"MISSING_BUFFALO_SERIES"):
            assess(bad,VISIBLE)
        bad=fixture()
        bad[25]["pending_work"]="nan"
        with self.assertRaisesRegex(ValueError,"NONFINITE_BUFFALO_SERIES"):
            assess(bad,VISIBLE)

    def test_non_euler_step_or_time_backwards_blocked(self):
        bad=fixture();bad[12]["time"]="0.8"
        with self.assertRaisesRegex(ValueError,"BUFFALO_TIME_BACKWARDS"):
            assess(bad,VISIBLE)
        bad=fixture();bad[12]["time"]="1.55"
        with self.assertRaisesRegex(ValueError,"BUFFALO_EULER_GRID_MISMATCH|BUFFALO_TIME_BACKWARDS"):
            assess(bad,VISIBLE)

    def test_no_implicit_cross_arm_ranking(self):
        result=assess(fixture(),VISIBLE)
        self.assertTrue(result["not_cross_arm_ranking"])
        self.assertEqual(result["arm_id"],"B")
        self.assertNotIn("other_arm",result)


if __name__=="__main__":
    unittest.main()
