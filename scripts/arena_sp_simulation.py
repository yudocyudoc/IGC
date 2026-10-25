"""Build and verify an independently executed S molecular simulation AFTER S handoff.

Synthetic/mock S drafts are strictly unscorable. They demonstrate the model
handoff -> ATMS -> solver contract, not LLM discovery or blind prediction.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

from .arena_round import hash_obj, exclusive_json
from .arena_sp_producers import ProviderError
from .arena_sp_handoff import verify_handoff, simulation_selection
from .arena_s_real import verify_s_only_seal, ORIGIN as S_REAL_ORIGIN, TEST_ORIGIN as S_TEST_ORIGIN
from .fm_b3_dynamic_evaluation import (
    render_evaluation_modelica, render_openmodelica_script,
    assess_trace, result_prefix, class_name, digest as file_digest
)


PACKAGE = "ArenaSProposalDynamics"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProviderError(message)


def prepare_s(seal: dict, draft: dict, package: dict,
              catalog: dict, views: dict, composed: dict,
              supports: dict, plan: dict, out: Path,
              *, s_capture: dict | None = None,
              calibration: dict | None = None) -> dict:
    if seal.get("origin") in (S_REAL_ORIGIN, S_TEST_ORIGIN):
        check(isinstance(s_capture, dict), "S_CAPTURE_EVIDENCE_REQUIRED")
        verify_s_only_seal(seal,package,catalog,views,composed,supports,
                           s_capture["response"],s_capture["draft"],s_capture["receipt"],
                           calibration=calibration)
        if seal["origin"] == S_REAL_ORIGIN:
            check(isinstance(calibration,dict)
                  and hash_obj(calibration) == seal["calibration_receipt_hash"]
                  and calibration.get("calibrated_composed_hash") == hash_obj(composed)
                  and calibration.get("evaluation_plan_hash") == hash_obj(plan)
                  and calibration.get("construction_hash") == views["S"]["primary_hash"],
                  "S_REAL_REQUIRES_CALIBRATED_PARAMETERS")
    else:
        verify_handoff(seal,draft,package,catalog,views,composed,supports)
        check(seal["origin"] == "MOCK_SYNTHETIC",
              "Unknown S handoff origin")
    check(plan.get("synthetic") is True and
          plan.get("empirical_or_causal_claim") is False and
          supports.get("origin_ref") == plan.get("id"),
          "S scenario is not the registered synthetic Modelica plan")
    check({x["id"] for x in plan["candidates"]} ==
          {x["id"] for x in composed["candidates"]},
          "S execution candidate universe differs from Modelica plan")
    selection = simulation_selection(seal,composed,supports)
    check(bool(selection["selected"]), "S_ABSTAINED_NO_MODEL_TO_SIMULATE")
    out.mkdir(parents=True,exist_ok=True)
    modelica = render_evaluation_modelica(plan,composed,selection,
                                          package_name=PACKAGE)
    mos = render_openmodelica_script(plan,composed,selection,
                                    package_name=PACKAGE)
    (out/(PACKAGE+".mo")).write_text(modelica,encoding="utf-8")
    (out/"run-s-selected.mos").write_text(mos,encoding="utf-8")
    manifest = {
        "schema":"igc-arena-s-simulation/0.1",
        "status":("S_SIMULATION_PREPARED_MOCK_ONLY" if seal["origin"] == "MOCK_SYNTHETIC"
                  else "S_SIMULATION_PREPARED_CAPTURED_NOT_SCORED"),
        "synthetic":True,
        "empirical_adequacy_evaluated":False,
        "S_provider_origin":seal["origin"],
        "handoff_hash":seal["handoff_hash"],
        "selection_hash":hash_obj(selection),
        "composed_hash":hash_obj(composed),
        "support_plan_hash":hash_obj(supports),
        "plan_hash":hash_obj(plan),
        "calibration_receipt_hash":seal.get("calibration_receipt_hash"),
        "simulated_ids":[x["candidate_id"] for x in selection["selected"]],
        "atms_rejected_ids":[x["candidate_id"] for x in selection["rejected"]],
        "modelica_sha256":file_digest(out/(PACKAGE+".mo")),
        "mos_sha256":file_digest(out/"run-s-selected.mos"),
    }
    exclusive_json(out/"s-execution-plan.json",manifest)
    return manifest


def verify_s(manifest: dict, seal: dict, composed: dict, plan: dict,
             out: Path, log: Path) -> dict:
    origin = seal.get("origin")
    check(origin in ("MOCK_SYNTHETIC", S_REAL_ORIGIN, S_TEST_ORIGIN)
          and manifest.get("S_provider_origin") == origin,
          "S simulation origin or manifest mismatch")
    check(manifest.get("status") ==
          ("S_SIMULATION_PREPARED_MOCK_ONLY" if origin == "MOCK_SYNTHETIC"
           else "S_SIMULATION_PREPARED_CAPTURED_NOT_SCORED"),
          "S simulation manifest status mismatch")
    check(manifest.get("handoff_hash")==seal["handoff_hash"]
          and manifest.get("composed_hash")==hash_obj(composed)
          and manifest.get("plan_hash")==hash_obj(plan),
          "S execution manifest dependencies changed")
    check(file_digest(out/(PACKAGE+".mo")) == manifest["modelica_sha256"]
          and file_digest(out/"run-s-selected.mos") == manifest["mos_sha256"],
          "S modelica or solver instructions tampered")
    expected=manifest["simulated_ids"]
    check(expected==seal["S"]["selection"] and expected,
          "S simulation changed selected candidates")
    log_text=log.read_text(encoding="utf-8",errors="replace")
    check(not re.search(r"Error:|Failed to load|Class .* not found",log_text),
          "OpenModelica S log contains an error")
    structures={x["id"]:x for x in composed["structures"]}
    candidates={x["id"]:x for x in composed["candidates"]}
    check(set(expected)<=set(candidates),"S simulated unknown candidate")
    check(not (set(expected)&set(manifest["atms_rejected_ids"])),
          "ATMS excluded structure simulated")
    all_ids={x["id"] for x in composed["candidates"]}
    for other in all_ids-set(expected):
        check(not (out/(result_prefix(other)+"_res.csv")).exists(),
              "S simulator executed an unselected candidate")
    traces={}
    for candidate_id in expected:
        marker=f"Check of {PACKAGE}.{class_name(candidate_id)} completed successfully"
        check(marker in log_text, "S model did not pass OpenModelica checkModel")
        c=candidates[candidate_id]
        structure=structures[c["structure_revision_id"]]
        stage_ids=[x["id"] for x in structure["molecule_instances"]
                   if x["molecule_definition_id"]==plan["roles"]["stage"]]
        result=out/(result_prefix(candidate_id)+"_res.csv")
        check(result.is_file(), "S selected simulation CSV missing")
        metrics=assess_trace(result,stage_ids,
                             float(plan["simulation"]["start_time"]),
                             float(plan["simulation"]["stop_time"]),
                             int(plan["simulation"]["intervals"]))
        metrics["csv_sha256"]=file_digest(result)
        traces[candidate_id]=metrics
    report={
        "schema":"igc-arena-s-simulation/0.1",
        "status":("S_MOCK_MODEL_EXECUTION_PASS_SYNTHETIC" if origin == "MOCK_SYNTHETIC"
                  else "S_CAPTURED_MODEL_EXECUTION_PASS_SYNTHETIC"),
        "source_handoff_hash":seal["handoff_hash"],
        "source_manifest_hash":hash_obj(manifest),
        "simulated_ids":list(expected),
        "excluded_ids":sorted(all_ids-set(expected)),
        "trace_checks":traces,
        "openmodelica_log_sha256":file_digest(log),
        "empirical_adequacy_evaluated":False,
        "real_s_provider_called":origin == S_REAL_ORIGIN,
        "provider_attestation":("MOCK_ONLY" if origin in ("MOCK_SYNTHETIC", S_TEST_ORIGIN)
                                else "LOCAL_CAPTURE_ONLY_NOT_INDEPENDENT"),
        "lane_submission_created":False,
        "holdout_accessed":False
    }
    report["report_hash"]=hash_obj(report)
    return report


def read(p:Path)->dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    p=argparse.ArgumentParser(description="Independent synthetic S proposal solver")
    commands=p.add_subparsers(dest="action",required=True)
    prep=commands.add_parser("prepare")
    verify=commands.add_parser("verify")
    for sub in (prep,verify):
        for key in ("handoff","composed","plan","out"):
            sub.add_argument("--"+key,required=True,type=Path)
    for key in ("draft","package","catalog","views-dir","supports"):
        prep.add_argument("--"+key,required=True,type=Path)
    verify.add_argument("--log",required=True,type=Path)
    prep.add_argument("--s-archive",type=Path,
                      help="S-only captured provider response, draft and receipt")
    prep.add_argument("--calibration",type=Path,
                      help="construction-only grid fit bound to S seal")
    args=p.parse_args()
    seal,composed,plan=read(args.handoff),read(args.composed),read(args.plan)
    if args.action=="prepare":
        is_single=seal.get("origin") in (S_REAL_ORIGIN,S_TEST_ORIGIN)
        views={lane:read(args.views_dir/(lane+".json"))
               for lane in (("S",) if is_single else ("S","P"))}
        check(not is_single or args.s_archive is not None,
              "S_CAPTURE_EVIDENCE_REQUIRED")
        record=({name:read(args.s_archive/(filename+".json")) for name,filename in (
            ("response","response"),("draft","s-draft"),("receipt","receipt"))}
            if is_single else None)
        report=prepare_s(seal,read(args.draft),read(args.package),
                         read(args.catalog),views,composed,read(args.supports),
                         plan,args.out,s_capture=record,
                         calibration=read(args.calibration) if args.calibration else None)
    else:
        report=verify_s(read(args.out/"s-execution-plan.json"),seal,
                        composed,plan,args.out,args.log)
        exclusive_json(args.out/"s-verification.json",report)
    print(json.dumps({"status":report["status"],
                      "simulated_ids":report.get("simulated_ids",[]),
                      "holdout_accessed":False}))


if __name__=="__main__":
    main()
