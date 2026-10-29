#!/usr/bin/env python3
"""Offline/PR security tests for D runner. Never execute a real RK4 integration."""
import json
import os
import unittest
from unittest.mock import patch

from caf01_d_rk4_github import (
    DScreenBlocked, INPUTS, read_view, require_github_one_shot, run_case,
)


class TestDOfficialGitHubRunner(unittest.TestCase):
    def test_exact_public_evidence_and_masks(self):
        caf, c, _ = read_view("CAF01")
        neg, _, _ = read_view("CAFN")
        self.assertEqual([x["t_min"] for x in caf["observations"]],
                         [0, 5, 10, 15, 20, 30, 40])
        self.assertEqual([x["t_min"] for x in neg["observations"]],
                         [0, 40])
        self.assertEqual([x["delivered"] for x in neg["observations"]], [0, 24])
        self.assertEqual(len(c["methods"]["D"]["topology_stock_counts"]), 3)

    def test_wrong_sha_rejected_without_integrations(self):
        with patch("caf01_d_rk4_github.INPUTS",
                   {"CAF01":("CAF01.json","0"*64,(0,5,10,15,20,30,40))}):
            with self.assertRaisesRegex(DScreenBlocked, "BYTES_CHANGED"):
                read_view("CAF01")

    def test_main_manual_first_attempt_required(self):
        good={"GITHUB_ACTIONS":"true",
              "GITHUB_EVENT_NAME":"workflow_dispatch",
              "GITHUB_REF":"refs/heads/main",
              "GITHUB_REPOSITORY":"yudocyudoc/IGC",
              "GITHUB_RUN_NUMBER":"1","GITHUB_RUN_ATTEMPT":"1"}
        with patch.dict(os.environ,good,clear=True):
            require_github_one_shot()
        for key,value in [
            ("GITHUB_REF","refs/heads/other"),
            ("GITHUB_EVENT_NAME","pull_request"),
            ("GITHUB_REPOSITORY","fork/IGC"),
            ("GITHUB_RUN_NUMBER","2"),
            ("GITHUB_RUN_ATTEMPT","2"),
        ]:
            with self.subTest(key=key):
                with patch.dict(os.environ,{**good,key:value},clear=True):
                    with self.assertRaisesRegex(DScreenBlocked,
                                                "ONLY_FIRST_GITHUB_MAIN"):
                        require_github_one_shot()

    def test_mocked_screen_18_per_mask_never_evaluation(self):
        calls=[]
        def fake_integrate(stocks,loss,params,pulse,times,step):
            calls.append(tuple(times))
            self.assertFalse(loss)
            self.assertEqual(pulse,{"rate":72,"duration":1/3})
            self.assertLessEqual(step,1/120 + 1e-12)
            return [min(60*t,24) for t in times]
        with patch("caf01_d_rk4_github.integrate",side_effect=fake_integrate):
            neg=run_case("CAFN")
            self.assertEqual(len(neg["candidate_rows"]),18)
            self.assertEqual(len(calls),18)
            self.assertTrue(all(x==(0.0,2/3) for x in calls))
            self.assertTrue(all(len(row["construction_delivered"])==2
                                for row in neg["candidate_rows"]))
            self.assertFalse(neg["future_evaluation_forecasts_produced"])
            self.assertFalse(neg["CAFN_intermediate_readings_used"])
            calls.clear()
            pos=run_case("CAF01")
            self.assertEqual(len(calls),18)
            self.assertTrue(all(x==(0.0,1/12,1/6,1/4,1/3,1/2,2/3)
                                for x in calls))
            self.assertEqual(len(pos["D_preliminary_representatives"]),3)
            self.assertTrue(all(not row["native_G2_verified"]
                                for row in pos["candidate_rows"]))
            self.assertFalse(pos["joint_D_B_M_G3_selection_performed"])
            self.assertEqual(pos["DES_world_runs"],0)

    def test_markers_precede_all_calls_even_if_rk4_fails(self):
        order=[]
        def marker(case,num):order.append(("marker",case,num))
        def failing(*args,**kwargs):
            order.append(("rk4",))
            raise RuntimeError("fictional integration failure")
        with patch("caf01_d_rk4_github.integrate",side_effect=failing):
            with self.assertRaisesRegex(RuntimeError,"fictional"):
                run_case("CAF01",on_invocation=marker)
        self.assertEqual(order,[("marker","CAF01",1),("rk4",)])


if __name__=="__main__":
    unittest.main()
