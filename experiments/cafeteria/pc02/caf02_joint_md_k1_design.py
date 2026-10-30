#!/usr/bin/env python3
"""CAF-02 joint M+D K1 choice, BEFORE reading any new evidence.

Design objective: chance of reducing compatible parameter hypotheses, NOT
guaranteed family separation. Equal weight to M/D; equal weight per surviving
structure within each arm; equal weight among survivors within each structure.
Hypothetical integer outcomes are rounded model predictions, not posterior
probabilities, real DES outcomes, calibration labels or G4/G5 custody.

One public K1 reset is shared. The K0 observer provides only D5/D10.
This adapter uses existing M and D mathematics without DES or native G2.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import caf02_structural_k0k1k2 as m
import caf02_d_k0k1k2_adapter as d

SCHEMA="igc-caf02-joint-md-k1-evidence-design/0.1"
FAMILIES={"M":("C00","C01"),"D":("D1","D2","D3")}


def require(ok,reason):
    if not ok:
        raise ValueError(reason)


def hash_object(obj):
    return "sha256:"+hashlib.sha256(
        json.dumps(obj,sort_keys=True,separators=(",",":"),
                   allow_nan=False).encode("utf-8")).hexdigest()


def from_public_k0(d5,d10,policy):
    """Explicit two-observation data firewall: no other world K0 readings."""
    d.parse_policy(policy)
    obs=[{"t_min":5,"delivered":d5},{"t_min":10,"delivered":d10}]
    d.parse_observed_k0(obs,policy)
    require(type(d5) is int and type(d10) is int,
            "DES_K0_MUST_BE_TWO_INTEGER_COUNTS")
    grid=policy["candidate_parameters"]
    mgrid={
        "preparation_tau":grid["preparation_tau_minutes"],
        "dispatch_tau":grid["dispatch_tau_minutes"],
        "shared_cap":grid["shared_preparation_dispatch_capacity_orders_per_hour"],
        "transit_tau":grid["transit_tau_minutes_C01"],
    }
    # The trailing zeros are NOT observations; indices 0,1 are the only
    # construction readings passed to fitting.
    mk0=m.k0_calibrate([d5,d10,0,0,0,0],
        policy["k0"]["public_arrival_pulse"]["rate_per_minute"],
        [0,1],mgrid,
        policy["k0"]["model_adequacy_absolute_MAE_orders"],
        policy["k0"]["model_adequacy_relative_to_family_best_MAE_orders"])
    dk0=d.calibrate_k0(obs,policy)
    require(mk0["C00"]["all_evaluated"]==32 and
            mk0["C01"]["all_evaluated"]==96 and
            dk0["candidate_evaluations"]==54,
            "M_D_K0_GRID_COUNT_WRONG")
    return mk0,dk0


def _members(arm,k0,structure):
    return (k0[structure]["eligible"] if arm=="M"
            else k0["compatible"][structure])


def _pred(arm,row,pulse):
    if arm=="M":
        i=m.T_VALUES.index(pulse["t_min"])
        return m.curve(row,pulse["rate_per_minute"])[i]
    return d.predicted(row["stocks"],row["capacity_per_hour"],
             row["shared_response_time_minutes"],
             pulse["rate_per_minute"],(pulse["t_min"],))[0]


def _family_weights(arm,k0):
    families=[f for f in FAMILIES[arm] if _members(arm,k0,f)]
    return {f:1/len(families) for f in families} if families else {}


def _predictions(arm,k0,pulse):
    weights=_family_weights(arm,k0)
    rows=[]
    for family,w in weights.items():
        members=_members(arm,k0,family)
        for row in members:
            rows.append({"family":family,
                         "pred":_pred(arm,row,pulse),
                         "weight":w/len(members)})
    return rows


def _round_integer(x):
    # Deterministic half-up for nonnegative counts; do not use Python's
    # round(x) tie-to-even as an unstated assumption.
    return int(x+.5)


def _expected_reduction(rows,epsilon,maximum_count):
    """Finite hypothetical ensemble, not probabilistic calibration.

    For each candidate-predicted integer outcome, count the *weighted*
    fraction of all candidates that would fail the declared K1 residual
    tolerance. Outcomes arise only from the candidate ensemble, not a
    uniform prior over all physically feasible integer counts.
    """
    if not rows:return None
    require(abs(sum(r["weight"] for r in rows)-1)<1e-9,
            "INVALID_BALANCED_FAMILY_WEIGHTS")
    total=0.0
    min_elimination=1.0
    counter={}
    for origin in rows:
        value=min(maximum_count,max(0,_round_integer(origin["pred"])))
        removed=sum(row["weight"] for row in rows
                    if abs(row["pred"]-value)>epsilon+1e-12)
        total+=origin["weight"]*removed
        min_elimination=min(min_elimination,removed)
        counter[value]=counter.get(value,0)+origin["weight"]
    return {
        "expected_candidate_support_removed_fraction":total,
        "min_removed_fraction_over_hypothetical_outcomes":min_elimination,
        "distinct_hypothetical_integer_counts":sorted(counter),
        "number_nominal_members":len(rows),
        "family_count":len(set(x["family"] for x in rows)),
        "diagnostic_only_not_predictive_probability":True,
    }


def select(mk0,dk0,policy):
    d.parse_policy(policy)
    require(policy["k1"]["selection_version"]=="JOINT_M_D_DESIGN_V1"
            and policy["k1"]["effective_revision_tolerance_orders"]==.77
            and policy["k1"]["trigger"]==
                "EXECUTE_ONE_SHARED_K1_IF_ANY_M_OR_D_K0_CANDIDATE_SURVIVES; OTHERWISE_SKIP",
            "K1_DESIGN_POLICY_INVALID")
    require(dk0["policy_sha256"]==d.digest(policy),
            "D_K0_FOREIGN_OR_TAMPERED_POLICY")
    require(set(mk0)==set(m.FAMILIES)
            and mk0["C00"]["all_evaluated"]==32
            and mk0["C01"]["all_evaluated"]==96,
            "M_K0_WRONG_STRUCTURE_OR_GRID")
    counts={arm:{f:len(_members(arm,k0,f))
                for f in FAMILIES[arm]}
            for arm,k0 in (("M",mk0),("D",dk0))}
    active=[arm for arm in FAMILIES
            if sum(counts[arm].values())>0]
    pp={
        "absolute_residual_max_orders":
            policy["k1"]["absolute_residual_tolerance_orders"],
        "numerical_guard_orders":
            policy["k1"]["numerical_allowance_orders"],
        "effective_revision_tolerance_orders":
            policy["k1"]["effective_revision_tolerance_orders"],
        "minimum_expanded_nonoverlap_gap_orders":
            policy["k1"]["minimum_positive_expanded_gap_orders"],
        "method":policy["k1"]["selection_version"],
    }
    common={
        "schema":SCHEMA,
        "precommitted_policy":pp,
        "K0_fingerprints":{"M":hash_object(mk0),"D":hash_object(dk0)},
        "policy_fingerprint":hash_object(policy),
        "K0_candidate_counts":counts,
        "K1_real_observation_seen":False,
        "single_shared_K1":True,
        "no_guarantee_of_structural_identification":True,
    }
    if not active:
        return {**common,"status":"K1_NO_ADEQUATE_HYPOTHESIS_NO_TRIAL",
                "proposed_measurement":None,"all_menu_scores":[],
                "reason":"NEITHER_ARM_HAS_ANY_COMPATIBLE_K0_CANDIDATE"}
    eps=pp["effective_revision_tolerance_orders"]
    scored=[]
    for option in policy["k1"]["menu"]:
        pulse={"rate_per_minute":option["rate_per_minute"],
               "t_min":option["t_min"]}
        bound=int(option["rate_per_minute"]*min(option["t_min"],20))
        require(bound>=0 and
                option["rate_per_minute"]*min(option["t_min"],20)==bound,
                "K1_DES_ACCEPTED_COUNT_MUST_BE_INTEGER")
        arm_reports={}
        for arm,k0 in (("M",mk0),("D",dk0)):
            arm_reports[arm]=_expected_reduction(
                _predictions(arm,k0,pulse),eps,bound)
        joint=sum(arm_reports[arm]["expected_candidate_support_removed_fraction"]
                  for arm in active)/len(active)
        # Preserve full-family guarantee diagnostic separately, with original
        # no-overlap rule. Its failure NEVER prevents K1 acquisition.
        if all(mk0[f]["eligible"] for f in m.FAMILIES):
            i=m.T_VALUES.index(pulse["t_min"])
            first=m.observable_envelope(mk0["C00"]["eligible"],
                                       pulse["rate_per_minute"],i)
            second=m.observable_envelope(mk0["C01"]["eligible"],
                                        pulse["rate_per_minute"],i)
            separation=m.expanded_interval_separation(
                first,second,pp["absolute_residual_max_orders"],
                pp["numerical_guard_orders"])
            robust=separation["expanded_gap_orders"]
        else:robust=None
        scored.append({
            "measurement":pulse,
            "joint_expected_removed_fraction":joint,
            "M":arm_reports["M"],"D":arm_reports["D"],
            "M_full_family_expanded_robust_gap_orders":robust,
            "M_structural_guarantee_in_current_menu":
                robust is not None and robust>=
                    pp["minimum_expanded_nonoverlap_gap_orders"]
                    and robust>0,
        })
    index,item=max(enumerate(scored),
                   key=lambda x:(x[1]["joint_expected_removed_fraction"],-x[0]))
    return {
        **common,
        "status":("K1_PRECOMMITTED_POTENTIAL_HYPOTHESIS_REDUCTION"
                  if item["joint_expected_removed_fraction"]>1e-12
                  else "K1_PRECOMMITTED_NO_MODELLED_REDUCTION_ADEQUACY_TEST"),
        "proposed_measurement":item["measurement"],
        "all_menu_scores":scored,
        "selected_menu_index":index,
        "expected_reduction_is_not_identification":True,
        "selection_uses_equal_arm_weights":len(active)==2,
        "precommitted_policy_does_not_depend_on_K1_result":True,
    }


def audit_admissible_integer_k0(policy):
    """Exhaustive input-space SOFTWARE scan, not synthetic world testing.

    The public K0 accepts at most 6 at t5 and 12 at t10. Enumeration of
    all nondecreasing integer pairs is 70. Does not read DES or K2 data.
    """
    results=[]
    for a in range(7):
        for b in range(a,13):
            mk0,dk0=from_public_k0(a,b,policy)
            decision=select(mk0,dk0,policy)
            results.append({
                "K0_D5":a,"K0_D10":b,
                "M_two_families":all(mk0[f]["eligible"] for f in m.FAMILIES),
                "D_any":bool(d.all_survivors(dk0)),
                "any_survivor":any(
                    sum(v.values())>0 for v in
                    decision["K0_candidate_counts"].values()),
                "K1_status":decision["status"],
                "K1_chosen":decision["proposed_measurement"],
                "K1_joint_expected_removed_fraction":
                    (max((x["joint_expected_removed_fraction"] for x in
                          decision["all_menu_scores"]),default=None)),
            })
    require(len(results)==70,"K0_ADMISSIBLE_DOMAIN_ENUMERATION_MISMATCH")
    summary={
        "admissible_pairs":len(results),
        "M_both_families":sum(x["M_two_families"] for x in results),
        "no_adequate_hypothesis_both_arms":sum(not x["any_survivor"]
                                               for x in results),
        "K1_precommitted":sum(x["K1_chosen"] is not None for x in results),
        "K1_predicted_candidate_reduction_positive":sum(
            x["K1_status"]=="K1_PRECOMMITTED_POTENTIAL_HYPOTHESIS_REDUCTION"
            for x in results),
        "K1_precommitted_without_predicted_reduction":sum(
            x["K1_status"]=="K1_PRECOMMITTED_NO_MODELLED_REDUCTION_ADEQUACY_TEST"
            for x in results),
        "truth_K1_seen":False,
        "DES_runs":0,"OMC_runs":0,"provider_calls":0,"K2_truth_seen":False,
    }
    return {"schema":SCHEMA,"status":"OFFLINE_FULL_INPUT_SPACE_AUDIT_ONLY",
            "summary":summary,"rows":results}


if __name__=="__main__":
    p=json.loads(d.POLICY.read_text())
    data=audit_admissible_integer_k0(p)
    print(json.dumps(data["summary"],sort_keys=True))
    print("CAF02_JOINT_MD_K1_DESIGN_AUDIT_NO_DES_NO_K2")
