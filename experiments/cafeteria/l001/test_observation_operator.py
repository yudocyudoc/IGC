"""Adversarial controls for L001 joint observation operator. NOT model predictions."""
import unittest
from experiments.cafeteria.l001.observation_operator import compatibility,native_projection_gate
from experiments.cafeteria.l001.three_arms import perform

def fixture():
    return {"H04":[42,42],"H05":[45.5,45.5],"H06":[47.4,47.4],"H07":[49,49]}

class TestOperator(unittest.TestCase):
    def test_jointly_compatible_point_control(self):
        r=compatibility(fixture())
        self.assertEqual(r["status"],"COMPATIBLE_ROBUST")
        self.assertAlmostEqual(r["metric_tests"]["F09"]["candidate_min"],92.9)
        self.assertEqual(r["point_max_violation_F01_F08_video_s"],0)

    def test_exactly_simultaneous_receipts_incompatible(self):
        p={**fixture(),"H05":[47.4,47.4]}
        r=compatibility(p)
        self.assertEqual(r["status"],"INCOMPATIBLE_JOINT_CONSTRAINTS")
        self.assertIn("F04",r["disjoint_metric_ids"])

    def test_both_received_at_pickup_end_incompatible(self):
        p={**fixture(),"H05":[42,42],"H06":[42,42]}
        self.assertEqual(compatibility(p)["status"],"INCOMPATIBLE_JOINT_CONSTRAINTS")

    def test_noninformative_wide_intervals_not_promoted(self):
        p={n:[0,120] for n in ("H04","H05","H06","H07")}
        r=compatibility(p)
        self.assertEqual(r["status"],"COMPATIBLE_EXISTENTIAL_ONLY")
        self.assertTrue(r["reference_region_fully_covered_by_candidate"])
        self.assertIsNone(r["point_max_violation_F01_F08_video_s"])

    def test_partial_overlap_does_not_mean_robust(self):
        p={"H04":[42,44],"H05":[45.5,46.2],"H06":[47.4,49],"H07":[49,52]}
        r=compatibility(p)
        self.assertEqual(r["status"],"COMPATIBLE_EXISTENTIAL_ONLY")
        self.assertFalse(r["reference_region_fully_covered_by_candidate"])

    def test_model_temporal_order_invalid(self):
        p={**fixture(),"H05":[47,47],"H06":[46,46]}
        self.assertEqual(compatibility(p)["status"],"INVALID_MODEL_INTERNAL_ORDER")

    def test_missing_individual_events_rejected(self):
        with self.assertRaisesRegex(ValueError,"NEED_H04_H05_H06_H07_SEPARATELY"):
            compatibility({"H05":[45,46],"H06":[47,48]})

    def test_video_time_is_not_physical_time(self):
        for clock in ("PHYSICAL_SECONDS","HOURS_FROM_MODEL_INITIAL_STATE"):
            with self.assertRaisesRegex(ValueError,"TIMEBASE_NOT_COMPARABLE"):
                compatibility(fixture(),timebase=clock)

    def test_nonfinite_boolean_and_negative_rejected(self):
        for val in (float("nan"),float("inf"),True):
            with self.assertRaisesRegex(ValueError,"INVALID_EVENT_INTERVAL"):
                compatibility({**fixture(),"H04":[val,42]})
        with self.assertRaisesRegex(ValueError,"INVALID_EVENT_BOUNDS"):
            compatibility({**fixture(),"H04":[-1,42]})

    def test_F09_not_double_counted(self):
        r=compatibility(fixture())
        self.assertTrue(r["metric_tests"]["F09"]["derived_not_independent"])
        self.assertTrue(r["F09_derived_from_F07_F08"])
        self.assertTrue(r["no_additive_metric_score"])

    def test_real_three_arm_outputs_not_scorable(self):
        _,_,e,outputs,_=perform()
        r=native_projection_gate(outputs,e)
        self.assertEqual(set(r["arms"]),{"D","B","M"})
        self.assertTrue(all(x["status"]=="NOT_SCORABLE" for x in r["arms"].values()))
        self.assertEqual(r["arms"]["B"]["reason"],"B_PROVIDER_NOT_RUN_NO_NATIVE_CANDIDATE")
        self.assertEqual(r["provider_calls"],0)
        self.assertTrue(r["control_fixtures_are_not_arm_predictions"])

    def test_cross_arm_substitution_rejected(self):
        _,_,e,outputs,_=perform()
        cross={**outputs,"D":outputs["M"]}
        with self.assertRaisesRegex(ValueError,"NATIVE_EVIDENCE_OR_ARM_MISMATCH"):
            native_projection_gate(cross,e)

if __name__=="__main__":
    unittest.main()
