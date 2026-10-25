"""Non-blind CI integration: calibrate two candidates and test OpenModelica parity.

The generator used here is an openly declared fixture. Never use as a blind
experiment, evidence of LLM inference, or demonstration of causal discovery.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .arena_round import prepare, exclusive_json
from .arena_s_calibration import calibrate
from .arena_s_pilot_enumeration import prepare_enumeration, enumeration_submission
from .compose_molecular_candidates import compose
from .fm_b5_parameter_identifiability import sample_times,simulate

ROOT=Path(__file__).resolve().parents[1]


def read(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def setup(out:Path)->None:
    out.mkdir(parents=True,exist_ok=False)
    spec=read(ROOT/"data/synthetic/arena_s_pilot_round_spec.json")
    fit=read(ROOT/"data/synthetic/arena_s_pilot_fit_config.json")
    supports=read(ROOT/"data/synthetic/arena_s_pilot_supports.json")
    plan=read(ROOT/"data/synthetic/fm_b3_dynamic_plan.json")
    plan["candidates"]=plan["candidates"][:2]
    composed=compose(plan,read(ROOT/"data/synthetic/fm_a_structural_candidates.json"))
    cal=fit["calibration"]
    trial_times=sample_times(float(cal["stop_time"]),
                             float(cal["observation_interval"]))
    primary={
        "investigation_id":spec["investigation_id"],"observable_id":"delivered",
        "unit":"units","times":[t-float(cal["stop_time"]) for t in trial_times],
        "calibration_times":trial_times,"independent_trial_reset_at_t0":True,
        "values":simulate(2,1.8,0.8,float(cal["input_amplitude"]),
            float(cal["input_duration"]),float(cal["stop_time"]),
            float(cal["observation_interval"]),
            float(fit["numerics"]["integration_step"])),
        "sources":["CI_PUBLIC_SYNTHETIC_GENERATOR_NOT_BLIND"],
        "input_profile":{"kind":"pulse","amplitude":cal["input_amplitude"],
            "duration":cal["input_duration"],"initial_stocks_zero":True}}
    views=prepare(spec,primary)
    calibrated,eval_plan,fit_receipt=calibrate(composed,plan,fit,primary)
    for name,value in (("original-composed",composed),("original-plan",plan),
        ("calibrated-composed",calibrated),("evaluation-plan",eval_plan),
        ("calibration-receipt",fit_receipt),("primary",primary),
        ("spec",spec),("fit-config",fit),("supports",supports),
        ("D-view",views["D"])):
        exclusive_json(out/(name+".json"),value)
    (out/"calibration").mkdir()
    from .arena_s_pilot_physics import composer_bytes
    (out/"calibration/GeneratedMolecularCandidates.mo").write_bytes(
        composer_bytes(eval_plan,calibrated))
    report=prepare_enumeration(composed,calibrated,plan,eval_plan,supports,
                               fit,primary,fit_receipt,out/"enumeration")
    print(json.dumps({"status":"PUBLIC_CI_CALIBRATED_PREPARED_NOT_EXECUTED",
                      "candidates":report["candidate_ids"]}))


def verify(out:Path)->None:
    keys=("original-composed","original-plan","calibrated-composed",
          "evaluation-plan","calibration-receipt","primary","spec",
          "fit-config","supports","D-view")
    records={key:read(out/(key+".json")) for key in keys}
    r=records
    report=enumeration_submission(
        manifest=read(out/"enumeration/enumeration-plan.json"),
        base_composed=r["original-composed"],
        composed=r["calibrated-composed"],
        base_plan=r["original-plan"],plan=r["evaluation-plan"],
        fit_plan=r["fit-config"],supports=r["supports"],
        fit_receipt=r["calibration-receipt"],
        primary=r["primary"],view=r["D-view"],out=out/"enumeration",
        log=out/"enumeration/openmodelica.log",human_minutes=0,
        composer_file=out/"calibration/GeneratedMolecularCandidates.mo")
    # Both structures are predicted by the SAME solver, after independent
    # construction-only fits. Confirm parameter/solver parity at target times.
    max_gaps={}
    fit=r["fit-config"]; pulse=fit["held_out_discrimination"]
    for candidate in r["calibrated-composed"]["candidates"]:
        cid=candidate["id"]
        n=int(cid.rsplit("-",1)[-1])
        best=r["calibration-receipt"]["fits"][cid]["best_fit"]
        predicted=simulate(n,float(best["maxThroughput"]),float(best["responseTime"]),
            float(pulse["input_amplitude"]),float(pulse["input_duration"]),
            float(pulse["stop_time"]),float(pulse["observation_interval"]),
            float(fit["numerics"]["integration_step"]))
        grid=sample_times(float(pulse["stop_time"]),
                          float(pulse["observation_interval"]))
        csv_path=out/"enumeration"/("b3-cs_0"+str(n)+"_res.csv")
        with csv_path.open(newline="",encoding="utf-8") as stream:
            rows=list(csv.DictReader(stream))
        gaps=[]
        for t,estimate in zip(grid,predicted):
            actual=[float(row["delivered"]) for row in rows
                    if abs(float(row["time"])-t)<=1e-6]
            if not actual:
                raise RuntimeError("MODEL_PARITY_MISSING_GRID_SAMPLE")
            gaps.append(abs(actual[-1]-estimate))
        max_gaps[cid]=max(gaps)
        if max(gaps)>0.03:
            raise RuntimeError("MODEL_RK4_OPENMODELICA_PARITY_FAILED")
    exclusive_json(out/"enumeration/parity.json",{
        "status":"MODEL_PARITY_PASS_PUBLIC_FIXTURE",
        "max_abs_delivered_error":max_gaps,
        "absolute_threshold":0.03,
        "not_a_blind_experiment":True})
    exclusive_json(out/"enumeration/d-submission.json",report)
    print(json.dumps({"status":"PUBLIC_CI_MODEL_PARITY_AND_PULSE_VERIFIED",
                      "max_abs_error":max_gaps}))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["prepare","verify"])
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    (setup if args.action=="prepare" else verify)(args.out)


if __name__=="__main__":
    main()
