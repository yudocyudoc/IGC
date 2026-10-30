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
        self.assertEqual(summary["K1_precommitted"],44)
        self.assertEqual(summary["no_adequate_hypothesis_both_arms"],26)
        self.assertEqual(summary["K1_predicted_candidate_reduction_positive"],43)
        self.assertEqual(summary["K1_precommitted_without_predicted_reduction"],1)
        self.assertEqual(summary["M_both_families"],21)
        self.assertEqual(summary["prior_M_only_guaranteed_K1_selected"],0)
        self.assertLess(summary["max_prior_raw_M_family_separation_orders"],1.59)
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

    def test_M_K0_single_C01_K1_prunes_parameters_not_structure(self):
        p=policy()
        mk0,dk0=joint.from_public_k0(0,2,p)
        self.assertEqual(len(mk0["C00"]["eligible"]),0)
        self.assertEqual(len(mk0["C01"]["eligible"]),6)
        chosen=joint.select(mk0,dk0,p)
        self.assertIsNotNone(chosen["proposed_measurement"])
        option=chosen["proposed_measurement"]
        cap=int(option["rate_per_minute"]*min(option["t_min"],20))
        revisions=[
            m.k1_revise(mk0,chosen,{**option,"delivered":y},.75)
            for y in range(cap+1)
        ]
        pruned=[x for x in revisions if x["updated"]["C00"]["count_after"]==0
                and 0<x["updated"]["C01"]["count_after"]<6]
        self.assertTrue(pruned,"Expected at least one parameter-pruning K1 value")
        for updated in pruned:
            self.assertEqual(updated["families_before_K1"],["C01"])
            self.assertEqual(updated["surviving_families"],["C01"])
            self.assertEqual(updated["families_excluded_by_K1"],[])
            self.assertFalse(updated["structural_hypothesis_reduction_at_K1"])
            self.assertTrue(updated["parametric_only_reduction_at_K1"])
            self.assertEqual(updated["status"],"K1_PARAMETRIC_REDUCTION_ONLY")
            self.assertEqual(updated["revision_type"],
                "PARAMETRIC_RESTRICTION_WITHIN_EXISTING_FAMILY")

    def test_M_structural_revision_requires_family_lost_since_K0(self):
        p=policy()
        mk0,dk0=joint.from_public_k0(1,5,p)
        selected=joint.select(mk0,dk0,p)
        self.assertTrue(all(mk0[f]["eligible"] for f in m.FAMILIES))
        option=selected["proposed_measurement"]
        self.assertIsNotNone(option)
        cap=int(option["rate_per_minute"]*min(option["t_min"],20))
        results=[
            m.k1_revise(mk0,selected,{**option,"delivered":y},.75)
            for y in range(cap+1)
        ]
        actual=[r for r in results if r["structural_hypothesis_reduction_at_K1"]]
        self.assertTrue(actual,"Should distinguish family support reduction")
        for updated in actual:
            self.assertEqual(updated["families_before_K1"],["C00","C01"])
            self.assertEqual(len(updated["families_excluded_by_K1"]),1)
            self.assertEqual(updated["status"],"STRUCTURAL_REVISION_ONE_FAMILY_REMAINS")

    def test_D_can_trigger_K1_when_M_had_no_K0_hypotheses(self):
        p=policy()
        qualifying=[]
        for d5 in range(7):
            for d10 in range(d5,13):
                mk0,dk0=joint.from_public_k0(d5,d10,p)
                if (not any(mk0[f]["eligible"] for f in m.FAMILIES)
                    and d.all_survivors(dk0)):
                    qualifying.append((d5,d10,mk0,dk0))
        self.assertEqual(len(qualifying),10)
        d5,d10,mk0,dk0=qualifying[0]
        selected=joint.select(mk0,dk0,p)
        self.assertIsNotNone(selected["proposed_measurement"])
        chosen=selected["proposed_measurement"]
        evidence={**chosen,"delivered":0}
        revised=m.k1_revise(mk0,selected,evidence,.75)
        self.assertEqual(revised["families_before_K1"],[])
        self.assertEqual(revised["surviving_families"],[])
        self.assertFalse(revised["structural_hypothesis_reduction_at_K1"])
        self.assertEqual(revised["status"],
                         "K0_NO_ADEQUATE_M_FAMILY_K1_OBSERVED")
        self.assertEqual(revised["revision_type"],
                         "K0_ALREADY_NO_ADEQUATE_HYPOTHESIS")
        d1=d.revise_k1(dk0,selected,evidence,p)
        self.assertTrue(d1["K1_evidence_used"])

    def test_rejects_changing_d_parent_or_m_parent(self):
        p=policy()
        mk0,dk0=joint.from_public_k0(3,8,p)
        choice=joint.select(mk0,dk0,p)
        self.assertIsNotNone(choice["proposed_measurement"])
        opt=choice["proposed_measurement"]
        evidence={**opt,"delivered":int(opt["rate_per_minute"]*
                                          min(opt["t_min"],20)/2)}
        m0altered=copy.deepcopy(mk0)
        fam=next(f for f in m.FAMILIES if mk0[f]["eligible"])
        m0altered[fam]["eligible"].pop()
        with self.assertRaises(m.Blocked):
            m.k1_revise(m0altered,choice,evidence,.75)
        d0altered=copy.deepcopy(dk0)
        fam=next(f for f in ("D1","D2","D3") if dk0["compatible"][f])
        d0altered["compatible"][fam].pop()
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
