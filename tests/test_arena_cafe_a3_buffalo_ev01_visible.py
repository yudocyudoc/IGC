"""A3 B Cloudflare preflight: no inference, public evidence and no cross-view leak."""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction as Q
import unittest

from scripts import arena_event_observability as obs
from scripts.arena_cafe import ev01,evidence
from scripts.arena_cafe.buffalo_ev01_visible import stage
from scripts.arena_v0_contract import ArenaContractError, validate_visible_input


class BuffaloEV01PublicStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw,snap=ev01.trace_generator()
        ev01.verify_des_parity(snap)
        cls.views=evidence.build(obs.project_events(raw,"POS"),
                                 obs.project_events(raw,"FULL"))["views"]

    def test_both_conditions_preserve_source_exact_and_one_frozen_reconstruction(self):
        r={}
        for c in ("O0","O1"):
            src=self.views[c]
            payload,receipt=stage(src,c)
            r[c]=(payload,receipt)
            self.assertEqual(validate_visible_input(payload),
                             receipt["buffalo_visible_hash"])
            self.assertEqual(src["source_snapshot_hash"],payload["source_snapshot_hash"])
            self.assertEqual(15,len(payload["construction"]["events"]))
            self.assertEqual(6,len(payload["construction"]["observation_series"]))
            p=payload["construction"]["declared_input_reconstruction"]
            self.assertEqual(20,len(p["piecewise_constant_bins"]))
            self.assertEqual(15,sum(x["orders_integrated"] for x in
                                    p["piecewise_constant_bins"]))
            self.assertEqual(Q(15),sum(
                (Q(x["end_hours_exact"])-Q(x["start_hours_exact"]))*
                Q(x["rate_orders_per_hour_exact"])
                for x in p["piecewise_constant_bins"]))
            self.assertEqual(Q(1,6),Q(p["piecewise_constant_bins"][-1]["end_hours_exact"]))
            self.assertEqual(1,payload["resources"]["max_llm_calls"])
            self.assertEqual(0,payload["resources"]["max_simulations"])
            self.assertEqual(0,receipt["provider_calls"])
            self.assertEqual("NOT_RUN",receipt["g2"])
            self.assertEqual("NOT_RUN",receipt["scientific_native_inference"])
            self.assertNotIn("transferencia_final",str(payload))
            self.assertNotIn("resource_id",str(payload))
            self.assertNotIn("des_engine",str(payload))
            self.assertNotIn("generator_parameters",str(payload))
        o0,o1=r["O0"][0],r["O1"][0]
        self.assertNotIn("authorized_preparation_aggregate",o0["construction"])
        self.assertIn("authorized_preparation_aggregate",o1["construction"])
        self.assertEqual(o0["construction"]["events"],o1["construction"]["events"])
        self.assertEqual(o0["construction"]["observation_series"],
                         o1["construction"]["observation_series"])
        self.assertEqual(o0["construction"]["declared_input_reconstruction"],
                         o1["construction"]["declared_input_reconstruction"])
        self.assertNotEqual(o0["source_snapshot_hash"],o1["source_snapshot_hash"])
        self.assertNotEqual(r["O0"][1]["buffalo_visible_hash"],
                            r["O1"][1]["buffalo_visible_hash"])

    def test_forged_cross_condition_and_timestamp_fails_closed(self):
        with self.assertRaisesRegex(ArenaContractError,"A1_CROSS_CONDITION"):
            stage(self.views["O0"],"O1")
        src=deepcopy(self.views["O0"])
        src["construction"]["pos_arrival_events"][0]["t_minutes_exact"]="11"
        with self.assertRaisesRegex(ArenaContractError,
                                    "A1_POS_ARRIVALS_TIME_OR_ID"):
            stage(src,"O0")
        src=deepcopy(self.views["O0"])
        src["construction"]["observation_series"][-1][
            "orders_created_cumulative"]+=1
        with self.assertRaisesRegex(ArenaContractError,
                                    "A1_POS_ARRIVALS_COUNT_PARITY"):
            stage(src,"O0")

    def test_historical_success_not_equated_with_this_case(self):
        native,record=stage(self.views["O0"],"O0")
        self.assertTrue(record["historical_B_cloudflare_success_is_not_current_EV01_call"])
        self.assertEqual("B_NATIVE_INPUT_STAGED_ZERO_PROVIDER_CALLS",record["status"])
        self.assertIn("Buffalo",native["question"])
        self.assertTrue(native["construction"][
            "declared_input_reconstruction"]["not_an_observed_instantaneous_rate"])


if __name__=="__main__":
    unittest.main()
