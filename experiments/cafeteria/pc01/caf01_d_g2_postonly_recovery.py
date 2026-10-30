#!/usr/bin/env python3
"""CAF-01 D G2 post-only salvage of ONE already-executed D1 from GitHub.

Reads the failed run #40982542200 artifact, NEVER runs OMC/RK4/DES or changes
the frozen D representatives. Historical failed receipts stay under 'original'.
This does NOT authorize spending the two remaining D2/D3 G2 slots.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from caf01_d_g2_native import verify, PARENT_SHA256, PARENT_RUN

RUN = 40982542200
ARTIFACT_ID = 12944887907
ZIP_SHA256 = "d5a2b7d624526306ee045f15683a3d76684a89e665fe0224b41548367583f0bd"
FIXED_BYTES = {
    "preflight.json":"e0509cc0ba4310a0c037939ae35451466a4036f8e07ab849d16528edda67f5ee",
    "D_G2_1_res.csv":"85e19d1523d841f370d92dbea9b48bc06e63ad6d4d7d3a8d30b913c4fa001ca3",
    "D_G2_1.log":"5a85889a51668a4914b30b01757a9f0dd6aa37c67b5ee8ba869f384a5451b06a",
    "D_G2_1.attempt":"47bc1f5daf18b26ac329fa190b4b97d21183dac539aa6ac404a245f505e0d340",
    "D_G2_1.exit_code":"9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3ab86aa",
    "D_G2_VERIFIED.json":"58b10e787659bd76cc56411ab58cd36a006570426636190788efd2a2288e843d",
    "D_G2_1_receipt.json":"d124fa8a0c148c4015a9d9f7e89c255d9354769891bfe9688e03446620caa47d",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition,code):
    if not condition:
        raise ValueError(code)


def check_original(original):
    require(original.is_dir(),"G2_RECOVERY_MISSING_FAILED_GITHUB_ARTIFACT")
    for name,h in FIXED_BYTES.items():
        p=original/name
        require(p.is_file() and sha256(p)==h,
                "G2_RECOVERY_PINNED_ORIGINAL_BYTES_CHANGED_"+name)
    mf=json.loads((original/"preflight.json").read_bytes())
    require(mf.get("source_RK4_screen_run")==PARENT_RUN
            and mf.get("source_file_sha256")=="sha256:"+PARENT_SHA256
            and mf.get("selected_model_count")==3
            and [r["ordinal"] for r in mf["selected_models"]]==[1,2,3],
            "G2_RECOVERY_PARENT_MANIFEST_CHANGED")
    for n in (2,3):
        require(not (original/f"D_G2_{n}.attempt").exists()
                and not (original/f"D_G2_{n}.exit_code").exists()
                and not (original/f"D_G2_{n}_res.csv").exists(),
                "G2_RECOVERY_UNRECORDED_LATER_OMC_ATTEMPT")
    require((original/"D_G2_1.attempt").read_bytes()==b"INVOCATION_STARTED\n"
            and (original/"D_G2_1.exit_code").read_bytes()==b"0\n",
            "G2_RECOVERY_D1_ATTEMPT_OR_EXIT_INVALID")
    # This model did finish successfully even though an unrelated shell tee
    # later failed to append to its root-owned native log.
    require("The simulation finished successfully" in
            (original/"D_G2_1.log").read_text(),
            "G2_RECOVERY_D1_NATIVE_SOLVER_NOT_SUCCESSFUL")
    require(json.loads((original/"D_G2_VERIFIED.json").read_bytes())
            ["native_construction_simulations_consumed"]==1,
            "G2_RECOVERY_HISTORICAL_BUDGET_CHANGED")
    return mf


def salvage(original,out):
    require(not out.exists(),"G2_RECOVERY_OUTPUT_ALREADY_EXISTS")
    manifest=check_original(original)
    shutil.copytree(original,out)
    historical=out/"historical_receipts_do_not_overwrite"
    historical.mkdir()
    for n in (1,2,3):
        shutil.copy2(out/f"D_G2_{n}_receipt.json",
                     historical/f"D_G2_{n}_receipt.json")
    shutil.copy2(out/"D_G2_VERIFIED.json",historical/"D_G2_VERIFIED.json")
    new=verify(out)
    status=[r["status"] for r in new["native_candidates"]]
    require(status==["PASS","FAIL","FAIL"] and
            [r["invocation_started"] for r in new["native_candidates"]]==
            [True,False,False] and
            new["native_construction_simulations_consumed"]==1,
            "G2_RECOVERY_D1_PASS_ONLY_EXPECTED")
    receipt={
        "schema":"igc-caf01-d-g2-post-only-recovery/0.1",
        "status":"D1_NATIVE_G2_POST_ONLY_PASS_D2_D3_NOT_EXECUTED",
        "source_failed_GitHub_run":RUN,
        "source_failed_GitHub_artifact_id":ARTIFACT_ID,
        "source_artifact_zip_sha256":"sha256:"+ZIP_SHA256,
        "source_pinned_bytes_sha256":
            {k:"sha256:"+v for k,v in FIXED_BYTES.items()},
        "source_RK4_screen_run":PARENT_RUN,
        "selected_ids":[x["id"] for x in manifest["selected_models"]],
        "original_failed_receipts_preserved":True,
        "original_consumed_G2_OMC":1,
        "post_only_new_OMC":0,
        "post_only_new_RK4":0,
        "post_only_new_DES":0,
        "remaining_D2_D3_G2_OMC_budget":2,
        "new_receipts_file_sha256":{
            f"D_G2_{n}_receipt.json":
              "sha256:"+sha256(out/f"D_G2_{n}_receipt.json")
            for n in (1,2,3)
        },
    }
    (out/"D_G2_POSTONLY_RECOVERY.json").write_text(
        json.dumps(receipt,sort_keys=True,ensure_ascii=False,separators=(",",":"))+"\n",
        encoding="utf-8")
    return receipt


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=salvage(a.original,a.out)
    print(result["status"])


if __name__=="__main__":
    main()
