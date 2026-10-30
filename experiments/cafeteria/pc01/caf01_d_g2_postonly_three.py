#!/usr/bin/env python3
"""CAF-01 D G2 post-only final receipt from EXISTING, unchanged GitHub CSVs.

No OpenModelica execution, no RK4 integration, no DES, no access to holdout.
This is a supplemental verification of the failed global job 40983808227.
It does not rewrite the original GitHub artifact or pretend the job was green.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from caf01_d_g2_native import verify, PARENT_RUN, PARENT_SHA256, EVIDENCE_SHA256

FAILED_G2_RUN = 40983808227
FAILED_G2_ARTIFACT_ID = 12945997813
GITHUB_ZIP_SHA256 = "7e45378a7958f3ef3f4f7624d5380e49bdcde2701a453de616e2b8a6ae447468"
ORIGINAL_D1_G2_RUN = 40982542200
ORIGINAL_D1_ZIP_SHA256 = "d5a2b7d624526306ee045f15683a3d76684a89e665fe0224b41548367583f0bd"

# Byte-level precommit of the actual *already completed* solver products.
# Mutable original files are not accepted: not even a corrected exit code.
PIN = {
    "preflight.json": "e0509cc0ba4310a0c037939ae35451466a4036f8e07ab849d16528edda67f5ee",
    "D_G2_VERIFIED.json": "d6cf8217a1c605bce5410be96f18793ab0cc3b5dfc6db299aeb55f03bf8272a6",
    "D_G2_CROSS_RUN_ACCOUNTING.json": "edec50abcc4eab46765fac18523508e1cea83fc5147e10e8593626622a442921",
    "D_G2_1_receipt.json": "5315e14f3d62b77f25e1c8e58e572db3fb4e16a4404934537dbf2542fce216bb",
    "D_G2_2_receipt.json": "928343735d1c8273210b33591ec56c018791af2681c3f6500bb816cd3a70ce7b",
    "D_G2_3_receipt.json": "73503a1d344cfe8042afb6f4a5d73e36b67a276a8973dc735062c6fa39927559",
    "D_G2_1_res.csv": "85e19d1523d841f370d92dbea9b48bc06e63ad6d4d7d3a8d30b913c4fa001ca3",
    "D_G2_2_res.csv": "cd83330cbd736d7c902a62906809471158da402517938d0fca08c69a35924afc",
    "D_G2_3_res.csv": "2ee2a2c5cc5a3f0d2628e4aa28880c45b73a6080e14",
    "D_G2_1.log": "5a85889a51668a4914b30b01757a9f0dd6aa37c67b5ee8ba869f384a5451b06a",
    "D_G2_2.log": "5a85889a51668a4914b30b01757a9f0dd6aa37c67b5ee8ba869f384a5451b06a",
    "D_G2_3.log": "5a85889a51668a4914b30b01757a9f0dd6aa37c67b5ee8ba869f384a5451b06a",
    **{f"D_G2_{i}.attempt": "47bc1f5daf18b26ac329fa190b4b97d21183dac539aa6ac404a245f505e0d340"
       for i in (1,2,3)},
    **{f"D_G2_{i}.exit_code": "9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa"
       for i in (1,2,3)},
}
# Correct/check all digest literal lengths at import; never infer them.
for _name,_sha in PIN.items():
    if len(_sha)!=64 or any(c not in "0123456789abcdef" for c in _sha):
        raise ValueError("G2_POSTONLY_STATIC_PIN_MALFORMED:"+_name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok,code):
    if not ok:
        raise ValueError(code)


def authenticate(original):
    require(original.is_dir(),"G2_POSTONLY_ORIGINAL_ARTIFACT_MISSING")
    for name,digest in PIN.items():
        f=original/name
        require(f.is_file() and sha(f)==digest,
                "G2_POSTONLY_PINNED_ORIGINAL_BYTES_DIFFER:"+name)
    mf=json.loads((original/"preflight.json").read_bytes())
    require(mf.get("source_RK4_screen_run")==PARENT_RUN
            and mf.get("source_file_sha256")=="sha256:"+PARENT_SHA256
            and mf.get("public_evidence_sha256")=="sha256:"+EVIDENCE_SHA256
            and [x["ordinal"] for x in mf.get("selected_models",[])]==[1,2,3]
            and [x["topology_stocks"] for x in mf["selected_models"]]==[1,2,3],
            "G2_POSTONLY_UPSTREAM_IDENTITY_DRIFT")
    ledger=json.loads((original/"D_G2_CROSS_RUN_ACCOUNTING.json").read_bytes())
    require(ledger["original_native_run"]==ORIGINAL_D1_G2_RUN
            and ledger["original_consumed_D1"]==1
            and ledger["new_recovery_run"]==str(FAILED_G2_RUN)
            and ledger["newly_invoked_ordinals"]==[2,3]
            and ledger["newly_consumed_count"]==2
            and ledger["cumulative_construction_native_attempts"]==3
            and ledger["evaluation_world_opened"] is False,
            "G2_POSTONLY_WRONG_CROSS_RUN_BUDGET")
    prior=json.loads((original/"D_G2_VERIFIED.json").read_bytes())
    require(prior["status"]=="PARTIAL_NATIVE_G2"
            and [x["status"] for x in prior["native_candidates"]]==["PASS","FAIL","FAIL"]
            and [x["invocation_started"] for x in prior["native_candidates"]]==[True]*3,
            "G2_POSTONLY_HISTORICAL_FAILURE_NOT_MATCHED")
    for i in (1,2,3):
        require((original/f"D_G2_{i}.attempt").read_bytes()==b"INVOCATION_STARTED\n"
                and (original/f"D_G2_{i}.exit_code").read_bytes()==b"0\n"
                and "The simulation finished successfully" in
                    (original/f"D_G2_{i}.log").read_text(encoding="utf-8"),
                "G2_POSTONLY_MISSING_OR_FAILED_SOLVER:"+str(i))
    return mf


def recover(original,out):
    require(not out.exists(),"G2_POSTONLY_OUTPUT_EXISTS")
    mf=authenticate(original)
    out.mkdir(parents=True)
    historical=out/"historical_failed_runner_reports_unchanged"
    historical.mkdir()
    for name in ("D_G2_VERIFIED.json","D_G2_1_receipt.json",
                 "D_G2_2_receipt.json","D_G2_3_receipt.json",
                 "D_G2_CROSS_RUN_ACCOUNTING.json"):
        shutil.copy2(original/name,historical/name)
    for name in ["preflight.json",*[
        f"D_G2_{i}{suffix}" for i in (1,2,3)
        for suffix in (".log",".exit_code",".attempt","_res.csv")
    ]]:
        shutil.copyfile(original/name,out/name)
    # Explicitly make *only these copied files* readable. Does not touch
    # original GitHub evidence or execute any solver.
    for f in out.iterdir():
        if f.is_file():
            f.chmod(0o644)
    result=verify(out)
    require(result["status"]=="ALL_THREE_NATIVE_G2_PASSED"
            and result["native_construction_simulations_consumed"]==3
            and len(result["native_candidates"])==3
            and all(x["status"]=="PASS" and x["invocation_started"]
                    and x["balance_max_abs"]<=0.008
                    and x["rk4_native_max_abs_delta"]<=0.012
                    for x in result["native_candidates"]),
            "G2_POSTONLY_NATIVE_REVERIFICATION_DID_NOT_PASS")
    record={
        "schema":"igc-caf01-d-g2-postonly-three-final/0.1",
        "status":"ALL_THREE_G2_POSTONLY_PASS",
        "original_failed_workflow_run":FAILED_G2_RUN,
        "original_artifact_id":FAILED_G2_ARTIFACT_ID,
        "original_artifact_zip_sha256":"sha256:"+GITHUB_ZIP_SHA256,
        "D1_prior_workflow_run":ORIGINAL_D1_G2_RUN,
        "D1_prior_artifact_zip_sha256":"sha256:"+ORIGINAL_D1_ZIP_SHA256,
        "three_cumulative_native_construction_attempts":3,
        "post_only_new_OMC_simulations":0,
        "post_only_new_RK4_integrations":0,
        "post_only_new_DES_runs":0,
        "evaluation_world_accessed":False,
        "original_failed_receipts_retained":True,
        "verified_receipts_sha256":{
            f"D_G2_{i}_receipt.json":"sha256:"+sha(out/f"D_G2_{i}_receipt.json")
            for i in (1,2,3)
        },
        "verified_aggregate_sha256":"sha256:"+sha(out/"D_G2_VERIFIED.json"),
    }
    (out/"D_G2_POSTONLY_FINAL.json").write_text(
        json.dumps(record,sort_keys=True,ensure_ascii=False,separators=(",",":"))+"\n",
        encoding="utf-8")
    return record


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(recover(a.original,a.out)["status"],flush=True)


if __name__=="__main__":
    main()
