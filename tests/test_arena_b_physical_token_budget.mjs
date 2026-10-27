import test from 'node:test';
import assert from 'node:assert/strict';
import {requestToCloudflare,OR_SLUG} from '../scripts/arena_b_cf_protocol_adapter.mjs';

const upstream=()=>{
  const schema={type:'object',properties:{
    variables:{type:'array'},relationships:{type:'array'}}};
  return {model:OR_SLUG,response_format:{type:'json_schema',
    json_schema:{name:'buffalo',schema}},
    messages:[{role:'system',content:'Buffalo original'},
              {role:'assistant',content:'Previous own stock-flow model'},
              {role:'user',content:'Own OpenModelica construction feedback'}],
    max_completion_tokens:8000};
};

test('Original Buffalo transport cap remains pinned to 3500',()=>{
  const p=requestToCloudflare(upstream());
  assert.equal(p.max_completion_tokens,3500);
  assert.equal(p.messages[2].content,'Own OpenModelica construction feedback');
  assert.equal(p.response_format.type,'json_schema');
});
test('Only explicitly scoped physical extension can request 7000 tokens',()=>{
  const p=requestToCloudflare(upstream(),{physicalRevision:true});
  assert.equal(p.max_completion_tokens,7000);
  assert.deepEqual(p.messages,upstream().messages);
  assert.deepEqual(p.response_format.json_schema,upstream().response_format.json_schema.schema);
  assert.equal(requestToCloudflare(upstream(),{physicalRevision:false}).max_completion_tokens,3500);
});
test('Cannot override physical budget with arbitrary option or malformed request',()=>{
  assert.throws(()=>requestToCloudflare(upstream(),{max_completion_tokens:90000}),
                /INVALID_TOKEN_BUDGET_OPTIONS/);
  assert.throws(()=>requestToCloudflare(upstream(),{physicalRevision:'yes'}),
                /INVALID_TOKEN_BUDGET_OPTIONS/);
  const broken=upstream();broken.model='another-service';
  assert.throws(()=>requestToCloudflare(broken,{physicalRevision:true}),
                /OPENROUTER_MODEL_MISMATCH/);
});
