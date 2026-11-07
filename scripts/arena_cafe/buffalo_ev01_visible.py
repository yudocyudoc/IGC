"""A3 Buffalo EV-01 *public only* native SD-AI input staging, no inference.

Use the existing Buffalo quantitative engine through the existing Cloudflare
OpenRouter transport. This module never imports EV01/DES or any other-arm model.
Its only legal input is one already authenticated A1 visible O0/O1 envelope.
The common half-minute POS reconstruction is disclosed as an engineering
ASSUMPTION, not as a physically observed continuous arrival rate.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import json
from pathlib import Path

from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_cafe import r2_causal_pos_signal as causal
from scripts.arena_v0_contract import INPUT_SCHEMA, canonical, digest, validate_visible_input

SCHEMA="igc-a3-buffalo-ev01-public-construction-preflight/0.1"
MODEL="@cf/zai-org/glm-5.3-flash"
ORIGINAL_ENGINE="UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc"
MAX_PROVIDER_CALLS=1
MAX_MODEL_PROPOSALS=1
# Existing F0-pinned bridge permits 3500 tokens outside historical R1/R2.
MAX_COMPLETION_TOKENS=3500


def stage(visible,condition,kind="initial"):
    need(kind in ("initial","revision"),"A3_B_INVALID_ROUND_KIND")
    validate_a1_visible(visible,condition)
    need(condition in ("O0","O1"),"A3_B_BAD_CONDITION")
    kernel=causal.from_visible(visible,condition)
    rate=kernel['signal']
    series=visible["construction"]["observation_series"]
    public_event=visible["construction"]["pos_arrival_events"]
    need(len(public_event)==15 and rate["events_count"]==15 and
         Q(rate["total_event_mass_orders_exact"])==15 and
         rate["policy"]==causal.POLICY,
         "A3_B_POS_MASS_OR_KNOWN_CONTROL_DRIFT")
    need([x["t_minutes_exact"] for x in series]==
         ["0","2","4","6","8","10"],"A3_B_GRID_DRIFT")
    construction={
      "boundary":"POS order created -> POS order delivered",
      "events":public_event,
      "observation_series":[{
           "t_minutes_exact":x["t_minutes_exact"],
           "t_hours_exact":str(Q(x["t_minutes_exact"])/60),
           "orders_created_cumulative":x["orders_created_cumulative"],
           "delivered_cumulative":x["delivered_cumulative"]
      } for x in series],
      "declared_input_reconstruction":{
           "policy":rate["policy"],
           "signal_sha256":rate["event_rate_signal_sha256"],
           "events_hash":kernel["events_hash"],
           "width_minutes_exact":rate["width_minutes_exact"],
           "cutoff_minutes_exact":rate["cutoff_minutes_exact"],
           "support_end_minutes_exact":rate["support_end_minutes_exact"],
           "total_event_mass_orders_exact":rate["total_event_mass_orders_exact"],
           "mass_before_cutoff_orders_exact":rate["mass_before_cutoff_orders_exact"],
           "mass_deferred_after_cutoff_orders_exact":rate["mass_deferred_after_cutoff_orders_exact"],
           "event_times_minutes_exact":rate["event_times_minutes_exact"],
           "time_unit_for_buffalo":"hour",
           "rate_unit_for_buffalo":"orders/hour",
           "piecewise_constant_segments":[{
               "start_hours_exact":str(Q(b["start_minutes_exact"])/60),
               "end_hours_exact":str(Q(b["end_minutes_exact"])/60),
               "rate_orders_per_hour_exact":str(Q(b["rate_orders_per_minute_exact"])*60),
               "mass_orders_exact":b["mass_orders_exact"],
           } for b in rate["segments"]],
           "source":"PUBLIC_POS_CREATION_TIMES",
           "not_an_observed_instantaneous_rate":True,
           "mass_not_moved_before_event":True,
           "tail_not_truncated_or_moved_before_event":True,
           "no_delivery_data_used_to_generate_stimulus":True,
      },
      "initial_conditions":{"orders_in_process":0,"orders_delivered":0},
      "known_material_accounting":"A(t)=P(t)+D(t); no cancellations or losses in this declared synthetic control",
      "data_origin":"synthetic_event_projection_not_real_POS",
      "actual_station_count":"NOT_DISCLOSED",
      "physical_capacity":"UNKNOWN_NOT_A_MODEL_PARAMETER",
    }
    if condition=="O1":
        # The preparation aggregate is explicitly authorized, not derived from
        # any secret FULL record in this arm. No resource ID or hidden stage.
        permitted=visible["construction"]["physical_observation"]
        need(permitted["stage_disclosed"]=="preparacion",
             "A3_B_UNAUTHORIZED_O1_STAGE")
        construction["authorized_preparation_aggregate"]=dict(permitted)
    # It is Buffalo, not this bridge, that proposes stocks, flows, capacities
    # and feedback structure. Reconstructed public POS flow is an input signal.
    prompt=(
      "Independently propose ONE original Buffalo SD-AI native quantitative "
      "stock-flow model for a synthetic cafe from public observations only. "
      "Use accepted orders as the external input and delivered orders as an "
      "observed cumulative output. Use hours for time, orders for stocks and "
      "orders/hour for flows. Simulate construction [0,1/6] hours from zero "
      "initial stocks. The public exact POS event times are supplied, together "
      "with an explicitly ASSUMED CAUSAL right-hand event kernel "
      "on [event_t,event_t+0.5 min), converted exactly to hours; it is not a measured instantaneous "
      "rate. Do not move input mass before each event, truncate support after cutoff, " 
      "or substitute a constant or invented pulse for the declared "
      "piecewise input without explicitly marking a limitation. Propose your "
      "OWN mechanism; no D or molecular candidates are supplied. Include only "
      "mechanistically motivated assumptions; don't claim unique causal "
      "identification from six cumulative counts. Do not infer any unobserved "
      "station or server as a fact. Preserve the Buffalo native schema. "
      "Explain non-identifiable mechanisms and limitations in your response. "
      "Do not reveal or assume future observations, private service times or "
      "evaluator stage configurations."
    )
    if condition=="O1":
        prompt+=(
          " The only additional permitted physical evidence is an aggregate "
          "of completed PREPARATION services and their measured wait/service "
          "durations before the cutoff, supplied as authorized_preparation_aggregate. "
          "It is NOT a time series and it does not reveal other stations or "
          "allow an unobserved stage to be identified."
        )
    # The shared IGC input contract caps question at 180 characters.
    # Preserve the complete method instruction inside construction, which
    # Buffalo's ORIGINAL engine passes through as backgroundKnowledge.
    construction["modeling_task_instructions"]=prompt
    brief=(
      "Buffalo SD-AI: propose one native stock-flow model of EV01 from "
      "permitted POS data; see modeling_task_instructions and public "
      "reconstruction. Report limits."
    )
    result={
        "schema":INPUT_SCHEMA,
        "investigation_id":"cafeteria-known-control-a3-b",
        "round_id":"a3-"+condition.lower()+"-buffalo-"+kind,
        "question":brief,
        "construction":construction,
        "observability":{
            "condition_id":condition,
            "world_public_id":visible["observability"]["world_public_id"],
            "public_cutoff_minutes_exact":"10",
            "observation_semantics":"strictly_before_sample_t",
            "physical_view":("POS_ONLY" if condition=="O0"
                             else "POS_PLUS_AUTHORIZED_PREPARATION_AGGREGATE"),
        },
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "iteration_limit":1,
        "resources":{"max_llm_calls":MAX_PROVIDER_CALLS,
                     "max_model_proposals":MAX_MODEL_PROPOSALS,
                     "max_simulations":0},
    }
    validate_visible_input(result)
    receipt={
        "schema":SCHEMA,"status":"B_NATIVE_INPUT_STAGED_ZERO_PROVIDER_CALLS",
        "round_kind":kind,
        "arm":"B","condition":condition,
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "source_visible_hash":digest(visible),
        "buffalo_visible_hash":digest(result),
        "model":MODEL,"native_original_engine":ORIGINAL_ENGINE,
        "provider_calls":0,"possible_later_max_provider_calls":MAX_PROVIDER_CALLS,
        "historical_bridge_token_cap_not_ev01_config":MAX_COMPLETION_TOKENS,
        "ev01_original_engine_max_tokens_opt_in":16000,
        "native_model_horizon_hours_exact":"1/6",
        "b_live_authorized":False,
        "arrival_signal_sha256":rate["event_rate_signal_sha256"],
        "original_engine_unchanged":True,
        "public_pos_orders":15,
        "input_reconstruction_is_declared_assumption":True,
        "physical_available":"NONE" if condition=="O0" else "PREPARATION_AGGREGATE_ONLY",
        "other_arm_candidates_supplied":False,
        "truth_after_cutoff_supplied":False,
        "scientific_native_inference":"NOT_RUN",
        "g0":"NOT_RUN","g1":"NOT_RUN","g2":"NOT_RUN","g3":"NOT_RUN",
        "historical_B_cloudflare_success_is_not_current_EV01_call":True,
    }
    return result,receipt


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--condition",choices=("O0","O1"),required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--kind",choices=("initial","revision"),default="initial")
    a=p.parse_args()
    need(not a.out.exists(),"A3_B_REFUSE_OVERWRITE")
    v=json.loads(a.input.read_text(encoding="utf-8"))
    native,report=stage(v,a.condition,a.kind)
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/"b-visible.json").write_bytes(canonical(native)+b"\n")
    (a.out/"staging-receipt.json").write_bytes(canonical(report)+b"\n")
    print(json.dumps({"status":report["status"],"condition":a.condition,
                      "source_hash":report["source_snapshot_hash"],
                      "provider_calls":0}))


if __name__=="__main__":main()
