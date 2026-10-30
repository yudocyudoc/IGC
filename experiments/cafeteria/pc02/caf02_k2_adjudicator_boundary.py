#!/usr/bin/env python3
"""POST-RELEASE adjudicator-side K2 syntax only. NOT a release authorization.

Must be deployed in a separate controlled process, after independently
authenticated G5/G4a/G4b receipts. There is NO K2 release functionality or
witness-verification method here. Never install this module in the G4a/G4b
producer execution environment.
"""
from fractions import Fraction
from caf02_public_cut_bridge import checked_receipt, need, TIMES

def validate_k2_after_external_release(payload,g4a,g4b):
    """Adjudication-side schema only: never call in a producer G4a/G4b step.

    Does NOT authorize release. Independent G5/G4a/G4b external receipts
    must be authenticated *outside this module* before even reading K2.
    """
    checked_receipt(g4a)
    checked_receipt(g4b)
    need(g4b["parent_G4a_candidate_sha256"]==g4a["candidate_sha256"],
         "K2_PARENT_G4a_CHANGED")
    need(type(payload) is dict
         and set(payload)=={"cut","delivered","world_precommitment_ref"}
         and payload["cut"]=="K2"
         and payload["world_precommitment_ref"]==g4a["world_precommitment_ref"],
         "K2_RESERVED_MASK_OR_WORLD_REF_INVALID")
    ys=payload["delivered"]
    # The private DES schedules t_j=(j+1/2)/1.35, with acceptances at
    # snapshot time INCLUDED. Simple floor(1.35*t) is WRONG at minutes 5
    # and 10: there can be 7 and 14 accepted orders, respectively.
    rate=Fraction(27,20)
    arrivals=[Fraction(2*j+1,2)/rate for j in range(27)]
    max_accepted=[sum(x<=t for x in arrivals) for t in TIMES]
    need(max_accepted==[7,14,20,27,27,27],
         "K2_PUBLIC_ARRIVAL_SCHEDULE_CHANGED")
    need(type(ys) is list and len(ys)==6
         and all(type(y) is int for y in ys)
         and all(0<=x<=y for x,y in zip([0]+ys[:-1],ys))
         and all(y<=cap for y,cap in zip(ys,max_accepted)),
         "K2_RESERVED_INTEGER_OR_PHYSICAL_LIMIT")
    return ys



def authorize_K2_reveal(*args,**kwargs):
    raise ValueError("K2_REVEAL_NOT_AUTHORIZED_OR_IMPLEMENTED_EXTERNAL_WITNESS_REQUIRED")
