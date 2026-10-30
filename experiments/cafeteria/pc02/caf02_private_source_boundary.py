#!/usr/bin/env python3
"""Evaluator-side CAF02 private -> strictly masked public observation adapter.

This module is NOT imported by producer-side caf02_public_cut_bridge.
Accepts snapshots from a discrete event implementation, but DOES NOT run it,
choose private stages or parameters, or have an execution CLI. The former
CAF01 generic engine may serve as the evaluator implementation only AFTER
new independent source/configuration G5 custody and separate authorization.

Never send full snapshots, stage positions, queue sizes, service times, seed,
nonce, private source paths, or K2 values to the G4a/G4b producer process.
"""
from __future__ import annotations
from fractions import Fraction
import re

REF=re.compile(r"^sha256:[0-9a-f]{64}$")
K2_TIMES=(5,10,15,20,30,40)


class PrivateBoundaryBlocked(ValueError):
    pass


def req(ok,code):
    if not ok:raise PrivateBoundaryBlocked(code)


def public_arrival_count(rate,minute):
    """Exact count of half-open mid-point arrivals up to inclusive snapshot.

    Arrival times t_j=(j+1/2)/rate, subject to t_j<20. Completes and
    acceptances at timestamp are counted by the DES. Fraction prevents
    rounding-dependent false physical rejection at t=5,10.
    """
    rate=Fraction(str(rate))
    minute=Fraction(str(minute))
    req(rate>0 and 0<=minute<=40,"PRIVATE_BAD_PUBLIC_PULSE_OR_TIME")
    count=0
    while Fraction(2*count+1,2)/rate<20 and (
        Fraction(2*count+1,2)/rate<=minute):
        count+=1
        req(count<=10000,"PRIVATE_ACCEPTANCE_BUDGET")
    return count


def sanitized_series(snapshots,times,rate):
    req(type(snapshots) in (list,tuple) and len(snapshots)==len(times),
        "PRIVATE_SNAPSHOT_COUNT_INVALID")
    delivered=[]
    previous=0
    for snap,t in zip(snapshots,times):
        # Exact fields in a private Snapshot, not a producer report.
        req(hasattr(snap,"t_min")
            and hasattr(snap,"accepted_cum_orders")
            and hasattr(snap,"delivered_cum_orders")
            and hasattr(snap,"pending_orders"),
            "PRIVATE_MALFORMED_ENGINE_SNAPSHOT")
        req(snap.t_min==Fraction(t,1)
            and type(snap.delivered_cum_orders) is int
            and type(snap.accepted_cum_orders) is int
            and type(snap.pending_orders) is int,
            "PRIVATE_BAD_SNAPSHOT_TIME_OR_COUNTS")
        a,d,p=(snap.accepted_cum_orders,snap.delivered_cum_orders,
               snap.pending_orders)
        expected=public_arrival_count(rate,t)
        req(a==expected and a==d+p and 0<=previous<=d<=a,
            "PRIVATE_DES_MASS_OR_PUBLIC_ARRIVAL_SCHEDULE_INVALID")
        delivered.append(d)
        previous=d
    return delivered


def masked_k0(snapshots,world_commitment):
    req(type(world_commitment) is str and REF.fullmatch(world_commitment),
        "PRIVATE_G5_COMMITMENT_REQUIRED")
    a,b=sanitized_series(snapshots,(5,10),1.2)
    return {"cut":"K0","delivered_t5":a,"delivered_t10":b,
            "world_precommitment_ref":world_commitment}


def masked_k1(snapshot,measurement,world_commitment):
    req(type(world_commitment) is str and REF.fullmatch(world_commitment),
        "PRIVATE_G5_COMMITMENT_REQUIRED")
    allowed={(1.0,10),(1.5,20),(1.8,30)}
    req(type(measurement) is dict
        and set(measurement)=={"rate_per_minute","t_min"}
        and (measurement["rate_per_minute"],measurement["t_min"]) in allowed,
        "PRIVATE_K1_NOT_PRESELECTED_PUBLIC_MENU")
    rate,minute=measurement["rate_per_minute"],measurement["t_min"]
    y=sanitized_series((snapshot,),(minute,),rate)[0]
    return {"cut":"K1","measurement":dict(measurement),"delivered":y,
            "world_precommitment_ref":world_commitment}


def reserved_k2_inside_evaluator(snapshots,world_commitment):
    """NEVER release this from the evaluator before verified external G4b."""
    req(type(world_commitment) is str and REF.fullmatch(world_commitment),
        "PRIVATE_G5_COMMITMENT_REQUIRED")
    ys=sanitized_series(snapshots,K2_TIMES,1.35)
    return {"cut":"K2","delivered":ys,
            "world_precommitment_ref":world_commitment}


if __name__=="__main__":
    print("PRIVATE_EVALUATOR_BOUNDARY_ONLY_NO_WORLD_RUN_NO_K2_RELEASE")
