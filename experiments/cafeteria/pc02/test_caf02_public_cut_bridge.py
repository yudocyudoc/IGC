#!/usr/bin/env python3
"""Public-cut contract tests: candidate math only, no real DES/OMC/G5/K2."""
import copy
import json
import unittest

import caf02_public_cut_bridge as bridge
import caf02_d_k0k1k2_adapter as d
import caf02_joint_md_k1_design as joint


def policy():
    return json.loads(d.POLICY.read_text(encoding="utf-8"))


G5="sha256:"+"a"*64


def k0(a=1,b=5):
    return {"cut":"K0","delivered_t5":a,"delivered_t10":b,
            "world_precommitment_ref":G5}


class PublicCutsTest(unittest.TestCase):
    def test_public_K0_two_values_make_both_arms_and_G4a_prior(self):
        p=policy()
        a=bridge.create_g4a_candidate(k0(),p)
        self.assertTrue(bridge.checked_receipt(a))
        self.assertEqual(a["cut"],"G4a_PRE_K1_CANDIDATE_NOT_SEALED")
        self.assertEqual(a["K0_public"],k0())
        self.assertEqual(a["K0_M"]["C00"]["all_evaluated"],32)
        self.assertEqual(a["K0_M"]["C01"]["all_evaluated"],96)
        self.assertEqual(a["K0_D"]["candidate_evaluations"],54)
        self.assertEqual(set(a["K2_prior_M_by_family"]),{"C00","C01"})
        self.assertEqual(set(a["K2_prior_D_by_family"]),{"D1","D2","D3"})
        self.assertEqual(a["K2_K0_only_references"]["K1_measurement_seen"],False)
        self.assertFalse(a["K2_scored_values_present"])
        self.assertFalse(a["external_custody_verified"])
        self.assertFalse(a["ATMS_persistence_verified"])

    def test_selected_K1_shared_data_revises_both_and_preserves_prior(self):
        p=policy()
        a=bridge.create_g4a_candidate(k0(),p)
        opt=a["K1_preselected_common"]["proposed_measurement"]
        self.assertEqual(opt,{"rate_per_minute":1.8,"t_min":30})
        evidence={"cut":"K1","measurement":opt,"delivered":31,
                  "world_precommitment_ref":G5}
        bb=bridge.create_g4b_candidate(a,evidence,p)
        self.assertTrue(bridge.checked_receipt(bb))
        self.assertEqual(bb["parent_G4a_candidate_sha256"],
                         a["candidate_sha256"])
        self.assertEqual(bb["M_K1_revision"]["K1_observation"],
                         bb["D_K1_revision"]["K1_evidence"])
        self.assertEqual(bb["M_K1_revision"]["status"],
                         "K1_BOTH_FAMILIES_REMAIN")
        self.assertEqual(
            [len(bb["M_K1_revision"]["updated"][f]["kept"])
             for f in ("C00","C01")],[1,4])
        self.assertEqual([len(bb["D_K1_revision"]["compatible"][f])
                          for f in ("D1","D2","D3")],[1,1,0])
        self.assertEqual(bb["D_K1_revision"]["families_excluded_by_K1"],["D3"])
        self.assertFalse(bb["external_custody_verified"])
        self.assertEqual(bb["DES_runs"],0)
        self.assertFalse(bb["K2_scored_values_present"])
        self.assertEqual(bb["K2_prior_M_by_family_sha256"],
                         bridge.digest(a["K2_prior_M_by_family"]))

    def test_extra_private_accepted_counts_or_K2_in_K0_blocked(self):
        for field in ("accepted_t5","stage_waiting","K2_truth",
                      "private_parameters","nonce","delivered_t15"):
            v=k0()
            v[field]=0
            with self.subTest(field=field),self.assertRaises(bridge.CutBlocked):
                bridge.create_g4a_candidate(v,policy())

    def test_bad_K1_pulse_time_world_or_private_fields_fail(self):
        p=policy()
        a=bridge.create_g4a_candidate(k0(),p)
        choice=a["K1_preselected_common"]["proposed_measurement"]
        good={"cut":"K1","measurement":choice,"delivered":31,
              "world_precommitment_ref":G5}
        modifications=[
            {"cut":"K2"},
            {"world_precommitment_ref":"sha256:"+"b"*64},
            {"measurement":{"rate_per_minute":1.0,"t_min":10}},
            {"measurement":{"rate_per_minute":1.8,"t_min":20}},
            {"delivered":32.5},
            {"delivered":37},
            {"secret_stage_count":3},
            {"K2_truth":[1,2,3]},
        ]
        for changed in modifications:
            bad={**good,**changed}
            with self.subTest(changed=changed),self.assertRaises(bridge.CutBlocked):
                bridge.create_g4b_candidate(a,bad,p)

    def test_G4a_tamper_or_policy_drift_blocks_G4b(self):
        p=policy()
        a=bridge.create_g4a_candidate(k0(),p)
        evidence={"cut":"K1",
                 "measurement":a["K1_preselected_common"]["proposed_measurement"],
                 "delivered":31,"world_precommitment_ref":G5}
        bad=copy.deepcopy(a)
        bad["K2_prior_M_by_family"]["C00"]=None
        with self.assertRaisesRegex(bridge.CutBlocked,"LOCAL_HASH_CHANGED"):
            bridge.create_g4b_candidate(bad,evidence,p)
        drift=copy.deepcopy(p)
        drift["k1"]["effective_revision_tolerance_orders"]=2
        with self.assertRaisesRegex(bridge.CutBlocked,"WRONG_PARENT_OR_POLICY"):
            bridge.create_g4b_candidate(a,evidence,drift)

    def test_no_K1_is_exact_no_change_pre_post_forecast(self):
        p=policy()
        scan=joint.audit_admissible_integer_k0(p)["rows"]
        empty=next((x["K0_D5"],x["K0_D10"]) for x in scan
                   if not x["any_survivor"])
        a=bridge.create_g4a_candidate(k0(*empty),p)
        self.assertIsNone(a["K1_preselected_common"]["proposed_measurement"])
        with self.assertRaisesRegex(bridge.CutBlocked,"K1_INJECTED"):
            bridge.create_g4b_candidate(a,{"cut":"K1"},p)
        bb=bridge.create_g4b_candidate(a,None,p)
        self.assertFalse(bb["K1_used"])
        self.assertEqual(bb["K2_revised_M_by_family"],
                         a["K2_prior_M_by_family"])
        self.assertEqual(bb["K2_revised_D_by_family"],
                         a["K2_prior_D_by_family"])

    def test_G4a_b_cannot_consume_reserved_K2_or_authorize_DES(self):
        p=policy()
        a=bridge.create_g4a_candidate(k0(),p)
        selected=a["K1_preselected_common"]["proposed_measurement"]
        e={"cut":"K1","measurement":selected,"delivered":31,
           "world_precommitment_ref":G5}
        bb=bridge.create_g4b_candidate(a,e,p)
        payload={"cut":"K2","world_precommitment_ref":G5,
                 "delivered":[0,1,2,3,5,6]}
        self.assertEqual(bridge.validate_k2_reserved(payload,a,bb),
                         payload["delivered"])
        with self.assertRaisesRegex(bridge.CutBlocked,"K0_PUBLIC_MASK"):
            bridge.create_g4a_candidate(payload,p)
        with self.assertRaisesRegex(bridge.CutBlocked,"K1_PUBLIC_MASK"):
            bridge.create_g4b_candidate(a,payload,p)
        with self.assertRaisesRegex(bridge.CutBlocked,"NOT_IMPLEMENTED"):
            bridge.authorize_world_execution(
                alleged_witness={"verified":True},alleged_secret="123")

    def test_posthoc_self_attested_seal_is_not_external_custody(self):
        p=policy()
        a=bridge.create_g4a_candidate(k0(),p)
        bad=copy.deepcopy(a)
        bad["external_custody_verified"]=True
        with self.assertRaises(bridge.CutBlocked):
            bridge.checked_receipt(bad)
        self.assertNotIn("K2_truth",bridge.canonical(a).decode())
        self.assertNotIn("private_parameters",bridge.canonical(a).decode())


if __name__=="__main__":
    unittest.main()
