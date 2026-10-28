"""R5/PT-08 first cut: read-only verification of SIX reconstructed Clef observations.

No provider or OpenModelica calls. Original request bytes are reconstructed
from the frozen, archived PR #69 manifest, while NOUL scores are observations
transcribed from a connector response after the batch. They are NOT independently
attested provider raw records and must never be represented as pre-grade raw.
"""
import argparse
import json
from pathlib import Path

from scripts.arena_clef_dual_pilot import answer_probability
from scripts.arena_pt08_clef_paired_preflight import SCHEMA,guard
from scripts.arena_v0_contract import canonical,digest

SOURCE="data/diagnostics/ARENA_PT08_R5_CLEF_OBSERVACIONES_RECONSTRUIDAS_2026-10-28.json"
CLASSES=("C00","C01","C02")

def reconstruct(frozen_dir,result_path=SOURCE):
    base=Path(frozen_dir)
    public=json.loads((base/"public-six-requests-NOT-SENT.json").read_text())
    oracle=json.loads((base/"researcher-private/paired-oracle-NOT-FOR_PROVIDER.json").read_text())
    manifest=json.loads((base/"manifest.json").read_text())
    observed=json.loads(Path(result_path).read_text())
    guard(public["schema"]==manifest["schema"]==oracle["schema"]==SCHEMA and
          observed["source_original_predeclared_request_digest"]==
          manifest["public_six_request_sha256"]==digest(public) and
          observed["source_original_oracle_digest"]==
          manifest["private_oracle_sha256"]==digest(oracle),
          "R5_ORIGINAL_FROZEN_REQUESTS_OR_ORACLE_DRIFT")
    guard(observed["data_status"]==
          "POSTHOC_RECONSTRUCTION_OF_CONNECTOR_TOOL_OUTPUT_NOT_ORIGINAL_PROVIDER_RAW_ARCHIVE"
          and observed["original_provider_raw_archive_available"] is False
          and observed["verified_provider_latency"] is False
          and observed["execution_path"]==
             "Cloudflare connector direct; no GitHub Actions inference run",
          "R5_RECONSTRUCTION_PROVENANCE_OVERCLAIMED")
    reqs=public["requests"]
    records=observed["observed_responses"]
    expected=oracle["private"]
    guard(len(reqs)==len(records)==len(expected)==6 and
          observed["request_count_observed"]==6 and
          observed["new_OpenModelica_simulations"]==0 and
          observed["automatic_retries_reported"]==0 and
          observed["decision_cutoffs"]=={"exclude_lte":0.3,"strong_support_gte":0.7},
          "R5_BUDGET_OR_RULES_CHANGED")
    rows=[]
    for i,(req,obs,truth) in enumerate(zip(reqs,records,expected),1):
        guard(req["request_id"]==obs["request_id"]==truth["request_id"]
              and obs["original_request_sha256"]==digest(req["body"])
              and obs["observed_http_status"]==200,
              "R5_ORIGINAL_REQUEST_OR_HTTP_STATUS_DRIFT")
        raw=obs["provider_result_reconstructed"]
        probs={k:answer_probability(raw,"path_"+k) for k in CLASSES}
        guard(all(p is not None for p in probs.values()),
              "R5_NON_PARSEABLE_RECONSTRUCTED_NOUL")
        supported=set(truth["note_based_compatibility"])
        exclusions={k for k,p in probs.items() if p<=0.3}
        high={k for k,p in probs.items() if p>=0.7}
        possible=set(CLASSES)-exclusions
        rows.append({
          "request_id":req["request_id"],"condition":req["condition"],
          "paired_case":req["paired_case"],
          "observed_NOUL_probability_by_structure":probs,
          "conservatively_not_excluded":sorted(possible),
          "synthetic_expected_compatible":sorted(supported),
          "conservative_exact":possible==supported,
          "false_exclusions":sorted(supported&exclusions),
          "false_strong_support":sorted(high-supported),
          "provider_input_tokens_reported":
              raw["usage_reported"]["input_tokens"]
        })
    pair_checks=[]
    for i in range(0,6,2):
        a,b=rows[i:i+2]
        guard(a["condition"]=="NUMERIC_ONLY" and
              b["condition"]=="NUMERIC_PLUS_NOTE" and
              a["paired_case"]==b["paired_case"],
              "R5_PAIRED_ORDER_INVALID")
        pair_checks.append({
          "paired_case":a["paired_case"],
          "control_conservatively_not_excluded":a["conservatively_not_excluded"],
          "note_conservatively_not_excluded":b["conservatively_not_excluded"],
          "note_expected_compatible":b["synthetic_expected_compatible"],
          "with_note_exact":b["conservative_exact"],
          "with_note_false_exclusions":b["false_exclusions"]
        })
    metrics={
      "numeric_only_exact":sum(x["conservative_exact"] for x in rows
                               if x["condition"]=="NUMERIC_ONLY"),
      "with_note_exact":sum(x["conservative_exact"] for x in rows
                            if x["condition"]=="NUMERIC_PLUS_NOTE"),
      "numeric_only_false_exclusions":sum(len(x["false_exclusions"]) for x in rows
                               if x["condition"]=="NUMERIC_ONLY"),
      "with_note_false_exclusions":sum(len(x["false_exclusions"]) for x in rows
                                 if x["condition"]=="NUMERIC_PLUS_NOTE"),
      "input_tokens_reported":sum(x["provider_input_tokens_reported"] for x in rows)
    }
    guard(metrics=={
        "numeric_only_exact":0,"with_note_exact":1,
        "numeric_only_false_exclusions":3,"with_note_false_exclusions":3,
        "input_tokens_reported":16881},
        "R5_PREDECLARED_CONCLUSION_NOT_REPRODUCED")
    return {
      "schema":"igc-arena-r5-pt08-first-cut-reconstructed-offline-verification/0.1",
      "predeclared_request_digest":digest(public),
      "reconstructed_response_digest":digest(observed),
      "number_of_provider_responses_observed":6,
      "provenance":"RECONSTRUCTED_FROM_TOOL_OUTPUT_AFTER_BATCH_NOT_INDEPENDENT_PROVIDER_ARCHIVE",
      "method":"SAME_PREDECLARED_NOUL_CUTOFFS_0_30_0_70",
      "metrics":metrics,"pairs":pair_checks,
      "closure":"PT08_R5_FIRST_CUT_NEGATIVE_NO_CLEF_PROMOTION",
      "additional_provider_calls":0,"additional_solver_calls":0,
      "R5_structural_identification":"NOT_DEMONSTRATED",
      "actual_solver_savings":"NONE_ESTABLISHED",
      "generalization":"NOT_ESTABLISHED"
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    guard(not a.out.exists(),"R5_CLOSURE_OUTPUT_ALREADY_EXISTS")
    x=reconstruct(a.original)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(x)+b"\n")
    print(json.dumps({"status":x["closure"],"metrics":x["metrics"],
                      "provenance":x["provenance"],
                      "new_provider_calls":0,"new_solver_calls":0},
                     sort_keys=True))
if __name__=="__main__":
    main()
