#!/usr/bin/env python3
"""End-to-end synthetic calibration-to-evidence tests, no DES or K2 truth."""
import unittest
import caf02_structural_k0k1k2 as s
import caf02_discriminability_map as study


class SyntheticMapTests(unittest.TestCase):
    def test_declared_cases_and_grids_are_not_invented_after_selection(self):
        self.assertEqual(len(study.CASES),5)
        self.assertEqual(set(study.GRIDS),{"COARSE","REFINED"})
        self.assertEqual(set(study.K0_MASKS),{"SPARSE","RICHER"})
        self.assertEqual(len(study.MENU),3)
        self.assertEqual(study.PARAMS["k1_absolute_residual_max_orders"],.2)

    def test_K0_real_calibration_feeds_K1_then_revision_without_shortcut(self):
        # NO rival_members injected: BOTH survivors are computed by k0_calibrate.
        original=s.params("C01",1,1,72,10)
        obs=list(s.curve(original,1.2))
        grid={"preparation_tau":[1],"dispatch_tau":[1],
              "shared_cap":[72],"transit_tau":[10]}
        k0=s.k0_calibrate(obs,1.2,[0],grid,4,3)
        self.assertEqual(k0["C00"]["all_evaluated"],1)
        self.assertEqual(k0["C01"]["all_evaluated"],1)
        self.assertTrue(k0["C00"]["eligible"])
        self.assertTrue(k0["C01"]["eligible"])
        menu=[{"rate_per_minute":1.5,"t_min":20}]
        selected=s.select_k1_measurement(k0,menu,.05,.2,.02)
        self.assertEqual(selected["status"],
                         "K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION")
        t=s.T_VALUES.index(20)
        y=s.curve(original,1.5)[t]
        updated=s.k1_revise(k0,selected,{**menu[0],"delivered":y},.2)
        self.assertEqual(updated["surviving_families"],["C01"])
        self.assertTrue(updated["updated"]["C01"]["kept"])
        self.assertFalse(updated["updated"]["C00"]["kept"])
        k2=s.prepare_k2_comparison(k0,updated,1.35)
        self.assertTrue(k2["K0_frozen"]["C00"])
        self.assertIsNone(k2["K1_frozen"]["C00"])
        self.assertFalse(k2["K2_truth_included"])

    def test_map_runs_predeclared_crossed_scenarios(self):
        r=study.run()
        self.assertEqual(r["status"],
                         "DETERMINISTIC_INTERNAL_SOFTWARE_MAPPING_NOT_PROSPECTIVE")
        self.assertEqual(len(r["case_results"]),20)
        self.assertEqual(r["resource_use"]["DES"],0)
        self.assertEqual(r["resource_use"]["external_holdout"],0)
        for x in r["case_results"]:
            self.assertEqual(set(x["k0_candidate_counts"]),{"C00","C01"})
            self.assertTrue(x["k1_policy_precommitted"])
            self.assertIsNone(x["true_family_retained_after_K1"]) if (
                not x["k1_actual_evidence_used"]) else self.assertIsInstance(
                    x["true_family_retained_after_K1"],bool)
            self.assertEqual(x["k2_proposals_formed_no_truth"],
                             x["k1_actual_evidence_used"])
            if x["k1_design_status"] == "K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION":
                self.assertGreater(x["k1_best_expanded_robust_gap_orders"],0)
            else:
                self.assertIsNone(x["k1_chosen"])
        self.assertIn("C01_NEAR_INVISIBLE_EXTRA_STAGE",
                      {x["case"] for x in r["case_results"]})
        self.assertIn("C00_OFF_GRID",
                      {x["case"] for x in r["case_results"]})

    def test_near_zero_transit_is_approx_invisible_not_exact_equal(self):
        p=s.params("C00",1,3,72,None)
        q=s.params("C01",1,3,72,.1)
        c0=s.curve(p,1.2)
        c1=s.curve(q,1.2)
        difference=max(abs(a-b) for a,b in zip(c0,c1))
        self.assertGreater(difference,0)
        self.assertLess(difference,1)

if __name__=="__main__":
    unittest.main()
