import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyEv01NativeResult as classify} from '../scripts/arena_b_ev01_status.mjs';

const base={case_id:'EV-01',mode:'live',provider_calls:1,
  model_returned:false,bridge_error:'The operation was aborted due to timeout',
  http_status:undefined,raw_provider_saved:false,horizon_matches_case:false};

test('timeout before HTTP is not a native horizon failure',()=>{
  const x=classify(base);
  assert.equal(x.status,'EV01_PROVIDER_TRANSPORT_TIMEOUT_NO_NATIVE_MODEL');
  assert.equal(x.provider_calls_attempted,1);
  assert.equal(x.native_model_available,false);
  assert.equal(x.provider_response_observed,false);
  assert.equal(x.provider_billing,'UNKNOWN');
  assert.equal(x.G0,'NOT_REACHED_NO_NATIVE_MODEL');
});
test('only genuine native output can trigger horizon mismatch',()=>{
  const x=classify({...base,model_returned:true,bridge_error:undefined});
  assert.equal(x.status,'EV01_NATIVE_HORIZON_NOT_COMPARABLE');
});
test('native present and correct horizon is not scientific G0/G3 proof',()=>{
  const x=classify({...base,model_returned:true,horizon_matches_case:true,
    bridge_error:undefined});
  assert.equal(x.status,'ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED');
  assert.equal(x.G0,'NATIVE_GENERATION_ONLY_TRANSLATION_PENDING');
});
test('failure before provider attempt remains distinct from failed transport',()=>{
  const x=classify({...base,provider_calls:0,bridge_error:undefined});
  assert.equal(x.status,'EV01_NO_PROVIDER_CALL_OR_NATIVE_MODEL');
});
test('historic runner cannot accidentally use EV01 status adjudicator',()=>{
  assert.throws(()=>classify({...base,case_id:undefined}),/EV01_RECEIPT_CASE_REQUIRED/);
});