"""F4 developmental physical witness: one action, two indistinguishable O0 mechanisms.

No parameter grid or native D/B/M replacement. Actual engine = historical DES.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import f4_rival_bottleneck_witness as f4
from scripts.arena_physical import des_engine as des
from scripts.arena_v0_contract import ArenaContractError


class PureFixtureContracts(unittest.TestCase):
    def test_00_no_grid_only_two_declared_physical_mechanisms(self):
        self.assertEqual(("1","3/5","2/5"),f4.A_SERVICE)
        self.assertEqual(("3/5","1","2/5"),f4.B_SERVICE)
        self.assertEqual("ADD_ONE_PREPARATION_SERVER_FROM_TIME_ZERO",f4.ACTION)
        self.assertEqual(3,len(f4.STAGES))
        self.assertEqual(0,f4.S0_TOLERANCE_ORDERS)
        self.assertEqual(3,f4.MIN_COUNTERFACTUAL_DIVERGENCE_ORDERS)

    def test_01_original_engine_mass_balance_on_each_rival(self):
        arrivals=tuple(Q(1,5)+Q(2,5)*j for j in range(15))
        for service in (f4.A_SERVICE,f4.B_SERVICE):
            for prep_servers in (1,2):
                config=f4._config(service,prep_servers=prep_servers)
                self.assertEqual(des.TIE_POLICY,config["tie_policy"])
                rows=f4._run(config,arrivals)
                for s in rows:
                    self.assertEqual(s.accepted_cum_orders,
                                     s.delivered_cum_orders+s.pending_orders)
                    self.assertEqual(s.pending_orders,
                                     sum(s.stage_waiting)+sum(s.stage_in_service))

    def test_02_intervention_is_same_action_on_both_not_hidden_tune(self):
        for service in (f4.A_SERVICE,f4.B_SERVICE):
            origin=f4._config(service)
            action=f4._config(service,prep_servers=2)
            self.assertEqual([1,1,1],[s["servers"] for s in origin["stages"]])
            self.assertEqual([2,1,1],[s["servers"] for s in action["stages"]])
            self.assertEqual([s["service_minutes"] for s in origin["stages"]],
                             [s["service_minutes"] for s in action["stages"]])


@unittest.skipUnless(bool(os.environ.get("F4_O0")),
                     "Requires existing A1 public O0")
class FrozenO0Witness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o0=json.loads(Path(os.environ["F4_O0"]).read_text())
        cls.report=f4.build(cls.o0)

    def test_10_exact_o0_equivalence_and_rival_mechanisms(self):
        r=self.report
        self.assertEqual([0,0,2,4,6,8],r["S0_observed_delivered_cumulative"])
        self.assertEqual(r["S0_observed_delivered_cumulative"],
                         r["S0_model_baselines"]["PREP_SLOW_A"]["delivered_cumulative"])
        self.assertEqual(r["S0_observed_delivered_cumulative"],
                         r["S0_model_baselines"]["DISPATCH_SLOW_B"]["delivered_cumulative"])
        self.assertNotEqual(r["S0_model_baselines"]["PREP_SLOW_A"]["private_evaluator_stage_states"],
                            r["S0_model_baselines"]["DISPATCH_SLOW_B"]["private_evaluator_stage_states"])
        self.assertTrue(r["fixed_rivals_selected_constructively_not_parameter_grid"])

    def test_11_one_action_diverges_predictively_at_ten(self):
        r=self.report
        baseline=r["S0_observed_delivered_cumulative"][-1]
        self.assertEqual(baseline,r["b_postaction_delivered_t10"])
        self.assertGreaterEqual(
            r["a_postaction_delivered_t10"]-baseline,
            f4.MIN_COUNTERFACTUAL_DIVERGENCE_ORDERS)
        self.assertEqual(abs(r["a_postaction_delivered_t10"]-
                             r["b_postaction_delivered_t10"]),
                         r["absolute_counterfactual_divergence_orders"])
        self.assertFalse(r["one_common_intervention"]["business_costs_available"])
        self.assertEqual("NOT_ASSESSED",
                         r["one_common_intervention"][
                             "physical_space_staff_inventory_feasibility"])

    def test_12_development_not_blind_or_pm_recovery(self):
        r=self.report
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertFalse(r["preregistered_future_experiment"])
        self.assertTrue(r["development_witness_is_not_prospective_confirmation"])
        self.assertEqual("NOT_RUN",r["PM_ablation_with_without_P"])
        self.assertEqual("NOT_ESTABLISHED",r["PM_incremental_over_B1_B2"])
        self.assertTrue(r["no_new_DES_or_parameter_grid_or_provider_or_PM"])
        self.assertEqual("NOT_RUN",r["D_B_M_native_inference_on_this_F4_pair"])

    def test_13_reject_relabelled_o1_as_o0(self):
        v=deepcopy(self.o0)
        v["observability"]["condition_id"]="O1"
        with self.assertRaises((ArenaContractError,ValueError)):
            f4.build(v)

    def test_14_reject_tampered_public_delivery_series(self):
        v=deepcopy(self.o0)
        v["construction"]["observation_series"][3]["delivered_cumulative"]+=1
        with self.assertRaises((ArenaContractError,ValueError)):
            f4.build(v)

    def test_15_reject_tampered_arrival_event(self):
        v=deepcopy(self.o0)
        v["construction"]["pos_arrival_events"][0]["t_minutes_exact"]="1/10"
        with self.assertRaises((ArenaContractError,ValueError)):
            f4.build(v)

    def test_16_reject_hidden_stage_field_on_o0(self):
        v=deepcopy(self.o0)
        v["construction"]["physical_observation"]={"stage_disclosed":"despacho"}
        with self.assertRaises((ArenaContractError,ValueError)):
            f4.build(v)


if __name__=="__main__":
    unittest.main()
