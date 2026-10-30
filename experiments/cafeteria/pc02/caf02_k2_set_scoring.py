"""CAF-02 prospective K2 loss contract (software-only, no truth or DES access).

Scoring is intentionally deterministic and NON-PROBABILISTIC:
  L(y,[lo,hi]) = (hi-lo)/2 + max(lo-y, 0, y-hi)
For a singleton [m,m], L = |m-y| (the reference MAE component).
Do NOT call these parameter-compatibility envelopes 80/95% prediction
intervals. Abstention is not a zero-error forecast. All policy parameters
must be locked independently before any new K2 truth is accessible.
"""
import math

TIMES=(5,10,15,20,30,40)


class InvalidK2Score(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise InvalidK2Score(code)


def finite(x):
    return type(x) in (float,int) and math.isfinite(x)


def validate_curve(values):
    need(type(values) in (tuple,list)
         and len(values)==len(TIMES)
         and all(finite(x) and x>=0 for x in values)
         and all(a<=b+1e-10 for a,b in zip(values,values[1:])),
         "INVALID_CUMULATIVE_DELIVERY_CURVE")


def summarize_envelope(lower,upper,truth,point_max_width=2.0):
    """Score a NONEMPTY set of physically valid cumulative outputs."""
    if lower is None and upper is None:
        return {"status":"ABSTAIN_NO_CANDIDATE","set_loss_mean":None,
                "point_MAE":None,"point_RMSE":None,"coverage_count":None}
    validate_curve(lower)
    validate_curve(upper)
    validate_curve(truth)
    need(finite(point_max_width) and point_max_width>=0,
         "INVALID_POINT_WIDTH_POLICY")
    need(all(l<=u+1e-10 for l,u in zip(lower,upper)),
         "LOWER_GREATER_THAN_UPPER")
    widths=[u-l for l,u in zip(lower,upper)]
    misses=[max(l-y,0,y-u) for l,u,y in zip(lower,upper,truth)]
    value=sum(0.5*w+d for w,d in zip(widths,misses))/len(TIMES)
    point_allowed=max(widths)<=point_max_width
    mid=[(l+u)/2 for l,u in zip(lower,upper)]
    mae=sum(abs(m-y) for m,y in zip(mid,truth))/len(TIMES) if point_allowed else None
    rmse=(sum((m-y)**2 for m,y in zip(mid,truth))/len(TIMES))**.5 if point_allowed else None
    return {
        "status":"POINT_ELIGIBLE" if point_allowed
        else "SET_ONLY_POINT_ABSTENTION",
        "set_loss_mean":value,
        "mean_envelope_width_orders":sum(widths)/len(TIMES),
        "max_envelope_width_orders":max(widths),
        "outside_envelope_distance_mean_orders":sum(misses)/len(TIMES),
        "coverage_count":sum(l<=y<=u for l,u,y in zip(lower,upper,truth)),
        "n_scored_times":len(TIMES),
        "point_MAE":mae,
        "point_RMSE":rmse,
        "set_score_interpretation":"NON_PROBABILISTIC_WIDTH_PLUS_DISTANCE",
    }


def combine_family_envelopes(family_envelopes):
    """Unite ALL eligible structural families without picking a winner."""
    need(type(family_envelopes) is dict
         and set(family_envelopes)=={"C00","C01"},
         "MISSING_C00_C01_FAMILY_ENVELOPES")
    active=[x for x in family_envelopes.values() if x is not None]
    if not active:
        return None,None
    for a in active:
        need(type(a) is dict and set(a)>= {"lower","upper","candidate_count"}
             and type(a["candidate_count"]) is int
             and a["candidate_count"]>0,
             "BAD_COMPATIBLE_FAMILY_ENVELOPE")
        validate_curve(a["lower"])
        validate_curve(a["upper"])
    return (
        [min(x["lower"][i] for x in active) for i in range(len(TIMES))],
        [max(x["upper"][i] for x in active) for i in range(len(TIMES))],
    )


def adjudicate(k0_by_family,k1_by_family,ref_caf,ref_scale,truth,
              min_improvement=.25,point_max_width=2.0):
    """One K2 truth for ALL methods, with paired nonempty K0/K1 comparison.

    This function takes arrays only and performs no GitHub/data fetching.
    It does NOT prove external witness/custody or truth independence.
    """
    need(finite(min_improvement) and min_improvement>=0,
         "BAD_SUCCESS_MARGIN")
    validate_curve(ref_caf)
    validate_curve(ref_scale)
    validate_curve(truth)
    lo0,up0=combine_family_envelopes(k0_by_family)
    lo1,up1=combine_family_envelopes(k1_by_family)
    k0=summarize_envelope(lo0,up0,truth,point_max_width)
    k1=summarize_envelope(lo1,up1,truth,point_max_width)
    ref0=summarize_envelope(ref_caf,ref_caf,truth,point_max_width)
    ref1=summarize_envelope(ref_scale,ref_scale,truth,point_max_width)
    paired=(k0["set_loss_mean"] is not None and
            k1["set_loss_mean"] is not None)
    gain=(k0["set_loss_mean"]-k1["set_loss_mean"]) if paired else None
    return {
        "status":"PAIRED" if paired else "NOT_PAIRED_ABSTENTION",
        "K0":k0,"K1":k1,"REF_CAF":ref0,"REF_SCALE":ref1,
        "paired_set_loss_gain_orders":gain,
        "revision_predictive_improvement_pass":
            gain>=min_improvement if paired else None,
        "descriptive_gain_margin_orders":min_improvement,
        "do_not_infer_structural_identification_from_score":True,
        "do_not_count_abstention_as_zero_error":True,
    }
