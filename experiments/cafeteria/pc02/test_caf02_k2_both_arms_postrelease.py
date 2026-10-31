#!/usr/bin/env python3
"""CAF02 synthetic G4a -> G4b -> reserved K2 -> both arms scoring.

All observations are handwritten synthetic integers, NOT an external DES.
The K2 post-release function does not certify G5/G4a/G4b witnesses; it only
checks chain integrity and scores six numbers AFTER hypothetical release.
"""
import copy
import json
import unittest

import caf02_d_k0k1k2_adapter as d
import caf02_public_cut_bridge as bridge
import caf02_k2_set_scoring as score
import caf02_k2_adjudicator_boundary as adjudicator
import caf02_joint_md_k1_design as joint

G5="sha256:"+"b"*64
TRUTH=[0,1,5,10,20,25]


def policy():
    return json.loads(d.POLICY.read_text())


def k0(a,b):
    return {"cut":"K0","delivered_t5":a,"delivered_t10":b,
            "world_precommitment_ref":G5}


def k2(values=None):
    return {"cut":"K2","delivered":list(TRUTH if values is None else values),
            "world_precommitment_ref":G5}


def scenario(a=1,b=5,delivered=31):
    p=policy()
    g4a=bridge.create_g4a_candidate(k0(a,b),p)
    choice=g4a["K1_preselected_common"]["proposed_measurement"]
    if choice is None:
        e=None
    else:
        e={"cut":"K1","measurement":choice,
           "delivered":delivered,"world_precommitment_ref":G5}
    g4b=bridge.create_g4b_candidate(g4a,e,p)
    return p,g4a,g4b


class BothArmsScoringTest(unittest.TestCase):
    def test_direct_D_three_families_scored_without_M_names(self):
        y=[1,2,3,4,5,6]
        d_set={"D1":{"lower":y,"upper":y,"candidate_count":1},
               "D2":None,"D3":None}
        result=score.adjudicate(d_set,d_set,None,y,y,arm="D")
        self.assertEqual(result["arm"],"D")
        self.assertEqual(result["status"],"PAIRED")
        self.assertEqual(result["paired_set_loss_gain_orders"],0)
        self.assertFalse(result["revision_predictive_improvement_pass"])
        self.assertEqual(result["REF_CAF"]["status"],"ABSTAIN_NO_CANDIDATE")
        self.assertFalse(result["equal_information_method_advantage_claim_allowed"])

    def test_D_rejects_misspelled_or_mixed_structures(self):
        y=[1,2,3,4,5,6]
        correct={"D1":None,"D2":None,"D3":None}
        for wrong in ({"C00":None,"C01":None},
                      {"D1":None,"D2":None},
                      {"D1":None,"D2":None,"D3":None,"C00":None}):
            with self.subTest(wrong=wrong),self.assertRaisesRegex(
                    score.InvalidK2Score,"MISSING_OR_UNEXPECTED_D"):
                score.adjudicate(wrong,correct,y,y,y,arm="D")
        with self.assertRaisesRegex(score.InvalidK2Score,"UNKNOWN_K2_ARM"):
            score.adjudicate(correct,correct,y,y,y,arm="B")

    def test_complete_synthetic_G4a_G4b_K2_scores_M_and_D(self):
        p,a,bb=scenario()
        result=adjudicator.score_both_arms_after_external_release(
            k2(),a,bb,p)
        self.assertEqual(result["scored_times_minutes"],[5,10,15,20,30,40])
        self.assertTrue(result["same_six_observations_for_both_arms"])
        self.assertTrue(result["K1_was_used"])
        self.assertEqual(result["parent_G4a_candidate_sha256"],
                         a["candidate_sha256"])
        self.assertEqual(result["parent_G4b_candidate_sha256"],
                         bb["candidate_sha256"])
        for arm,labels in (("M",{"C00","C01"}),
                           ("D",{"D1","D2","D3"})):
            self.assertEqual(result[arm]["arm"],arm)
            self.assertEqual(result[arm]["status"],"PAIRED")
            self.assertIsNotNone(result[arm]["paired_set_loss_gain_orders"])
            self.assertEqual(result[arm]["K1"]["n_scored_times"],6)
            self.assertIsNone(result[arm]["REF_CAF"]["set_loss_mean"])
            self.assertEqual(result[arm]["REF_SCALE"]["status"],
                             "POINT_ELIGIBLE")
            self.assertFalse(
                result[arm]["equal_information_method_advantage_claim_allowed"])
        self.assertFalse(result["G5_G4a_G4b_external_receipts_verified_here"])
        self.assertFalse(result["ATMS_persisted_here"])
        self.assertFalse(result["native_G2_verified_here"])
        self.assertFalse(result["baseline_updated_with_K1"])

    def test_no_K0_candidates_both_arms_abstain_not_zero_loss(self):
        p=policy()
        scan=joint.audit_admissible_integer_k0(p)["rows"]
        x=next(x for x in scan if not x["any_survivor"])
        p,a,bb=scenario(x["K0_D5"],x["K0_D10"])
        self.assertFalse(bb["K1_used"])
        report=adjudicator.score_both_arms_after_external_release(k2(),a,bb,p)
        for arm in ("M","D"):
            self.assertEqual(report[arm]["status"],"NOT_PAIRED_ABSTENTION")
            self.assertEqual(report[arm]["K0"]["status"],"ABSTAIN_NO_CANDIDATE")
            self.assertEqual(report[arm]["K1"]["status"],"ABSTAIN_NO_CANDIDATE")
            self.assertIsNone(report[arm]["paired_set_loss_gain_orders"])
            self.assertIsNone(report[arm]["revision_predictive_improvement_pass"])
        self.assertFalse(report["K1_was_used"])

    def test_D_only_K0_support_keeps_M_abstention(self):
        p=policy()
        states=joint.audit_admissible_integer_k0(p)["rows"]
        x=next(x for x in states if (not x["M_two_families"]
               and not any(joint.from_public_k0(
                   x["K0_D5"],x["K0_D10"],p)[0][f]["eligible"]
                   for f in ("C00","C01")) and x["D_any"]))
        # Even if the K1 observation later rejects D, a missing M K0
        # hypothesis cannot be assigned an invented K2 set loss.
        p,a,bb=scenario(x["K0_D5"],x["K0_D10"],delivered=0)
        report=adjudicator.score_both_arms_after_external_release(k2(),a,bb,p)
        self.assertEqual(report["M"]["status"],"NOT_PAIRED_ABSTENTION")
        self.assertIsNone(report["M"]["K0"]["set_loss_mean"])
        self.assertFalse(report["M"]["revision_predictive_improvement_pass"])
        self.assertEqual(report["D"]["arm"],"D")

    def test_K1_can_abstain_D_after_positive_K0_but_still_score_M(self):
        p,a,bb=scenario()
        # Correct stored precommitments, but K1 posterior empty in D: this
        # is a valid negative outcome and must not be scored as zero.
        copied=copy.deepcopy(bb)
        copied["K2_revised_D_by_family"]={"D1":None,"D2":None,"D3":None}
        copied["candidate_sha256"]=bridge.digest({
            k:v for k,v in copied.items() if k!="candidate_sha256"})
        result=adjudicator.score_both_arms_after_external_release(
            k2(),a,copied,p)
        self.assertIsNone(result["D"]["K1"]["set_loss_mean"])
        self.assertEqual(result["D"]["status"],"NOT_PAIRED_ABSTENTION")
        self.assertIsNone(result["D"]["revision_predictive_improvement_pass"])
        self.assertEqual(result["M"]["status"],"PAIRED")
        # This is tampering to test the scorer's empty-set treatment. It is
        # NOT evidence of a real G4b with an actual contradictory K1 result.

    def test_invalid_K2_or_tampered_G4a_G4b_rejected_before_scoring(self):
        p,a,bb=scenario()
        evil=copy.deepcopy(a)
        evil["K2_prior_D_by_family"]["D1"]=None
        with self.assertRaises(bridge.CutBlocked):
            adjudicator.score_both_arms_after_external_release(k2(),evil,bb,p)
        evil=copy.deepcopy(bb)
        evil["K2_prior_D_by_family_sha256"]="sha256:"+"0"*64
        evil["candidate_sha256"]=bridge.digest({
            k:v for k,v in evil.items() if k!="candidate_sha256"})
        with self.assertRaisesRegex(bridge.CutBlocked,"PREVIOUS_PREDICTIONS"):
            adjudicator.score_both_arms_after_external_release(k2(),a,evil,p)
        with self.assertRaises(bridge.CutBlocked):
            adjudicator.score_both_arms_after_external_release(
                k2([8,14,20,27,27,27]),a,bb,p)
        altered=copy.deepcopy(p)
        altered["k2"]["delta_success_at_least_orders"]=0
        with self.assertRaises(bridge.CutBlocked):
            adjudicator.score_both_arms_after_external_release(k2(),a,bb,altered)
        with self.assertRaises(ValueError):
            adjudicator.authorize_K2_reveal(externally_verified=True)


if __name__=="__main__":
    unittest.main()
