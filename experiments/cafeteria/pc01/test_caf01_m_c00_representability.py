#!/usr/bin/env python3
"""Tests for a separate, openly post-hoc C00 construction-only sensitivity."""
import unittest
from unittest.mock import patch
import caf01_m_c00_representability as c


class TestC00Exploration(unittest.TestCase):
    def test_pinned_only_construction_and_in_sample_reference(self):
        observed = c.load_construction()
        self.assertEqual(observed,[3,8,13,18,24,24])
        ref=c.reference_caf_in_sample(observed)
        self.assertEqual(ref["effective_rate_orders_per_min"],1.0)
        self.assertAlmostEqual(ref["MAE"],8/6)
        self.assertEqual(ref["predicted_delivered"],[5,10,15,20,24,24])

    def test_pinned_bytes_reject_tamper(self):
        with patch.object(c,"PIN","0"*64):
            with self.assertRaisesRegex(c.Blocked,"SHA_CHANGED"):
                c.load_construction()

    def test_original_C00_analytic_uncapped_equivalence(self):
        native_equivalent=[c.analytic_equal_uncapped(t,30) for t in c.TIMES]
        coarse=c.integrate_c00(30,30,72,c.DT_COARSE)
        fine=c.integrate_c00(30,30,72,c.DT_FINE)
        self.assertLess(max(abs(a-b) for a,b in zip(fine,native_equivalent)),0.002)
        self.assertLess(max(abs(a-b) for a,b in zip(fine,coarse)),0.005)
        # Capacities 72/100 are nonbinding for rate 72/h in construction.
        alias=c.integrate_c00(30,30,100,c.DT_FINE)
        self.assertLess(max(abs(a-b) for a,b in zip(fine,alias)),1e-10)

    def test_fast_time_does_not_invent_deliveries(self):
        p=c.integrate_c00(1,1,100,c.DT_FINE)
        self.assertEqual(len(p),6)
        self.assertTrue(all(x>=0 for x in p))
        self.assertTrue(all(x<=24+1e-6 for x in p))
        self.assertTrue(all(b>=a for a,b in zip(p,p[1:])))

    def test_finite_cap_changes_behavior(self):
        low=c.integrate_c00(2,3,20,c.DT_FINE)
        high=c.integrate_c00(2,3,72,c.DT_FINE)
        self.assertLess(low[-1], high[-1])

    def test_bad_step_fails_closed(self):
        with self.assertRaisesRegex(c.Blocked,"STEP_MUST_SPLIT"):
            c.integrate_c00(30,30,72,0.07)

    def test_grid_and_epistemic_markers(self):
        report=c.campaign()
        self.assertEqual(report["status"],
                         "POSTHOC_CONSTRUCTION_ONLY_NOT_A_FORECAST")
        self.assertEqual(len(report["complete_grid"]),9*9*3)
        self.assertEqual(len(report["historical_response_times_minutes"]),3)
        self.assertTrue(all(row["native_G2_certification"] is False
                            for row in report["complete_grid"]))
        self.assertTrue(all(row["operational_parameter_justification_provided"] is False
                            for row in report["complete_grid"]))
        self.assertTrue(any("NOT the G4" in a for a in report["limitations"]))
        self.assertLess(report["max_coarse_fine_difference_orders"],0.005)


if __name__=="__main__":
    unittest.main()
