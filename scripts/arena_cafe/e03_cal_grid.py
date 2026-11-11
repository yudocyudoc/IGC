"""E03: externally attributed finite calibration grids, never native method learning.

One synthetic EV-01 public development world, O0/O1 paired views; the single
causal right-hand half-minute source remains fixed. Never read private DES,
Buffalo outputs or reserve. Original D and original E1 are imported unchanged.

D: 81 (three chain lengths x [no-loss 9 + loss 18] parameter sets).
M: 54 (six full E1 AST x 3 throughput x 3 response). The six original
20/hour,0.5-hour M AST and signal exact-match historical verified G2 and are
reused, not rerun. D historical fixture 1.23/2.7/8.1 is NOT on the E03 grid.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
from fractions import Fraction
from itertools import product
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_cafe import r2_causal_pos_signal as causal
from scripts.arena_cafe import r2_causal_g2 as d_g2
from scripts.arena_cafe import r2_m_six_causal_g2 as m_g2
from scripts.arena_cafe import observation_eval as oe
from scripts.arena_cafe import r2_observational_contracts as r2
from scripts.arena_m_short_e1 import get_composer
from scripts.arena_m_visible_pulse import backend, stimulus_only_replace

SCHEMA="igc-arena-e03-calibration-grid/0.1"
SCORE_SCHEMA="igc-arena-e03-calibration-scores/0.1"
D_GRID={"capacity_orders_min":[0.5,1.0,2.0],
        "response_minutes":[0.25,1.0,4.0],
        "loss_minutes_if_loss":[2.0,8.0]}
M_GRID={"maxThroughput_orders_hour":[20,60,100],
        "responseTime_hours":[0.1,0.5,1.0],
        "roles":["preparation","dispatch"]}
BANDS=(0.0,1.0,2.0)
CUTS=(0.,2.,4.,6.,8.,10.)
OBSERVED=(0,0,2,4,6,8)
TOL_MASS_ORDERS=0.08
ROOT=Path(__file__).resolve().parents[2]


def sha_file(path):
    return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_public(path):
    view=json.loads(Path(path).read_text(encoding="utf-8"))
    validate_a1_visible(view,"O0")
    points=view["construction"]["observation_series"]
    need(tuple(float(x["t_minutes_exact"]) for x in points)==CUTS and
         tuple(x["delivered_cumulative"] for x in points)==OBSERVED,
         "E03_DEVELOPMENT_OBSERVABLE_CHANGED")
    return view


def _base(arm,view):
    need(arm in ("D","M"),"E03_UNRECOGNIZED_ARM")
    signal=causal.from_visible(view,"O0")["signal"]
    need(signal["width_minutes_exact"]=="1/2" and
         signal["events_count"]==15 and
         signal["policy"]==causal.POLICY and
         signal["mass_before_cutoff_orders_exact"]=="15" and
         signal["mass_deferred_after_cutoff_orders_exact"]=="0",
         "E03_SHARED_CAUSAL_STIMULUS_CHANGED")
    need(r2.original_source_checks() is True,"E03_D_SOURCE_NOT_PINNED")
    need(m_g2.source_integrity() is True,"E03_M_SOURCE_NOT_PINNED")
    return {"schema":SCHEMA,"arm":arm,"condition":"O0",
            "origin":"EXTERNAL_FINITE_GRID_NOT_ORIGINAL_METHOD_INFERENCE",
            "source_snapshot_hash":view["source_snapshot_hash"],
            "public_view_sha256":digest(view),
            "signal_sha256":signal["event_rate_signal_sha256"],
            "signal":signal,"grid":D_GRID if arm=="D" else M_GRID,
            "bands_max_absolute_orders":list(BANDS),
            "sampling_minutes":list(CUTS),"observed_deliveries":list(OBSERVED),
            "source_blobs":{"D":r2.D_GIT_BLOB,
                            "M_registry":r2.REGISTRY_GIT_BLOB},
            "evidence":"SYNTHETIC_EV01_DEVELOPMENT_ONLY",
            "initial_method":"E02_D_M_UNCALIBRATED_BASELINES_SEPARATE",
            "Buffalo_calls":0,"scientific_structure_identification":False,
            "G4":"NOT_RUN","G5":"NOT_RUN"}


def _d_nominals(cap, response, loss):
    return {key:{"value":value,"unit":unit,"status":"ASSUMED",
                 "actor":"INVESTIGATOR","source_kind":"EXPLICIT_UNVALIDATED_ASSUMPTION",
                 "source_ref":"E03-EXTERNAL-D-CAL-GRID-0.1"}
            for key,value,unit in (
                ("capacity",cap,"orders/minute"),
                ("response_time",response,"minute"),
                ("loss_time",loss,"minute"))}


def prepare_d(view, out):
    base=_base("D",view)
    out=Path(out)
    need(not out.exists(),"E03_REFUSE_OVERWRITE")
    out.mkdir(parents=True)
    items=[]
    # Render once per nominal set with existing D source/extension; only use
    # loss_time=2 in no-loss models (the inactive parameter is not counted twice).
    for cap,response,loss in product(D_GRID["capacity_orders_min"],
                                      D_GRID["response_minutes"],
                                      D_GRID["loss_minutes_if_loss"]):
        render=causal.render_six_with_declared_nominals(
            view,"O0",_d_nominals(cap,response,loss))
        need(render["candidate_count"]==6,"E03_D_NOT_SIX_STRUCTURES")
        for structure in render["candidates"]:
            original_loss=bool(structure["structure"]["loss"]) if "structure" in structure else None
            # Rendering stores structure_hash but not its topology; resolve via
            # original grammar fixed 1,2,3 stocks/no-loss,loss ordering.
            if original_loss is None:
                grammar=r2._grammar({"max_stocks":3,"allow_loss":True,
                                   "max_candidates":6,"max_simulations":0})
                match=[x for x in grammar if x["structure_hash"]==structure["structure_hash"]]
                need(len(match)==1,"E03_D_NATIVE_TOPOLOGY_UNKNOWN")
                original_loss=bool(match[0]["structure"]["loss"])
                n=len(match[0]["structure"]["stocks"])
            else:
                n=len(structure["structure"]["stocks"])
            if not original_loss and loss!=D_GRID["loss_minutes_if_loss"][0]:
                continue
            index=len(items)
            name=f"E03D_{index:03d}"
            original_name=structure["model_name"]
            source=structure["modelica"]
            need(source.count("model "+original_name+"\n")==1 and
                 source.count("end "+original_name+";")==1 and
                 "  inputRate = " in source,"E03_D_NATIVE_RENDER_UNEXPECTED")
            renamed=source.replace("model "+original_name+"\n",
                                   "model "+name+"\n",1).replace(
                                    "end "+original_name+";","end "+name+";",1)
            # No equation changes. Class-name substitution is the only edit.
            need(renamed.replace("model "+name+"\n","model "+original_name+"\n",1)
                 .replace("end "+name+";","end "+original_name+";",1)==source,
                 "E03_D_NON_NAME_SOURCE_MUTATION")
            file=out/(name+".mo")
            file.write_text(renamed,encoding="utf-8",newline="\n")
            items.append({"id":name,"native_structure_hash":structure["structure_hash"],
                          "native_candidate_id":structure["candidate_id"],
                          "stock_count":n,"loss":original_loss,
                          "parameters":{"capacity":cap,"response_time":response,
                                        "loss_time":loss if original_loss else "INACTIVE_DEFAULT_2"},
                          "modelica_file":file.name,"modelica_sha256":sha_file(file),
                          "csv_prefix":name,
                          "G2":"NOT_RUN","origin":"EXTERNAL_GRID",
                          "equations":"ORIGINAL_D_UNCHANGED_EXCEPT_CAUSAL_STIMULUS"})
    need(len(items)==81 and len({x["id"] for x in items})==81,
         "E03_D_EXACT_81_VARIANTS_REQUIRED")
    source= ["getVersion();"]
    for x in items:
        name=x["id"]
        source.extend([f'loadFile("{name}.mo");',f'checkModel({name});',
                       'print(getErrorString());',
                       f'simulate({name},startTime=0,stopTime=10,'+
                       'numberOfIntervals=2000,method="dassl",tolerance=1e-9,'+
                       f'outputFormat="csv",fileNamePrefix="{name}");',
                       'print(getErrorString());'])
    script=out/"simulate.mos"
    script.write_text("\n".join(source)+"\n",encoding="utf-8",newline="\n")
    manifest={**base,"candidate_count":81,"new_solver_targets":81,
              "exact_reused":0,"candidates":items,
              "script_sha256":sha_file(script),"source_provenance":{
                "engine":"scripts.arena_d_v01.modelica via r2_causal_pos_signal",
                "nominals":"EXPLICIT_UNVALIDATED_ASSUMPTION_NOT_OPERATIONS_DATA",
                "original_D_G2_fixture":"NOT_REUSED_VALUES_NOT_ON_GRID"},
              "modelica_target":"D-original-six-structure-grammar"}
    (out/"manifest.json").write_bytes(canonical(manifest)+b"\n")
    return manifest


def prepare_m(view,out,historical_m):
    base=_base("M",view)
    out=Path(out)
    need(not out.exists(),"E03_REFUSE_OVERWRITE")
    # Validate historical original six CSV and source BEFORE any reuse.
    verified=m_g2.verify(view,Path(historical_m))
    need(verified["G2"]=="PASS_REAL_OMC_ENGINEERING_ONLY" and
         verified["candidate_count"]==6 and
         verified["same_causal_signal_hash_as_D"]==base["signal_sha256"],
         "E03_M_BASELINE_NOT_REUSABLE")
    old=json.loads((Path(historical_m)/"manifest.json").read_text())
    c=get_composer()
    cfg,classes,_=c.load_registry(r2.BASE_PATH)
    orig=c.enumerate_graphs(cfg,classes)
    need(len(orig)==6 and len(old["candidates"])==6,
         "E03_M_NOT_SIX_ORIGINAL_GRAPHS")
    out.mkdir(parents=True)
    generated=[]
    items=[]
    for j,(key,original) in enumerate(orig):
        old_row=old["candidates"][j]
        need(key==old_row["canonical_sha256"] and
             digest(original)==old_row["full_ast_sha256"] and
             original==old_row["original_ast"],"E03_M_HISTORICAL_AST_DRIFT")
        for throughput,response in product(M_GRID["maxThroughput_orders_hour"],
                                           M_GRID["responseTime_hours"]):
            graph=copy.deepcopy(original)
            changed=[]
            for node in graph["instances"]:
                if node["role"] in M_GRID["roles"]:
                    need(node["class_id"]=="bounded-queue" and
                         set(node["parameters"])=={"maxThroughput","responseTime"},
                         "E03_M_DIFFERENT_COMPONENT_TYPE")
                    node["parameters"]["maxThroughput"]=throughput
                    node["parameters"]["responseTime"]=response
                    changed.append(node["role"])
                else:
                    need(node["parameters"]==next(x["parameters"] for x in original["instances"]
                                                      if x["id"]==node["id"]),
                         "E03_M_OTHER_ROLE_MUTATED")
            need(sorted(changed)==["dispatch","preparation"],
                 "E03_M_MANDATORY_ROLES_MISSING")
            c.check_graph(graph,cfg,classes)
            index=len(items)
            name=f"E03M_{index:03d}"
            rendered=backend.render_model(name,graph,cfg,classes)
            baseline=stimulus_only_replace(rendered,1.0,1.0)
            need(baseline.count(m_g2.PULSE_STIMULUS)==1,
                 "E03_M_ORIGINAL_STIMULUS_MISSING")
            adapted=baseline.replace(m_g2.PULSE_STIMULUS,
                "    Modelica.Blocks.Sources.RealExpression stimulus(y="+
                m_g2._expression_hours(base["signal"])+");")
            need("der(" not in adapted and "when " not in adapted and
                 "    deliveredTotal=" in adapted and "    reportedDeliveryRate=" in adapted and
                 baseline.replace(m_g2.PULSE_STIMULUS,"<SIGNAL>")==
                 adapted.replace("    Modelica.Blocks.Sources.RealExpression stimulus(y="+
                                  m_g2._expression_hours(base["signal"])+");","<SIGNAL>"),
                 "E03_M_NON_STIMULUS_SOURCE_MUTATION")
            reused=(throughput==20.0 and response==0.5)
            if reused:
                need(graph==original,"E03_M_BASELINE_REUSED_BUT_AST_NOT_EXACT")
                # Compare rendered original E1 body with historical Modelica
                # after canonical name-only replacement, not with a projection.
                _,_,orig_rows,orig_source=m_g2._original_models(view,"O0")
                hist_name=orig_rows[j]["model_name"]
                current_named=adapted.replace(f"  model {name}\n",
                                               f"  model {hist_name}\n",1).replace(
                                                f"  end {name};",f"  end {hist_name};",1)
                need(current_named in orig_source,
                     "E03_M_BASELINE_MODEL_SOURCE_NOT_EXACT")
                original_csv=Path(historical_m)/(old_row["csv_prefix"]+"_res.csv")
                target=out/(name+"_res.csv")
                shutil.copyfile(original_csv,target)
                need(sha_file(target)==sha_file(original_csv),
                     "E03_M_HISTORICAL_BYTES_CHANGED")
            else:
                generated.append(adapted)
            items.append({"id":name,"native_base_ast_sha256":digest(original),
                          "native_canonical_sha256":key,
                          "full_variant_ast_sha256":digest(graph),
                          "variant_ast":graph,
                          "parameters":{"maxThroughput":throughput,
                                        "responseTime":response,
                                        "roles":"preparation+dispatch jointly"},
                          "csv_prefix":name,"origin":"HISTORICAL_EXACT_G2_REUSE" if reused
                                                    else "EXTERNAL_GRID_NEW_SOLVER",
                          "historical_csv_sha256":sha_file(target) if reused else None,
                          "G2":"VERIFIED_REUSED_G2" if reused else "NOT_RUN"})
    need(len(items)==54 and len(generated)==48 and
         sum(x["origin"]=="HISTORICAL_EXACT_G2_REUSE" for x in items)==6,
         "E03_M_GRID_NOT_54_OR_REUSE_NOT_6")
    generated_ids=[x for x in items if x["origin"]=="EXTERNAL_GRID_NEW_SOLVER"]
    package="\n".join(["within;","package ArenaE03M","\n\n".join(generated),
         '  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));',
         "end ArenaE03M;",""])
    file=out/"native.mo"
    file.write_text(package,encoding="utf-8",newline="\n")
    cutoff=Fraction(base["signal"]["cutoff_minutes_exact"])/60
    script=["getVersion();",'loadFile("/repo/src/modelica/IGCMolecules.mo");',
            'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");',
            'loadFile("native.mo");']
    for item in generated_ids:
        name="ArenaE03M."+item["id"]
        script.extend([f"checkModel({name});","print(getErrorString());",
                       f'simulate({name},startTime=0,stopTime={causal._real(cutoff)},'+
                       'numberOfIntervals=2000,method="dassl",tolerance=1e-9,'+
                       f'outputFormat="csv",fileNamePrefix="{item["csv_prefix"]}");',
                       "print(getErrorString());"])
    mos=out/"simulate.mos"
    mos.write_text("\n".join(script)+"\n",encoding="utf-8",newline="\n")
    manifest={**base,"candidate_count":54,"new_solver_targets":48,
              "exact_reused":6,"candidates":items,
              "script_sha256":sha_file(mos),"modelica_sha256":sha_file(file),
              "source_provenance":{"engine":"ORIGINAL_SHORT_E1_backend.render_model",
                "historical_G2":"41591727790",
                "reused_by":"FULL_AST_PARAMETER_IDENTITY_CAUSAL_INPUT_AND_CSV_HASH",
                "other_roles":"FIXED_ORIGINAL_BASE_PARAMETERS",
                "variant_policy":"EXTERNAL_FINITE_GRID_NOT_NATIVE_E1_INFERENCE"}}
    (out/"manifest.json").write_bytes(canonical(manifest)+b"\n")
    return manifest


def _score_row(item, arm, path, signal):
    """One vector for ONE full parameterization; no marginal-envelope shortcut."""
    rows=oe._rows(path)
    need(len(rows)>=1000,"E03_G2_TRACE_TOO_SHORT")
    time_factor=1 if arm=="D" else 60
    delivered_name="delivered" if arm=="D" else "deliveredTotal"
    if arm=="D":
        stock_ports=["s"+str(i) for i in range(1,item["stock_count"]+1)]
    else:
        stock_ports=m_g2._all_material_queue_stock_ports({"original_ast":item["variant_ast"]})
    times=[float(Fraction(t)) for t in signal["event_times_minutes_exact"]]
    width=float(Fraction(signal["width_minutes_exact"]))
    samples={}
    prev_time=-1
    prev_delivered=-1
    max_mass_error=0.0
    for row in rows:
        t=oe._column(row,"time")*time_factor
        val=oe._column(row,delivered_name)
        stocks=[oe._column(row,x) for x in stock_ports]
        lost=oe._column(row,"lost") if arm=="D" else 0.0
        need(t>=prev_time-1e-7 and t>=-1e-7 and t<=10+1e-6 and
             val>=prev_delivered-1e-6 and min([val,lost]+stocks)>=-1e-6,
             "E03_NONPHYSICAL_NEGATIVE_OR_TIME_REVERSE")
        injected=sum(min(width,max(0.,t-x))/width for x in times)
        max_mass_error=max(max_mass_error,abs(sum(stocks)+lost+val-injected))
        for cut in CUTS:
            if abs(t-cut)<1e-7:
                if cut in samples:
                    need(abs(samples[cut]-val)<=1e-5,"E03_DISCONTINUOUS_DELIVERED_AT_OBSERVATION")
                samples[cut]=val
        prev_time=t
        prev_delivered=val
    need(abs(prev_time-10.)<=1e-6 and
         len(samples)==len(CUTS) and abs(oe._column(rows[0],"time"))<=1e-8,
         "E03_MISSING_OBSERVATION_CUT_OR_END")
    need(max_mass_error<=TOL_MASS_ORDERS,"E03_MATERIAL_CONSERVATION_FAIL")
    predicted=[samples[t] for t in CUTS]
    residuals=[a-b for a,b in zip(predicted,OBSERVED)]
    max_abs=max(abs(x) for x in residuals)
    return {"status":"G2_PASS_DESCRIPTIVE_G3_DEVELOPMENT_ONLY",
            "delivered_at_six_cuts":[round(x,7) for x in predicted],
            "residuals":[round(x,7) for x in residuals],
            "MAE":round(sum(abs(x) for x in residuals)/6,7),
            "RMSE":round(math.sqrt(sum(x*x for x in residuals)/6),7),
            "max_abs":round(max_abs,7),
            "bands":{str(int(b)):max_abs<=b+1e-8 for b in BANDS},
            "G2_max_mass_error":round(max_mass_error,7),
            "csv_sha256":sha_file(path),"output_rows":len(rows)}


def evaluate(arm,view,root):
    root=Path(root)
    manifest=json.loads((root/"manifest.json").read_text())
    need(manifest["schema"]==SCHEMA and manifest["arm"]==arm and
         manifest["source_snapshot_hash"]==view["source_snapshot_hash"] and
         manifest["public_view_sha256"]==digest(view) and
         manifest["signal"]==causal.from_visible(view,"O0")["signal"] and
         manifest["candidate_count"]=={"D":81,"M":54}[arm] and
         manifest["new_solver_targets"]=={"D":81,"M":48}[arm] and
         manifest["exact_reused"]=={"D":0,"M":6}[arm],
         "E03_MANIFEST_DOES_NOT_MATCH_PINNED_GRID")
    need(sha_file(root/"simulate.mos")==manifest["script_sha256"] and
         (root/"INVOCATION_STARTED").read_text().strip()=="INVOCATION_STARTED" and
         (root/"exit_code.txt").read_text().strip()=="0",
         "E03_NO_AUTHENTIC_SOLVER_INVOCATION")
    if arm=="M":
        need(sha_file(root/"native.mo")==manifest["modelica_sha256"],
             "E03_M_SOURCE_HASH_DRIFT")
    else:
        need(all(sha_file(root/x["modelica_file"])==x["modelica_sha256"]
                 for x in manifest["candidates"]),"E03_D_SOURCE_HASH_DRIFT")
    results=[]
    for item in manifest["candidates"]:
        path=root/(item["csv_prefix"]+"_res.csv")
        if not path.is_file():
            results.append({"id":item["id"],"parameters":item["parameters"],
                            "origin":item["origin"],"status":"MISSING_SOLVER_CSV"})
            continue
        try:
            diag=_score_row(item,arm,path,manifest["signal"])
            if item.get("historical_csv_sha256"):
                need(diag["csv_sha256"]==item["historical_csv_sha256"],
                     "E03_REUSED_HISTORICAL_CSV_CHANGED")
            results.append({"id":item["id"],"parameters":item["parameters"],
                            "origin":item["origin"],**diag})
        except (ValueError,KeyError,IndexError,AssertionError) as exc:
            results.append({"id":item["id"],"parameters":item["parameters"],
                            "origin":item["origin"],"status":"G2_OR_OPERATOR_FAIL",
                            "reason":str(exc)})
    comparable=[x for x in results if x["status"]=="G2_PASS_DESCRIPTIVE_G3_DEVELOPMENT_ONLY"]
    sets={str(int(b)):[x["id"] for x in comparable if x["bands"][str(int(b))]]
          for b in BANDS}
    report={"schema":SCORE_SCHEMA,"arm":arm,
            "status":"FINITE_GRID_COMPLETE" if len(comparable)==len(results)
                     else "FINITE_GRID_PARTIAL_WITH_FAILURES",
            "candidate_count":len(results),"comparable_count":len(comparable),
            "not_comparable_count":len(results)-len(comparable),
            "new_omc_targets":manifest["new_solver_targets"],
            "historical_exact_reused":manifest["exact_reused"],
            "bands_max_abs_orders":[0,1,2],"compatible_sets":sets,
            "candidate_scores":results,
            "common_observed_vector":list(OBSERVED),
            "G3":"DESCRIPTIVE_ON_DEVELOPMENT_NO_SCIENTIFIC_IDENTITY",
            "method_original_untouched":True,
            "parameter_origin":"EXTERNAL_EXPLICIT_UNVALIDATED_GRID",
            "no_best_only_selection":True,
            "no_marginal_envelope_combination":True,"G4":"NOT_RUN","G5":"NOT_RUN",
            "no_buffalo_inference":True,
            "source_snapshot_hash":view["source_snapshot_hash"]}
    (root/"scores.json").write_bytes(canonical(report)+b"\n")
    return report


def combine(d_report,m_report,e02_report):
    need(d_report["arm"]=="D" and m_report["arm"]=="M" and
         d_report["source_snapshot_hash"]==m_report["source_snapshot_hash"],
         "E03_MISMATCHED_CONSTRUCTION")
    need(e02_report["schema"]=="igc-arena-cafe-continuity-e02-development/0.1" and
         e02_report["Buffalo"]["provider_calls"]==0 and
         e02_report["conditions"]["O0"]["D"]["candidate_count"]==6 and
         e02_report["conditions"]["O0"]["M"]["candidate_count"]==6,
         "E03_E02_BASELINE_INVALID")
    old={arm:[r["diagnostic"] for r in e02_report["conditions"]["O0"][arm]["H_j"]]
         for arm in ("D","M")}
    baseline={arm:{"min_RMSE":min(x["RMSE"] for x in rows),
                   "max_RMSE":max(x["RMSE"] for x in rows),
                   "model_count":len(rows),
                   "status":"ORIGINAL_NOMINALS_NOT_EMPIRICAL"}
              for arm,rows in old.items()}
    return {"schema":"igc-arena-e03-joint-summary/0.1",
            "status":"FINITE_EXTERNAL_GRID_COMPLETE" if d_report["status"]==
              m_report["status"]=="FINITE_GRID_COMPLETE" else "PARTIAL_WITH_FAILURES",
            "original_E02_unfitted_baselines":baseline,
            "calibration":{"D":{k:d_report[k] for k in
                               ("candidate_count","comparable_count","compatible_sets")},
                           "M":{k:m_report[k] for k in
                               ("candidate_count","comparable_count","compatible_sets")}},
            "budget":{"new_OMC":d_report["new_omc_targets"]+
                     m_report["new_omc_targets"],
                     "historical_reused":m_report["historical_exact_reused"],
                     "max_new_OMC":135,"Buffalo":0},
            "band_1_is_development_operational_not_sensor_resolution":True,
            "comparability_is_conditional_on_trajectory_semantics":True,
            "no_new_hidden_world_or_prospective_claims":True,
            "no_selection_across_arms_or_outside_grid":True,
            "G4":"NOT_RUN","G5":"NOT_RUN"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare-d","prepare-m","score-d","score-m","combine"))
    p.add_argument("--public",type=Path)
    p.add_argument("--historical-m",type=Path)
    p.add_argument("--root",type=Path)
    p.add_argument("--d-score",type=Path)
    p.add_argument("--m-score",type=Path)
    p.add_argument("--e02",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.action=="combine":
        need(all(x is not None for x in (a.d_score,a.m_score,a.e02,a.out)),
             "E03_JOIN_MISSING_INPUT")
        need(not a.out.exists(),"E03_REFUSE_OVERWRITE")
        report=combine(*[json.loads(x.read_text())
                         for x in (a.d_score,a.m_score,a.e02)])
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_bytes(canonical(report)+b"\n")
    else:
        need(a.public is not None and a.root is not None,"E03_SOURCE_MISSING")
        view=load_public(a.public)
        if a.action=="prepare-d": report=prepare_d(view,a.root)
        elif a.action=="prepare-m":
            need(a.historical_m is not None,"E03_M_NEEDS_PROVEN_HISTORICAL")
            report=prepare_m(view,a.root,a.historical_m)
        else:
            report=evaluate("D" if a.action=="score-d" else "M",view,a.root)
    print(json.dumps({"action":a.action,"status":report.get("status","PREPARED"),
                      "candidates":report.get("candidate_count"),
                      "new":report.get("new_solver_targets"),
                      "reused":report.get("exact_reused")},sort_keys=True))


if __name__=="__main__":
    main()