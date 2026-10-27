"""First honest offline Arena round: native D and M methods, B explicitly blocked.

No solver or provider calls. Shared evidence digest is retained separately from
arm-specific derived input hashes; absent capabilities are not synthesized.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.arena_v0_contract import canonical, digest, arm_view, validate_submission
from scripts.arena_v0_common_evidence import prepare as prepare_evidence
from scripts.arena_d_v01 import generate as generate_d
from scripts.arena_m3_common import prepare as prepare_m, evaluate as evaluate_m, write_models

SCHEMA="igc-arena-offline-first-round/0.1"

def run(source, assumptions=None, *, m_csv_root=None):
    evidence=prepare_evidence(source,assumptions)
    arms=evidence["arms"]
    record={"schema":SCHEMA,"round_id":source["round_id"],
            "common_input_hash":evidence["common_input_hash"],
            "source_snapshot_hash":evidence["source_snapshot_hash"],
            "empirical_status":"NOT_EVALUATED",
            "cross_arm_ranking":"NOT_RUN",
            "holdout":"NOT_ACCESSED",
            "provider_calls":0,"solver_calls":0,"arms":{}}
    d=arms["D"]
    if d["status"]=="READY_CONDITIONAL_ASSUMPTIONS":
        native=generate_d(d["derived_input"])
        record["arms"]["D"]={"status":"NATIVE_CANDIDATES_GENERATED_NOT_SIMULATED",
            "source_input_hash":d["common_input_hash"],
            "derived_input_hash":digest(d["derived_input"]),
            "native_sha256":digest(native),
            "native":native,
            "limits":["NOMINAL_PARAMETERS_ARE_DECLARED_ASSUMPTIONS","NO_G2_OR_G3_IN_THIS_ROUND"]}
    else:
        record["arms"]["D"]={"status":"BLOCKED","reason":d["reason"],
                            "source_input_hash":d["common_input_hash"]}
    # No inference provider is authorized. Do not substitute prior historical
    # Buffalo results (they had a different prompt and information boundary).
    record["arms"]["B"]={"status":"BLOCKED","reason":"NATIVE_INFERENCE_NOT_EXECUTED",
                         "source_input_hash":arms["B"]["common_input_hash"],
                         "derived_input_hash":digest(arms["B"]["derived_input"]),
                         "provider_calls":0}
    m=arms["M"]
    prepared=prepare_m(m["derived_input"])
    native,submission,event=(prepared[k] for k in ("native","submission","event"))
    validate_submission(arm_view(m["derived_input"],"M"),submission)
    record["arms"]["M"]={"status":"M3_CANDIDATES_PREPARED_NOT_SIMULATED",
        "source_input_hash":m["common_input_hash"],
        "derived_input_hash":digest(m["derived_input"]),
        "native_sha256":digest(native),
        "submission_sha256":digest(submission),
        "event_sha256":digest(event),
        "native":native,
        "submission":submission,
        "event":event,
        "modelica":prepared["models"]}
    if m_csv_root is not None:
        result=evaluate_m(m["derived_input"],prepared,m_csv_root)
        record["arms"]["M"]["evaluation"]=result
        record["arms"]["M"]["status"]=result["status"]
        record["arms"]["M"]["replayed_candidate_traces"]=3
        record["empirical_status"]="M_CONSTRUCTION_EVALUATED_ONLY"
    if set(record["arms"])!={"D","B","M"}:
        raise ValueError("INCOMPLETE_ARM_SET")
    if len({x["source_input_hash"] for x in record["arms"].values()})!=1:
        raise ValueError("CROSS_ARM_SOURCE_DIVERGED")
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--assumptions",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--m-modelica-dir",type=Path,
                   help="Prepare M3 models for a separate OpenModelica execution")
    p.add_argument("--m-csv-root",type=Path,
                   help="Evaluate that preparation with its three candidate CSVs")
    a=p.parse_args()
    if a.out.exists():raise ValueError("OUTPUT_EXISTS")
    source=json.loads(a.source.read_text())
    assumptions=json.loads(a.assumptions.read_text()) if a.assumptions else None
    obj=run(source,assumptions,m_csv_root=a.m_csv_root)
    if a.m_modelica_dir:
        evidence=prepare_evidence(source,assumptions)
        write_models(prepare_m(evidence["arms"]["M"]["derived_input"]),a.m_modelica_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(obj)+b"\n")
    print(json.dumps({"round_id":obj["round_id"],"status":obj["empirical_status"],
        "arms":{k:v["status"] for k,v in obj["arms"].items()},
        "record_sha256":digest(obj)}))

if __name__=="__main__":
    main()
