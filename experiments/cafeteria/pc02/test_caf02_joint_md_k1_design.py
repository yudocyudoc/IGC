#!/usr/bin/env python3
"""Regressions for the corrected CAF02 joint evidence rule, no independent world."""
import copy
import json
import unittest

import caf02_joint_md_k1_design as joint
import caf02_structural_k0k1k2 as m
import caf02_d_k0k1k2_adapter as d


def policy():
    return json.loads(d.POLICY.read_text())


class JointK1Tests(unittest.TestCase):
    def test_70_all_physically_admitted_integer_K0_pairs(self):
        scan=joint.audit_admissible_integer_k0(policy())
        self.assertEqual(len(scan["rows"]),70)
        summary=scan["summary"]
        self.assertEqual(summary["admissible_pairs"],70)
        self.assertEqual(summary["K1_precommitted"]+
                         summary["no_adequate_hypothesis_both_arms"],70)
        self.assertGreater(summary["K1_precommitted"],0)
        self.assertFalse(summary["truth_K1_seen"])
        self.assertEqual(summary["DES_runs"],0)
        self.assertEqual(summary["K2_truth_seen"],False)

    def test_joint_precommit_preserves_tolerance_and_no_guarantee(self):
        p=policy()
        m0,d0=joint.from_public_k0(3,8,p)
        decision=joint.select(m0,d0,p)
        self.assertEqual(decision["precommitted_policy"][
            "effective_revision_tolerance_orders"],.77)
        self.assertTrue(decision["no_guarantee_of_structural_identification"])
        self.assertFalse(decision["K1_real_observation_seen"])
        if decision["proposed_measurement"]:
            self.assertEqual(len(decision["all_menu_scores"]),3)
            self.assertEqual(sum(x["measurement"]==
                                 decision["proposed_measurement"]
                                 for x in decision["all_menu_scores"]),1)
            self.assertIn(decision["status"],(
                "K1_PRECOMMITTED_POTENTIAL_HYPOTHESIS_REDUCTION",
                "K1_PRECOMMITTED_NO_MODELLED_REDUCTION_ADEQUACY_TEST"))
        else:
            self.assertEqual(decision["status"],
                             "K1_NO_ADEQUATE_HYPOTHESIS_NO_TRIAL")

    def test_no_change_to_K1_tolerance_merely_to_make_experiment_possible(self):
        p=policy()
        self.assertEqual(p["k1"]["absolute_residual_tolerance_orders"],.75)
        self.assertEqual(p["k1"]["numerical_allowance_orders"],.02)
        self.assertEqual(p["k1"]["effective_revision_tolerance_orders"],.77)
        self.assertEqual(p["k1"]["minimum_positive_expanded_gap_orders"],.05)
        self.assertNotIn("robust_nonoverlap",p["k1"]["selection"])
        self.assertEqual(p["k1"]["selection_version"],"JOINT_M_D_DESIGN_V1")
        self.assertEqual(p["k1"]["only_possible_one_K1"],True)

    def test_shared_K1_revises_both_arms_without_observation_leak(self):
        p=policy()
        model=m.params("C01",1,1,72,6)
        k0values=m.curve(model,1.2)
        # Surrogate continuous observations can be noninteger: the public
        # DES interface is intentionally integer. Use a physically possible
        # integer pair, rather than leaking unobserved K0 future samples.
        d5,d10=round(k0values[0]),round(k0values[1])
        mk0,dk0=joint.from_public_k0(d5,d10,p)
        selected=joint.select(mk0,dk0,p)
        self.assertIsNotNone(selected["proposed_measurement"])
        option=selected["proposed_measurement"]
        y=m.curve(model,option["rate_per_minute"])[
            m.T_VALUES.index(option["t_min"])]
        measured=int(y+.5)
        evidence={**option,"delivered":measured}
        m1=m.k1_revise(mk0,selected,evidence,.75)
        d1=d.revise_k1(dk0,selected,evidence,p)
        self.assertEqual(m1["K1_observation"],d1["K1_evidence"])
        self.assertEqual(m1["effective_residual_tolerance_orders"],.77)
        self.assertTrue(d1["K1_evidence_used"])
        for f in m.FAMILIES:
            after=len(m1["updated"][f]["kept"])
            self.assertLessEqual(after,len(mk0[f]["eligible"]))
        for f in ("D1","D2","D3"):
            self.assertLessEqual(len(d1["compatible"][f]),
                                 len(dk0["compatible"][f]))
        m2=m.prepare_k2_comparison(mk0,m1,1.35)
        d2=d.prepare_k2(dk0,d1,p)
        self.assertFalse(m2["K2_truth_included"])
        self.assertFalse(d2["K2_truth_included"])
        self.assertFalse(d2["G4_external_witness_verified"])

    def test_rejects_changing_d_parent_or_m_parent(self):
        p=policy()
        mk0,dk0=joint.from_public_k0(3,8,p)
        choice=joint.select(mk0,dk0,p)
        self.assertIsNotNone(choice["proposed_measurement"])
        opt=choice["proposed_measurement"]
        evidence={**opt,"delivered":int(opt["rate_per_minute"]*
                                          min(opt["t_min"],20)/2)}
        m0altered=copy.deepcopy(mk0)
        m0altered["C00"]["eligible"].pop()
        with self.assertRaises(m.Blocked):
            m.k1_revise(m0altered,choice,evidence,.75)
        d0altered=copy.deepcopy(dk0)
        d0altered["compatible"]["D1"].clear()
        with self.assertRaises(d.DBlocked):
            d.revise_k1(d0altered,choice,evidence,p)

    def test_no_extra_K1_can_be_injected_when_no_adequate_models(self):
        p=policy()
        mk0,dk0=joint.from_public_k0(0,0,p)
        selection=joint.select(mk0,dk0,p)
        if selection["status"]=="K1_NO_ADEQUATE_HYPOTHESIS_NO_TRIAL":
            self.assertIsNone(selection["proposed_measurement"])
            with self.assertRaises(d.DBlocked):
                d.revise_k1(dk0,selection,
                    {"rate_per_minute":1.8,"t_min":30,"delivered":0},p)
        else:
            self.assertTrue(selection["proposed_measurement"])

    def test_missing_K0_input_or_integer_impossible_is_rejected(self):
        p=policy()
        for a,b in ((7,12),(-1,8),(5,13),(9,2),(3.5,8)):
            with self.assertRaises((ValueError,d.DBlocked,m.Blocked)):
                joint.from_public_k0(a,b,p)

    def test_equal_family_weights_ignore_grid_size_as_probability(self):
        p=policy()
        mk0,dk0=joint.from_public_k0(3,8,p)
        decision=joint.select(mk0,dk0,p)
        for menu in decision["all_menu_scores"]:
            for arm in ("M","D"):
                r=menu[arm]
                if r is not None:
                    self.assertGreaterEqual(r[
                        "expected_candidate_support_removed_fraction"],0)
                    self.assertLessEqual(r[
                        "expected_candidate_support_removed_fraction"],1)
                    self.assertFalse(not r["diagnostic_only_not_predictive_probability"])

if __name__=="__main__":
    unittest.main()
