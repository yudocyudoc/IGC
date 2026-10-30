#!/usr/bin/env python3
"""Synthetic-only tests; NEVER use CAF01 DES evaluation or a CAF02 real world."""
import copy
import unittest

import caf02_class_predictor as c


def policy():
    return {
        "schema":c.POLICY_SCHEMA,
        "campaign_id":"CAF02",
        "status":"DRAFT_NOT_OPERATIONALLY_APPROVED",
        "construction_pulse":{"rate_per_minute":1.2,"duration_minutes":20},
        "future_public_pulse":{"rate_per_minute":1.5,"duration_minutes":20},
        "response_times_preparation_minutes":[1.0,3.0],
        "response_times_dispatch_minutes":[1.0,3.0],
        "shared_capacities_per_hour":[72,100],
        "compatibility_mae_allowance_orders":0.0,
        "point_max_envelope_width_orders":0.5,
        "operational_basis":{
            "status":"NOT_YET_JUSTIFIED",
            "responseTime_interpretation":
                "AGGREGATE_STOCK_TO_OUTFLOW_NOT_PER_ORDER_SERVICE_DURATION",
            "notes":"FABRICATED_NUMBERS_NO_INDEPENDENT_OPERATIONAL_EVIDENCE",
        },
        "future_truth_available":False,
        "independent_world_custody_verified":False,
        "independent_forecast_custody_verified":False,
    }


def evidence():
    return {
        "schema":c.CONSTRUCTION_SCHEMA,
        "campaign_id":"CAF02",
        "world_public_commitment_sha256":"sha256:"+("f"*64),
        "public_pulse":{"rate_per_minute":1.2,"duration_minutes":20},
        "observations":[{"t_min":t,"delivered":d} for t,d in
                        zip(c.TIMES,(0,2,7,13,19,24,24))],
        "data_provenance":{
            "source_kind":"PROPOSED_CONSTRUCTION_PUBLIC_ONLY",
            "synthetic_fixture":True,
            "witness_verified":False,
        },
    }


class ClassProtocolTests(unittest.TestCase):
    def test_nonbinding_stage_permutation_and_capacity_alias_construction(self):
        p=c.integrate_c00(1,3,72,1.2)
        swapped=c.integrate_c00(3,1,100,1.2)
        self.assertLess(max(abs(a-b) for a,b in zip(p,swapped)),1e-8)
        key=c.model_group_key(1,3,72,1.2)
        self.assertEqual(key,c.model_group_key(3,1,100,1.2))

    def test_alias_in_construction_breaks_under_future_rate(self):
        old=c.integrate_c00(1,3,72,1.2)
        other=c.integrate_c00(1,3,100,1.2)
        future72=c.integrate_c00(1,3,72,1.5)
        future100=c.integrate_c00(1,3,100,1.5)
        self.assertLess(max(abs(a-b) for a,b in zip(old,other)),1e-8)
        self.assertGreater(max(abs(a-b) for a,b in zip(future72,future100)),1)

    def test_compatible_class_keeps_both_capacities_in_future(self):
        r=c.fit(policy(),evidence())
        self.assertEqual(r["schema"],c.SCHEMA)
        self.assertEqual(r["nominal_grid_candidates"],8)
        self.assertEqual(r["construction_equivalent_classes"],1)
        members=r["construction_class_details"][0]["members"]
        self.assertEqual(len(members),4)
        self.assertEqual({m["capacity_per_hour"] for m in members},{72,100})
        self.assertFalse(r["construction_class_details"][0][
            "class_remains_equivalent_in_future"])
        self.assertGreater(r["full_compatible_envelope_max_width_orders"],1)
        self.assertEqual(r["point_status"],
                         "ABSTAIN_POINT_COMPATIBLE_FORECASTS_DIVERGE")
        self.assertIsNone(r["illustrative_point_mid_envelope"])
        self.assertFalse(r["evaluation_authorized"])
        self.assertFalse(r["future_truth_seen"])

    def test_guard_disallows_old_world_and_future_truth(self):
        e=evidence()
        e["campaign_id"]="CAF01"
        with self.assertRaises(c.Blocked): c.validate_construction(e,policy())
        e=evidence()
        e["evaluation_observations"]=[{"t_min":40,"delivered":30}]
        with self.assertRaisesRegex(c.Blocked,"EXACT_FIELDS"):
            c.validate_construction(e,policy())

    def test_no_self_declared_real_execution_or_external_custody(self):
        p=policy()
        p["status"]="OPERATIONALLY_APPROVED"
        with self.assertRaises(c.Blocked):c.validate_policy(p)
        p=policy()
        p["independent_world_custody_verified"]=True
        with self.assertRaises(c.Blocked):c.validate_policy(p)
        e=evidence()
        e["data_provenance"]["synthetic_fixture"]=False
        with self.assertRaises(c.Blocked):c.validate_construction(e,policy())

    def test_references_do_not_read_future_truth(self):
        r=c.fit(policy(),evidence())
        refs=r["frozen_rule_reference_proposals_construction_only"]
        self.assertEqual(set(refs),{"REF_CAF","REF_SCALE"})
        self.assertEqual(refs["REF_SCALE"]["ratio"],1.25)
        self.assertEqual(len(refs["REF_SCALE"]["predicted_delivered"]),6)
        self.assertEqual(refs["REF_CAF"]["status"],
                         "READY_EMPIRICAL_ONLY_NOT_PHYSICAL_CAPACITY")
        self.assertEqual(len(refs["REF_CAF"]["predicted_delivered"]),6)

    def test_reference_abstains_without_eligible_intervals(self):
        r=c.construction_only_references([0,1,2,3,4,5],1.2,1.5)
        # These data DO qualify if backlog exists; force no backlog instead:
        r=c.construction_only_references([6,12,18,24,24,24],1.2,1.5)
        self.assertIsNone(r["REF_CAF"]["predicted_delivered"])
        self.assertEqual(r["REF_SCALE"]["status"],"READY_PROPORTIONALITY_CONTROL")

    def test_saturating_capacity_does_not_inherit_swap_symmetry(self):
        self.assertNotEqual(c.model_group_key(1,3,20,1.2),
                            c.model_group_key(3,1,20,1.2))

    def test_policy_requires_explicit_aggregate_response_time_basis(self):
        p=policy()
        p["operational_basis"]["responseTime_interpretation"]="SERVICE_MINUTES_PER_ORDER"
        with self.assertRaisesRegex(c.Blocked,"OPERATIONAL_BASIS"):
            c.validate_policy(p)

    def test_balances_and_monotonicity(self):
        curve=c.integrate_c00(2,3,20,1.5)
        self.assertEqual(len(curve),6)
        self.assertTrue(all(a<=b for a,b in zip(curve,curve[1:])))
        self.assertLessEqual(curve[-1],30)


if __name__=="__main__":
    unittest.main()
