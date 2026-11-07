"""Project 12 real D/M own-ledger decisions into lock-shaped rows, no seal.

The final 13-slot seal belongs only AFTER authentic B initial/revision and
after any M revision has its own new OMC G2 CSV/receipt. No absent trace is
replaced by a zero, a copy of initial or a fake B row. The existing exact
CT-03 prospective-lock registry/validate_row remain the sole row contract.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from scripts.arena_v0_contract import canonical,digest
from scripts.arena_cafe.ct03_dm_feedback_round import SCHEMA as DM_SCHEMA
from scripts.arena_cafe.ct03_prospective_lock import registry,validate_row
from scripts.arena_cafe.ct_feedback_bridge import require

SCHEMA="igc-ct03-dm-twelve-lock-ready-rows-no-B/1.0"

def project(dm:dict,d_manifest:dict,m_manifest:dict,revisions:dict):
    require(type(dm) is dict and dm.get("schema")==DM_SCHEMA and
            len(dm.get("rows",[]))==12 and
            dm.get("new_provider_calls")==0 and
            type(revisions) is dict,
            "CT03_DM_LOCK_REQUIRES_ALL_TWELVE_OWN_INITIALS")
    world=dm["world_public_id"]
    expected=registry(d_manifest,m_manifest)
    rows=[]
    seen=set()
    for r in dm["rows"]:
        arm,cid=r["arm"],r["candidate_id"]
        require(arm in ("D","M") and (arm,cid) in expected and
                (arm,cid) not in seen and
                r["parent_hash"]==expected[(arm,cid)]["parent_hash"] and
                r["material_group"]==expected[(arm,cid)]["group"],
                "CT03_DM_LOCK_WRONG_CANDIDATE_OR_PARENT")
        seen.add((arm,cid))
        initial=r["initial"]
        require(initial["status"]=="PREDICTED" and
                initial.get("trace_sha256") and initial.get("receipt_sha256"),
                "CT03_DM_LOCK_REQUIRES_REAL_INITIAL_PREDICTION")
        raw=r["decision"]
        decision={
            "status":raw["status"],
            "policy":raw["policy"],
            "feedback_hash":raw["feedback_hash"],
            "retrieved_item_id":r["retrieved_before_policy"]["item_id"],
            "new_model_sha256":None
        }
        if raw["status"]=="REVISED":
            require(arm=="M" and cid in revisions and
                    r["revision_native_manifest"] is not None,
                    "CT03_DM_LOCK_REVISED_M_MISSING_PHYSICAL_OUTCOME")
            final=revisions[cid]
            native=r["revision_native_manifest"]
            require(type(final) is dict and
                    set(final)=={"status","native_sha256","trace_sha256",
                                 "receipt_sha256","forecast"} and
                    final["status"] in ("PREDICTED","G2_FAILED") and
                    final["native_sha256"]==native["native_modelica_sha256"] and
                    final["native_sha256"]!=initial["native_sha256"],
                    "CT03_DM_LOCK_REVISED_NATIVE_OR_G2_RESULT_MISMATCH")
            # The separate revision OMC runner must authenticate source and
            # receipt; no in-process signatures/phantom truth claimed here.
            decision["new_model_sha256"]=native["native_modelica_sha256"]
        else:
            require(raw["status"] in ("RATIFIED","ABSTAINED") and
                    r["revision_native_manifest"] is None,
                    "CT03_DM_LOCK_UNREVISED_CANNOT_HAVE_NEW_NATIVE")
            final=initial
            require(cid not in revisions,
                    "CT03_DM_LOCK_UNAUTHORIZED_EXTRA_REVISION_OUTCOME")
        row={
            "arm":arm,"candidate_id":cid,"parent_hash":r["parent_hash"],
            "material_group":r["material_group"],"initial":initial,
            "decision":decision,"final":final
        }
        validate_row(row,expected,world)
        rows.append(row)
    require(len(seen)==12 and
            sum(x["arm"]=="D" for x in rows)==6 and
            sum(x["arm"]=="M" for x in rows)==6 and
            set(revisions)=={
                r["candidate_id"] for r in dm["rows"]
                if r["arm"]=="M" and r["decision"]["status"]=="REVISED"
            },
            "CT03_DM_LOCK_WRONG_TWELVE_OR_EXTRA_REVISIONS")
    return {
        "schema":SCHEMA,
        "status":"TWELVE_D_M_LOCK_ROWS_VALID_B_NOT_INCLUDED_NOT_SEALED",
        "world_public_id":world,
        "source_snapshot_hash":dm["source_snapshot_hash"],
        "dm_feedback_sha256":digest(dm),
        "candidate_count":12,
        "D_count":6,"M_count":6,
        "M_physical_revised_count":len(revisions),
        "B_status":"REQUIRES_SEPARATE_REAL_ORIGINAL_B_EVIDENCE",
        "reserved_world_truth_read":False,
        "new_omc_by_projection":0,
        "new_provider_calls":0,
        "rows":rows,
    }

def main():
    p=argparse.ArgumentParser()
    for key in ("dm-feedback","d-manifest","m-manifest","revision-outcomes","out"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    require(not a.out.exists(),"CT03_DM_LOCK_PROJECTION_REFUSE_OVERWRITE")
    def read(x):return json.loads(x.read_text(encoding="utf-8"))
    report=project(read(a.dm_feedback),read(a.d_manifest),
                   read(a.m_manifest),read(a.revision_outcomes))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({"status":report["status"],"rows":12,
                      "new_omc":0,"provider_posts":0}))

if __name__=="__main__":
    main()
