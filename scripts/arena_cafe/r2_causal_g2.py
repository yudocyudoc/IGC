"""Six original-D engineering traces on a causal POS signal, NEVER G3 evidence.

RF-02G deliberately validates compiler/solver conservation with an EXPLICIT
FIXTURE, not a cafeteria parameter estimate. The native D stock/flow equations
come from the pinned original renderer. The source input changes exclusively
to a declared, causal, non-observed continuous event kernel.

prepare: six .mo + one .mos, but NO solver invocation.
verify: only accepts six real CSVs plus invocation marker, exit=0, bound
        source hashes and exact integrated event mass. Reports G2 engineering.
No evaluator DES, no private world, no Buffalo/Cloudflare, no selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as Q
from pathlib import Path

from scripts.arena_v0_contract import canonical,digest
from scripts.arena_cafe.native_handoff import need,validate_a1_visible
from scripts.arena_cafe import r2_causal_pos_signal as causal
from scripts.arena_cafe import observation_eval as oe

SCHEMA="igc-arena-rf02-causal-six-d-engineering-g2/0.1"
FIXTURE_SCHEMA="igc-arena-rf02-g2-nominal-fixture/0.1"
REPORT_SCHEMA="igc-arena-rf02-causal-six-d-engineering-g2-audit/0.1"
TOLERANCE_ORDERS=0.08  # declared before run, inherited from A1 engineering G2


def sha_file(path):
    return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_fixture(obj):
    need(type(obj) is dict and set(obj)=={
          "schema","scope","not_ev01_empirical_estimate","parameters"},
         "RF02G_FIXTURE_SCHEMA")
    need(obj["schema"]==FIXTURE_SCHEMA and
         obj["scope"]=="NON_EMPIRICAL_OPENMODELICA_CONFORMANCE_ONLY" and
         obj["not_ev01_empirical_estimate"] is True,
         "RF02G_FIXTURE_NOT_CONFORMANCE")
    # This is the same strict nominal provenance validator as RF02.
    from scripts.arena_cafe.r2_observational_contracts import _declared_params
    params=_declared_params(obj["parameters"])
    need(params is not None,"RF02G_MISSING_NOMINAL")
    need(all(value["source_ref"]=="RF02G-G2-ENGINEERING-FIXTURE-ONLY"
             and value["status"]=="ASSUMED"
             for value in params.values()),
         "RF02G_NOT_AN_EXPLICIT_NON_EMPIRICAL_FIXTURE")
    return params


def _script(rows,stop):
    result=["getVersion();"]
    for i,row in enumerate(rows):
        name=row["model_name"]
        prefix=row["csv_prefix"]
        result.extend([
            'loadFile("'+name+'.mo");',
            "checkModel("+name+");",
            "print(getErrorString());",
            "simulate("+name+",startTime=0,stopTime="+format(stop,".17g")+
            ',numberOfIntervals=2000,method="dassl",tolerance=1e-9,'+
            'outputFormat="csv",fileNamePrefix="'+prefix+'");',
            "print(getErrorString());",
        ])
    return "\n".join(result)+"\n"


def prepare(visible,condition,fixture,out):
    validate_a1_visible(visible,condition)
    params=validate_fixture(fixture)
    generated=causal.render_six_with_declared_nominals(
        visible,condition,params)
    need(generated["candidate_count"]==6 and
         generated["selection_owner"]=="NONE" and
         generated["G2"]=="NOT_RUN" and generated["G3"]=="NOT_RUN",
         "RF02G_ENGINEERING_GENERATION_NOT_SIX")
    out=Path(out)
    need(not out.exists(),"RF02G_REFUSE_OVERWRITE")
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for i,model in enumerate(generated["candidates"]):
        file=out/(model["model_name"]+".mo")
        file.write_text(model["modelica"],encoding="utf-8",newline="\n")
        need(sha_file(file)==model["modelica_sha256"],
             "RF02G_MODEL_EMISSION_HASH_CHANGED")
        rows.append({
            "candidate_id":model["candidate_id"],
            "structure_hash":model["structure_hash"],
            "model_name":model["model_name"],
            "modelica_file":file.name,
            "modelica_sha256":model["modelica_sha256"],
            "csv_prefix":"d"+str(i).zfill(2),
            "stock_count":i//2+1,
            "loss":bool(i%2),
            "equations_original_native":True,
            "policy_owner":"ARENA_ENGINEERING_NOT_D_NATIVE_INFERENCE",
            "G2":"NOT_RUN","G3":"NOT_RUN",
        })
    cutoff=float(Q(visible["observability"]["cutoff_minutes_exact"]))
    script=_script(rows,cutoff)
    script_file=out/"simulate.mos"
    script_file.write_text(script,encoding="utf-8",newline="\n")
    manifest={
        "schema":SCHEMA,"condition_id":condition,
        "modeling_track":"ENGINEERING_SOURCE_CONSERVATION_ONLY",
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "public_view_sha256":digest(visible),
        "source_event_count":generated["policy"]["events_count"],
        "signal":generated["policy"],
        "signal_sha256":generated["policy"]["event_rate_signal_sha256"],
        "nominal_fixture_schema":FIXTURE_SCHEMA,
        "nominal_fixture_sha256":digest(fixture),
        "nominal_parameters":params,
        "nominal_parameters_are_non_empirical":True,
        "solver_image":"openmodelica/openmodelica:v1.26.5-minimal",
        "solver_script_sha256":sha_file(script_file),
        "candidate_count":len(rows),
        "candidates":rows,
        "G2":"NOT_RUN_UNTIL_REAL_CSV",
        "G3":"NOT_RUN","G4":"NOT_RUN","G5":"NOT_RUN",
        "no_model_selection":True,
        "no_EV01_parameter_inference":True,
        "truth_or_holdout_not_accessible":True,
        "provider_calls":0,
    }
    (out/"manifest.json").write_bytes(canonical(manifest)+bytes([10]))
    return manifest


def verify(visible,root):
    root=Path(root)
    m=json.loads((root/"manifest.json").read_text())
    cond=m["condition_id"]
    validate_a1_visible(visible,cond)
    need(m["schema"]==SCHEMA and m["source_snapshot_hash"]==
         visible["source_snapshot_hash"] and
         m["public_view_sha256"]==digest(visible) and
         m["candidate_count"]==6 and m["no_model_selection"] is True and
         m["nominal_parameters_are_non_empirical"] is True and
         m["no_EV01_parameter_inference"] is True and
         m["G3"]==m["G4"]==m["G5"]=="NOT_RUN" and
         m["G2"]=="NOT_RUN_UNTIL_REAL_CSV",
         "RF02G_FALSE_NATIVE_OR_PREVIOUS_G2_CLAIM")
    observed=causal.from_visible(visible,cond)
    need(m["signal"]==observed["signal"] and
         m["signal_sha256"]==observed["signal"]["event_rate_signal_sha256"],
         "RF02G_INPUT_RECONSTRUCTION_CHANGED")
    need(sha_file(root/"simulate.mos")==m["solver_script_sha256"] and
         (root/"INVOCATION_STARTED").read_text().strip()=="INVOCATION_STARTED" and
         (root/"exit_code.txt").read_text().strip()=="0",
         "RF02G_NO_REAL_SOLVER_SUCCESS")
    width=Q(m["signal"]["width_minutes_exact"])
    times=[Q(x) for x in m["signal"]["event_times_minutes_exact"]]
    cutoff=float(Q(m["signal"]["cutoff_minutes_exact"]))
    reports=[]
    for item in m["candidates"]:
        csv=root/(item["csv_prefix"]+"_res.csv")
        model=root/item["modelica_file"]
        need(sha_file(model)==item["modelica_sha256"] and
             csv.is_file() and csv.stat().st_size>500,
             "RF02G_MODEL_OR_SOLVER_OUTPUT_UNAUTHENTICATED")
        rows=oe._rows(csv)
        need(len(rows)>=1000,"RF02G_NOT_ENOUGH_NATIVE_ROWS")
        last_t=-1.0
        last_delivery=-1.0
        last_loss=-1.0
        max_residual=0.0
        for record in rows:
            t=oe._column(record,"time")
            delivery=oe._column(record,"delivered")
            lost=oe._column(record,"lost")
            stocks=[oe._column(record,"s"+str(i+1))
                    for i in range(item["stock_count"])]
            need(t+1e-8>=last_t and -1e-8<=t<=cutoff+1e-7,
                 "RF02G_SOLVER_TIME_OR_CUTOFF")
            need(delivery>=last_delivery-1e-6 and
                 lost>=last_loss-1e-6 and
                 min([delivery,lost]+stocks)>=-1e-6,
                 "RF02G_SOLVER_NEGATIVE_OR_REVERSED_MATERIAL")
            emitted=float(causal.event_mass_until(times,width,Q(str(t))))
            residual=abs(sum(stocks)+delivery+lost-emitted)
            max_residual=max(max_residual,residual)
            last_t,last_delivery,last_loss=t,delivery,lost
        need(abs(oe._column(rows[0],"time"))<=1e-7 and
             abs(last_t-cutoff)<=1e-6,
             "RF02G_NATIVE_TRACE_NOT_COMPLETE")
        need(max_residual<=TOLERANCE_ORDERS,
             "RF02G_MATERIAL_BALANCE_FAILED")
        reports.append({
            "candidate_id":item["candidate_id"],
            "structure_hash":item["structure_hash"],
            "modelica_sha256":item["modelica_sha256"],
            "csv_sha256":sha_file(csv),
            "stock_count":item["stock_count"],
            "loss":item["loss"],
            "output_rows":len(rows),
            "max_mass_residual_orders":max_residual,
            "delivered_end_engineering":last_delivery,
            "lost_end_engineering":last_loss,
            "input_mass_at_cutoff_orders_exact":
                m["signal"]["mass_before_cutoff_orders_exact"],
            "status":"G2_ENGINEERING_MATERIAL_BALANCE_PASS",
            "G3":"NOT_RUN",
        })
    need(len(reports)==6 and
         len({r["structure_hash"] for r in reports})==6,
         "RF02G_NOT_FULL_SIX_CANDIDATES")
    return {
        "schema":REPORT_SCHEMA,
        "condition_id":cond,
        "source_snapshot_hash":m["source_snapshot_hash"],
        "original_method":"D grammar/renderer, versioned external causal input",
        "solver":"OpenModelica real external Docker job",
        "real_solver_invoked_evidenced_by_ci_job":True,
        "solver_exit_code":0,
        "solver_script_sha256":m["solver_script_sha256"],
        "signal_sha256":m["signal_sha256"],
        "nominal_parameters_are_fixtures_not_ev01_estimates":True,
        "expected_mass_at_cutoff_orders_exact":
            m["signal"]["mass_before_cutoff_orders_exact"],
        "mass_deferred_after_cutoff_orders_exact":
            m["signal"]["mass_deferred_after_cutoff_orders_exact"],
        "tolerance_orders_predeclared":TOLERANCE_ORDERS,
        "candidate_count":6,
        "candidates":reports,
        "G2":"PASS_REAL_OMC_ENGINEERING_ONLY",
        "G3":"NOT_RUN","G4":"NOT_RUN","G5":"NOT_RUN",
        "A3":"PARTIAL","scientific_adequacy":"NOT_ESTABLISHED",
        "selection_actor":"NONE",
        "no_compare_with_EV01_deliveries_or_truth":True,
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    p.add_argument("--visible",required=True,type=Path)
    p.add_argument("--condition",required=True,choices=("O0","O1"))
    p.add_argument("--fixture",type=Path)
    p.add_argument("--native-dir",required=True,type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    view=json.loads(args.visible.read_text())
    if args.action=="prepare":
        need(args.fixture is not None,"RF02G_PREPARE_FIXTURE_REQUIRED")
        result=prepare(view,args.condition,
                       json.loads(args.fixture.read_text()),args.native_dir)
    else:
        need(args.out is not None and not args.out.exists(),
             "RF02G_VERIFY_OUT_REFUSE_OVERWRITE")
        result=verify(view,args.native_dir)
        args.out.write_bytes(canonical(result)+bytes([10]))
    print(json.dumps({
        "status":result["G2"],"candidate_count":result["candidate_count"],
        "condition":result["condition_id"],"G3":result["G3"]},sort_keys=True))


if __name__=="__main__":
    main()
