import test from "node:test";
import assert from "node:assert/strict";
import {digest} from "../scripts/arena_b_cf_protocol_adapter.mjs";
import {validateCt03Visible,validateCt03Revision,classifyCt03NativeResult,
        CT03_SCHEMA,CT03_INPUT,CT03_OWN_FEEDBACK_SCHEMA}
  from "../scripts/arena_b_ct03_contract.mjs";

const SHA="sha256:"+"a".repeat(64);
const visible=(round="initial")=>({
  schema:CT03_SCHEMA,case_id:"CT-03",arm:"B",round_id:"ct03-b-"+round,
  source_snapshot_hash:SHA,world_public_id:"W1",condition_id:"C0",
  question:"Build a quantitative aggregate stock-flow model for conserved items.",
  construction:{input:CT03_INPUT,observations:[
    {time:0,delivered:0},{time:1,delivered:.1},
    {time:2,delivered:.2},{time:4,delivered:.4}],
    observation_times_hours:[0,1,2,4]},
  observability:{quantity_unit:"items",time_unit:"hours",
    observable:"cumulative_delivered",construction_times_hours:[0,1,2,4],
    horizon_hours:8}
});

test("CT03 B sees same fixed pulse and only four construction observations",()=>{
  assert.equal(validateCt03Visible(visible(),"initial").condition,"C0");
  assert.equal(validateCt03Visible(visible("revision"),"revision").world,"W1");
});

test("CT03 B rejects reserved truth, extra fields, wrong cuts, wrong pulse",()=>{
  const v=visible();v.heldout_t6=3;
  assert.throws(()=>validateCt03Visible(v,"initial"),/SCOPE_OR_KEYS/);
  const w=visible();w.construction.observations.push({time:6,delivered:2.1});
  assert.throws(()=>validateCt03Visible(w,"initial"),/FOUR_CONSTRUCTION/);
  const x=visible();x.construction.input={...CT03_INPUT,pulse_rate:2};
  assert.throws(()=>validateCt03Visible(x,"initial"),/PULSE_OR_CUTS/);
  const y=visible();y.question+=" EVALUATOR_PRIVATE_TRUTH";
  assert.throws(()=>validateCt03Visible(y,"initial"),/EVALUATOR_OR_RIVAL/);
});

test("CT03 B validates own currentModel parent exactly, never accepts other world",()=>{
  const native={model:{specs:{stopTime:8},variables:[],relationships:[]}};
  const receipt={case_id:"CT-03",world_public_id:"W1",condition_id:"C0",
    round_kind:"initial",source_snapshot_hash:SHA,model_returned:true,
    mode:"mock",provider_calls:0,result_sha256:digest(native)};
  const feedback={schema:CT03_OWN_FEEDBACK_SCHEMA,arm:"B",
    world_public_id:"W1",condition_id:"C0",source_snapshot_hash:SHA,
    parent_result_sha256:receipt.result_sha256,
    own_diagnostic_sha256:"sha256:"+"b".repeat(64),
    retrieved_before_policy:{item_id:"W1:own",projection_hash:"sha256:"+"c".repeat(64)},
    own_diagnostic:{construction_status:"mock_only"}};
  const v=visible("revision");
  assert.equal(validateCt03Revision({native,receipt,feedback,visible:v,mode:"mock"}).model,
               native.model);
  assert.throws(()=>validateCt03Revision({native,receipt:{...receipt,world_public_id:"W2"},
    feedback,visible:v,mode:"mock"}),/PARENT_RECEIPT_MISMATCH/);
  assert.throws(()=>validateCt03Revision({native,receipt,feedback:{...feedback,arm:"M"},
    visible:v,mode:"mock"}),/FEEDBACK_NOT_OWN/);
  assert.throws(()=>validateCt03Revision({native,receipt,feedback,
    visible:v,mode:"live"}),/PARENT_RECEIPT_MISMATCH/);
});

test("CT03 B has separate NONE vs malformed horizon statuses",()=>{
  assert.equal(classifyCt03NativeResult({provider_calls:0,model_returned:false}).status,
               "CT03_PREPROVIDER_NO_NATIVE");
  assert.equal(classifyCt03NativeResult({provider_calls:1,model_returned:false}).status,
               "CT03_PROVIDER_ATTEMPT_NO_NATIVE");
  assert.equal(classifyCt03NativeResult({mode:"mock",model_returned:true,
    horizon_matches_case:false}).status,"CT03_NATIVE_HORIZON_MISMATCH");
});
