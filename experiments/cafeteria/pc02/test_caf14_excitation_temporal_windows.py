"""CAF-14: preregistered factor design, rational event-clock parity and provenance.

Tests do NOT assert that any program wins, that doubles become unique,
or that any unknown topology is always detected.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
import caf12_continuous_observability as v12
import caf13_structural_distinguishability as v13
import caf14_excitation_temporal_windows as a
from experiments.cafeteria.pc01 import caf01_des_engine as des

SHA="a"*40
HEAD="b"*40


class CAF14Tests(unittest.TestCase):
    def test_frozen_factorial_and_two_windows(self):
        f=a.frozen_programs()
        self.assertEqual(tuple(f),a.PROGRAM_NAMES)
        self.assertEqual(len(f),18)
        self.assertEqual(len(a.TIMES),5)
        self.assertEqual(a.TIMES,(10,15,20,25,40))
        self.assertEqual(a.RATES,(
            ("R15","3/2"),("R18","9/5"),("R25","5/2")))
        self.assertEqual(len({(x["rate"],x["minute"])
                              for seq in f.values() for x in seq}),17)
        self.assertEqual(len(f["BASE"]),2)
        self.assertEqual([len(x["channels"]) for x
                          in f["F_R25_T15"]],[1,1,6])
        self.assertEqual([p["minute"] for p
                          in f["W_R25_T10_T20"][-2:]],[10,20])
        self.assertEqual([p["minute"] for p
                          in f["W_R25_T15_T20"][-2:]],[15,20])
        self.assertEqual([p["rate"] for p
                          in f["W_R25_T15_T20"][-2:]],["5/2","5/2"])
        self.assertEqual(len(v12.worlds()),32)
        self.assertEqual(sum(x["truth_class"] is None
                             for x in v12.worlds()),5)
        with self.assertRaisesRegex(ValueError,"CAF14_UNDECLARED_TIME"):
            a.make_probe("X","5/2",13)

    def test_prefix_snapshot_equal_full_des_future_arrivals_not_affect_past(self):
        worlds=v12.worlds()
        for w in (worlds[0],worlds[9],worlds[-1]):
            for rate in ("3/2","9/5","5/2"):
                arrivals=des.half_open_arrivals(rate,20)
                full=des.run_toy_engine(
                    w["config"],arrivals,(0,10,15,20,25,40))
                for idx,time in enumerate((10,15)):
                    prefix=a.physical_snapshot(w["config"],rate,time)
                    self.assertEqual(prefix,full[idx+1],(w["id"],rate,time))
                    self.assertEqual(
                        prefix.delivered_cum_orders
                        +prefix.pending_orders,
                        prefix.accepted_cum_orders)

    def test_all_new_temporal_sensors_match_original_DES(self):
        rates=("3/2","9/5","5/2")
        capacities=(Fraction(55),Fraction(69),Fraction(83),
                    Fraction(97),Fraction(110),Fraction(145,2))
        for model in v11.models():
            calendars=a.clocks_for_model(model)
            for rate in rates:
                cal=calendars[rate]
                for c in capacities:
                    d=Fraction(60)/c
                    config={
                        "schema":des.SCHEMA,
                        "tie_policy":des.TIE_POLICY,
                        "stages":[{
                            "servers":1 if ix in model["stages"] else 2,
                            "service_minutes":str(d)
                                if ix in model["stages"] else "1"
                        } for ix in range(3)]
                    }
                    for t in a.TIMES:
                        physical=a.physical_snapshot(config,rate,t)
                        actual=a.physical_fields(physical,a.FULL_CHANNELS)
                        expected=v12.predict_channels(
                            cal,a.FULL_CHANNELS,t,d)
                        self.assertEqual(actual,expected,
                                         (model["id"],rate,t,str(c)))

    def test_base_and_t20_low_pressure_equal_caf13(self):
        for model in v11.models():
            clocks=a.clocks_for_model(model)
            for pid,other in (
                ("BASE","BASE"),
                ("F_R15_T20","FULL20_15"),
            ):
                new=a.family_program_catalog(model,pid,clocks)
                old=v13.family_signatures(model["stages"],other)
                actual={x["signature"] for x in new["signatures"]}
                prior={x["signature"] for x in old["signatures"]}
                self.assertEqual(actual,prior,(model["id"],pid))
                if pid=="BASE":
                    self.assertEqual(len(new["atoms"]),
                                     old["n_atomic_regimes"])

    def test_two_window_signature_has_same_duration_both_snapshots(self):
        model=v11.models()[3]
        pid="W_R25_T15_T20"
        cal=a.clocks_for_model(model)
        obj=a.family_program_catalog(model,pid,cal)
        probes=a.frozen_programs()[pid]
        for row in obj["signatures"]:
            d=row["witness_duration"]
            predicted={p["id"]:v12.predict_channels(
                cal[p["rate"]],p["channels"],p["minute"],d)
                for p in probes}
            self.assertEqual(a.signature_flat(predicted,probes),
                             row["signature"])
            self.assertEqual(row["witness_capacity"]*d,60)
        self.assertTrue(any(x["kind"]=="point" for x in obj["atoms"]))
        self.assertTrue(any(x["kind"]=="open" for x in obj["atoms"]))
        self.assertEqual(obj["atoms"][0]["left"],v11.D_LOW)
        self.assertEqual(obj["atoms"][-1]["right"],v11.D_HIGH)

    def test_structural_confusability_respects_two_independent_parameters(self):
        self.assertTrue(v13.compatible_signatures((0,),(2,)))
        self.assertFalse(v13.compatible_signatures((0,),(3,)))
        # "Two time windows" cannot be checked independently at different c:
        # the witness must carry a joint signature from a single atom.
        model=v11.models()[0]
        obj=a.family_program_catalog(
            model,"W_R25_T10_T20",a.clocks_for_model(model))
        for row in obj["signatures"]:
            self.assertEqual(len(row["signature"]),14)
        self.assertEqual(len({z["signature"] for z in obj["signatures"]}),
                         len(obj["signatures"]))

    def test_complete_run_has_all_precommitted_artifacts_and_no_promotion(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/"caf14"
            result=a.run(root,SHA,HEAD)
            self.assertEqual((
                result["n_worlds"],result["n_programs"],
                result["n_global_pair_comparisons"],
                result["n_structural_parameter_filters"],
                result["n_exact_family_program_catalogs"]),
                (32,18,270,3456,108))
            self.assertTrue(result["truth_never_passed_to_inverse"])
            self.assertTrue(result["no_external_validation"])
            self.assertTrue(result["fully_precomputed_before_world_evaluation"])
            self.assertFalse(result["no_new_selector"] is False)
            self.assertEqual(result["promotion_gate"],a.GATE)
            plan=json.loads((root/"00_PLAN_BEFORE_EVAL.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],a.PROTO_COMMIT)
            self.assertEqual(plan["n_frozen_inversions"],3456)
            self.assertEqual(plan["new_world_DES_calls_before_plan"],0)
            self.assertEqual(plan["pr_head_sha"],HEAD)
            self.assertEqual(plan["checkout_sha"],SHA)
            self.assertEqual(plan["catalog_sha256"],"sha256:"+sha256(
                (root/"00B_EXACT_SIGNATURES_BEFORE_EVAL.json").read_bytes()
            ).hexdigest())
            self.assertEqual(len(result["evaluations"]),576)
            for pid,s in result["summary"].items():
                self.assertEqual((s["n_within"],s["n_unknown_extra"]),(27,5))
                self.assertEqual(
                    (s["true_class_coverage"],s["true_parameter_coverage"]),
                    (27,27))
                self.assertEqual(s["global_confusable_pairs"]
                                 +s["global_separable_pairs"],15)
            for row in result["evaluations"]:
                if row["truth_class_EVALUATOR_ONLY"] is None:
                    self.assertIsNone(
                        row["robust_true_singleton_EVALUATOR_ONLY"])
                    self.assertIsNone(
                        row["truth_parameter_contained_EVALUATOR_ONLY"])
                else:
                    self.assertTrue(
                        row["truth_parameter_contained_EVALUATOR_ONLY"])
            manifest=json.loads((root/"03_MANIFIESTO.json").read_text())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(
                    digest,"sha256:"+sha256((root/name).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"CAF14_REFUSE_OVERWRITE"):
                a.run(root,SHA,HEAD)


if __name__=="__main__":
    unittest.main(verbosity=2)
