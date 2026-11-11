#!/usr/bin/env python3
"""CAF-01 M six-model post-only G2 recovery from ORIGINAL GitHub 40999625128.

No OMC, no RK4, no DES, no Buffalo, no external data and no holdout.
Original historical six FAIL receipts preserved. The exact, SHA-pinned, already
simulated native CSVs alone are reverified using material stocks rather than
the former transit-only display variable. No simulations may be repeated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from caf01_m_g2_six_native import verify,canonical

RUN=40999625128
ARTIFACT=12951919738
ARTIFACT_ZIP_SHA256="1a6518c5debc2ad83cb4d57d68a06a7c58458e658ddde3610fd058def74fb01d"
WORLD="sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"
CSV=[
 "2bca794bdf640e83352e84e9b10418461f4f6d18652ddcbabf50fb2458f588fd",
 "e61597ea4e7f2aa82face0085282f9249ef4100dbc3fc44946d707ed000b1b21",
 "7ecf6488ba9a75ce8a9193081ef2081ef5edde761949c9875ff1557fbdd7b76a",
 "a7dc59a6d6b18a39fedd4409c95b89721bef970ce7859daef4181c31f347a86f",
 "ee71b5fb4b8c40b89860804957e85b0c7aff36503e338a9b0d52554799986d74",
 "b95e92c53d72bacd68b070f49da9b9febb49c68c172eed1645d916692dc822b1"
]
SCRIPTS=[
 "2c2f8c4f27c630bbb2f727a0692d8ec7edfae23bb4e3da7e42dcd878ed1dcec0",
 "fe901cf9ad0969f034d44fce29c36d5fd22ef3cab6831bbe82183e13e1788508",
 "326a32f01e7d6abf5c284ce35ed7b7fbd1f678372ae59149eb51f94b8d97b594",
 "7e8d56f378b72a39ad3f91b85b4f5f233a20e7ca717df454251d6fb55c218df7",
 "ccfdaa4e448e846fe080b4205f2337c7ff5a70d142900241a7b20c84c7c521ca",
 "3ff0af22e107693c8bf737dc283adce7030298a4b4ab3fa9ab9bf3d3e701d4f6"
]
CONSOLE=[
 "c6052bb28167cd1bb6cab79695aad5a9b2e7ff2a4f8532d47f1a3d29ba0d572c",
 "574a8d06c6397094b3de40046633ab30761b992e04bde96784945a25958617fa",
 "1292b11dceff988a82afc7b79f4bc8087ca64416b3bf51c04a8e450d3c6afe1c",
 "ac11214b2c2709ae53cfed1a952508bbb5bd43720e4bd08405958c86c1bfac67",
 "3dde80378c1a551de6063b3493431a283f510e2047527d467fd98eb58b1f610f",
 "7805f547c743b3e2e23c8aac7c4451377863452ad894a98b6091e2cdf5d002a6"
]
HIST=[
 "2d61e85a66107331b22b0c1e05604710a70cae371f0b50a9c63a0d2bfe970d83",
 "eda6903458982a88b6d7b8bba9d71f4b6b38ee66b378299e3e27cc3b1f67b903",
 "8f6eb503ea542705c4dee018ce8a2a4e4b80939da3d88c11045595b8a5702a40",
 "3d4355b93ba2172d114540387642633986da7a55c504e8ed9b2f17c1b2e10cd7",
 "423e3e19bb9307f3190fb3ffb1e9c81de1f0d7c0602a2a053d099f87b0570f46",
 "dd98d7abe01a1697109df3587cce8ccb0a71faf2a924bf2bb281f9412c6c3fe4"
]
PIN={
 "M_G2_PREFLIGHT.json":"5cd1a7edc363be1cbd15e51ce937170221fa7f1326fa54bd53728a11537692f2",
 "M_G2_AGGREGATE.json":"ac23299e370168f89608518d4c0ca335e5cd79e7966b4e78c3abc0f604ec6a7a",
 "CAF01MPreflight.mo":"53966be7dd6275d33c5894a6c58063bc845a67ff8c9dfdacabc13eabc0794612",
 "M_PRODUCER_PACKET.json":"f99a9276844103e6332f40ad5c8c76932942e70596bfa1eb6c23b0a5827a3c0f",
 "M_CHECK_ONLY.mos":"1d87e49dee930dd63083ed60da4a99c651554a65b740eb443102c7cc891429c7",
 "check_only.console.txt":"0f566e672f2acaeaf21cd4092c7f8745fc8bb521c7aa9eb6ec592e829d9f51e9",
}
for n in range(1,7):
    PIN[f"M_G2_{n}_res.csv"]=CSV[n-1]
    PIN[f"M_G2_{n}.mos"]=SCRIPTS[n-1]
    PIN[f"M_G2_{n}.console.txt"]=CONSOLE[n-1]
    PIN[f"M_G2_{n}_receipt.json"]=HIST[n-1]
    PIN[f"M_G2_{n}.log"]="5a85889a51668a4914b30b01757a9f0dd6aa37c67b5ee8ba869f384a5451b06a"
    PIN[f"M_G2_{n}.attempt"]="47bc1f5daf18b26ac329fa190b4b97d21183dac539aa6ac404a245f505e0d340"
    PIN[f"M_G2_{n}.exit_code"]="9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa"
for name,hexstr in PIN.items():
    if len(hexstr)!=64 or any(ch not in "0123456789abcdef" for ch in hexstr):
        raise ValueError("M_G2_POSTONLY_BAD_STATIC_PIN:"+name)

def need(ok,code):
    if not ok: raise ValueError(code)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def authenticate(original):
    need(original.is_dir(),"M_G2_POSTONLY_SOURCE_MISSING")
    for filename,expected in PIN.items():
        p=original/filename
        need(p.is_file() and sha(p)==expected,
             "M_G2_POSTONLY_ORIGINAL_BYTES_CHANGED:"+filename)
    p=json.loads((original/"M_G2_PREFLIGHT.json").read_bytes())
    need(p["schema"]=="igc-caf01-m-native-g2/0.1"
         and p["source_public_world"]==WORLD
         and p["native_invocations_at_prepare"]==0
         and p["M_OMC_construction_max_new_attempts"]==6
         and p["C72_C100_equivalence_conditionally_assumed"] is True
         and len(p["six_predeclared_members"])==6
         and [r["ordinal"] for r in p["six_predeclared_members"]]==[1,2,3,4,5,6]
         and p["source_package_sha256"]=="sha256:"+sha(original/"CAF01MPreflight.mo"),
         "M_G2_POSTONLY_ORIGINAL_MANIFEST_INCOMPLETE")
    old=json.loads((original/"M_G2_AGGREGATE.json").read_bytes())
    need(old["status"]=="PARTIAL_M_NATIVE_G2"
         and old["native_construction_simulations_consumed"]==6
         and old["native_g2_pass_count"]==0
         and [x["status"] for x in old["native_candidates"]]==["FAIL"]*6
         and [x["reason_code"] for x in old["native_candidates"]]==
             ["M_G2_NATIVE_MASS_BALANCE_FAILED"]*6,
         "M_G2_POSTONLY_NOT_EXPECTED_HISTORICAL_RUN")
    for n in range(1,7):
        need((original/f"M_G2_{n}.attempt").read_bytes()==b"INVOCATION_STARTED\n"
             and (original/f"M_G2_{n}.exit_code").read_bytes()==b"0\n"
             and "The simulation finished successfully" in
                (original/f"M_G2_{n}.log").read_text(),
             "M_G2_POSTONLY_NATIVE_RUN_NOT_SUCCESSFUL:"+str(n))
    return p

def recover(original,out):
    need(not out.exists(),"M_G2_POSTONLY_OUTPUT_EXISTS")
    pre=authenticate(original)
    out.mkdir(parents=True)
    historical=out/"historical_original_FAIL_receipts"
    historical.mkdir()
    for n in range(1,7):
        shutil.copyfile(original/f"M_G2_{n}_receipt.json",
                        historical/f"M_G2_{n}_receipt.json")
    shutil.copyfile(original/"M_G2_AGGREGATE.json",historical/"M_G2_AGGREGATE.json")
    for name in ["M_G2_PREFLIGHT.json", "CAF01MPreflight.mo",
                 "M_PRODUCER_PACKET.json",
                 *[f"M_G2_{n}{s}" for n in range(1,7)
                   for s in (".mos",".console.txt",".log",".attempt",".exit_code","_res.csv")]]:
        shutil.copyfile(original/name,out/name)
    report=verify(out)
    need(report["status"]=="ALL_SIX_M_NATIVE_G2_PASS"
         and report["native_construction_simulations_consumed"]==6
         and report["native_g2_pass_count"]==6
         and all(r["status"]=="PASS" and
                 len(r["native_material_stock_columns"]) in (2,3,4) and
                 r["balance_max_abs"]<=0.008 and
                 r["transit_report_max_abs_delta"]<=0.008 and
                 r["delivery_counter_max_abs_delta"]<=0.008
                 for r in report["native_candidates"]),
         "M_G2_POSTONLY_CORRECTED_BALANCE_NOT_VERIFIED")
    record={
        "schema":"igc-caf01-m-six-postonly-recovery/0.1",
        "status":"ALL_SIX_M_G2_PHYSICAL_CONSERVATION_PASS_POSTONLY",
        "source_failed_scientific_run":RUN,
        "source_original_GitHub_artifact_id":ARTIFACT,
        "source_GitHub_zip_sha256":"sha256:"+ARTIFACT_ZIP_SHA256,
        "original_file_hashes_sha256":{n:"sha256:"+v for n,v in PIN.items()},
        "all_original_FAIL_receipts_preserved":True,
        "postonly_OMC_simulations":0,
        "postonly_RK4_integrations":0,
        "postonly_DES_world_runs":0,
        "postonly_B_provider_calls":0,
        "cumulative_M_native_construction_invocations":6,
        "nominal_M_native_construction_budget_ceiling":9,
        "G3_selection_performed":False,
        "evaluation_world_accessed":False,
        "scientific_scope":"PHYSICAL_BALANCE_ONLY_NOT_PREDICTIVE_VALIDATION",
        "corrected_native_receipts_sha256":{
           f"M_G2_{n}_receipt.json":"sha256:"+sha(out/f"M_G2_{n}_receipt.json")
           for n in range(1,7)},
        "corrected_aggregate_sha256":"sha256:"+sha(out/"M_G2_AGGREGATE.json"),
    }
    (out/"M_G2_POSTONLY_FINAL.json").write_bytes(canonical(record))
    return record

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    print(recover(args.original,args.out)["status"],flush=True)

if __name__=="__main__":
    main()
