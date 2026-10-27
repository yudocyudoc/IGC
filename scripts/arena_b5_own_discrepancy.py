"""B5: strict neutral self-discrepancy feedback from B4's OWN claims and own G2.

Not Astra's critique, no equation hint, no capacity bound computation,
no new observations, no alternative arm. All source bytes are pinned.
"""
import argparse,hashlib,json,re
from pathlib import Path

B4_SHA="c3662f90d7fb7a6211b62f35e13739000d2f6b90bcbb6d44cabc131dd45e7bbb"
G2_SHA="2e97c1f7d87d75c3c91649c340d97c6ff0557bfcc30a1456f1d4bda6cd9e3533"
EXPECTED=[0.35,1.05,2.45]
TIMES=[1,2,4]

def require(ok,msg):
    if not ok:raise ValueError(msg)

def read(path,sha):
    data=path.read_bytes()
    require(hashlib.sha256(data).hexdigest()==sha,"B5_SOURCE_BYTES_CHANGED")
    return json.loads(data)

def build(native,adjudication):
    parent=read(native,B4_SHA)
    physical=read(adjudication,G2_SHA)
    explanation=parent["supportingInfo"]["explanation"]
    # Extract ONLY the LLM's explicitly claimed delivery numbers, not guesses.
    require("near 0.35, 1.05, and 2.45 at hours 1, 2, and 4" in explanation,
            "B4_OWN_NARRATIVE_DIFFERENT")
    require(physical["g2_status"]=="PASS_REAL_OPENMODELICA_OWN_CANDIDATE"
            and physical["revised_native_sha256"]=="sha256:"+B4_SHA,
            "B5_MISSING_B4_OWN_REAL_SIMULATION")
    rows=physical["construction_check"]["construction_observations"]
    require([x["time_hour"] for x in rows]==[0.,1.,2.,4.],
            "B5_CONSTRUCTION_TIMES_CHANGED")
    out=[]
    for t,p,row in zip(TIMES,EXPECTED,rows[1:]):
        out.append({
          "t_hour":t,
          "own_explanation_expected_delivered_approximately_items":p,
          "own_equations_openmodelica_delivered_items":row["predicted_items"],
          "construction_observed_delivered_items":row["observed_items"],
          "own_equations_minus_own_explanation_items":row["predicted_items"]-p,
        })
    return {
      "schema":"igc-b5-own-explanation-vs-physical-simulation/0.1",
      "arm_id":"B",
      "parent_native_bytes_sha256":"sha256:"+B4_SHA,
      "parent_g2_bytes_sha256":"sha256:"+G2_SHA,
      "parent_own_explanation_verbatim":explanation,
      "comparisons":out,
      "original_iteration_budget_finished":True,
      "separately_authorized_followup":True,
      "holdout":"NOT_RUN",
      "other_arms_included":False,
      "causal_truth":"UNKNOWN",
      "native_simulator_lookup_parity":"NOT_CERTIFIED",
      "instructions":"Reconcile your OWN stated expected deliveries with the physical consequences of your OWN equations. Decide whether to revise a mechanism, revise a claim, or abstain; no particular variable or equation is identified as the cause."
    }

def main():
    ap=argparse.ArgumentParser()
    for k in ("native","adjudication","out"):
        ap.add_argument("--"+k,type=Path,required=True)
    a=ap.parse_args()
    require(not a.out.exists(),"B5_OUTPUT_ALREADY_EXISTS")
    o=build(a.native,a.adjudication)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":"B5_PARENT_AUTHENTICATED_OWN_DISCREPANCY_ONLY",
      "rows":len(o["comparisons"]),"input_sha":o["parent_native_bytes_sha256"]}))

if __name__=="__main__":main()
