"""CAF-15A tests: positive-only counterexample search with exact native DES.

Never assert global 2D separation when a finite lattice has no witness.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import tempfile
import json
import unittest

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
import caf12_continuous_observability as v12
import caf13_structural_distinguishability as v13
import caf14_excitation_temporal_windows as v14
import caf15a_two_capacity_witnesses as a
from experiments.cafeteria.pc01 import caf01_des_engine as des

SHA="a"*40
HEAD="b"*40

class TwoIndependentCapacityWitnessTests(unittest.TestCase):
    def test_720_rows_including_90_diagonal_and_exact_capacities(self):
        rows=a.rows()
        self.assertEqual(len(rows),720)
        self.assertEqual(sum(r["diagonal"] for r in rows),90)
        self.assertEqual(sum(not r["diagonal"] for r in rows),630)
        self.assertEqual(len(a.C_GRID),15)
        self.assertEqual(len(set(x["id"] for x in rows)),720)
        self.assertEqual(len({x["model"] for x in rows}),6)
        for r in rows:
            validated=des.validate_private_config(r["config"])
            self.assertEqual(len(validated),3)
            self.assertEqual(sum(n==1 for n,_ in validated),len(r["stages"]))
            for st,capacity in zip(r["stages"],r["capacity_by_stage"]):
                self.assertEqual(validated[st][1],Fraction(60,capacity))
        with self.assertRaisesRegex(ValueError,"CAF15A_CAPACITY_NOT_ON_FROZEN_LATTICE"):
            a.config_for((0,1),(68,71))

    def test_diagonal_subset_and_frozen_programs(self):
        self.assertEqual(a.PIDS,("BASE","F_R18_T20","F_R25_T20","F_R25_T25"))
        programs=a.programs()
        self.assertEqual(set(programs),set(a.PIDS))
        self.assertEqual(
            [len(programs[k]) for k in a.PIDS],[2,3,3,3])
        self.assertEqual(
            [len(programs[k][-1]["channels"]) for k in a.PIDS[1:]],
            [6,6,6])
        for m in v11.models():
            for c in (68,83,110):
                caps=(c,)*len(m["stages"])
                config=a.config_for(m["stages"],caps)
                old=b.make_physical_config(m["stages"],c)
                self.assertEqual(config,old)
                predicted=a.native_readings(config)
                cal=v14.clocks_for_model(m)
                for pid,probes in programs.items():
                    d=Fraction(60,c)
                    expected=tuple(z for probe in probes
                                   for z in v12.predict_channels(
                                       cal[probe["rate"]],probe["channels"],
                                       probe["minute"],d))
                    self.assertEqual(predicted[pid],expected,(m["id"],c,pid))

    def test_non_diagonal_caps_still_share_config_across_all_probes(self):
        config=a.config_for((0,2),(68,95))
        durations=des.validate_private_config(config)
        self.assertEqual([x[0] for x in durations],[1,2,1])
        self.assertEqual(durations[0][1],Fraction(60,68))
        self.assertEqual(durations[2][1],Fraction(60,95))
        observed=a.native_readings(config)
        self.assertEqual(len(observed["BASE"]),2)
        for pid in a.PIDS[1:]:
            self.assertEqual(observed[pid][:2],observed["BASE"])
            self.assertEqual(len(observed[pid]),8)

    def test_shared_reading_vs_fixed_reading_are_distinct(self):
        self.assertEqual(a.candidate_with_witness((0,),(2,)),(1,))
        self.assertEqual(a.candidate_with_witness((0,),(3,)),None)
        self.assertFalse(a.compatible_with_fixed_reading((0,),(2,)))
        self.assertTrue(a.compatible_with_fixed_reading((1,),(2,)))
        self.assertIsNone(a.candidate_with_witness((0,4),(0,7)))
        with self.assertRaisesRegex(ValueError,"CAF15A_FIXED_READING_MISMATCH"):
            a.compatible_with_fixed_reading((0,),(0,0))

    def test_fast_extra_stages_bypass_legacy_constructor_without_truth_leak(self):
        for cap in (64,86,106,160,220):
            config=a.extra_config(cap)
            stage=des.validate_private_config(config)
            self.assertEqual(len(stage),4)
            self.assertEqual(stage[-1],(1,Fraction(60,cap)))
            self.assertEqual([n for n,t in stage[:3]],[2,2,2])
            observed=a.native_readings(config)
            self.assertEqual(len(observed["F_R25_T20"]),8)
            if cap<120:
                self.assertEqual(config,b.make_physical_config((),cap,extra=True))
            else:
                with self.assertRaisesRegex(ValueError,
                                             "CAF07B_INVALID_BOTTLENECK_CONFIGURATION"):
                    b.make_physical_config((),cap,extra=True)
        self.assertEqual(len(a.worlds()),29)

    def test_positive_2d_witnesses_are_exact_and_nontransitive(self):
        ra=[{"id":"a","model":"A","class":"A","diagonal":True,
             "capacity_by_stage":(68,),"signatures":{"P":(0,0,0)}}]
        rb=[{"id":"b","model":"B","class":"B","diagonal":False,
             "capacity_by_stage":(68,95),"signatures":{"P":(0,0,2)}}]
        rc=[{"id":"c","model":"C","class":"C","diagonal":True,
             "capacity_by_stage":(70,),"signatures":{"P":(0,0,4)}}]
        found=a.witness_for(ra,rb,"P")
        self.assertIsNotNone(found)
        self.assertTrue(found["at_least_one_off_diagonal"])
        self.assertEqual(found["common_integer_reading"],[0,0,1])
        self.assertIsNone(a.witness_for(ra,rc,"P"))
        self.assertIsNotNone(a.witness_for(rb,rc,"P"))
        self.assertTrue(v13.compatible_signatures((0,0,0),(0,0,2)))

    def test_full_audit_does_not_claim_global_2d_certification(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"caf15a"
            result=a.run(out,SHA,HEAD)
            self.assertEqual(result["n_hypothesis_rows"],720)
            self.assertEqual(result["n_programs"],4)
            self.assertEqual(result["n_worlds"],29)
            self.assertEqual(result["n_world_program_evaluations"],116)
            self.assertEqual(result["n_global_lattice_pair_comparisons"],60)
            self.assertTrue(result["no_global_2d_certificate"])
            self.assertTrue(result["no_external_validation"])
            self.assertTrue(result["truth_not_passed_to_infer"])
            self.assertTrue(result["all_24_true_two_capacities_recovered_on_lattice"])
            self.assertEqual(result["promotion_gate"],a.GATE)
            plan=json.loads((out/"00_PLAN_PRE_MUNDOS.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],a.PRECOMMIT)
            self.assertEqual(plan["precode_amendment"],a.PRECODE_AMENDMENT)
            self.assertEqual(plan["checkout_sha"],SHA)
            self.assertEqual(plan["pr_head_sha"],HEAD)
            self.assertTrue(plan["no_world_evaluator_called_before_bank_and_plan"])
            self.assertEqual(plan["catalog_sha256"],"sha256:"+sha256(
                (out/"00B_CATALOGO_TESTIGOS_PRE_MUNDOS.json").read_bytes()).hexdigest())
            for p in a.PIDS:
                m=result["summary"][p]
                self.assertEqual(m["offdiag_worlds"],24)
                self.assertEqual(m["extra_worlds"],5)
                self.assertEqual(m["offdiag_true_class_covered_2D_grid"],24)
                self.assertLessEqual(m["diag_witness_edges"],m["expanded_witness_edges"])
                self.assertEqual(len(result["graphs"][p]["pairs"]),15)
                for edge in result["graphs"][p]["pairs"]:
                    w=edge["expanded_witness"]
                    if w is not None:
                        self.assertTrue(all(abs(x-y)<=2 for x,y in zip(
                            w["first_signature"],w["second_signature"])))
                        self.assertTrue(all(abs(z-x)<=1 and abs(z-y)<=1
                            for z,x,y in zip(w["common_integer_reading"],
                                             w["first_signature"],
                                             w["second_signature"])))
            digest=json.loads((out/"03_MANIFIESTO.json").read_text())
            for filename,h in digest["sha256"].items():
                self.assertEqual(h,"sha256:"+sha256(
                    (out/filename).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"CAF15A_REFUSE_OVERWRITE"):
                a.run(out,SHA,HEAD)


if __name__=="__main__":
    unittest.main(verbosity=2)
