#!/usr/bin/env python3
"""Private boundary masking tests. Hand-built Snapshots; NO DES simulation."""
import unittest
from dataclasses import dataclass
from fractions import Fraction

import caf02_private_source_boundary as source
import caf02_public_cut_bridge as bridge
import caf02_k2_adjudicator_boundary as adjudicator

G5="sha256:"+"a"*64


@dataclass
class PrivateSnapshot:
    t_min:Fraction
    accepted_cum_orders:int
    delivered_cum_orders:int
    pending_orders:int
    stage_waiting:tuple=(99,)
    stage_in_service:tuple=(7,)
    private_service_minutes:str="SECRET_DONT_RELEASE"


def snap(t,accepted,delivered):
    return PrivateSnapshot(Fraction(t),accepted,delivered,accepted-delivered)


class SourceMasksTest(unittest.TestCase):
    def test_exact_public_half_open_arrivals_inclusive_snapshot(self):
        self.assertEqual([source.public_arrival_count(1.2,t) for t in (5,10)],
                         [6,12])
        self.assertEqual([source.public_arrival_count(1.35,t)
                          for t in (5,10,15,20,30,40)],
                         [7,14,20,27,27,27])
        self.assertEqual(source.public_arrival_count(1.8,30),36)

    def test_private_K0_does_not_expose_queues_or_private_fields(self):
        packet=source.masked_k0([snap(5,6,1),snap(10,12,5)],G5)
        self.assertEqual(packet,{"cut":"K0","delivered_t5":1,
                                 "delivered_t10":5,
                                 "world_precommitment_ref":G5})
        bridge.validate_k0_visible(packet)
        self.assertNotIn("stage_waiting",str(packet))
        self.assertNotIn("SECRET_DONT_RELEASE",str(packet))

    def test_K1_only_chosen_sample_is_public_not_full_curve(self):
        option={"rate_per_minute":1.8,"t_min":30}
        packet=source.masked_k1(snap(30,36,31),option,G5)
        self.assertEqual(packet,{"cut":"K1","measurement":option,
                                 "delivered":31,
                                 "world_precommitment_ref":G5})
        self.assertNotIn("pending_orders",str(packet))
        with self.assertRaises(source.PrivateBoundaryBlocked):
            source.masked_k1(snap(10,10,3),
                             {"rate_per_minute":1.7,"t_min":10},G5)
        with self.assertRaises(source.PrivateBoundaryBlocked):
            source.masked_k1(snap(30,35,31),option,G5)

    def test_reserved_K2_is_not_K0_or_K1_evidence(self):
        times=(5,10,15,20,30,40)
        counts=[7,14,20,27,27,27]
        delivered=[0,1,5,10,20,25]
        snaps=[snap(t,a,y) for t,a,y in zip(times,counts,delivered)]
        reserved=source.reserved_k2_inside_evaluator(snaps,G5)
        self.assertEqual(reserved["delivered"],delivered)
        with self.assertRaises(bridge.CutBlocked):
            bridge.validate_k0_visible(reserved)
        with self.assertRaises(bridge.CutBlocked):
            bridge.validate_k1_visible(
                reserved,{"proposed_measurement":{
                    "rate_per_minute":1.8,"t_min":30}},G5)
        # Crucial boundary case: at t5/t10 the DES may have accepted 7/14
        # while the continuum rate*t is 6.75/13.5, respectively.
        optimistic={"cut":"K2","delivered":counts,
                    "world_precommitment_ref":G5}
        a=bridge.package({"cut":"G4a_PRE_K1_CANDIDATE_NOT_SEALED",
                           "world_precommitment_ref":G5})
        bb=bridge.package({"cut":"G4b_PRE_K2_CANDIDATE_NOT_SEALED",
                           "parent_G4a_candidate_sha256":a["candidate_sha256"]})
        self.assertEqual(adjudicator.validate_k2_after_external_release(optimistic,a,bb),counts)

    def test_private_mass_violation_and_wrong_sample_blocked(self):
        bad=snap(5,6,2)
        bad.pending_orders=1
        with self.assertRaises(source.PrivateBoundaryBlocked):
            source.masked_k0([bad,snap(10,12,5)],G5)
        with self.assertRaises(source.PrivateBoundaryBlocked):
            source.masked_k0([snap(5,6,1),snap(15,18,5)],G5)
        with self.assertRaises(source.PrivateBoundaryBlocked):
            source.masked_k0([snap(5,7,1),snap(10,12,5)],G5)

if __name__=="__main__":
    unittest.main()
