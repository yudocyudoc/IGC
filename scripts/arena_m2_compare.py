"""Compare two REAL molecular OpenModelica experiments on construction data only.

This is a numerical report, never a new held-out G3 validation. Verify the M2
CSV through the already-tested typed stock conservation method before scoring.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from scripts.arena_m2_feedback import read_parent, ROOT
from scripts.arena_m_visible_verify import verify
from scripts.arena_v0_contract import digest


def compare(visible, parent_dir, revised_dir, catalog):
    old_native, old_sub, old_event, original, old_rows = read_parent(parent_dir)
    new_native=json.loads((revised_dir/"native-graph.json").read_text())
    new_sub=json.loads((revised_dir/"submission.json").read_text())
    feedback=json.loads((revised_dir/"feedback.json").read_text())
    receipt=json.loads((revised_dir/"translation-receipt.json").read_text())
    events=json.loads((revised_dir/"memory-events.json").read_text())
    with (revised_dir/"m2-visible_res.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if not (new_native["parent_native_hash"]==digest(old_native)
            and new_native["canonical_graph_sha256"]==old_native["canonical_graph_sha256"]
            and new_sub["parent_revision_id"]==old_sub["hypothesis_ids"][0]+":r0"
            and new_sub["native_artifact_sha256"]==digest(new_native)
            and feedback["arm_id"]==new_sub["arm_id"]=="M"
            and events[0]["previous_event_hash"]==old_event["event_hash"]
            and events[1]["previous_event_hash"]==events[0]["event_hash"]
            and receipt["graph_topology_unchanged"] is True):
        raise ValueError("M2_REVISION_LINEAGE_BROKEN")
    actual_previous=verify(old_rows,visible,old_native,catalog)
    actual_revised=verify(rows,visible,new_native,catalog)
    if abs(actual_previous["rmse_items"]-original["rmse_items"])>1e-8:
        raise ValueError("OLD_RUN_DIFFERENT_FROM_ORIGINAL_REPORT")
    comparisons=[]
    for before,after in zip(actual_previous["observations"],actual_revised["observations"]):
        if (before["time"]!=after["time"] or before["observed"]!=after["observed"]):
            raise ValueError("DIFFERENT_CONSTRUCTION_OBSERVATIONS")
        comparisons.append({"hour":before["time"],
            "observed_items":before["observed"],
            "m1_predicted_items":before["simulated"],
            "m2_predicted_items":after["simulated"],
            "m1_error_items":before["residual"],
            "m2_error_items":after["residual"]})
    before=actual_previous["rmse_items"];after=actual_revised["rmse_items"]
    return {"schema":"igc-arena-m2-real-modelica-construction-compare/0.1",
        "arm_id":"M","parent_iteration":0,"revision_iteration":1,
        "parent_native_sha256":digest(old_native),
        "revised_native_sha256":digest(new_native),
        "topology_unchanged":True,
        "parameter_edits":new_native["parameter_edits"],
        "parent_source":"GitHub Actions 40271768284 archived source",
        "engine":"OpenModelica actual CSV for both model versions",
        "simulation_status":"G2_PASS" if actual_revised["status"]=="G2_SIMULATED_CONDITIONALLY" else "BLOCKED",
        "parent_samples":actual_previous["technical_samples"],
        "revision_samples":actual_revised["technical_samples"],
        "revision_mass_balance_max_items":actual_revised["max_material_balance_residual"],
        "m1_rmse_construction_items":before,
        "m2_rmse_construction_items":after,
        "rmse_reduction_items":before-after,
        "outcome":"CONSTRUCTION_RMSE_IMPROVED" if after<before-1e-10 else "NOT_IMPROVED_ON_CONSTRUCTION",
        "comparisons":comparisons,
        "holdout_status":"NOT_RUN",
        "structural_identification":"NOT_DEMONSTRATED",
        "parameter_identification":"NOT_DEMONSTRATED",
        "uncertainty":"NOT_ESTIMATED",
        "causality":"NOT_DEMONSTRATED",
        "warning":"M2 consumed M1 construction residuals to revise a model; apparent RMSE improvement is in-sample, NOT fresh predictive evidence."}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--visible",type=Path,required=True)
    ap.add_argument("--parent-dir",type=Path,required=True)
    ap.add_argument("--revised-dir",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    result=compare(json.loads(a.visible.read_text()),a.parent_dir,a.revised_dir,
                   json.loads((ROOT/"experiments/e0/catalog.json").read_text()))
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["outcome"],
        "m1_rmse":result["m1_rmse_construction_items"],
        "m2_rmse":result["m2_rmse_construction_items"],
        "no_holdout":True,"balance_max":result["revision_mass_balance_max_items"]}))


if __name__=="__main__":
    main()
