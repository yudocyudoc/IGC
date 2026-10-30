#!/usr/bin/env python3
"""Synthetic tests of K0/K1/K2 decision process, no real K2 evaluation."""
import unittest
import caf02_structural_k0k1k2 as s


def rival_members():
    slow=s.params("C01",1.,1.,72.,20.)
    fast=s.params("C00",1.,1.,72.,None)
    return {
        "C00":{"eligible":[fast],"passes_absolute_adequacy":True},
        "C01":{"eligible":[slow],"passes_absolute_adequacy":True},
    }


def select(k0, menu, gap, residual=.01, numerical=.01):
    return s.select_k1_measurement(k0,menu,gap,residual,numerical)


class K0K1K2Tests(unittest.TestCase):
    def test_registry_contains_existing_rivals_only(self):
        evidence=s.verify_existing_repertoire()
        self.assertEqual(evidence["C00"],["preparation","dispatch"])
        self.assertEqual(evidence["C01"],["preparation","dispatch","transit"])

    def test_physical_balances_and_three_stage_delay(self):
        d=s.simulate("C00",1,1,72,1,1.2)
        t=s.simulate("C01",1,1,72,20,1.2)
        self.assertLess(t[0],d[0])
        self.assertLess(t[-1],d[-1])
        self.assertLessEqual(d[-1],24)
        self.assertTrue(all(x<=y for x,y in zip(t,t[1:])))

    def test_smaller_transit_response_brings_C01_closer_to_C00(self):
        d=s.simulate("C00",2,3,100,1,1.2)
        short=s.simulate("C01",2,3,100,.5,1.2)
        long=s.simulate("C01",2,3,100,20,1.2)
        dist_short=sum(abs(a-b) for a,b in zip(d,short))
        dist_long=sum(abs(a-b) for a,b in zip(d,long))
        self.assertLess(dist_short,dist_long)

    def test_k0_calibration_preserves_both_families_if_adequate(self):
        obs=s.simulate("C00",1,1,72,1,1.2)
        grid={"preparation_tau":[1,3],"dispatch_tau":[1,3],
              "shared_cap":[72],"transit_tau":[1,3]}
        result=s.k0_calibrate(obs,1.2,[1,3],grid,3.0,.5)
        self.assertEqual(set(result),{"C00","C01"})
        self.assertTrue(result["C00"]["eligible"])
        self.assertEqual(result["C00"]["all_evaluated"],4)
        self.assertEqual(result["C01"]["all_evaluated"],8)

    def test_k0_absolute_adequacy_rejects_both_bad_families(self):
        grid={"preparation_tau":[60],"dispatch_tau":[60],
              "shared_cap":[72],"transit_tau":[60]}
        result=s.k0_calibrate([0,3,8,13,18,24],1.2,
                              [0,1,2,3],grid,.01,1.)
        self.assertFalse(result["C00"]["eligible"])
        self.assertFalse(result["C01"]["eligible"])
        out=select(result,[{"rate_per_minute":1.5,"t_min":20}],.1)
        self.assertEqual(out["status"],"K0_NO_TWO_ADEQUATE_STRUCTURES")

    def test_k1_design_is_based_on_calibrated_rival_envelopes(self):
        k0=rival_members()
        menu=[{"rate_per_minute":1.2,"t_min":10},
              {"rate_per_minute":1.5,"t_min":20},
              {"rate_per_minute":1.0,"t_min":30}]
        chosen=select(k0,menu,.25)
        self.assertEqual(chosen["status"],
                         "K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION")
        self.assertIn(chosen["proposed_measurement"],menu)
        self.assertEqual(len(chosen["all_menu_scores"]),3)
        self.assertFalse(chosen["evidence_result_read"])

    def test_k1_abstains_on_uninformative_menu_not_posthoc_select(self):
        k0=rival_members()
        menu=[{"rate_per_minute":1.2,"t_min":10}]
        chosen=select(k0,menu,100)
        self.assertEqual(chosen["status"],"K1_MENU_CANNOT_ROBUSTLY_DISCRIMINATE")
        self.assertIsNone(chosen["proposed_measurement"])
        with self.assertRaises(s.Blocked):
            s.k1_revise(k0,chosen,{"rate_per_minute":1.2,
                                   "t_min":10,"delivered":7},.25)

    def test_k1_revision_removes_only_contradicted_family(self):
        k0=rival_members()
        menu=[{"rate_per_minute":1.5,"t_min":20}]
        chosen=select(k0,menu,.1)
        chosen_p=chosen["proposed_measurement"]
        self.assertIsNotNone(chosen_p)
        i=s.T_VALUES.index(chosen_p["t_min"])
        y=s.curve(k0["C01"]["eligible"][0],chosen_p["rate_per_minute"])[i]
        evidence={**chosen_p,"delivered":y}
        revised=s.k1_revise(k0,chosen,evidence,.01)
        self.assertEqual(revised["surviving_families"],["C01"])
        self.assertEqual(revised["status"],"STRUCTURAL_REVISION_ONE_FAMILY_REMAINS")
        self.assertEqual(revised["revision_type"],
                         "EPISTEMIC_RESTRICTION_OF_EXISTING_HYPOTHESES")
        self.assertFalse(revised["new_architecture_created"])

    def test_evidence_cannot_change_the_preselected_menu(self):
        k0=rival_members()
        selected=select(k0,
            [{"rate_per_minute":1.2,"t_min":20}],.1)
        with self.assertRaises(s.Blocked):
            s.k1_revise(k0,selected,
                {"rate_per_minute":1.2,"t_min":40,"delivered":10},.1)

    def test_k1_rejects_physically_impossible_delivery_count(self):
        k0=rival_members()
        option={"rate_per_minute":1.2,"t_min":20}
        selected=select(k0,[option],.1)
        with self.assertRaises(s.Blocked):
            s.k1_revise(k0,selected,{**option,"delivered":25.0},.1)

    def test_overlap_with_K1_tolerance_has_no_robust_separation(self):
        gap=s.expanded_interval_separation(
            (10.0,10.0),(10.2,10.2),.15,.01)
        self.assertAlmostEqual(gap["raw_gap_orders"],.2)
        self.assertEqual(gap["expanded_gap_orders"],0)
        self.assertLessEqual(10.1,10.0+.15)
        self.assertGreaterEqual(10.1,10.2-.15)

    def test_revision_refuses_unannounced_tolerance_change(self):
        k0=rival_members()
        selected=select(k0,[{"rate_per_minute":1.5,"t_min":20}],.1,
                        residual=.01,numerical=.01)
        self.assertIsNotNone(selected["proposed_measurement"])
        option=selected["proposed_measurement"]
        val=s.curve(k0["C01"]["eligible"][0],
                    option["rate_per_minute"])[s.T_VALUES.index(option["t_min"])]
        with self.assertRaises(s.Blocked):
            s.k1_revise(k0,selected,{**option,"delivered":val},.25)

    def test_k2_both_versions_present_without_future_truth(self):
        k0=rival_members()
        selected=select(k0,
            [{"rate_per_minute":1.5,"t_min":20}],.1)
        option=selected["proposed_measurement"]
        i=s.T_VALUES.index(option["t_min"])
        y=s.curve(k0["C01"]["eligible"][0],option["rate_per_minute"])[i]
        k1=s.k1_revise(k0,selected,{**option,"delivered":y},.01)
        pack=s.prepare_k2_comparison(k0,k1,1.8)
        self.assertTrue(pack["K0_frozen"]["C00"])
        self.assertIsNone(pack["K1_frozen"]["C00"])
        self.assertTrue(pack["K1_frozen"]["C01"])
        self.assertFalse(pack["K2_truth_included"])
        self.assertEqual(pack["K2_DES_runs"],0)


if __name__=="__main__":
    unittest.main()
