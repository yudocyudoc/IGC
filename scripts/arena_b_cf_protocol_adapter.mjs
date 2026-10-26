/** Pure protocol adapter: ORIGINAL Buffalo OpenRouter SDK <-> Cloudflare Workers AI.
 * No hypothesis synthesis, equation repair, retry, or SDK changes.
 * Cloudflare REST JSON mode receives exactly the Buffalo generated schema.
 */
import {createHash} from "node:crypto";
export const CF_MODEL="@cf/zai-org/glm-5.3-flash";
// Deliberately NOT a real OpenRouter catalog model: namespaced virtual alias
// triggers the unmodified Buffalo ModelCapabilities.OPEN_ROUTER code path.
export const OR_SLUG="cloudflare/glm-5.3-flash";
export const CF_MODE="CLOUDFLARE_WORKERS_AI_DIRECT_REST_JSON_SCHEMA";
export const digest=x=>"sha256:"+createHash("sha256").update(typeof x==="string"?x:JSON.stringify(x)).digest("hex");

export function requestToCloudflare(orBody) {
  if(orBody?.model!==OR_SLUG)throw Error("OPENROUTER_MODEL_MISMATCH");
  if(orBody?.response_format?.type!=="json_schema")throw Error("BUFFALO_SCHEMA_NOT_REQUESTED");
  const schema=orBody.response_format.json_schema?.schema;
  if(!schema?.properties?.variables || !schema?.properties?.relationships)
    throw Error("QUANTITATIVE_SCHEMA_NOT_PRESENT");
  if(!Array.isArray(orBody.messages) || orBody.messages.length<2 ||
     orBody.messages.some(m=>!["system","user","assistant"].includes(m.role)||
                    typeof m.content!=="string"))
    throw Error("INVALID_UPSTREAM_MESSAGES");
  // Real Cloudflare JSON Mode documents a *bare* JSON schema, not OpenRouter's
  // json_schema:{name,schema,strict} wrapper.
  return {
    messages:orBody.messages.map(({role,content})=>({role,content})),
    response_format:{type:"json_schema",json_schema:schema},
    max_completion_tokens:Math.min(orBody.max_completion_tokens??3500,3500),
    reasoning_effort:"low",
    stream:false
  };
}

export function responseToOpenRouter(cf, originalRequestHash) {
  // Workers AI REST wraps the answer in {result:{response:"..."}}. JSON mode
  // might put a JS object in response; serialize only, never modify content.
  if(!cf || cf.success!==true || !cf.result || typeof cf.result!=="object")
    throw Error("WORKERS_AI_UNSUCCESSFUL");
  const r=cf.result;
  let content=r.response;
  if(content===undefined && Array.isArray(r.choices)){
    content=r.choices[0]?.message?.content;
  }
  if(content && typeof content==="object" && !Array.isArray(content)){
    content=JSON.stringify(content);
  }
  if(typeof content!=="string" || !content.trim())throw Error("WORKERS_AI_NO_CONTENT");
  // The REST /ai/run wrapper has no finish_reason. The HTTP request completed,
  // not necessarily proof of model completion. This inferred transport marker
  // and the raw Cloudflare receipt must remain paired in the audit.
  const finish=r.choices?.[0]?.finish_reason??"stop";
  return {
    id:typeof r.id==="string"?r.id:"bridge-"+originalRequestHash.slice(7,25),
    object:"chat.completion",
    created:Math.floor(Date.now()/1000),
    model:OR_SLUG, // OpenRouter-facing alias; actual model recorded separately
    system_fingerprint:"igc-cloudflare-compat-v01",
    choices:[{index:0,finish_reason:finish,
      message:{role:"assistant",content}}],
    ...(r.usage && typeof r.usage==="object"?{usage:r.usage}:{})
  };
}
