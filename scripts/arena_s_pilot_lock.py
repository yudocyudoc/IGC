"""Create PredictionLock for B0 / enumerated D / captured S, with P skipped.

All four lane slots exist as required by arena_round. D/S submissions must be
generated and verified independently BEFORE this command, with holdout access
forbidden. This tool never reads the reserved observation or scores it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .arena_round import (COST_UNITS, LANES, SCHEMA, b0_submission,
                          exclusive_json, lock_round, prepare,
                          validate_submission)
from .arena_sp_producers import ProviderError


def build_lock(spec:dict,primary:dict,s:dict,d:dict,*,run_ref:str) -> tuple[dict,dict,dict]:
    views=prepare(spec,primary)
    for name,submission in (("S",s),("D",d)):
        validate_submission(submission,views[name])
    if (s["status"] not in ("SUBMITTED","ABSTAINED")
        or s.get("capture_receipt_hash") is None
        or s.get("calibration_receipt_hash") is None):
        raise ProviderError("PILOT_S_MUST_BE_FROM_VERIFIED_CAPTURE_OR_ABSTENTION")
    if (d["status"]!="SUBMITTED" or
        d.get("source_manifest_hash") is None or
        d.get("openmodelica_log_sha256") is None):
        raise ProviderError("PILOT_D_MUST_BE_INDEPENDENT_VERIFIED_ENUMERATION")
    p={
        "schema":SCHEMA,"round_id":views["P"]["round_id"],"lane":"P",
        "view_hash":views["P"]["view_hash"],"status":"NOT_IMPLEMENTED",
        "producer":"p-explicitly-skipped-for-s-only-pilot",
        "proposals":[],
        "unknowns":["P deliberately excluded; no Clef or Clairic response"],
        "objections":[], "cost":{key:0 for key in COST_UNITS}}
    submissions={"B0":b0_submission(views["B0"],spec),"D":d,"S":s,"P":p}
    lock=lock_round(spec,views,submissions,run_ref=run_ref)
    return views,submissions,lock


def main():
    p=argparse.ArgumentParser(description="Lock B0/D/S comparison without opening reserve")
    for key in ("spec","primary","s","d","out-dir","run-ref"):
        p.add_argument("--"+key,required=True)
    args=p.parse_args()
    read=lambda p:json.loads(Path(p).read_text(encoding="utf-8"))
    views,submissions,lock=build_lock(read(args.spec),read(args.primary),
                                      read(args.s),read(args.d),
                                      run_ref=args.run_ref)
    out=Path(args.out_dir)
    for lane in LANES:
        exclusive_json(out/"views"/(lane+".json"),views[lane])
        exclusive_json(out/"submissions"/(lane+".json"),submissions[lane])
    exclusive_json(out/"prediction-lock.json",lock)
    print(json.dumps({"status":"PILOT_B0_D_S_LOCKED_NOT_EVALUATED",
                      "lock_hash":lock["lock_hash"]}))


if __name__=="__main__":
    main()
