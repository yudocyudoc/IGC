"""PT-05: replay immutable R1, D/M decisions, BOTH real Buffalo R2 calls.

The successful 16k native response gets a supplementary semantic-view check;
the historical auto-verdict remains G2_OR_G3_REJECTED, never overwritten.
All timestamps supplied here are administrative REPLAY cuts, not event times.
"""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

from scripts.arena_b_native_series import assess_native
from scripts.arena_r2_dm_decisions import own_decisions,persist
from scripts.arena_r2_memory_first_cut import ingest,snapshot,MIGRATION
from scripts.arena_r1_buffalo_postonly import SHARED_SOURCE,ORIGINAL_NATIVE_SHA
from scripts.arena_v0_contract import canonical,digest
from scripts.ledger import Ledger

SCHEMA="igc-arena-r2-pt05-joint-closure/0.1"
B7_REQUEST="sha256:67015d6b469d1a89048aa6e729f1ab003192eba422492c04b1c85a2568d7b8f7"
B16_REQUEST="sha256:d0426c72a2b19856cb9d1a9ff5f6e322a7aaa8f31395ead032588065ba76ad4c"
B16_NATIVE="sha256:c47a0752755fc10b3ec7b626677afcb26e962e7e3cf4582bb70aa7488694f229"
TIMES=("2026-10-27T15:00:00Z","2026-10-27T15:01:00Z",
       "2026-10-27T15:02:00Z","2026-10-27T15:03:00Z")

def require(ok,reason):
    if not ok: raise ValueError(reason)

def load(z,name):
    return json.loads(z.read(name).decode("utf-8"))

def hashbytes(raw):
    return "sha256:"+sha256(raw).hexdigest()

def inspect(dossier, old_zip, new_zip):
    source=json.loads((Path(dossier)/"b-visible.json").read_text())
    require(source["source_snapshot_hash"]==SHARED_SOURCE,"WRONG_SHARED_CASE")
    dm=own_decisions(dossier)
    with zipfile.ZipFile(old_zip) as old,zipfile.ZipFile(new_zip) as new:
        r7=load(old,"r2-b-real/receipt.json")
        q7=load(old,"r2-b-real/cloudflare-raw.json")["result"]
        r16=load(new,"r2-b-real/receipt.json")
        q16=load(new,"r2-b-real/cloudflare-raw.json")["result"]
        native_bytes=new.read("r2-b-real/native-output.json")
        native=json.loads(native_bytes)
        original=load(new,"r2-b-16k-outcome.json")
        modelica=new.read("r2-b-physical/BuffaloNative_d3c8b77bb184.mo")
        csv_bytes=new.read("r2-b-physical/BuffaloNative_d3c8b77bb184_res.csv")
        omc_bytes=new.read("r2-b-physical/omc.log")
    require(r7["request_sha256"]==B7_REQUEST and r16["request_sha256"]==B16_REQUEST
            and r7["parent_bytes_sha256"]==r16["parent_bytes_sha256"]==
            "sha256:"+ORIGINAL_NATIVE_SHA,"BUFFALO_CHANGED_PARENT_OR_REQUEST")
    require(r7["live_provider_calls"]==r16["live_provider_calls"]==1 and
            r7["status"]=="BUFFALO_RETURNED_NO_NATIVE_MODEL" and
            r16["status"]=="REAL_CLOUDFLARE_BUFFALO_R2_OWN_REVIEW_RETURNED" and
            r16["r2_extended_budget"] is True and
            r16["current_model_seen"] and r16["no_suspect_equation_hint"] and
            r16["r2_feedback_seen"],"BUFFALO_CALL_LINEAGE_NOT_AUTHENTIC")
    require(q7["choices"][0]["finish_reason"]=="length" and
            q7["usage"]["completion_tokens"]==7000 and
            q16["choices"][0]["finish_reason"]=="stop" and
            q16["usage"]["prompt_tokens"]<=8000 and
            q16["usage"]["completion_tokens"]<=16000,"BUFFALO_TOKEN_OUTCOME_CHANGED")
    require(hashbytes(native_bytes)==B16_NATIVE and
            len(native["model"]["variables"])==16 and
            len(native["model"]["relationships"])==16,
            "BUFFALO_NATIVE_16K_BYTES_CHANGED")
    require(original["request_sha256"]==B16_REQUEST and
            original["g2"]=="G2_OR_G3_REJECTED" and
            original["g2_reason"]=="MISSING_BUFFALO_SERIES:pending_work" and
            original["g0"]=="TRANSLATED_CONDITIONALLY" and
            original["g3"]=="NOT_COMPUTABLE" and
            original["provider_calls"]==1 and
            original["actual_native_bytes_sha256"]==B16_NATIVE and
            original["modelica_sha256"]==hashbytes(modelica),
            "ORIGINAL_R2_VERDICT_MUST_NOT_BE_REWRITTEN")
    require(b"Simulation execution failed" not in omc_bytes and
            (b"simulation finished" in omc_bytes.lower() or
             b"simulation succeeded" in omc_bytes.lower() or
             b"LOG_SUCCESS" in omc_bytes),
            "OPENMODELICA_SUCCESS_NOT_EVIDENCED")
    # The original CSV is not rewritten or normalized on disk.
    rows=list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    supplemental=assess_native(rows,source,native)
    g2=supplemental["construction_diagnostic"]
    require(g2["modelica_status"]=="G2_SIMULATED_CONDITIONALLY" and
            g2["balance_residual_max_items"]<1e-4 and
            abs(g2["rmse_all_observations_items"]-0.355555)<1e-5 and
            g2["g3_construction_status"]=="DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND",
            "SUPPLEMENTAL_G2_OR_DESCRIPTIVE_ERROR_CHANGED")
    values=sorted({float(row["time"]):row for row in rows}.items())
    role=supplemental["series_view"]["roles"]
    delivered=[(t,float(row[role["delivered_work"]])) for t,row in values]
    # Frozen original public pulse from construction source: 1.7 items/h, t in [0,2).
    input_integral=sum((tb-ta)*float(a[role["arrivals"]])
                       for (ta,a),(tb,_) in zip(values,values[1:]))
    expected_input=3.4
    require(abs(input_integral-2.65625)<1e-6,"PULSE_INTEGRAL_CHANGED")
    require(float(dict(values)[1.5][role["arrivals"]])==0.85,"R2_PULSE_NOT_RAMPED")
    # A completed physical run on a different input does not establish G3.
    pulse={"specified_profile":"RECTANGLE_1.7_ITEMS_PER_HOUR_0_TO_2H",
           "requested_integral_items":expected_input,
           "realized_euler_integral_items":input_integral,
           "deficit_items":expected_input-input_integral,
           "deficit_fraction":(expected_input-input_integral)/expected_input,
           "realized_at_1_5h_items_per_hour":0.85,
           "required_at_1_5h_items_per_hour":1.7,
           "same_stimulus_as_D_M":False}
    return {"schema":SCHEMA,"case_id":dm["case_id"],"source_snapshot_hash":SHARED_SOURCE,
        "r1":{"D":"6_REAL_G2_ALTERNATIVES_NO_IDENTIFIED_WINNER",
              "M":"3_REAL_G2_M3_ABSTAIN","B":"ORIGINAL_NATIVE_G1_NEGATIVE_NO_CSV_NO_RMSE"},
        "r2":{"D":dm["d"]["decision"],"M":dm["m"]["decision"],
              "B":"REVISED_NATIVE_EXECUTABLE_CONDITIONALLY_PULSE_MISMATCH"},
        "calls":{"buffalo_r1":1,"buffalo_r2_7000":1,"buffalo_r2_16000":1,
                 "additional_calls_in_PT05":0},
        "b7":{"request_sha256":B7_REQUEST,"finish_reason":"length","tokens_output":7000,
              "status":"INVALID_TRUNCATED_NATIVE_NOT_PHYSICALLY_EVALUABLE"},
        "b16":{"request_sha256":B16_REQUEST,"original_native_bytes_sha256":B16_NATIVE,
               "original_auto_verdict":original["g2"],
               "original_auto_error":original["g2_reason"],
               "original_auto_report_sha256":hashbytes(canonical(original)),
               "solver_csv_sha256":hashbytes(csv_bytes),
               "solver_log_sha256":hashbytes(omc_bytes),
               "modelica_sha256":hashbytes(modelica),
               "actual_input_tokens":q16["usage"]["prompt_tokens"],
               "actual_output_tokens":q16["usage"]["completion_tokens"],
               "finish_reason":q16["choices"][0]["finish_reason"],
               "supplementary":supplemental,
               "pulse_fidelity":pulse,
               "g0":"CONDITIONAL_TRANSLATION_NOT_UPSTREAM_EQUIVALENCE",
               "g2":"REAL_OPENMODELICA_TRAJECTORY_ON_ALTERED_INPUT",
               "g3":"NOT_ESTABLISHED",
               "causal_identification":"NOT_DEMONSTRATED"},
        "method_comparison":"PROHIBITED_NONCOMPARABLE_INPUT_AND_PARAMETER_POLICIES",
        "r1_b_rmse":"NOT_COMPUTABLE",
        "holdout":"NOT_RUN",
        "no_new_solver_runs":True,
        "original_artifacts_unchanged":True,
        "atms_status":"LOGICAL_DEPENDENCIES_ONLY_NOT_TRUTH"}

def close(db,dossier,old_zip,new_zip):
    r=inspect(dossier,old_zip,new_zip)
    ingest(db,dossier,TIMES[0],TIMES[1])
    d=own_decisions(dossier)
    persist(db,dossier,d,prior_cut=TIMES[1],recorded_at=TIMES[2])
    case=r["case_id"]
    base="arena:r2:"+case+":B:"
    ledger=Ledger(db,MIGRATION)
    for key,kind,body in [
      ("r2-7k-truncated","fact",{"source_id":B7_REQUEST,"reason":"FINISH_LENGTH_BAD_NATIVE"}),
      ("r2-16k-native","assumption",{"source_id":B16_NATIVE,"status":"NATIVE_COMPLETE"}),
      ("r2-16k-solver-csv","assumption",{"source_id":r["b16"]["solver_csv_sha256"],
                                      "status":"REAL_EULER_CSV_EXISTS"}),
      ("r2-16k-supplemental","fact",{"diagnostic":r["b16"]["supplementary"],
                                   "original_auto_verdict":"G2_OR_G3_REJECTED",
                                   "original_auto_error":"MISSING_BUFFALO_SERIES:pending_work"}),
      ("r2-16k-pulse-discrepancy","fact",{"pulse":r["b16"]["pulse_fidelity"],
                                        "epistemic_status":"OWN_INPUT_DIFFERS_FROM_PUBLIC_PULSE"}),
      ("r2-16k-solver-evidence","justification",{
          "antecedents":[base+"r2-16k-native",base+"r2-16k-solver-csv"],
          "consequent":base+"r2-16k-conditional-physical-trajectory",
          "epistemic_status":"PHYSICAL_EXISTENCE_NOT_FIT"})]:
        entity=base+key
        payload={"kind":kind,"active":True,"phase":"R2_B_BUFFALO_TWO_ACTUAL_CALLS",
                 "source_id":B16_NATIVE,**body}
        ledger.append_revision(entity_id=entity,entity_type="ArenaR2ClosureEvidence",
           case_id=case,actor_id="arena:evaluator:pt05",
           idempotency_key=entity+":"+digest(payload),
           recorded_at=TIMES[3],created_at=TIMES[3],
           payload=payload,access_policy="lane:B")
    before=snapshot(db,case,TIMES[2],"B")
    after=snapshot(db,case,TIMES[3],"B")
    claim=base+"r2-16k-conditional-physical-trajectory"
    require(claim not in before["logical"]["labels"] and
            claim in after["logical"]["labels"] and
            after["logical"]["labels"][claim] and
            base+"r2-16k-pulse-discrepancy" in after["visible_entities"],
            "B_ATMS_NOT_RECONSTRUCTED_AFTER_16K")
    for lane in ("D","M"):
        old=snapshot(db,case,TIMES[2],lane)
        new=snapshot(db,case,TIMES[3],lane)
        require(old["visible_entities"]==new["visible_entities"] and
                old["logical"]["labels"]==new["logical"]["labels"],
                "PT05_LEAKED_BUFFALO_EVIDENCE_TO_RIVAL")
    r["ledger"]={"administrative_replay_cuts_not_historical_event_timestamps":list(TIMES),
                 "b_before_labels":len(before["logical"]["labels"]),
                 "b_after_labels":len(after["logical"]["labels"]),
                 "b_supported_physical_claim":claim,
                 "d_m_views_unchanged_after_b_result":True}
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dossier",type=Path,required=True)
    p.add_argument("--r2-7k",type=Path,required=True)
    p.add_argument("--r2-16k",type=Path,required=True)
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    require(not a.db.exists() and not a.out.exists(),"PT05_OUTPUT_EXISTS")
    result=close(a.db,a.dossier,a.r2_7k,a.r2_16k)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":"PT05_R2_CLOSED_B_CONDITIONAL_G2_PULSE_MISMATCH",
        "b_rmse":result["b16"]["supplementary"]["construction_diagnostic"]["rmse_all_observations_items"],
        "calls_pt05":0,"hash":digest(result)}))

if __name__=="__main__":
    main()
