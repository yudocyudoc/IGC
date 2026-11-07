"""CT-03 public protocol shared by D/B/M, never true-world metadata.

Only the exogenous waveform, units and time windows live here. Construction
observations enter separately after custodial release. The evaluator has no
import path from this module.
"""
PUBLIC_INPUT = {
    "schema": "igc-ct03-fixed-aggregate-input/1.0",
    "quantity_unit": "items",
    "time_unit": "hours",
    "rate_unit": "items/hour",
    "pulse_rate": 1.7,
    "pulse_start": 0,
    "pulse_end": 2,
    "after_rate": 0,
    "continuous_requested_mass": 3.4,
    "initial_stock": 0,
    "start_time": 0,
    "stop_time": 8,
    "solver": "euler",
    "dt": 0.125,
    "construction_times": [0, 1, 2, 4],
    "reserved_times": [6, 8],
}
