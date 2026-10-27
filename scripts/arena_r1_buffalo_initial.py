"""One common-evidence Buffalo initial trial. No D/M outputs or hidden world.

This prepares an INPUT ONLY. Native inference is done by the untouched upstream
University at Buffalo SD-AI engine through the existing Cloudflare transport.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.arena_v0_common_evidence import prepare as prepare_shared
from scripts.arena_v0_contract import canonical, digest, arm_view, validate_visible_input

SCHEMA = "igc-arena-r1-buffalo-initial/0.1"
MAX_OUTPUT_TOKENS = 7000
MAX_CALLS = 1

# Solver protocol is a shared experimental constraint, not a topology hint.
NATIVE_SPEC = {"startTime":0,"stopTime":8,"dt":0.125,
               "timeUnits":"hour","integrationMethod":"Euler"}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def build(source):
    e = prepare_shared(source)
    b = e["arms"]["B"]
    require(b["status"] == "VISIBLE_INPUT_READY_NOT_GENERATOR_RUN",
            "NOT_COMMON_B_SOURCE")
    visible = json.loads(json.dumps(b["derived_input"]))
    visible["resources"] = {"max_model_proposals":1,
                            "max_llm_calls":1,"max_simulations":1}
    # The experimental protocol fixes a numerical solver, not the endogenous
    # variables, stock count, capacities, delays, or equations Buffalo may propose.
    visible["question"] = (
        source["question"] + " Build one independent quantitative stock-flow "
        "explanation using only the construction evidence supplied. Return a "
        "complete original Buffalo SD-AI native model. Its native simulation "
        "specifications must be startTime=0, stopTime=8, dt=0.125, "
        "timeUnits='hour', integrationMethod='Euler' for the shared technical "
        "replay. Treat initial cumulative delivered as zero; any other "
        "initial-state assumptions must be declared in your explanation. "
        "Infer all endogenous mechanisms yourself. Do not assume any "
        "particular number of stocks, queue structure, processing capacity "
        "or equation. If the observations do not distinguish mechanisms, "
        "state the uncertainty instead of asserting a unique true structure."
    )
    visible["construction"]["known_conditions"] = [
        "Only construction observations and public pulse are supplied.",
        "No generator model, independent future observations, or other model proposals were supplied.",
        "The declared numerical solver protocol is Euler, 0..8 hours, dt=0.125.",
        "Initial cumulative delivered is observed to be zero; other initial states are not measured.",
    ]
    validate_visible_input(visible)
    # Recomputed source hash remains the existing common primary evidence hash.
    require(visible["source_snapshot_hash"] == e["source_snapshot_hash"],
            "BUFFALO_COMMON_SOURCE_CHANGED")
    require(len(visible["construction"]["observations"]) == 4 and
            [o["t"] for o in visible["construction"]["observations"]] == [0,1,2,4],
            "BUFFALO_SOURCE_TIME_DRIFT")
    return visible


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    require(not a.out.exists(),"R1_B_VISIBLE_ALREADY_EXISTS")
    source=json.loads(a.source.read_text())
    result=build(source)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"schema":SCHEMA, "source_snapshot_hash":result["source_snapshot_hash"],
                      "visible_sha256":digest(result),
                      "max_calls":MAX_CALLS,"max_output_tokens":MAX_OUTPUT_TOKENS}))


if __name__=="__main__":
    main()
