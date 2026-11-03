"""Adversarial G3 construction: real O0 integration optional, no DES/provider/OMC."""
from __future__ import annotations

from bisect import bisect_left
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import g3_construction as g
from scripts.arena_cafe import r2_causal_pos_signal as signal
from scripts.arena_cafe import r2_causal_g2 as dg2
from scripts.arena_cafe import observation_eval as oe
from scripts.arena_v0_contract import ArenaContractError


class G3ConstructionPure(unittest.TestCase):
    def test_00_rk4_constant_rate_exact_one_stock(self):
        segments=[{"start_minutes_exact":"0", "end_minutes_exact":"10",
                   "rate_orders_per_minute_exact":"1"}]
        outputs, final=g.integrate_native_d_equations(
            segments,1,False,100,1,8.1)
        self.assertAlmostEqual(10-(1-math.exp(-10)), outputs[-1],delta=0.005)
        self.assertAlmostEqual(sum(final),10,delta=0.005)
        self.assertAlmostEqual(final[-1],0,delta=1e-8)
        self.assertTrue(all(a<=b for a,b in zip(outputs,outputs[1:])))

    def test_01_losses_mass_balance_and_convergence(self):
        s=signal._signal([F(1),F(2),F(9,1),F(39,4)],F(10),F(1,2))
        out, state=g.integrate_native_d_equations(
            s["segments"],3,True,1.23,2.7,8.1,dt=0.01)
        fine,_=g.integrate_native_d_equations(
            s["segments"],3,True,1.23,2.7,8.1,dt=0.005)
        emitted=float(signal.event_mass_until(
            [F(1),F(2),F(9),F(39,4)],F(1,2),F(10)))
        self.assertAlmostEqual(sum(state),emitted,delta=0.005)
        self.assertTrue(all(a>=-1e-6 for a in state))
        self.assertLess(max(abs(a-b) for a,b in zip(out,fine)),0.005)

    def test_02_adversarial_nonphysical_params_fail(self):
        s=[{"start_minutes_exact":"0", "end_minutes_exact":"10",
            "rate_orders_per_minute_exact":"1"}]
        for bad in (0,-1,float("nan"),float("inf")):
            with self.subTest(bad=bad),self.assertRaises(ArenaContractError):
                g.integrate_native_d_equations(s,1,False,bad,1,1)
        with self.assertRaises(ArenaContractError):
            g.integrate_native_d_equations(s,4,False,1,1,1)


@unittest.skipUnless(os.environ.get("G3_PUBLIC_DIR"),"Needs original frozen A1 O0")
class G3ConstructionO0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.visible=json.loads((Path(os.environ["G3_PUBLIC_DIR"]) /
                                "O0_VISIBLE.json").read_text())

    def test_10_original_M_fixed_prior_bound_six(self):
        m=g.m_analytical_bound(self.visible)
        self.assertEqual(8,g.public_observations(self.visible)[-1])
        self.assertEqual(6,m["candidate_count"])
        self.assertEqual(6,m["incompatible_count"])
        self.assertTrue(all(F(x["upper_bound_delivery_at_10_minutes_exact"]) ==
                            F(10,3) for x in m["candidate_results"]))
        self.assertEqual("48",m["necessary_throughput_for_eight_in_10min_orders_per_hour"])
        self.assertEqual(0,m["new_native_simulations"])

    def test_11_six_D_external_small_grid_no_hidden_selection(self):
        d=g.d_external_grid(self.visible,capacities=(0.8,1.6),
                          responses=(0.35,1.4),losses=(1.,8.1))
        self.assertEqual(6,d["candidate_count"])
        self.assertEqual(3,sum(x["native_loss"] for x in d["candidates"]))
        self.assertEqual(6,len({x["native_structure_sha256"]
                                for x in d["candidates"]}))
        self.assertEqual([4,8,4,8,4,8],
                         [x["external_grid_evaluations"] for x in
                          d["candidates"]])
        self.assertEqual("NONE_ALL_SIX_RETAINED",d["candidate_selection_owner"])
        self.assertTrue(d["MAE_posthoc_exploratory"])
        self.assertTrue(all(x["search_is_not_identification"]
                            for x in d["candidates"]))

    def test_12_G3_is_construction_not_future(self):
        r=g.build(self.visible)
        self.assertIn("DESCRIPTIVE_CONSTRUCTION",r["gates"]["G3"])
        self.assertEqual("NOT_RUN",r["gates"]["G4"])
        self.assertEqual("NOT_RUN",r["gates"]["G5"])
        self.assertEqual("PARTIAL",r["gates"]["A3"])
        self.assertFalse(r["G3_is_prospective_blind_holdout"])
        self.assertEqual("NOT_RUN_OPT_IN_ONLY",r["D"]["mode"])
        self.assertEqual("NOT_AVAILABLE_NO_EV01_NATIVE_MODEL",r["H_j"]["B"])

    def test_13_mutated_observed_source_cannot_be_washed(self):
        from copy import deepcopy
        altered=deepcopy(self.visible)
        for row in altered["construction"]["observation_series"]:
            if row["t_minutes_exact"]=="10":
                row["delivered_cumulative"]=9
        with self.assertRaises(ArenaContractError):
            g.public_observations(altered)

    def test_14_causal_width_no_posthoc_outside_declared(self):
        with self.assertRaises(ArenaContractError):
            g.d_external_grid(self.visible,width=F(1,3),
                              capacities=(1,),responses=(1,),losses=(1,))


@unittest.skipUnless(os.environ.get("G3_PUBLIC_DIR") and
                     os.environ.get("G3_D_G2_DIR"),
                     "Needs existing frozen real OMC D traces")
class G3ConformanceToFrozenNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.visible=json.loads((Path(os.environ["G3_PUBLIC_DIR"]) /
                                "O0_VISIBLE.json").read_text())
        cls.native=Path(os.environ["G3_D_G2_DIR"])

    def test_20_rk4_mirror_agrees_with_six_original_OMC_fixture_traces(self):
        # This is ONLY numerical conformance at the prior engineering fixture.
        # It does not promote fixture params to an EV-01 estimate.
        dg2.verify(self.visible,self.native)
        m=json.loads((self.native/"manifest.json").read_text())
        seg=signal.from_visible(self.visible,"O0")["signal"]["segments"]
        p={k:v["value"] for k,v in m["nominal_parameters"].items()}
        for item in m["candidates"]:
            pred,_=g.integrate_native_d_equations(
                seg,item["stock_count"],item["loss"],
                p["capacity"],p["response_time"],p["loss_time"])
            rows=oe._rows(self.native/(item["csv_prefix"]+"_res.csv"))
            ts=[oe._column(x,"time") for x in rows]
            ys=[oe._column(x,"delivered") for x in rows]
            for t,value in zip(g.SAMPLES,pred):
                k=bisect_left(ts,t)
                self.assertLess(k,len(ts))
                if k==0:
                    native=ys[k]
                elif ts[k]==t:
                    native=ys[k]
                else:
                    w=(t-ts[k-1])/(ts[k]-ts[k-1])
                    native=ys[k-1]+w*(ys[k]-ys[k-1])
                self.assertLess(abs(value-native),0.15,
                                msg=f"native mirror drift: {item['candidate_id']} t={t}")


if __name__=="__main__":
    unittest.main()
