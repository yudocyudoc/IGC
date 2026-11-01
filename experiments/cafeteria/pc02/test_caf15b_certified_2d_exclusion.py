"""CAF-15B: falsification, monotone event-clock bounds and proof replay tests.

A green test suite is NOT a license to declare unexplored 2D regions
separable. All global-negative claims need a fully replayed box tree.
"""
from __future__ import annotations
from fractions import Fraction as Q
from itertools import product
import copy
import unittest

import caf11_parametric_des_inversion as v11
import caf15b_certified_2d_exclusion as s


class CAF15BCertificateTests(unittest.TestCase):
    def test_model_and_program_contract(self):
        self.assertEqual(s.PROGRAMS,("F_R25_T20","F_R25_T25"))
        self.assertEqual((s.MAX_NODES,s.MAX_DEPTH),(5000,32))
        self.assertEqual((s.D_LOW,s.D_HIGH),(Q(6,11),Q(12,11)))
        self.assertEqual(len(s.rational_models()),6)
        self.assertEqual(len(list(__import__("itertools").combinations(
            s.rational_models(),2))),15)
        self.assertEqual(len(s.FULL),6)
        for p in s.PROGRAMS:
            self.assertEqual(len(s.probe_def(p)),3)
        with self.assertRaisesRegex(ValueError,"CAF15B_PROGRAM_NOT_FROZEN"):
            s.probe_def("Q20")

    def test_native_des_parity_at_diagonal_and_off_diagonal(self):
        ds1=(Q(60,55),Q(60,68),Q(60,83),Q(60,97),Q(60,110),Q(60,73))
        for model in s.rational_models():
            _,stages,_=model
            duration_vectors=(
                [(d,) for d in ds1] if len(stages)==1 else
                [(Q(60,68),Q(60,70)),(Q(60,70),Q(60,68)),
                 (Q(60,83),Q(60,83)),(Q(60,110),Q(60,55)),
                 (Q(60,110),Q(60,110)),(Q(60,73),Q(60,91))]
            )
            for ds in duration_vectors:
                for pid in s.PROGRAMS:
                    actual=s.signature(stages,ds,pid)
                    native=s.physical_signature(stages,ds,pid)
                    self.assertEqual(actual,native,
                                     (stages,ds,pid))

    def test_rational_outer_bounds_contain_every_grid_point(self):
        boxes=[
            ((s.D_LOW,s.D_HIGH),(s.D_LOW,s.D_HIGH)),
            ((Q(60,100),Q(60,80)),(Q(60,90),Q(60,70))),
            ((Q(60,105),Q(60,100)),(Q(60,105),Q(60,100))),
            ((Q(60,68),Q(60,68)),(Q(60,70),Q(60,70))),
        ]
        for pid in s.PROGRAMS:
            for stages in ((0,),(1,),(2,),(0,1),(0,2),(1,2)):
                for pair in boxes:
                    box=pair if len(stages)==2 else pair[:1]
                    outer=s.bounds(stages,box,pid)
                    points=[
                        (l,(l+h)/2,h) for l,h in box
                    ]
                    for ds in product(*points):
                        out=s.signature(stages,ds,pid)
                        self.assertTrue(all(l<=x<=h for (l,h),x
                                            in zip(outer,out)),
                                        (pid,stages,box,ds,outer,out))

    def test_count_difference_rule_and_strict_separation(self):
        self.assertTrue(s.close_signatures((0,)*8,(2,)*8))
        self.assertFalse(s.close_signatures((0,)*8,(3,)*8))
        self.assertEqual(s.common_reading((0,)*8,(2,)*8),(1,)*8)
        with self.assertRaisesRegex(ValueError,"CAF15B_NO_COMMON_READ"):
            s.common_reading((0,)*8,(3,)*8)
        x=((0,0),)*8
        z=((3,3),)*8
        self.assertEqual(s.exclusion_channel(x,z),0)
        z=((2,2),)*8
        self.assertIsNone(s.exclusion_channel(x,z))

    def test_monotone_event_clock_corner_semantics(self):
        for stages in ((0,), (0,1), (1,2)):
            slow=tuple(s.D_HIGH for _ in stages)
            fast=tuple(s.D_LOW for _ in stages)
            for rate,t in (("6/5",10),("3/2",20),("5/2",20),("5/2",25)):
                a=s.clock_counts(stages,fast,rate,t)
                z=s.clock_counts(stages,slow,rate,t)
                for kind in ("arrivals","starts","ends"):
                    self.assertTrue(all(u>=v for u,v
                                        in zip(a[kind],z[kind])),
                                    (stages,rate,t,kind))

    def test_split_replay_rejects_fake_or_missing_domain(self):
        # Root X would assert global separation without a margin: reject.
        sa,sb=(0,),(0,1)
        self.assertFalse(s.verify_exclusion_tree(
            sa,sb,"F_R25_T20",{"type":"X","channel":0}))
        # Neither incomplete nor malformed trees may certify.
        root={"type":"S","family":0,"dim":0,
              "mid":str((s.D_LOW+s.D_HIGH)/2),
              "left":{"type":"X","channel":0},
              "right":{"type":"U","reason":"NODE_BUDGET"}}
        self.assertFalse(s.verify_exclusion_tree(sa,sb,"F_R25_T20",root))
        corrupted=copy.deepcopy(root)
        corrupted["mid"]="3/4"
        self.assertFalse(s.verify_exclusion_tree(sa,sb,"F_R25_T20",corrupted))
        self.assertFalse(s.verify_exclusion_tree(
            sa,sb,"F_R25_T20",{"type":"W"}))

    def test_positive_witness_rechecks_with_native_des(self):
        sa,sb=(0,1),(0,2)
        for p in s.PROGRAMS:
            full_a,full_b=s.initial_boxes(sa,sb)
            witness=s.find_witness(sa,sb,full_a,full_b,p)
            self.assertIsNotNone(witness)
            self.assertTrue(s.verify_witness(sa,sb,p,witness))
            bad=copy.deepcopy(witness)
            bad["signature_a"][0]+=1
            self.assertFalse(s.verify_witness(sa,sb,p,bad))

    def test_limited_search_must_report_unresolved_not_separable(self):
        # Tiny budget intentionally insufficient to cover pair's parameter
        # product. A non-certification may not be promoted into a proof.
        r=s.run_pair((0,), (1,), "F_R25_T20",
                     max_nodes=1,max_depth=1)
        self.assertIn(r["verdict"],(
            "CONFUSABLE_WITNESS_CERTIFIED",
            "UNRESOLVED_NOT_CERTIFIED",
            "SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED"))
        if r["verdict"]=="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED":
            self.assertTrue(r["independent_tree_verification"])
            self.assertTrue(s.verify_exclusion_tree(
                (0,),(1,),"F_R25_T20",r["certificate_tree"]))
        elif r["verdict"]=="UNRESOLVED_NOT_CERTIFIED":
            self.assertNotIn("certificate_tree",r)


if __name__=="__main__":
    unittest.main(verbosity=2)
