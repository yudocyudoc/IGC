/** CT-03 strict Buffalo visible input and own-parent gates.
 * Pure validation, no engine, no provider. The same original engine and
 * Cloudflare adapter are invoked ONLY by arena_b_ct03_native_runner.mjs.
 */
import {digest} from "./arena_b_cf_protocol_adapter.mjs";

export const CT03_SCHEMA="igc-ct03-b-visible/1.0";
export const CT03_OWN_FEEDBACK_SCHEMA="igc-ct03-b-own-feedback/1.0";
export const CT03_INPUT={pulse_rate:1.7,pulse_start:0,pulse_end:2,
                         total_mass:3.4,unit:"items/hour",horizon_hours:8,
                         integration_step_hours:0.125};
const hash=/^sha256:[0-9a-f]{64}$/;
const fail=code=>{throw Error(code);};
const keys=(obj,allowed)=>Object.keys(obj).every(k=>allowed.includes(k));
const finite=n=>typeof n==="number"&&Number.isFinite(n);
const stable=x=>Array.isArray(x)?x.map(stable):
  (x&&typeof x==="object")?Object.fromEntries(Object.entries(x).sort().map(([k,v])=>[k,stable(v)])):x;
const same=(a,b)=>JSON.stringify(stable(a))===JSON.stringify(stable(b));
const unsafe=/holdout|gold|truth|private|rival|secret|future_observation|t6|t8|evaluator/i;

export function validateCt03Visible(v,round) {
  if(!v||typeof v!=="object"||Array.isArray(v) ||
     v.schema!==CT03_SCHEMA || v.case_id!=="CT-03" || v.arm!=="B" ||
     v.round_id!=="ct03-b-"+round || !["initial","revision"].includes(round) ||
     !hash.test(v.source_snapshot_hash??"") ||
     !/^[A-Za-z0-9_-]{1,64}$/.test(v.world_public_id??"") ||
     v.condition_id!=="C0" || typeof v.question!=="string" ||
     !v.question.startsWith("Build a quantitative aggregate stock-flow model") ||
     !keys(v,["schema","case_id","arm","round_id","source_snapshot_hash",
              "world_public_id","condition_id","question","construction",
              "observability"]))
    fail("CT03_B_WRONG_VISIBLE_SCHEMA_SCOPE_OR_KEYS");
  if(!v.construction || !v.observability ||
     !keys(v.construction,["input","observations","observation_times_hours"]) ||
     !keys(v.observability,["quantity_unit","time_unit","observable",
                             "construction_times_hours","horizon_hours"]))
    fail("CT03_B_WRONG_OBSERVATION_SURFACE");
  if(!same(v.construction.input,CT03_INPUT)||
     !same(v.observability,{
       quantity_unit:"items",time_unit:"hours",observable:"cumulative_delivered",
       construction_times_hours:[0,1,2,4],horizon_hours:8
     }) ||
     !same(v.construction.observation_times_hours,[0,1,2,4]))
    fail("CT03_B_INPUT_PULSE_OR_CUTS_CHANGED");
  if(!Array.isArray(v.construction.observations) || v.construction.observations.length!==4)
    fail("CT03_B_FOUR_CONSTRUCTION_OBSERVATIONS_REQUIRED");
  let previous=-1;
  for(let i=0;i<4;i++){
    const o=v.construction.observations[i];
    if(!o || typeof o!=="object" || !keys(o,["time","delivered"]) ||
       o.time!==[0,1,2,4][i] || !finite(o.delivered) ||
       o.delivered<previous || o.delivered>3.4+1e-8)
      fail("CT03_B_INVALID_CONSTRUCTION_POINT");
    previous=o.delivered;
  }
  if(unsafe.test(JSON.stringify(v)))fail("CT03_B_EVALUATOR_OR_RIVAL_LEAK");
  if(v.question.length>2000)fail("CT03_B_QUESTION_TOO_LONG");
  return {condition:"C0",world:v.world_public_id,source_hash:v.source_snapshot_hash};
}

export function validateCt03Revision({native,receipt,feedback,visible,mode}){
  const check=validateCt03Visible(visible,"revision");
  if(!native||!native.model||!Array.isArray(native.model.variables)||
     !Array.isArray(native.model.relationships)||!native.model.specs||
     !receipt || receipt.case_id!=="CT-03" ||
     receipt.world_public_id!==check.world ||
     receipt.condition_id!==check.condition ||
     receipt.round_kind!=="initial" ||
     receipt.source_snapshot_hash!==check.source_hash ||
     receipt.model_returned!==true ||
     receipt.result_sha256!==digest(native) ||
     (mode==="live" && (receipt.mode!=="live"||receipt.provider_calls!==1)))
    fail("CT03_B_ORIGINAL_PARENT_RECEIPT_MISMATCH");
  if(!feedback || feedback.schema!==CT03_OWN_FEEDBACK_SCHEMA ||
     feedback.arm!=="B" || feedback.world_public_id!==check.world ||
     feedback.condition_id!==check.condition ||
     feedback.source_snapshot_hash!==check.source_hash ||
     feedback.parent_result_sha256!==receipt.result_sha256 ||
     !hash.test(feedback.own_diagnostic_sha256??"") ||
     !feedback.retrieved_before_policy || typeof feedback.own_diagnostic!=="object" ||
     feedback.own_diagnostic===null ||
     unsafe.test(JSON.stringify(feedback)))
    fail("CT03_B_FEEDBACK_NOT_OWN_OR_MISSING_LEDGER_RETRIEVAL");
  return {model:native.model,feedback,source:check};
}

export function classifyCt03NativeResult(r){
  const n=Number(r?.provider_calls??0),native=r?.model_returned===true;
  const out={provider_calls_attempted:n,
             provider_response_observed:Number.isInteger(r?.http_status),
             raw_provider_response_observed:r?.raw_provider_saved===true,
             provider_billing:r?.provider_usage?"PROVIDER_USAGE_RECEIVED":"UNKNOWN",
             native_model_available:native};
  if(!native)return {...out,status:n?
    "CT03_PROVIDER_ATTEMPT_NO_NATIVE":"CT03_PREPROVIDER_NO_NATIVE",
    G0:"NOT_REACHED_NO_NATIVE"};
  if(r.horizon_matches_case!==true)return {...out,
    status:"CT03_NATIVE_HORIZON_MISMATCH",G0:"REJECTED_HORIZON"};
  return {...out,status:r.mode==="mock"?
    "ORIGINAL_ENGINE_OFFLINE_PATH_PASS":"ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED",
    G0:"NATIVE_GENERATED_NOT_YET_G1_G2"};
}
