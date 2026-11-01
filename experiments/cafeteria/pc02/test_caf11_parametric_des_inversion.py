"""CAF-11: finite contract/parity evidence for exact rational parametric inversion."""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as x
from experiments.cafeteria.pc01 import caf01_des_engine as des

SHA = "a"*40
HEAD = "b"*40


def exact_config(indices,c):
    c=Fraction(c)
    stages=[
        {"servers":1 if j in indices else 2,
         "service_minutes":str(Fraction(60,1)/c)
                           if j in indices else "1"}
        for j in range(3)
    ]
    conf={"schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,"stages":stages}
    des.validate_private_config(conf)
    return conf


class CAF11ExactInverseTests(unittest.TestCase):
    def test_piecewise_max_creates_and_preserves_exact_root(self):
        a=x.Clock.line(1,0)
        v=x.Clock.line(0,1)
        s=a.vmax(v)
        self.assertEqual(s.at(Fraction(4,5)),Fraction(1))
        self.assertEqual(s.at(Fraction(1)),Fraction(1))
        self.assertEqual(s.at(Fraction(21,20)),Fraction(21,20))
        self.assertIn(Fraction(1),[k[0] for k in s.knots])
        r=x.Clock.line(1,0).roots_at(Fraction(9,10))
        self.assertEqual(r,{Fraction(9,10)})
        m=a.add(v)
        self.assertEqual(m.at(Fraction(9,10)),Fraction(19,10))
        # A flat coincident event has to include BOTH interval endpoints.
        constant=x.Clock.line(0,10)
        self.assertEqual(constant.roots_at(10),{x.D_LOW,x.D_HIGH})

    def test_regimes_are_exhaustive_rational_partition(self):
        for m in x.models():
            atoms=x.certified_regimes(m["stages"])
            self.assertEqual(atoms[0]["left"],x.D_LOW)
            self.assertEqual(atoms[-1]["right"],x.D_HIGH)
            self.assertEqual(atoms[0]["kind"],"point")
            self.assertEqual(atoms[-1]["kind"],"point")
            self.assertTrue(all(a["left"]<=a["right"] for a in atoms))
            self.assertTrue(all(atoms[i]["kind"]==
                                ("point" if i%2==0 else "open")
                                for i in range(len(atoms))))
            self.assertTrue(all(a["right"]==b["left"]
                                for a,b in zip(atoms,atoms[1:])))
            self.assertTrue(all(v>=0 for a in atoms
                                for row in a["pred"].values() for v in row))

    def test_exact_clocks_match_native_des_over_structures_and_capacities(self):
        capacities=[
            Fraction(55),Fraction(60),Fraction(68),
            Fraction(69),Fraction(75),Fraction(83),
            Fraction(90),Fraction(97),Fraction(105),
            Fraction(110),Fraction(137,2)
        ]
        for structure in x.STAGE_SETS:
            for probe in x.PROBES:
                clocks=x.clock_tandem(structure,probe["rate"])
                for c in capacities:
                    d=Fraction(60)/c
                    symbolic=sum(v.at(d)<=probe["minute"] for v in clocks)
                    observed=b.read_physical(
                        exact_config(structure,c),
                        probe["rate"],probe["minute"],probe["channels"])
                    self.assertEqual([symbolic],observed,(
                        structure,probe["id"],c))

    def test_event_time_boundary_is_counted_in_native_des(self):
        # Locate actual internal root: at root, completion at t must be counted.
        structure=(0,)
        probe=x.K1
        clocks=x.clock_tandem(structure,probe["rate"])
        roots=sorted(set().union(*(
            f.roots_at(probe["minute"]) for f in clocks)))
        interior=[r for r in roots if x.D_LOW<r<x.D_HIGH]
        self.assertTrue(interior)
        for d in interior[:3]:
            at=sum(f.at(d)<=probe["minute"] for f in clocks)
            left=sum(f.at(d-Fraction(1,10**7))<=probe["minute"] for f in clocks)
            right=sum(f.at(d+Fraction(1,10**7))<=probe["minute"] for f in clocks)
            self.assertGreaterEqual(left,at)
            self.assertGreaterEqual(at,right)
            real=b.read_physical(
                exact_config(structure,Fraction(60)/d),
                probe["rate"],probe["minute"],probe["channels"])
            self.assertEqual([at],real)

    def test_capacity_region_merges_and_endpoint_inversion(self):
        l,r=Fraction(3,5),Fraction(4,5)
        atoms=[
            {"kind":"point","left":l,"right":l,
             "include_left":True,"include_right":True,
             "pred":{"K0":[7],"K1":[17]}},
            {"kind":"open","left":l,"right":r,
             "include_left":False,"include_right":False,
             "pred":{"K0":[7],"K1":[17]}},
            {"kind":"point","left":r,"right":r,
             "include_left":True,"include_right":True,
             "pred":{"K0":[9],"K1":[19]}},
        ]
        c=x.merge_atoms(atoms,{"K0":[7],"K1":[17]})
        self.assertEqual(len(c),1)
        self.assertTrue(c[0]["include_left"])
        self.assertFalse(c[0]["include_right"])
        self.assertTrue(x.contains_duration(c,l))
        self.assertFalse(x.contains_duration(c,r))
        z=x.capacity_regions(c)[0]
        self.assertEqual(z["capacity_low"],"75")
        self.assertFalse(z["low_included"])
        self.assertEqual(z["capacity_high"],"100")
        self.assertTrue(z["high_included"])

    def test_parity_against_old_discrete_bank_and_true_parameter_containment(self):
        bank=b.bank(True)
        pred=b.precompute(bank)
        families=[
            {"id":m["id"],"label":m["label"],
             "atoms":x.certified_regimes(m["stages"])}
            for m in x.models()
        ]
        for world in x.worlds():
            observed=x.observe_world(world["config"])
            self.assertEqual(x.baseline_classes(bank,pred,observed),
                             b.classes(bank,b.eligible(bank,pred,{
                                 "baseline":observed["K0"],
                                 b.FIRST_ACTION_ID:observed["K1"],
                             })))
            inv=x.analyze(observed,families)
            self.assertEqual(len(inv),6)
            labels={m["label"]:m for m in inv}
            if world["truth_class"] is not None:
                family=labels[world["truth_class"]]
                self.assertTrue(
                    x.contains_duration(family["_duration_components"],
                                        Fraction(60,world["capacity"])),
                    world["id"])
            else:
                self.assertIsNone(world["truth_class"])
            self.assertNotIn("truth_class",str(
                [{k:v for k,v in a.items()
                  if k!="_duration_components"} for a in inv]))

    def test_run_records_20_worlds_without_promoting_diagnostics(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"caf11"
            r=x.run(out,SHA,HEAD)
            self.assertEqual(r["n_models"],6)
            self.assertEqual(r["n_worlds"],20)
            self.assertEqual(r["n_model_world_inversions"],120)
            self.assertEqual(r["promotion_gate"],x.GATE)
            self.assertFalse(r["deployment_validated"])
            self.assertEqual(r["summary"]["in_family_worlds"],18)
            self.assertEqual(r["summary"]["out_of_family_controls"],2)
            self.assertEqual(r["summary"]["continuous_true_parameter_coverage"],18)
            plan=json.loads((out/"00_PLAN_PRE_EVALUACION.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],x.PROTO_FIRST)
            self.assertEqual(plan["new_evaluation_world_DES_calls_before_plan"],0)
            self.assertEqual(plan["pr_head_sha"],HEAD)
            self.assertEqual(plan["checkout_sha"],SHA)
            self.assertEqual(len(plan["precomputed_rational_regimes"]),6)
            manifest=json.loads((out/"03_MANIFIESTO.json").read_text())
            for name,dig in manifest["files_sha256"].items():
                self.assertEqual(dig,"sha256:"+sha256(
                    (out/name).read_bytes()).hexdigest())
            for row in r["evaluations"]:
                if row["truth_class_EVALUATOR_ONLY"] is None:
                    self.assertIsNone(row["continuous_true_class_covered"])
                    self.assertIsNone(row[
                        "true_capacity_contained_in_true_family_EVALUATOR_ONLY"])
                self.assertEqual(len(row["continuous_regions"]),6)
            with self.assertRaisesRegex(ValueError,"CAF11_REFUSE_TO_OVERWRITE"):
                x.run(out,SHA,HEAD)


if __name__=="__main__":
    unittest.main(verbosity=2)
