#!/usr/bin/env python3
import copy
from fractions import Fraction
import unittest

from caf01_des_engine import (
    DESBlocked, SCHEMA, TIE_POLICY, half_open_arrivals,
    private_commitment, run_toy_engine, validate_private_config,
    verify_private_commitment,
)


def toy(*stages):
    return {"schema": SCHEMA, "tie_policy": TIE_POLICY,
            "stages": [{"servers": a, "service_minutes": b} for a, b in stages]}


class TestCAF01IndependentDESPreflight(unittest.TestCase):
    def test_public_arrivals_exact_no_world_run(self):
        construction = half_open_arrivals("6/5", "20")
        evaluation = half_open_arrivals("3/2", "20")
        self.assertEqual((len(construction), len(evaluation)), (24, 30))
        self.assertEqual(construction[0], Fraction(5, 12))
        self.assertEqual(evaluation[0], Fraction(1, 3))
        self.assertTrue(all(Fraction(0) < t < 20 for t in construction + evaluation))
        self.assertEqual(len(set(construction)), 24)

    def test_half_open_excludes_time_zero_and_pulse_end(self):
        arrivals = half_open_arrivals("1/2", "3")
        self.assertEqual(arrivals, (Fraction(1),))
        self.assertEqual(half_open_arrivals("1", "2"), (Fraction(1,2), Fraction(3,2)))

    def test_explicit_completion_before_arrival_at_same_timestamp(self):
        config = toy((1, "1"))
        out = run_toy_engine(config, [Fraction(1,2), Fraction(3,2)],
                             [0, 1, Fraction(3,2), 2, Fraction(5,2)])
        self.assertEqual([(x.accepted_cum_orders,x.delivered_cum_orders,
                           x.pending_orders) for x in out],
                         [(0,0,0), (1,0,1), (2,1,1), (2,1,1), (2,2,0)])
        self.assertTrue(all(x.stage_in_service[0] <= 1 for x in out))

    def test_sample_includes_events_at_exact_sample_timestamp(self):
        config = toy((1, "1/2"))
        out = run_toy_engine(config, [Fraction(1,2)], [0,Fraction(1,2),1])
        self.assertEqual(out[1].accepted_cum_orders, 1)
        self.assertEqual(out[1].delivered_cum_orders, 0)
        self.assertEqual(out[-1].delivered_cum_orders, 1)

    def test_servers_are_finite_parallel_capacity(self):
        config = toy((2, "3"))
        out = run_toy_engine(config, ["1/2","3/2","5/2"],
                             [0,3,4,5,"11/2"])
        self.assertEqual(out[1].accepted_cum_orders, 3)
        self.assertEqual(out[1].stage_in_service, (2,))
        self.assertEqual(out[1].stage_waiting, (1,))
        self.assertEqual(out[-1].delivered_cum_orders, 3)
        self.assertEqual(out[-1].pending_orders, 0)

    def test_multistage_fifo_and_independent_material_balance(self):
        config = toy((1,"1"),(1,"2"))
        out = run_toy_engine(config, ["1/2","3/2","5/2"],[0,1,2,3,4,5,7,9])
        self.assertEqual(out[-1].delivered_cum_orders, 3)
        for x in out:
            self.assertEqual(x.accepted_cum_orders, x.delivered_cum_orders
                             + sum(x.stage_waiting) + sum(x.stage_in_service))
            self.assertEqual(x.pending_orders,
                             sum(x.stage_waiting) + sum(x.stage_in_service))
            self.assertTrue(all(a <= 1 for a in x.stage_in_service))

    def test_invalid_worlds_are_not_silently_repaired(self):
        valid=toy((1,"1"))
        cases=[]
        x=copy.deepcopy(valid);x["tie_policy"]="ARRIVE_BEFORE_COMPLETE";cases.append(x)
        x=copy.deepcopy(valid);x["stages"][0]["servers"]=0;cases.append(x)
        x=copy.deepcopy(valid);x["stages"][0]["servers"]=1.5;cases.append(x)
        x=copy.deepcopy(valid);x["stages"][0]["service_minutes"]="0";cases.append(x)
        x=copy.deepcopy(valid);x["stages"][0]["service_minutes"]="-1";cases.append(x)
        x=copy.deepcopy(valid);x["stages"][0]["service_minutes"]="NaN";cases.append(x)
        x=copy.deepcopy(valid);x["unapproved_mechanism"]="hidden";cases.append(x)
        for config in cases:
            with self.subTest(config=config), self.assertRaises(DESBlocked):
                validate_private_config(config)

    def test_input_times_strictly_ordered_and_bounded(self):
        for arrivals, observations in [
            (["1","1"],[0,2]), (["2","1"],[0,2]),
            (["1"],[0,"1/2"]), (["1"],[1,2]),
            (["1"],[0,2,2])
        ]:
            with self.subTest(arrivals=arrivals, observations=observations):
                with self.assertRaises(DESBlocked):
                    run_toy_engine(toy((1,1)), arrivals, observations)

    def test_private_commitment_requires_secret_nonce(self):
        cfg=toy((2,"3/2"))
        with self.assertRaisesRegex(DESBlocked, "NONCE"):
            private_commitment(cfg, b"tiny")
        nonce=b"secret-toy-only-32-byte-nonce-value!!"
        receipt=private_commitment(cfg, nonce)
        self.assertTrue(verify_private_commitment(cfg, nonce, receipt))
        self.assertFalse(verify_private_commitment(cfg, b"x"*32, receipt))
        changed=toy((1,"3/2"))
        self.assertFalse(verify_private_commitment(changed, nonce, receipt))
        self.assertNotIn("3/2", receipt)
        self.assertNotIn("servers", receipt)

    def test_determinism_and_horizon_pending(self):
        config=toy((1,"10"))
        args=(config,["1/2","3/2","5/2"],[0,1,2,4])
        a=run_toy_engine(*args)
        self.assertEqual(a,run_toy_engine(*args))
        self.assertEqual(a[-1].accepted_cum_orders,3)
        self.assertEqual(a[-1].delivered_cum_orders,0)
        self.assertEqual(a[-1].pending_orders,3)


if __name__ == "__main__":
    unittest.main()
