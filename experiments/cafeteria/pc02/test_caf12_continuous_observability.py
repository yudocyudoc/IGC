"""CAF-12: audit physical sensors, temporal boundaries, exact regimes, CAF-11 baseline.

The test suite asserts correctness and recorded experimental contracts only,
NOT any target number of correctly identified structures or winner of scheme.
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
import caf11_parametric_des_inversion as old
import caf12_continuous_observability as s
from experiments.cafeteria.pc01 import caf01_des_engine as des

SHA="a"*40
HEAD="b"*40


def rational_config(stages,c):
    duration=Fraction(60)/Fraction(c)
    return {
        "schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
        "stages":[
            {"servers":1 if i in stages else 2,
             "service_minutes":str(duration) if i in stages else "1"}
            for i in range(3)
        ],
    }


class CAF12Tests(unittest.TestCase):
    def test_eight_scheme_contracts_costs_and_frozen_worlds(self):
        self.assertEqual(s.SCHEME_NAMES,(
            "BASE","PREP_Q","DISPATCH_Q","DELIVERY_Q",
            "DISPATCH_STOCK","PREP_DISPATCH_Q",
            "ALL_QUEUES","STRESS_PREP_DISPATCH"))
        expected_cost=(1,3,3,3,3,5,7,8)
        self.assertEqual(tuple(
            b.FIRST["cost"]+(
                b.ACTION_BY_ID[s.SCHEME_MAP[name]]["cost"]
                if s.SCHEME_MAP[name] else 0)
            for name in s.SCHEME_NAMES),expected_cost)
        self.assertEqual(s.K0["channels"],(("delivered",None),))
        self.assertEqual(s.K1["channels"],(("delivered",None),))
        self.assertEqual(s.scheme_probes("BASE"),(s.K0,s.K1))
        self.assertEqual(len(s.worlds()),32)
        self.assertEqual(Counter(w["cohort"] for w in s.worlds()),{
            "H_CAF11_EXPOSED_20":20,
            "N_ADDITIONAL_DOUBLE_9":9,
            "N_ADDITIONAL_EXTRA_3":3,
        })
        self.assertEqual(sum(w["truth_class"] is not None for w in s.worlds()),27)
        self.assertEqual(sum(w["truth_class"] is None for w in s.worlds()),5)
        self.assertEqual(
            [w["id"] for w in s.worlds()[:20]],
            [w["id"] for w in old.worlds()])

    def test_exact_stage_waiting_and_stock_parity_with_native_des(self):
        capacities=(
            Fraction(55),Fraction(68),Fraction(75),Fraction(83),
            Fraction(97),Fraction(105),Fraction(110),Fraction(147,2),
        )
        probes=tuple(
            p for scheme in s.SCHEME_NAMES for p in s.scheme_probes(scheme))
        unique={(p["rate"],p["minute"],p["channels"]):p for p in probes}
        for m in s.models():
            for rate in sorted({x["rate"] for x in unique.values()}):
                symbolic=s.build_parametric_calendar(m["stages"],rate)
                for p in unique.values():
                    if p["rate"]!=rate:
                        continue
                    for cap in capacities:
                        d=Fraction(60)/cap
                        computed=s.predict_channels(
                            symbolic,p["channels"],p["minute"],d)
                        physical=b.read_physical(
                            rational_config(m["stages"],cap),
                            rate,p["minute"],p["channels"])
                        self.assertEqual(computed,physical,
                                         (m["id"],rate,cap,p["channels"]))
                        self.assertTrue(all(z>=0 for z in computed))

    def test_exact_singletons_at_sensor_event_boundaries(self):
        probe=s.probe(b.ACTION_BY_ID["prep_dispatch_15_t20"])
        symbol=s.build_parametric_calendar((0,),"3/2")
        clocks=list(s.all_clocks_for_probes(
            {"3/2":symbol},(probe,)))
        roots=sorted({
            r for clock,t in clocks
            for r in clock.roots_at(t)
            if old.D_LOW<r<old.D_HIGH})
        self.assertTrue(roots,"No boundary roots for waiting, test vacuous")
        for d in roots[:8]:
            cap=Fraction(60)/d
            measured=s.predict_channels(symbol,probe["channels"],20,d)
            native=b.read_physical(
                rational_config((0,),cap),"3/2",20,probe["channels"])
            self.assertEqual(measured,native,(d,cap))
        # Readings before/after a boundary may differ, so each atom must
        # have its own integer vector, including the singleton itself.
        atoms=s.exact_atomic_regimes(
            {"3/2":symbol},(probe,))
        self.assertEqual(atoms[0]["left"],old.D_LOW)
        self.assertEqual(atoms[-1]["right"],old.D_HIGH)
        self.assertEqual(
            len(atoms),2*len({a["left"] for a in atoms if a["kind"]=="point"})-1)
        self.assertTrue(all(atoms[i]["kind"]==
                            ("point" if i%2==0 else "open")
                            for i in range(len(atoms))))
        for x,y in zip(atoms,atoms[1:]):
            self.assertEqual(x["right"],y["left"])

    def test_all_eight_scheme_regions_include_true_capacity(self):
        families=s.get_scheme_families()
        self.assertEqual(len(families),48)
        for w in s.worlds():
            observations={}
            for scheme in s.SCHEME_NAMES:
                measurements={
                    p["id"]:b.read_physical(
                        w["config"],p["rate"],p["minute"],p["channels"])
                    for p in s.scheme_probes(scheme)}
                obs=s.evaluated_scheme(measurements,scheme,families)
                labels={x["class"] for x in obs if x["nonempty"]}
                if w["truth_class"] is not None:
                    self.assertIn(w["truth_class"],labels,w["id"])
                    true=next(x for x in obs if x["class"]==w["truth_class"])
                    self.assertTrue(old.contains_duration(
                        true["_d_components"],Fraction(60,w["capacity"])),
                        (w["id"],scheme))
                observations[scheme]=labels
            for scheme in s.SCHEME_NAMES:
                self.assertTrue(observations[scheme].issubset(
                    observations["BASE"]),(w["id"],scheme))

    def test_base_matches_caf11_exactly_on_twenty_exposed_worlds(self):
        families=s.get_scheme_families()
        previous=[
            {"id":m["id"],"label":m["label"],
             "atoms":old.certified_regimes(m["stages"])}
            for m in old.models()]
        for w in old.worlds():
            measurements=old.observe_world(w["config"])
            original=old.analyze(measurements,previous)
            newer=s.evaluated_scheme(measurements,"BASE",families)
            by_old={x["label"]:x["regions_capacity"] for x in original}
            by_new={x["class"]:x["capacity_regions"] for x in newer}
            self.assertEqual(by_old,by_new,w["id"])

    def test_inverse_is_truth_blind_and_missing_channels_fail_closed(self):
        fam=s.get_scheme_families()
        obs={"K0":[8],"K1":[20]}
        actual=s.evaluated_scheme(obs,"BASE",fam)
        self.assertEqual(len(actual),6)
        self.assertTrue(all("truth" not in k for k in actual[0]))
        with self.assertRaisesRegex(ValueError,"CAF12_INVALID_OBSERVATION_SET"):
            s.evaluated_scheme({"K0":[8]},"BASE",fam)
        with self.assertRaisesRegex(ValueError,"CAF12_CHANNEL_SCHEMA_MISMATCH"):
            s.compatible({"K0":[8],"K1":[20]}, {"K0":[8]})
        with self.assertRaisesRegex(ValueError,"CAF12_UNKNOWN_SCHEME"):
            s.scheme_probes("PLACEHOLDER_BAD")

    def test_precommitted_evaluation_artifacts_and_invariants(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"CAF12"
            r=s.run(out,SHA,HEAD)
            self.assertEqual(r["n_worlds"],32)
            self.assertEqual(r["n_scheme_evaluations"],256)
            self.assertEqual(r["n_inversions"],1536)
            self.assertTrue(r["all_in_family_truth_capacity_covered"])
            self.assertTrue(r["truth_never_passed_to_inverse"])
            self.assertTrue(r["no_policy_selection"])
            self.assertTrue(r["no_external_validity_proven"])
            self.assertEqual(r["promotion_gate"],s.GATE)
            plan=json.loads((out/"00_PLAN_PRE_EVALUACION.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],s.PROTOCOL_COMMIT)
            self.assertEqual(plan["new_evaluation_world_DES_calls_before_plan"],0)
            self.assertEqual(plan["checkout_sha"],SHA)
            self.assertEqual(plan["pr_head_sha"],HEAD)
            self.assertEqual(plan["family_count"],6)
            self.assertEqual(len(plan["schemes"]),8)
            regimes=(out/"00B_EXACT_REGIMES_PRE_EVALUACION.json").read_bytes()
            self.assertEqual(plan["regimes_sha256"],
                             "sha256:"+sha256(regimes).hexdigest())
            manifest=json.loads((out/"03_MANIFIESTO.json").read_text())
            for name,dig in manifest["file_sha256"].items():
                self.assertEqual(dig,"sha256:"+sha256(
                    (out/name).read_bytes()).hexdigest())
            for scheme in s.SCHEME_NAMES:
                m=r["summary"][scheme]
                self.assertEqual((m["in_family"],m["unknown_extra"]),(27,5))
                self.assertEqual((m["parameter_coverage"],m["class_coverage"]),
                                 (27,27))
                self.assertLessEqual(m["cost_units"],8)
            with self.assertRaisesRegex(ValueError,"CAF12_DO_NOT_OVERWRITE"):
                s.run(out,SHA,HEAD)


if __name__=="__main__":
    unittest.main(verbosity=2)
