#!/usr/bin/env python3
"""CAF02 D-only offline integration tests; NO DES/OMC/Buffalo/CAF01 evaluation."""
import copy
import json
import unittest
from pathlib import Path

import caf02_d_k0k1k2_adapter as d
import caf02_k2_set_scoring as scoring
import caf02_structural_k0k1k2 as m
import caf02_joint_md_k1_design as joint
from scripts.arena_d_v1_screen import integrate


def policy():
    return json.loads(d.POLICY.read_text(encoding="utf-8"))


def k0_input(stocks=2,cap=72,tau=3,rate=1.2):
    y=d.predicted(stocks,cap,tau,rate,(5,10))
    return [{"t_min":5,"delivered":y[0]},
            {"t_min":10,"delivered":y[1]}]


def external_choice(p,rate=1.8,t=30):
    """Legacy synthetic choice fixture; NEVER an externally witnessed joint decision."""
    return {
        "status":"K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION",
        "proposed_measurement":{"rate_per_minute":rate,"t_min":t},
        "precommitted_policy":{
            "absolute_residual_max_orders":
                p["k1"]["absolute_residual_tolerance_orders"],
            "numerical_guard_orders":
                p["k1"]["numerical_allowance_orders"],
            "effective_revision_tolerance_orders":
                p["k1"]["effective_revision_tolerance_orders"],
            "minimum_expanded_nonoverlap_gap_orders":
                p["k1"]["minimum_positive_expanded_gap_orders"],
        },
    }


def no_k1(p):
    x=external_choice(p)
    x["status"]="K1_MENU_CANNOT_ROBUSTLY_DISCRIMINATE"
    x["proposed_measurement"]=None
    return x


class DCAF02AdapterTests(unittest.TestCase):
    def test_source_is_historical_D_integrator_with_explicit_units(self):
        result=d.predicted(2,72,3,1.2,(5,10,15,20,30,40))
        native=integrate(2,False,
            {"capacity":72,"response_time":3/60,"loss_time":1},
            {"rate":72,"duration":1/3},
            [x/60 for x in d.TIMES],1/1200)
        for a,b in zip(result,native):
            self.assertAlmostEqual(a,b,places=11)

    def test_policy_explicitly_distinguishes_D_and_M_grammars(self):
        p=policy()
        dd=d.parse_policy(p)
        self.assertEqual(dd["available_structures"],["D1","D2","D3"])
        self.assertEqual(dd["shared_response_time_minutes"],
                         [1,1.5,2,3,6,10])
        self.assertEqual(dd["capacity_items_per_hour"],[48,72,100])
        self.assertFalse(dd["loss"])
        self.assertFalse(p["scope"]["new_architecture"])
        self.assertEqual(dd["budget"]["total_distinct_candidate_trajectory_calls_max"],378)

    def test_k0_calibrates_ALL_54_and_keeps_ambiguity(self):
        p=policy()
        k0=d.calibrate_k0(k0_input(),p)
        self.assertEqual(k0["candidate_evaluations"],54)
        self.assertEqual(set(k0["compatible"]),{"D1","D2","D3"})
        self.assertTrue(any(r["id"]=="D2_C72_T3"
                            for r in k0["compatible"]["D2"]))
        self.assertTrue(any(r["id"]=="D2_C100_T3"
                            for r in k0["compatible"]["D2"]))
        self.assertFalse(k0["parameter_identifiable"])
        self.assertFalse(k0["native_G2_verified"])
        self.assertFalse(k0["K2_truth_seen"])

    def test_k0_can_reject_all_54_even_if_observed_totals_are_materially_possible(self):
        p=policy()
        # Six deliveries at minute 5, followed by no further deliveries at 10
        # are not materially impossible, but not adequately represented by
        # this D grid and should never create false narrow confidence.
        obs=[{"t_min":5,"delivered":6},
             {"t_min":10,"delivered":6}]
        result=d.calibrate_k0(obs,p)
        self.assertEqual(result["candidate_evaluations"],54)
        self.assertEqual(sum(len(x) for x in result["compatible"].values()),0)
        empty_revision=d.revise_k1(result,no_k1(p),None,p)
        forecast=d.prepare_k2(result,empty_revision,p)
        self.assertIsNone(forecast["K0_union"])
        self.assertIsNone(forecast["K1_union"])
        self.assertEqual(forecast["K0_pre_K2_point_decision"]["status"],
                         "ABSTAIN_ALL_NO_ADEQUATE_D_CANDIDATE")
        self.assertIsNone(forecast["K1_pre_K2_point_decision"]["point_delivered"])

    def test_nonbinding_D_capacities_alias_in_K0_but_not_future(self):
        initial=d.predicted(2,72,1,1.2,d.TIMES)
        initial_other=d.predicted(2,100,1,1.2,d.TIMES)
        self.assertLess(max(abs(a-b) for a,b in zip(initial,initial_other)),1e-8)
        later=d.predicted(2,72,1,1.8,d.TIMES)
        later_other=d.predicted(2,100,1,1.8,d.TIMES)
        self.assertGreater(max(abs(a-b) for a,b in zip(later,later_other)),1)

    def test_K1_uses_selected_ALTERNATE_pulse_and_retains_real_grid_witness(self):
        p=policy()
        k0=d.calibrate_k0(k0_input(),p)
        common=external_choice(p,rate=1.8,t=30)
        observed=d.predicted(2,72,3,1.8,(30,))[0]
        k1=d.revise_k1(k0,common,
                       {"rate_per_minute":1.8,"t_min":30,
                        "delivered":observed},p)
        self.assertTrue(k1["K1_evidence_used"])
        self.assertEqual(k1["source_preselected_measurement"],
                         common["proposed_measurement"])
        self.assertTrue(any(r["id"]=="D2_C72_T3"
                            for r in k1["compatible"]["D2"]))
        self.assertEqual(k1["revision_kind"],
                         "PARAMETRIC_RESTRICTION_NO_STRUCTURAL_EXCLUSION")
        self.assertFalse(k1["structural_hypothesis_reduction_at_K1"])
        self.assertTrue(k1["parametric_only_reduction_at_K1"])
        self.assertEqual(k1["families_excluded_by_K1"],[])
        for family in ("D1","D2","D3"):
            prior={x["id"] for x in k0["compatible"][family]}
            revised={x["id"] for x in k1["compatible"][family]}
            self.assertTrue(revised.issubset(prior))
        self.assertFalse(k1["ATMS_persisted"])

    def test_actual_M_selector_decision_wires_into_D_with_same_public_K0(self):
        p=policy()
        # Entirely SYNTHETIC scenario. Unlike external_choice(), this uses
        # the real M K0 fitter and selector (either selects or abstains).
        generated=m.params("C01",1,1,72,6)
        curve=list(m.curve(generated,1.2))
        observed=[{"t_min":5,"delivered":curve[0]},
                  {"t_min":10,"delivered":curve[1]}]
        grid={
            "preparation_tau":p["candidate_parameters"]["preparation_tau_minutes"],
            "dispatch_tau":p["candidate_parameters"]["dispatch_tau_minutes"],
            "shared_cap":p["candidate_parameters"][
                "shared_preparation_dispatch_capacity_orders_per_hour"],
            "transit_tau":p["candidate_parameters"]["transit_tau_minutes_C01"],
        }
        m_k0=m.k0_calibrate(curve,1.2,[0,1],grid,1.0,.4)
        m_choice=m.select_k1_measurement(m_k0,
            [{k:v for k,v in o.items() if k!="duration_minutes"}
             for o in p["k1"]["menu"]],
            p["k1"]["minimum_positive_expanded_gap_orders"],
            p["k1"]["absolute_residual_tolerance_orders"],
            p["k1"]["numerical_allowance_orders"])
        d_k0=d.calibrate_k0(observed,p)
        if m_choice["proposed_measurement"] is None:
            d_k1=d.revise_k1(d_k0,m_choice,None,p)
            self.assertFalse(d_k1["K1_evidence_used"])
        else:
            chosen=m_choice["proposed_measurement"]
            value=m.curve(generated,chosen["rate_per_minute"])[
                m.T_VALUES.index(chosen["t_min"])]
            d_k1=d.revise_k1(d_k0,m_choice,
                {**chosen,"delivered":value},p)
            self.assertTrue(d_k1["K1_evidence_used"])
        out=d.prepare_k2(d_k0,d_k1,p)
        self.assertFalse(out["K2_truth_included"])
        self.assertFalse(out["G4_external_witness_verified"])
        self.assertEqual(out["world_DES_runs"],0)

    def test_K1_rejects_wrong_pulse_or_time_even_if_D_prefers_it(self):
        p=policy()
        k0=d.calibrate_k0(k0_input(),p)
        common=external_choice(p)
        with self.assertRaisesRegex(d.DBlocked,
                                    "NOT_PRESELECTED"):
            d.revise_k1(k0,common,
                        {"rate_per_minute":1.2,"t_min":30,
                         "delivered":10},p)
        with self.assertRaisesRegex(d.DBlocked,
                                    "NOT_PRESELECTED"):
            d.revise_k1(k0,common,
                        {"rate_per_minute":1.8,"t_min":10,
                         "delivered":10},p)
        with self.assertRaisesRegex(d.DBlocked,
                                    "NOT_PRESELECTED"):
            d.revise_k1(k0,common,
                        {"rate_per_minute":1.8,"t_min":30,
                         "delivered":45},p)

    def test_K1_refuses_tolerance_change_or_grid_mutation(self):
        p=policy()
        k0=d.calibrate_k0(k0_input(),p)
        altered=copy.deepcopy(p)
        altered["k1"]["effective_revision_tolerance_orders"]=2
        with self.assertRaises(d.DBlocked):
            d.revise_k1(k0,external_choice(p),None,altered)
        altered=copy.deepcopy(p)
        altered["d_method"]["shared_response_time_minutes"].append(20)
        with self.assertRaises(d.DBlocked):
            d.revise_k1(k0,external_choice(p),None,altered)

    def test_legacy_no_K1_choice_means_no_D_experiment_or_fake_gain(self):
        p=policy()
        k0=d.calibrate_k0(k0_input(),p)
        d_rank=d.diagnostic_k1_preference(k0,p)
        self.assertTrue(d_rank["does_not_override_M_common_selection"])
        self.assertEqual(len(d_rank["options"]),3)
        unchanged=d.revise_k1(k0,no_k1(p),None,p)
        self.assertFalse(unchanged["K1_evidence_used"])
        forecasts=d.prepare_k2(k0,unchanged,p)
        self.assertEqual(forecasts["K0_union"],forecasts["K1_union"])
        self.assertFalse(forecasts["G4_external_witness_verified"])
        self.assertEqual(forecasts["world_DES_runs"],0)
        self.assertFalse(forecasts["D_native_G2_verified"])

    def test_D_set_not_forced_to_point_or_abstention_by_parameter_alias(self):
        p=policy()
        k0=d.calibrate_k0(k0_input(),p)
        forecast=d.prepare_k2(k0,d.revise_k1(k0,no_k1(p),None,p),p)
        vals=forecast["K0_union"]
        self.assertIsNotNone(vals)
        self.assertGreater(vals["candidate_count"],1)
        self.assertEqual(len(vals["lower"]),6)
        decision=forecast["K0_pre_K2_point_decision"]
        self.assertIn(decision["status"],
                      ("POINT_ELIGIBLE_MID_ENVELOPE","SET_ONLY_ABSTAIN_POINT"))
        self.assertEqual(decision["point_delivered"] is not None,
                         decision["status"]=="POINT_ELIGIBLE_MID_ENVELOPE")
        self.assertEqual(len(vals["upper"]),6)
        self.assertTrue(all(a<=b for a,b in zip(vals["lower"],vals["upper"])))
        # Scorer is pure and does not secretly read any DES world.
        y=list(d.predicted(2,72,3,1.35,d.TIMES))
        report=scoring.summarize_envelope(vals["lower"],vals["upper"],y)
        self.assertIsNotNone(report["set_loss_mean"])
        self.assertIn(report["status"],("POINT_ELIGIBLE",
                                        "SET_ONLY_POINT_ABSTENTION"))

    def test_D_single_family_before_and_after_K1_is_not_structural_revision(self):
        p=policy()
        mk0,dk0=joint.from_public_k0(1,5,p)
        # Unit-test D lineage on a K0 support subset. This is not a
        # claim that the full D grid originally had one surviving family.
        single=copy.deepcopy(dk0)
        self.assertGreater(len(single["compatible"]["D2"]),1)
        single["compatible"]["D1"]=[]
        single["compatible"]["D3"]=[]
        choice=joint.select(mk0,single,p)
        option=choice["proposed_measurement"]
        cap=int(option["rate_per_minute"]*min(option["t_min"],20))
        revisions=[
            d.revise_k1(single,choice,{**option,"delivered":y},p)
            for y in range(cap+1)
        ]
        candidates=[r for r in revisions
                    if 0<r["family_counts_after"]["D2"]<
                            len(single["compatible"]["D2"])]
        self.assertTrue(candidates)
        for r in candidates:
            self.assertEqual(r["families_before_K1"],["D2"])
            self.assertEqual(r["surviving_families"],["D2"])
            self.assertFalse(r["structural_hypothesis_reduction_at_K1"])
            self.assertTrue(r["parametric_only_reduction_at_K1"])
            self.assertEqual(r["status"],"K1_D_PARAMETRIC_REDUCTION_ONLY")

    def test_no_K1_evidence_can_be_injected_when_M_abstains(self):
        p=policy()
        k0=d.calibrate_k0(k0_input(),p)
        with self.assertRaisesRegex(d.DBlocked,"INJECTED_WITHOUT_SELECTION"):
            d.revise_k1(k0,no_k1(p),
                        {"rate_per_minute":1.8,"t_min":30,"delivered":12},p)

    def test_tampered_policy_cannot_be_approved_by_offline_adapter(self):
        p=policy()
        p["status"]="AUTHORIZED"
        with self.assertRaises(d.DBlocked):
            d.calibrate_k0(k0_input(),p)
        p=policy()
        p["no_world_runs_authorized"]=False
        with self.assertRaises(d.DBlocked):
            d.calibrate_k0(k0_input(),p)

if __name__=="__main__":
    unittest.main()
