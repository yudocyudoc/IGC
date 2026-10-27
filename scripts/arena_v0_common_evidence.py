"""One primary construction source; three method-specific, traceable views.

This layer does not run three independent generators and does not fabricate
nominal parameter estimates from observations.
"""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from scripts.arena_v0_contract import (
    INPUT_SCHEMA, validate_visible_input, arm_view, assert_same_evidence,
    digest, canonical, ArenaContractError,
)
SOURCE_SCHEMA = "igc-arena-primary-construction/0.1"

def common(source):
    if not isinstance(source, dict) or set(source) != {
        "schema","investigation_id","round_id","question","input_profile",
        "observations","observability","iteration_limit","source_id",
    } or source["schema"] != SOURCE_SCHEMA:
        raise ArenaContractError("INVALID_PRIMARY_SOURCE")
    p=source["input_profile"]
    if not isinstance(p,dict) or set(p)!={"kind","rate","duration"} or p["kind"]!="pulse":
        raise ArenaContractError("INVALID_PRIMARY_PULSE")
    import math
    if any(type(p[x]) not in (float,int) or not math.isfinite(p[x]) or p[x]<=0 for x in ("rate","duration")):
        raise ArenaContractError("INVALID_PRIMARY_PULSE_RATE")
    obs=source["observations"]
    if not isinstance(obs,list) or len(obs)<2 or any(not isinstance(x,dict) or set(x)!={"t","delivered"} or any(type(x[k]) not in (float,int) or not math.isfinite(x[k]) for k in ("t","delivered")) for x in obs):
        raise ArenaContractError("INVALID_PRIMARY_OBSERVATIONS")
    if obs[0]["t"]!=0 or any(b["t"]<=a["t"] for a,b in zip(obs,obs[1:])):
        raise ArenaContractError("INVALID_PRIMARY_TIME")
    if not isinstance(source["source_id"],str) or not source["source_id"].strip():
        raise ArenaContractError("MISSING_PRIMARY_SOURCE_ID")
    evidence={"input_profile":deepcopy(p),"observations":deepcopy(obs),
              "source_id":source["source_id"]}
    # Source snapshot is computed from actual evidence, not a placeholder hash.
    snapshot=digest(evidence)
    payload={"schema":INPUT_SCHEMA,"investigation_id":source["investigation_id"],
             "round_id":source["round_id"],"question":source["question"],
             "construction":evidence,"observability":deepcopy(source["observability"]),
             "source_snapshot_hash":snapshot,
             "iteration_limit":source["iteration_limit"],
             "resources":{"shared_source_only":True}}
    validate_visible_input(payload)
    views=[arm_view(payload,a) for a in ("D","B","M")]
    assert_same_evidence(views)
    return payload,views

def adapt(common_input, arm, *, assumptions=None, budgets=None):
    """Adapters expose assumptions as assumptions; no silent injection."""
    if arm not in ("D","B","M"):
        raise ArenaContractError("UNKNOWN_ARM")
    v=arm_view(common_input,arm)
    construction=common_input["construction"]
    common_fields={"input_profile":deepcopy(construction["input_profile"]),
                   "observations":deepcopy(construction["observations"])}
    if arm=="D":
        nominal=(assumptions or {}).get("nominal_parameters")
        if nominal is None:
            return {"arm_id":arm,"status":"BLOCKED","reason":"D_REQUIRES_DECLARED_NOMINAL_ASSUMPTIONS",
                    "common_input_hash":v["input_hash"],"source_snapshot_hash":common_input["source_snapshot_hash"]}
        if set(nominal)!={"capacity","response_time","loss_time"}:
            raise ArenaContractError("BAD_D_ASSUMPTION_KEYS")
        import math
        if any(type(x) not in (int,float) or not math.isfinite(x) or x<=0 for x in nominal.values()):
            raise ArenaContractError("BAD_D_ASSUMPTION_VALUES")
        derived=deepcopy(common_input)
        derived["construction"]={**common_fields,"nominal_parameters":deepcopy(nominal)}
        derived["resources"]=deepcopy(budgets or {"max_stocks":3,"allow_loss":True,"max_candidates":6,"max_simulations":6})
        from scripts.arena_d_v01 import validate_case
        validate_case(derived)
        return {"arm_id":arm,"status":"READY_CONDITIONAL_ASSUMPTIONS",
                "common_input_hash":v["input_hash"],"source_snapshot_hash":common_input["source_snapshot_hash"],
                "derived_input":derived,"assumption_provenance":"USER_DECLARED_NOT_OBSERVED"}
    derived=deepcopy(common_input)
    derived["construction"]={**common_fields,"known_conditions":[
        "Shared synthetic construction data; no disclosed generator structure",
        "Parameter values not estimated by this adapter"]}
    derived["resources"]=deepcopy(budgets or {"max_model_proposals":1,"max_llm_calls":0,"max_simulations":2})
    return {"arm_id":arm,"status":"VISIBLE_INPUT_READY_NOT_GENERATOR_RUN",
            "common_input_hash":v["input_hash"],"source_snapshot_hash":common_input["source_snapshot_hash"],
            "derived_input":derived,
            "limits":["B_REQUIRES_AUTHORIZED_INFERENCE" if arm=="B" else "M_OBSERVATION_TO_ROLE_MAPPING_NOT_IMPLEMENTED"]}

def prepare(source,assumptions=None):
    shared,views=common(source)
    results={arm:adapt(shared,arm,assumptions=assumptions) for arm in ("D","B","M")}
    assert len({r["common_input_hash"] for r in results.values()})==1
    return {"schema":"igc-arena-evidence-adaptation/0.1",
            "common_input_hash":digest(shared),
            "source_snapshot_hash":shared["source_snapshot_hash"],
            "arms":results,"science_status":"NOT_RUN"}

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--assumptions",type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    if a.out.exists(): raise ArenaContractError("OUTPUT_EXISTS")
    r=prepare(json.loads(a.source.read_text()),
              json.loads(a.assumptions.read_text()) if a.assumptions else None)
    a.out.write_bytes(canonical(r)+b"\n")
    print(json.dumps({"common_input_hash":r["common_input_hash"],
                      "statuses":{k:v["status"] for k,v in r["arms"].items()}}))
