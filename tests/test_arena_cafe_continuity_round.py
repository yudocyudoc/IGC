"""Finite checks for E02 policy: no arbitrary top-one, no Buffalo fabrication."""
import unittest
from scripts.arena_cafe.continuity_round import _vector, _policy_decision


class ContinuityPolicyTest(unittest.TestCase):
    def test_descriptive_vector_six_joint_cuts(self):
        ev={"comparisons":[{"observable":"delivered_cumulative",
             "t_minutes":t,"observed_orders":o,
             "native_prediction":p,"residual_orders":p-o}
            for t,o,p in zip((0,2,4,6,8,10),(0,0,2,4,6,8),
                              (0,1,2,4,5,8))]}
        result=_vector(ev)
        self.assertEqual(result["status"],"DESCRIPTIVE_ONLY_NOT_COMPATIBILITY")
        self.assertEqual(result["max_abs"],1)
        self.assertEqual(result["residuals"],[0,1,0,0,-1,0])
        self.assertTrue(result["no_epsilon_model_defended"])

    def test_no_fake_compatibility_from_missing_hj(self):
        self.assertEqual(_vector({"comparisons":[]})["status"],
                         "NOT_COMPARABLE_SIX_TERMINAL_CUTS")

    def test_d_and_m_retain_every_original_without_ranking(self):
        for arm in ("D","M"):
            candidates=[{"candidate":str(i),"diagnostic":{
                "status":"DESCRIPTIVE_ONLY_NOT_COMPATIBILITY", "RMSE":i}}
                for i in range(6)]
            d=_policy_decision(arm,candidates)
            self.assertEqual(d["first_decision"]["candidate_ids"],
                             d["second_decision"]["candidate_ids"])
            self.assertEqual(len(d["second_decision"]["candidate_ids"]),6)
            self.assertTrue(d["second_decision"]["own_feedback_considered"])
            self.assertEqual(d["second_decision"]["native_regeneration"],
                             "NOT_PERFORMED")
            self.assertEqual(d["author"],
                             "EXPLICIT_EXPERIMENTAL_POLICY_NOT_ORIGINAL_ENUMERATOR")
            self.assertFalse(d["private_feedback"]["rival_outputs_visible"])
            self.assertEqual(d["second_decision"]["scientific_compatibility"],
                             "NOT_CLAIMED")
            self.assertTrue(d["not_a_causal_O1_ablation"])


if __name__=="__main__":
    unittest.main()
