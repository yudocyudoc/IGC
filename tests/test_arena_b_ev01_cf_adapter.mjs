import test from "node:test";
import assert from "node:assert/strict";
import {requestToCloudflareEV01,cloudflareUrl,EV01_BUDGET_AUTH,
        EV01_TIMEOUT_MS,OR_SLUG,CF_MODEL,CF_MODE,responseToOpenRouter}
  from "../scripts/arena_b_ev01_cf_adapter.mjs";
import {requestToCloudflare as historicalRequest} from "../scripts/arena_b_cf_protocol_adapter.mjs";
const original={
  model:OR_SLUG,
  response_format:{type:"json_schema",json_schema:{name:"quantitative",strict:true,
    schema:{type:"object",properties:{
      variables:{type:"array"},relationships:{type:"array"}
    }}}},
  messages:[{role:"system",content:"System role untouched"},
            {role:"user",content:"Public EV01 O0 prompt"}],
  max_completion_tokens:16000
};
test("R2 validated backend alias and endpoint, 16K EV01 opt in only",()=>{
  assert.equal(OR_SLUG,"cloudflare/glm-5.3-flash");
  assert.equal(CF_MODEL,"@cf/zai-org/glm-5.3-flash");
  assert.equal(CF_MODE,"CLOUDFLARE_WORKERS_AI_DIRECT_REST_JSON_SCHEMA");
  assert.equal(EV01_TIMEOUT_MS,360000);
  assert.equal(cloudflareUrl("a".repeat(32)),
    "https://api.cloudflare.com/client/v4/accounts/"+ "a".repeat(32)+"/ai/run/"+CF_MODEL);
  assert.throws(()=>requestToCloudflareEV01(original),/EV01_BUDGET_NOT_AUTHORIZED/);
  assert.equal(historicalRequest(original).max_completion_tokens,3500);
  const result=requestToCloudflareEV01(original,{authorization:EV01_BUDGET_AUTH});
  assert.equal(result.max_completion_tokens,16000);
  assert.equal(result.reasoning_effort,"low");
  assert.equal(result.stream,false);
  assert.equal(result.response_format.json_schema.type,"object");
  assert.equal(result.response_format.json_schema.name,undefined);
  assert.deepEqual(result.messages,original.messages);
  assert.equal(result.model,undefined);
});
test("OpenRouter response envelope preserves the actual Cloudflare JSON model",()=>{
  const native={specs:{stopTime:1/6},variables:[{name:"Pending"}],
                relationships:[{from:"A",to:"B"}]};
  const cf={success:true,result:{response:native,usage:{prompt_tokens:8,completion_tokens:6}}};
  const r=responseToOpenRouter(cf,"sha256:"+"a".repeat(64));
  assert.deepEqual(JSON.parse(r.choices[0].message.content),native);
  assert.equal(r.model,OR_SLUG);
  assert.deepEqual(r.usage,cf.result.usage);
});
test("invalid alias, loose schema and >16K requests fail closed",()=>{
  assert.throws(()=>requestToCloudflareEV01({...original,model:"glm-5.3-flash"},
               {authorization:EV01_BUDGET_AUTH}),/OPENROUTER_MODEL_MISMATCH/);
  assert.throws(()=>requestToCloudflareEV01({...original,max_completion_tokens:20000},
               {authorization:EV01_BUDGET_AUTH}),/EV01_NATIVE_TOKENS_EXCEED_CAP/);
  assert.throws(()=>requestToCloudflareEV01({...original,response_format:{type:"json_object"}},
               {authorization:EV01_BUDGET_AUTH}),/BUFFALO_SCHEMA_NOT_REQUESTED/);
});
