import {test} from "node:test";
import assert from "node:assert/strict";
import {OR_SLUG,requestToCloudflare} from "../scripts/arena_b_cf_protocol_adapter.mjs";
const body={
 model:OR_SLUG,
 messages:[{role:"system",content:"original pinned Buffalo"},{role:"user",content:"own R1 model and neutral log"}],
 response_format:{type:"json_schema",json_schema:{name:"b",schema:{
  type:"object",properties:{variables:{type:"array"},relationships:{type:"array"}}
 }}},
 max_completion_tokens:8000
};
test("R2 7000-token proposed offline cap does not change B2/B5 initial caps",()=>{
 assert.equal(requestToCloudflare(body).max_completion_tokens,3500);
 assert.equal(requestToCloudflare(body,{r2Revision:true}).max_completion_tokens,7000);
 assert.equal(requestToCloudflare(body,{r1Initial:true}).max_completion_tokens,7000);
 assert.throws(()=>requestToCloudflare(body,{r1Initial:true,r2Revision:true}),
               /INVALID_TOKEN_BUDGET_OPTIONS/);
 assert.throws(()=>requestToCloudflare(body,{r2Revision:"true"}),
               /INVALID_TOKEN_BUDGET_OPTIONS/);
});

test("New R2 budget 16000 is opt-in; all other R2 and historical ceilings stay unchanged",()=>{
 assert.equal(requestToCloudflare(body,{r2Extended:true}).max_completion_tokens,8000);
 const big={...body,max_completion_tokens:16000};
 assert.equal(requestToCloudflare(big,{r2Extended:true}).max_completion_tokens,16000);
 assert.equal(requestToCloudflare(big,{r2Revision:true}).max_completion_tokens,7000);
 assert.equal(requestToCloudflare(big,{r1Initial:true}).max_completion_tokens,7000);
 assert.equal(requestToCloudflare(big).max_completion_tokens,3500);
 assert.throws(()=>requestToCloudflare(big,{r2Revision:true,r2Extended:true}),/INVALID_TOKEN_BUDGET_OPTIONS/);
 assert.throws(()=>requestToCloudflare(big,{r2Extended:"true"}),/INVALID_TOKEN_BUDGET_OPTIONS/);
});
