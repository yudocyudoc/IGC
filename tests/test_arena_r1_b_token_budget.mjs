import {test} from "node:test";
import assert from "node:assert/strict";
import {OR_SLUG,requestToCloudflare} from "../scripts/arena_b_cf_protocol_adapter.mjs";

const call={
  model:OR_SLUG,
  response_format:{type:"json_schema",json_schema:{name:"native",schema:{
    type:"object",properties:{variables:{type:"array"},relationships:{type:"array"}}
  }}},
  messages:[{role:"system",content:"unmodified Buffalo"}, {role:"user",content:"common R1 construction"}],
  max_completion_tokens:8000
};

test("R1 one-shot allows 7000 output tokens without changing historical B cap",()=>{
  assert.equal(requestToCloudflare(call).max_completion_tokens,3500);
  assert.equal(requestToCloudflare(call,{r1Initial:true}).max_completion_tokens,7000);
  assert.equal(requestToCloudflare(call,{physicalRevision:true}).max_completion_tokens,7000);
  assert.throws(()=>requestToCloudflare(call,{r1Initial:true,physicalRevision:true}),
                /INVALID_TOKEN_BUDGET_OPTIONS/);
  assert.throws(()=>requestToCloudflare(call,{r1Initial:"yes"}),
                /INVALID_TOKEN_BUDGET_OPTIONS/);
});
