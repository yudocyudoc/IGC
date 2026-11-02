"""CAF02 conventional references with ONLY t=5 and t=10 K0 deliveries.

These are NEW, separately versioned K0-limited references, not the frozen
CAF01 REF_CAF/REF_SCALE rules (which need more construction observations).
Do not read any holdout, K1 evidence or world-private event counts.
"""
import math

TIMES=(5,10,15,20,30,40)


def forecast(d5,d10,k0_rate=1.2,k2_rate=1.35):
    if not (type(d5) in (float,int) and type(d10) in (float,int)
            and type(k0_rate) in (float,int)
            and type(k2_rate) in (float,int)
            and all(math.isfinite(x) for x in (d5,d10,k0_rate,k2_rate))
            and 0<k0_rate<=3 and 0<k2_rate<=3
            and 0<=d5<=d10
            and d5<=5*k0_rate+1e-8
            and d10<=10*k0_rate+1e-8):
        raise ValueError("INVALID_K0_LIMITED_REFERENCE_INPUT")
    rate=(d10-d5)/5
    def a0(t):return k0_rate*min(t,20)
    def a2(t):return k2_rate*min(t,20)
    # Single-interval output-rate reference; identifiable only if queue
    # backlog is evidenced at t=5 and t=10. Not CAF01 median>=2.
    caf_ready=((a0(5)-d5)>1 and (a0(10)-d10)>1)
    ref_caf=(
        [min(a2(t),rate*t) for t in TIMES]
        if caf_ready else None
    )
    def d0_extrap(t):
        if t<=5:
            v=(d5/5)*t
        elif t<=10:
            v=d5+rate*(t-5)
        else:
            v=d10+rate*(t-10)
        return min(a0(t),max(0,v))
    ratio=k2_rate/k0_rate
    ref_scale=[min(a2(t),ratio*d0_extrap(t)) for t in TIMES]
    return {
        "REF_CAF":{
            "version":"REF_CAF_K0_1WINDOW_2026-10-30",
            "status":"READY" if caf_ready else
                "ABSTAIN_NO_SATURATED_5_TO_10_WINDOW",
            "estimated_rate_orders_per_minute":rate if caf_ready else None,
            "predicted_K2_delivered":ref_caf,
            "not_the_CAF01_two_window_median_rule":True,
        },
        "REF_SCALE":{
            "version":"REF_SCALE_K0_PIECEWISE_EXTRAPOLATION_2026-10-30",
            "status":"READY_FIXED_EXTRAPOLATION",
            "estimated_K0_D_from_only_5_and_10": [
                d0_extrap(t) for t in TIMES],
            "predicted_K2_delivered":ref_scale,
            "not_the_CAF01_full_construction_curve_scaling_rule":True,
        },
        "used_only_public_K0_two_values":True,
        "K1_measurement_seen":False,
        "K2_truth_seen":False,
    }
