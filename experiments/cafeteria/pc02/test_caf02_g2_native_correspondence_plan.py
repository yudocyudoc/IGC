#!/usr/bin/env python3
"""No-OMC bounded G2 plan test: numerical trace checks are NOT native proof."""
import copy
import json
import unittest
import caf02_g2_native_correspondence_plan as g2
import caf02_d_k0k1k2_adapter as d


class G2PlanTest(unittest.TestCase):
    def test_cases_are_fixed_and_budget_is_proposed_only(self):
        policy=json.loads(d.POLICY.read_text(encoding="utf-8"))
        plan=g2.plan(policy)
        self.assertEqual(len(plan["cases"]),15)
        self.assertEqual(len([x for x in plan["cases"] if x["arm"]=="M"]),12)
        self.assertEqual(len([x for x in plan["cases"] if x["arm"]=="D"]),3)
        self.assertEqual(plan["OpenModelica_invocations"],0)
        self.assertEqual(plan["private_DES_runs"],0)
        self.assertFalse(plan["K2_truth_read"])
        self.assertEqual(plan["state"],
                         "PLAN_ONLY_NO_OMC_EXECUTION_NO_PARITY_VERIFIED")
        self.assertEqual(set(x["structure"] for x in plan["cases"]),
                         {"C00","C01","D1","D2","D3"})
        self.assertEqual(len(set(x["id"] for x in plan["cases"])),15)
        self.assertTrue(all(x["native_verified"] is False and
                            x["native_OMC_result"] is None and
                            x["native_full_source_sha256"] is None
                            for x in plan["cases"]))

    def test_matching_synthetic_trace_is_not_fake_native_certification(self):
        policy=json.loads(d.POLICY.read_text())
        case=g2.plan(policy)["cases"][0]
        report=g2.evaluate_offline_submitted_trace(
            case,case["comparison_times_hours"],
            case["reference_curve_from_surrogate_not_OMC"])
        self.assertTrue(report["numeric_trace_within_proposed_tolerance"])
        self.assertFalse(report["real_native_modelica_source_verified"])
        self.assertFalse(report["native_execution_independently_verified"])
        self.assertFalse(report["full_G2_certification"])

    def test_declared_trace_tolerance_and_time_units_are_enforced(self):
        p=json.loads(d.POLICY.read_text())
        case=g2.plan(p)["cases"][4]
        values=case["reference_curve_from_surrogate_not_OMC"]
        times=case["comparison_times_hours"]
        bad=copy.deepcopy(values)
        bad[3]+=0.15
        report=g2.evaluate_offline_submitted_trace(case,times,bad)
        self.assertFalse(report["numeric_trace_within_proposed_tolerance"])
        with self.assertRaisesRegex(ValueError,"TIMES_OR_UNITS"):
            g2.evaluate_offline_submitted_trace(case,list(g2.TIMES),values)
        with self.assertRaisesRegex(ValueError,"PHYSICAL"):
            g2.evaluate_offline_submitted_trace(case,times,[-1]*6)

    def test_no_policy_mutation_or_unannounced_extra_native_candidates(self):
        p=json.loads(d.POLICY.read_text())
        p2=copy.deepcopy(p)
        p2["resource_ceiling"]["native_G2_verification_max_proposed"]=100
        with self.assertRaises(AssertionError):
            g2.plan(p2)
        p2=copy.deepcopy(p)
        p2["d_method"]["budget"]["OpenModelica_candidate_calls_max_proposed"]=99
        with self.assertRaises(AssertionError):
            g2.plan(p2)

if __name__=="__main__":
    unittest.main()
