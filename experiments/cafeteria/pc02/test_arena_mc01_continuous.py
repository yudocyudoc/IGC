"""ARENA-MC01: grid-free four-layer contracts and CAF continuous adapter."""
from __future__ import annotations
from fractions import Fraction as Q
from pathlib import Path
import json
import tempfile
import unittest
from hashlib import sha256

from scripts import arena_methodology_continuous as mc
import arena_mc01_caf_adapter as c
import caf15b_certified_2d_exclusion as v15b


class ToyBounds:
    """A rigorous monotonic scalar backend independent of CAF, for falsifiers."""
    def predict(self,f,p,prog):
        assert prog=="TOY"
        return (int(p[0]>=Q(2,3))*5,)

    def bounds(self,f,box,prog):
        a,b=box[0]
        return ((int(a>=Q(2,3))*5,int(b>=Q(2,3))*5),)


class UninformativeBounds:
    """Conservative but uninformative for proving impossible observations."""
    def predict(self,f,p,prog):
        return (0,)
    def bounds(self,f,box,prog):
        return ((0,100),)


class ContinuousMethodologyTests(unittest.TestCase):
    def test_generic_contracts_have_no_caf_or_grid_dependency(self):
        family=mc.Family("generic",("duration",),((Q(1,2),Q(1)),))
        self.assertEqual(family.duration_domains,((Q(1,2),Q(1)),))
        with self.assertRaisesRegex(ValueError,"MC01_BAD_CONTINUOUS_DOMAIN"):
            mc.Family("invalid",("d",),((Q(1),Q(1)),))
        with self.assertRaisesRegex(ValueError,"MC01_ERROR_AND_PHYSICAL_PROVENANCE_REQUIRED"):
            mc.Observation("TOY",(0,),1,"","physical")
        with self.assertRaisesRegex(ValueError,"MC01_BAD_ERROR_RADIUS"):
            mc.Observation("TOY",(0,),-1,"synthetic","physical")

    def test_toy_certified_empty_and_reject_tampered_exclusion(self):
        fam=mc.Family("generic",("d",),((Q(1,2),Q(1)),))
        obs=mc.Observation("TOY",(20,),0,"bounded_fixture","independent_toy")
        r=mc.solve(fam,obs,ToyBounds(),max_nodes=8,max_depth=3)
        self.assertEqual(r["status"],mc.EMPTY)
        self.assertEqual(r["n_retained_boxes"],0)
        self.assertTrue(r["certificate_verified"])
        # A falsified proof cannot be silently accepted.
        self.assertFalse(mc.verify_cover(fam,obs,ToyBounds(),{
            "type":"X","channel":1},None)["valid"])
        obs2=mc.Observation("TOY",(0,),0,"bounded_fixture","independent_toy")
        self.assertFalse(mc.verify_cover(fam,obs2,ToyBounds(),{
            "type":"X","channel":0},None)["valid"])

    def test_toy_feasible_off_any_grid_and_sound_outer_cover(self):
        fam=mc.Family("generic",("d",),((Q(1,2),Q(1)),))
        obs=mc.Observation("TOY",(5,),0,"bounded_fixture","toy")
        r=mc.solve(fam,obs,ToyBounds(),max_nodes=64,max_depth=7)
        self.assertEqual(r["status"],mc.WITNESS)
        point=tuple(Q(x) for x in r["witness"]["parameter_durations"])
        self.assertEqual(ToyBounds().predict(fam,point,"TOY"),(5,))
        self.assertTrue(any(any(
            Q(lo)<=Q(7,9)<=Q(hi) for lo,hi in box)
            for box in r["retained_outer_boxes"]))
        self.assertFalse(r["n_retained_boxes"]==0)

    def test_unresolved_is_not_falsified_even_with_zero_witnesses(self):
        fam=mc.Family("generic",("d",),((Q(1,2),Q(1)),))
        obs=mc.Observation("TOY",(90,),0,"bounded_fixture","toy")
        r=mc.solve(fam,obs,UninformativeBounds(),max_nodes=1,max_depth=0)
        self.assertEqual(r["status"],mc.UNRESOLVED)
        self.assertGreater(r["n_retained_boxes"],0)
        self.assertTrue(r["certificate_verified"])
        judgement=mc.falsify((fam,),(r,))
        self.assertEqual(judgement["conclusion"],
                         "INDETERMINATE_MULTIPLE_OR_UNRESOLVED_FAMILIES")

    def test_falsification_separates_misspecification_and_uniqueness(self):
        fam=(mc.Family("A",("d",),((Q(1,2),Q(1)),)),
             mc.Family("B",("d",),((Q(1,2),Q(1)),)))
        e={"family_id":"A","status":mc.EMPTY}
        e2={"family_id":"B","status":mc.EMPTY}
        self.assertEqual(mc.falsify(fam,[e,e2])["conclusion"],
                "KNOWN_FAMILIES_INADEQUATE_UNDER_DECLARED_MODEL_AND_ERROR")
        yes={"family_id":"B","status":mc.WITNESS}
        self.assertEqual(mc.falsify(fam,[e,yes])["conclusion"],
                "CONDITIONAL_UNIQUE_WITHIN_DECLARED_FAMILIES")
        unknown={"family_id":"A","status":mc.UNRESOLVED}
        self.assertEqual(mc.falsify(fam,[unknown,yes])["conclusion"],
                "INDETERMINATE_MULTIPLE_OR_UNRESOLVED_FAMILIES")

    def test_six_structural_families_not_24_or_720_point_bank(self):
        ff=c.families()
        self.assertEqual(len(ff),6)
        self.assertEqual(sum(len(f.parameter_names)==1 for f in ff),3)
        self.assertEqual(sum(len(f.parameter_names)==2 for f in ff),3)
        for f in ff:
            self.assertTrue(all(dom==(v15b.D_LOW,v15b.D_HIGH)
                                for dom in f.duration_domains))
            self.assertTrue(all("duration_" in name for name in f.parameter_names))
        adapter=c.CAFContinuousBackend()
        for f in ff:
            point=tuple(Q(60,69) for _ in f.parameter_names)
            for pid in c.PROGRAMS:
                self.assertEqual(
                    adapter.predict(f,point,pid),
                    v15b.physical_signature(adapter.stages(f),point,pid))

    def test_continuous_true_offgrid_is_never_pruned(self):
        fam=next(f for f in c.families() if f.id=="preparacion+despacho")
        adapter=c.CAFContinuousBackend()
        point=(Q(60,69),Q(60,101))
        predicted=adapter.predict(fam,point,"F_R25_T20")
        obs=mc.Observation("F_R25_T20",predicted,1,c.ERROR_SOURCE,"CAF15B")
        result=mc.solve(fam,obs,adapter,max_nodes=96,max_depth=10)
        self.assertNotEqual(result["status"],mc.EMPTY)
        self.assertTrue(result["certificate_verified"])
        self.assertTrue(any(all(Q(l)<=x<=Q(h) for (l,h),x in zip(
            ((Q(l),Q(h)) for l,h in box),point))
            for box in result["retained_outer_boxes"]))
        self.assertEqual(
            result["feasibility_predicate"].startswith("exists d in closed domain"),
            True)
        self.assertTrue(result["outer_cover_is_not_exact_feasible_region"])

    def test_a_priori_is_continuous_and_no_optimisation_without_cost(self):
        prior=c.prior_structural_analysis()
        for pid in c.PROGRAMS:
            verdicts=[x["verdict"] for x in prior[pid]]
            self.assertEqual(verdicts.count(
                "SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED"),11)
            self.assertEqual(verdicts.count(
                "CONFUSABLE_WITNESS_CERTIFIED"),4)
        design=mc.design_options(c.PROGRAMS,prior)
        self.assertIsNone(design["ranking"])
        self.assertIsNone(design["autonomous_action"])
        self.assertFalse(design["options"][0]["feasibility_verified"])

    def test_full_four_layer_run_manifest_and_no_lattice_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"mc01"
            result=c.run(root,"a"*40,"b"*40)
            self.assertEqual(result["n_structural_families"],6)
            self.assertEqual(result["n_finite_parameter_grid_points"],0)
            self.assertEqual(len(result["evaluations"]),2)
            self.assertEqual(result["gate"],mc.GATE)
            self.assertTrue(result["all_feasible_sets_are_exact_predicates_not_grid"])
            plan=json.loads((root/"00_PLAN_BEFORE_EVAL.json").read_text())
            self.assertTrue(plan["not_parameter_grid"])
            self.assertEqual(plan["max_box_nodes"],256)
            self.assertEqual(plan["max_depth"],14)
            for item in result["evaluations"]:
                for row in item["inference"]["per_family"]:
                    self.assertTrue(row["certificate_verified"])
                    self.assertIn(row["status"],(mc.EMPTY,mc.WITNESS,mc.UNRESOLVED))
            mani=json.loads((root/"03_MANIFIESTO.json").read_text())
            for name,digest in mani["files_sha256"].items():
                self.assertEqual(digest,"sha256:"+sha256((root/name).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"MC01_REFUSE_OVERWRITE"):
                c.run(root,"a"*40,"b"*40)


if __name__=="__main__":
    unittest.main(verbosity=2)
