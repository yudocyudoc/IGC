"""E04 construction: arm-native action representation audit, no evaluator truth.

Producer audit sees only E03 D/M development manifests and code definitions.
A bounded proportional-response queue is not an FCFS constant-service server;
an extra 30 seconds per order is not a native `responseTime += 0.5 min` map.
No DES, reserved truth, F4 pair labels, optimization, PM, or new OMC.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from scripts.arena_v0_contract import canonical,digest
from scripts.arena_cafe.native_handoff import need
from scripts.arena_cafe import r2_m_six_causal_g2 as m_g2
from scripts.arena_cafe import r2_observational_contracts as r2
from scripts.arena_cafe import e03_cal_grid as e03

SCHEMA="igc-arena-e04-action-capability-producer/0.1"
ACTION="ADD_HALF_MINUTE_PER_ORDER_OF_DETERMINISTIC_FCFS_DISPATCH_WORK_FROM_T0"


def producer(d_manifest,m_manifest,d_score,m_score):
    need(m_g2.source_integrity() is True and r2.original_source_checks() is True,
         "E04_NATIVE_SOURCE_UNPINNED")
    source=d_manifest["source_snapshot_hash"]
    need(d_manifest["schema"]==m_manifest["schema"]==e03.SCHEMA and
         d_score["schema"]==m_score["schema"]==e03.SCORE_SCHEMA and
         d_manifest["arm"]==d_score["arm"]=="D" and
         m_manifest["arm"]==m_score["arm"]=="M" and
         source==m_manifest["source_snapshot_hash"]==d_score["source_snapshot_hash"]
               ==m_score["source_snapshot_hash"] and
         d_manifest["signal_sha256"]==m_manifest["signal_sha256"] and
         d_manifest["candidate_count"]==d_score["candidate_count"]==81 and
         m_manifest["candidate_count"]==m_score["candidate_count"]==54 and
         d_score["comparable_count"]==81 and m_score["comparable_count"]==54,
         "E04_E03_SOURCE_OR_UNIVERSE_CHANGED")
    # Every original G2 candidate and every external CAL variant is retained.
    outcomes={}
    for arm,manifest,scores in (("D",d_manifest,d_score),("M",m_manifest,m_score)):
        scored={r["id"]:r for r in scores["candidate_scores"]}
        need(len(scored)==manifest["candidate_count"],"E04_CANDIDATE_SCORE_MISSING")
        rows=[]
        for candidate in manifest["candidates"]:
            ident=candidate["id"]
            need(ident in scored and scored[ident]["status"]==
                 "G2_PASS_DESCRIPTIVE_G3_DEVELOPMENT_ONLY",
                 "E04_NOT_A_DEVELOPMENT_CANDIDATE")
            if arm=="D":
                # Generic conservative stock chains encode no physical station.
                need(1<=candidate["stock_count"]<=3 and
                     type(candidate["loss"]) is bool and
                     "variant_ast" not in candidate,
                     "E04_D_NATIVE_MECHANISM_CHANGED")
                reason="GENERIC_CHAIN_STOCKS_NOT_TYPED_AS_FCFS_DISPATCH"
                native_role=None
            else:
                graph=candidate["variant_ast"]
                dispatch=[x for x in graph["instances"] if x["role"]=="dispatch"]
                need(len(dispatch)==1 and
                     dispatch[0]["class_id"]=="bounded-queue" and
                     set(dispatch[0]["parameters"])=={"responseTime","maxThroughput"},
                     "E04_M_NOT_NATIVE_BOUNDED_QUEUE")
                # Native SystemDynamics release is bounded proportional to
                # queue stock, not one-job-one-server FCFS deterministic timing.
                reason="BOUNDED_PROPORTIONAL_RESPONSE_NOT_CONSTANT_FCFS_WORK_PER_ORDER"
                native_role="dispatch"
            rows.append({"candidate_id":ident,
                         "origin":candidate["origin"],
                         "G3_development_max_abs":scored[ident]["max_abs"],
                         "action":ACTION,
                         "status":"INTERVENTION_NOT_REPRESENTABLE",
                         "reason":reason,"native_dispatch_role":native_role,
                         "unsupported_parameter_shortcut":"FORBIDDEN",
                         "targeted_action_simulated":False,
                         "predicted_action_effect":None,
                         "author":"EXTERNAL_REPRESENTABILITY_AUDIT_NOT_ARM_NATIVE_PROPOSAL"})
        outcomes[arm]={"candidates":rows,"attempted":len(rows),
                       "mapped":0,"conditional_approximations":0,
                       "not_representable":len(rows),
                       "native_second_decision":"NOT_GENERATED_BY_NATIVE_ENGINE",
                       "action_feedback":"UNSUPPORTED_TRANSLATION_NOT_NUMERICAL_EVIDENCE"}
    return {"schema":SCHEMA,
            "status":"E04_PARTIAL_D_M_REPRESENTATION_GAP_B_NOT_EXECUTED",
            "public_source_hash":source,
            "E03_status":{"D":d_score["status"],"M":m_score["status"]},
            "action":ACTION,"arms":outcomes,
            "B":{"status":"NATIVE_NOT_EXECUTED","candidate_count":0,
                 "action_mapping":"NOT_ATTEMPTED_NO_REAL_NATIVE_PARENT",
                 "abstention":False,"provider_calls":0},
            "S0":"SYNTHETIC_DEVELOPMENT_O0_O1_UNCHANGED",
            "S1":"OPTIONAL_TYPED_DISPATCH_COUNT_NOT_PROVIDED_TO_PRODUCERS",
            "evaluator_truth_visible_to_producer":False,
            "new_OMC_runs":0,"new_provider_calls":0,
            "no_demand_pulse_identification_claim":True,
            "native_mechanisms_unchanged":True,
            "representation_limits_are_not_scientific_adequacy":True,
            "G4":"NOT_RUN","G5":"NOT_RUN",
            "E05_gate":"BLOCKED_NO_ADMISSIBLE_LOCAL_ACTION_PREDICTION"}


def main():
    p=argparse.ArgumentParser()
    for name in ("d_manifest","m_manifest","d_score","m_score","out"):
        p.add_argument("--"+name.replace("_","-"),required=True,type=Path)
    a=p.parse_args()
    need(not a.out.exists(),"E04_REFUSE_OVERWRITE")
    result=producer(*[json.loads(getattr(a,n).read_text())
                      for n in ("d_manifest","m_manifest","d_score","m_score")])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["status"],
                      "D":result["arms"]["D"]["not_representable"],
                      "M":result["arms"]["M"]["not_representable"],
                      "B":result["B"]["status"]},sort_keys=True))

if __name__=='__main__':main()