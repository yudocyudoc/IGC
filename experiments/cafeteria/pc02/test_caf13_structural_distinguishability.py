"""CAF-13: exact global confusability, rational witnesses, sensor parity."""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
import caf12_continuous_observability as v12
import caf13_structural_distinguishability as d

SHA="a"*40
HEAD="b"*40


class CAF13Tests(unittest.TestCase):
    def test_frozen_programs_and_cardinality(self):
        self.assertEqual(d.IDS,(
            "BASE","Q20_15","STOCK20_15","FULL20_15",
            "Q40_15","FULL40_15","Q20_18","FULL40_18"))
        self.assertEqual(len(v12.worlds()),32)
        self.assertEqual(len(v11.models()),6)
        self.assertEqual(len(d.program_probes("BASE")),2)
        for pid in d.IDS[1:]:
            self.assertEqual(len(d.program_probes(pid)),3)
            self.assertEqual(d.program_probes(pid)[0],v12.K0)
            self.assertEqual(d.program_probes(pid)[1],v12.K1)
        with self.assertRaisesRegex(ValueError,"CAF13_UNDECLARED_PROGRAM"):
            d.program_probes("INVALID")
        self.assertTrue(all(
            p["minute"] in (10,20,40)
            for pid in d.IDS for p in d.program_probes(pid)))

    def test_nontransitivity_and_integer_box_overlap(self):
        self.assertTrue(d.compatible_signatures((0,),(2,)))
        self.assertTrue(d.compatible_signatures((2,),(4,)))
        self.assertFalse(d.compatible_signatures((0,),(4,)))
        self.assertFalse(d.compatible_signatures((0,5),(0,8)))
        self.assertTrue(d.compatible_signatures((2,5),(3,7)))
        self.assertTrue(d.compatible_exact((3,),(4,)))
        self.assertFalse(d.compatible_exact((3,),(5,)))
        with self.assertRaisesRegex(ValueError,"CAF13_BAD_SIGNATURE_LENGTH"):
            d.compatible_exact((0,),(0,0))

    def test_global_pair_has_witness_with_two_independent_parameters(self):
        vectorsA=[
            {"signature":(0,5,0),"witness_c":Fraction(67)},
            {"signature":(0,10,0),"witness_c":Fraction(83)}
        ]
        vectorsB=[
            {"signature":(0,8,0),"witness_c":Fraction(70)},
            {"signature":(1,4,2),"witness_c":Fraction(90)}
        ]
        w=d.sign_pair_witness(vectorsA,vectorsB)
        self.assertIsNotNone(w)
        self.assertTrue(d.compatible_signatures(
            w["first_signature"],w["second_signature"]))
        self.assertNotEqual(w["first_capacity"],w["second_capacity"])
        self.assertTrue(all(
            abs(x-y)<=d.TOLERANCE
            for x,y in zip(w["common_integer_observation_example"],
                           w["first_signature"])))
        self.assertTrue(all(
            abs(x-y)<=d.TOLERANCE
            for x,y in zip(w["common_integer_observation_example"],
                           w["second_signature"])))
        no=d.sign_pair_witness(
            [{"signature":(0,0,0),"witness_c":Fraction(60)}],
            [{"signature":(0,3,0),"witness_c":Fraction(60)}])
        self.assertIsNone(no)

    def test_one_parameter_joint_across_all_probes_and_exact_witnesses(self):
        model=v11.models()[0]
        for program in d.IDS:
            obj=d.family_signatures(model["stages"],program)
            self.assertTrue(obj["signatures"])
            self.assertEqual(
                len({tuple(z["signature"]) for z in obj["signatures"]}),
                len(obj["signatures"]))
            for row in obj["signatures"]:
                p=d.program_probes(program)
                dval=row["witness_d"]
                calendars={
                    rate:v12.build_parametric_calendar(model["stages"],rate)
                    for rate in {a["rate"] for a in p}
                }
                expected={
                    a["id"]:v12.predict_channels(
                        calendars[a["rate"]],a["channels"],a["minute"],dval)
                    for a in p
                }
                self.assertEqual(row["signature"],d.flattened(expected,p))
                self.assertTrue(v11.D_LOW<=dval<=v11.D_HIGH)
                self.assertEqual(row["witness_c"]*row["witness_d"],60)

    def test_new_horizons_channels_parity_to_original_des(self):
        values=(Fraction(55),Fraction(69),Fraction(83),
                Fraction(99,1),Fraction(143,2),Fraction(110))
        for model in v11.models():
            for program in d.IDS:
                if program=="BASE":
                    continue
                for cap in values:
                    config=b.make_physical_config(model["stages"],int(cap)) if cap.denominator==1 else {
                        "schema":b.des.SCHEMA,"tie_policy":b.des.TIE_POLICY,
                        "stages":[{
                            "servers":1 if i in model["stages"] else 2,
                            "service_minutes":str(Fraction(60)/cap)
                                if i in model["stages"] else "1"
                        } for i in range(3)],
                    }
                    readings=d.physical_observe(config,program)
                    probes=d.program_probes(program)
                    calendars={
                        rate:v12.build_parametric_calendar(model["stages"],rate)
                        for rate in {p["rate"] for p in probes}
                    }
                    dval=Fraction(60)/cap
                    symbolic={
                        p["id"]:v12.predict_channels(
                            calendars[p["rate"]],p["channels"],p["minute"],dval)
                        for p in probes
                    }
                    self.assertEqual(readings,symbolic,
                                     (model["id"],program,str(cap)))

    def test_base_matches_caf11_and_q20_matches_caf12(self):
        for model in v11.models():
            for program in ("BASE","Q20_15"):
                states=d.family_signatures(model["stages"],program)
                a={tuple(x["signature"]) for x in states["signatures"]}
                probes=d.program_probes(program)
                cals={
                    rate:v12.build_parametric_calendar(model["stages"],rate)
                    for rate in {p["rate"] for p in probes}
                }
                if program=="BASE":
                    old=v11.certified_regimes(model["stages"])
                else:
                    old=v12.exact_atomic_regimes(cals,v12.scheme_probes("ALL_QUEUES"))
                prev={tuple(d.flattened(at["pred"],probes))
                      if program=="BASE"
                      else tuple(v for p in v12.scheme_probes("ALL_QUEUES")
                                 for v in at["pred"][p["id"]])
                      for at in old}
                self.assertEqual(a,prev)

    def test_run_provenance_scientific_gate_and_pair_graph(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"caf13"
            res=d.run(folder,SHA,HEAD)
            self.assertEqual((res["n_worlds"],res["n_programs"],
                              res["n_pair_comparisons"],
                              res["n_family_world_program_filters"]),
                             (32,8,120,1536))
            self.assertEqual(res["promotion_gate"],d.GATE)
            self.assertTrue(res["not_real_world_validated"])
            self.assertTrue(res["truth_never_given_to_inference"])
            self.assertEqual(len(res["evaluations"]),256)
            self.assertEqual(len(res["global_graph"]),8)
            plan=json.loads((folder/"00_PLAN_ANTES_MUNDOS.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],d.PROTO_COMMIT)
            self.assertEqual(plan["true_world_DES_calls_before_plan"],0)
            self.assertEqual(plan["pr_head_sha"],HEAD)
            self.assertEqual(plan["checkout_sha"],SHA)
            self.assertEqual(plan["catalog_sha256"],"sha256:"+sha256(
                (folder/"00B_CATALOGO_FIRMAS_ANTES_MUNDOS.json").read_bytes()).hexdigest())
            self.assertTrue((folder/"00C_GRAFO_GLOBAL_PRE_EVALUACION.json").exists())
            for pid in d.IDS:
                graph=res["global_graph"][pid]
                self.assertEqual(graph["n_pairs"],15)
                self.assertEqual(
                    graph["n_existentially_confusable"]+
                    graph["n_robustly_separable_global"],15)
                self.assertEqual(res["summary"][pid]["in_family_covered"],27)
                self.assertEqual(res["summary"][pid]["n_in_family"],27)
                self.assertEqual(res["summary"][pid]["n_unknown"],5)
            for r in res["evaluations"]:
                if r["truth_class_EVALUATOR_ONLY"] is None:
                    self.assertIsNone(r["robustly_singleton_true_state_EVALUATOR_ONLY"])
                    self.assertIsNone(r["true_class_covered_EVALUATOR_ONLY"])
                else:
                    self.assertTrue(r["true_class_covered_EVALUATOR_ONLY"])
            manifest=json.loads((folder/"03_MANIFIESTO.json").read_text())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(
                    digest,"sha256:"+sha256((folder/name).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"CAF13_REFUSE_OVERWRITE"):
                d.run(folder,SHA,HEAD)


if __name__=="__main__":
    unittest.main(verbosity=2)
