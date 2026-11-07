/** EV-01 Buffalo ORIGINAL quantitative engine -> ORIGINAL OpenRouter SDK
 * -> same Workers AI /ai/run protocol as successful R2.
 * Read-only upstream: UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc.
 * This is transport engineering only; do NOT infer scientific G2/G3 from mock.
 * Historical arena_b_native_runner.mjs and adapter remain byte-for-byte intact.
 */
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve,join} from "node:path";
import {pathToFileURL} from "node:url";
import {classifyEv01NativeResult} from "./arena_b_ev01_status.mjs";
import {OR_SLUG,CF_MODEL,CF_MODE,digest,responseToOpenRouter,
        requestToCloudflareEV01,cloudflareUrl,EV01_BUDGET_AUTH,
        EV01_CAP,EV01_TIMEOUT_MS,EV01_ADAPTER_VERSION}
  from "./arena_b_ev01_cf_adapter.mjs";

const PIN="5199f7b45f3a7ae4a773cb0dd8542940aabe9edc";
const ORIGIN="UB-IAD/sd-ai";
const mode=process.env.BUFFALO_MODE??"mock";
const round=process.env.BUFFALO_ROUND_KIND??"initial";
const root=resolve(process.env.SDAI_ROOT??"upstream/sd-ai");
const out=resolve(process.env.BUFFALO_OUTPUT??"artifacts/buffalo-ev01");
const input=resolve(process.env.BUFFALO_VISIBLE_INPUT??"data/synthetic/arena_b_v0_visible.json");
const sha=x=>digest(x);
const recorded={
  schema:"igc-arena-b-native-engine-proof/0.1",
  origin:ORIGIN,upstream_sha:PIN,engine:"quantitative",
  mode,provider_model:mode==="live"?CF_MODEL:"OFFLINE_SCHEMA_STUB",
  transport:CF_MODE,adapter_version:EV01_ADAPTER_VERSION,
  original_engine_max_tokens:EV01_CAP,configured_http_timeout_ms:EV01_TIMEOUT_MS,
  backend_alias:OR_SLUG,backend:"OPEN_ROUTER",
  provider_calls:0,proxy_requests:0,
  status:"STARTED",native_error:null,raw_provider_saved:false,
  model_returned:false,quant_schema_seen:false,no_d_or_m_candidate_inputs:true,
  b_real_original_method:"UB-IAD_QUANTITATIVE_ENGINE_UNMODIFIED",
};
const save=(name,obj)=>writeFile(join(out,name),JSON.stringify(obj,null,2)+"\n");
const fail=code=>{throw Error(code);};
const originals={fetch:globalThis.fetch};
let visible,userPrompt,parentModel={variables:[],relationships:[]};
let ownFeedback;
await mkdir(out,{recursive:false});
try{
  if(!["mock","live"].includes(mode))fail("INVALID_MODE");
  if(!["initial","revision"].includes(round))fail("INVALID_ROUND_KIND");
  if(mode==="live" &&
       (process.env.BUFFALO_LIVE_AUTH!=="ONE_UPSTREAM_CALL" ||
        process.env.BUFFALO_EV01_LIVE_AUTH!=="EV01_ONE_ROUND_EXPRESS_AUTH" ||
        process.env.GITHUB_RUN_ATTEMPT!=="1" ||
        process.env.GITHUB_REF!=="refs/heads/experiment/arena-continuity-e00-e01-20261106"))
    fail("EV01_REAL_ONE_SHOT_AUTH_REQUIRED");
  visible=JSON.parse(await readFile(input,"utf8"));
  if(visible.schema!=="igc-arena-visible-input/0.1" ||
     visible.investigation_id!=="cafeteria-known-control-a3-b")
     fail("EV01_PUBLIC_INPUT_NOT_AUTHENTIC");
  if(Object.keys(visible).some(k=>/holdout|gold|other.arm/i.test(k)) ||
     Object.keys(visible.construction??{}).some(k=>/holdout|gold|other.arm/i.test(k)))
    fail("EV01_FORBIDDEN_EVALUATOR_FIELDS");
  const cond=visible.observability?.condition_id;
  const signal=visible.construction?.declared_input_reconstruction;
  if(!["O0","O1"].includes(cond) ||
     visible.round_id!=="a3-"+cond.toLowerCase()+"-buffalo-"+round ||
     visible.observability.public_cutoff_minutes_exact!=="10" ||
     visible.observability.physical_view!==(cond==="O0"?"POS_ONLY":"POS_PLUS_AUTHORIZED_PREPARATION_AGGREGATE") ||
     !/^sha256:[a-f0-9]{64}$/.test(visible.source_snapshot_hash??"") ||
     signal?.policy!=="CAUSAL_RIGHT_RECTANGULAR_EVENT_KERNEL/0.1" ||
     !/^sha256:[a-f0-9]{64}$/.test(signal.signal_sha256??"") ||
     signal.width_minutes_exact!=="1/2" ||
     signal.total_event_mass_orders_exact!=="15" ||
     !Array.isArray(signal.event_times_minutes_exact) ||
     signal.event_times_minutes_exact.length!==15 ||
     !Array.isArray(signal.piecewise_constant_segments) ||
     signal.no_delivery_data_used_to_generate_stimulus!==true ||
     signal.mass_not_moved_before_event!==true)
    fail("EV01_PUBLIC_CAUSAL_INPUT_CONTRACT_MISMATCH");
  recorded.case_id="EV-01";
  recorded.condition_id=cond;
  recorded.round_kind=round;
  recorded.source_snapshot_hash=visible.source_snapshot_hash;
  recorded.arrival_signal_sha256=signal.signal_sha256;
  recorded.expected_horizon_hours=1/6;
  if(cond==="O1" &&
     (visible.construction.authorized_preparation_aggregate?.stage_disclosed!=="preparacion"))
    fail("EV01_O1_ONLY_PREPARATION_ALLOWED");
  if(cond==="O0" && "authorized_preparation_aggregate" in visible.construction)
    fail("EV01_O0_CANNOT_SEE_PREPARATION");
  userPrompt=visible.question;
  if(round==="revision"){
    const a=process.env.BUFFALO_PARENT_NATIVE,b=process.env.BUFFALO_PARENT_RECEIPT,
          c=process.env.BUFFALO_OWN_FEEDBACK;
    if(!a||!b||!c)fail("EV01_REVISION_PARENT_FEEDBACK_REQUIRED");
    const parent=JSON.parse(await readFile(resolve(a),"utf8"));
    const receipt=JSON.parse(await readFile(resolve(b),"utf8"));
    const fb=JSON.parse(await readFile(resolve(c),"utf8"));
    if(!Array.isArray(parent?.model?.variables) ||
       !Array.isArray(parent?.model?.relationships) ||
       receipt.case_id!=="EV-01" ||
       receipt.condition_id!==cond ||
       receipt.round_kind!=="initial" ||
       receipt.source_snapshot_hash!==visible.source_snapshot_hash ||
       receipt.arrival_signal_sha256!==signal.signal_sha256 ||
       receipt.result_sha256!==sha(parent) ||
       receipt.model_returned!==true ||
       (mode==="live" && (receipt.mode!=="live" || receipt.provider_calls!==1)) )
       fail("EV01_PARENT_NOT_OWN_AUTHENTIC_NATIVE_MODEL");
    if(fb?.schema!=="igc-e02-b-own-feedback/0.1" ||
       fb.arm!=="B" || fb.condition_id!==cond ||
       fb.source_snapshot_hash!==visible.source_snapshot_hash ||
       fb.parent_result_sha256!==receipt.result_sha256 ||
       typeof fb.diagnostic!=="object" || fb.diagnostic===null ||
       Object.keys(fb).some(k=>/holdout|gold|other.arm|private.des/i.test(k)))
       fail("EV01_NOT_OWN_DIAGNOSTIC_FEEDBACK");
    parentModel=parent.model;
    ownFeedback=fb;
    recorded.parent_native_sha256=receipt.result_sha256;
    recorded.own_feedback_sha256=sha(fb);
    // Same original Buffalo Engine.generate(currentModel) review, with only own feedback.
    userPrompt=visible.question+"\n\nReconsider YOUR previous original Buffalo"+
      " native quantitative stock-flow model (provided as currentModel)."+
      " Here is the diagnostic of YOUR previous proposal only: "+
      JSON.stringify(fb.diagnostic)+
      ". Decide whether to revise or explicitly retain the model."+
      " The descriptive evidence does not identify an unobserved server."+
      " Do not use rival methods, private evaluator truth or future observations.";
    await save("own-feedback-sent.json",fb);
  }
  // Intercept the ORIGINAL upstream OpenRouter SDK, as in R2 16K.
  globalThis.fetch=async function intercept(request,init={}){
    recorded.proxy_requests++;
    const url=new URL(typeof request==="string"?request:request.url);
    const method=init.method??(request instanceof Request?request.method:"GET");
    if(url.origin!=="https://openrouter.ai"||
       !url.pathname.endsWith("/chat/completions")||
       method.toUpperCase()!=="POST")
      fail("EV01_UNEXPECTED_OUTBOUND_HTTP:"+url.origin+url.pathname);
    if(recorded.proxy_requests!==1)fail("EV01_ONE_PROVIDER_CALL_PER_ROUND_GATE");
    let bodyText=init.body??(request instanceof Request?await request.text():null);
    if(typeof bodyText!=="string")
      bodyText=Buffer.isBuffer(bodyText)?bodyText.toString("utf8"):String(bodyText??"");
    const body=JSON.parse(bodyText);
    if(body.model!==OR_SLUG)fail("EV01_WRONG_OPENROUTER_SDK_BACKEND");
    if(body.response_format?.type!=="json_schema")
      fail("EV01_NATIVE_SCHEMA_MISSING");
    const schema=body.response_format.json_schema?.schema;
    if(!schema?.properties?.variables||!schema?.properties?.relationships)
      fail("EV01_NATIVE_QUANTITATIVE_SCHEMA_MISSING");
    if(round==="revision"){
      const serialized=JSON.stringify(parentModel,null,2);
      if(!body.messages.some(m=>m.role==="assistant"&&m.content===serialized))
        fail("EV01_OWN_CURRENTMODEL_NOT_PRESENT_IN_SDK");
      if(body.messages.at(-1)?.role!=="user"||
         !body.messages.at(-1)?.content.endsWith(userPrompt))
        fail("EV01_OWN_FEEDBACK_NOT_IN_SDK_MESSAGES");
      recorded.parent_as_original_currentModel=true;
    }
    recorded.quant_schema_seen=true;
    recorded.request_sha256=sha(body);
    recorded.schema_sha256=sha(schema);
    recorded.message_roles=body.messages.map(m=>m.role);
    const cfBody=requestToCloudflareEV01(body,{authorization:EV01_BUDGET_AUTH});
    if(cfBody.max_completion_tokens!==16000||
       cfBody.reasoning_effort!=="low"||
       cfBody.stream!==false)
      fail("EV01_CF_ADAPTER_BUDGET_OR_REASONING_MISMATCH");
    recorded.translated_body_sha256=sha(cfBody);
    recorded.cloudflare_schema_sha256=sha(cfBody.response_format.json_schema);
    recorded.actual_endpoint="Workers AI /ai/run/{model}";
    await save("request-metadata.json",{
      source:"UNMODIFIED_UPSTREAM_OPENROUTER_SDK",
      original_alias_model:OR_SLUG,request_sha256:recorded.request_sha256,
      schema_sha256:recorded.schema_sha256,
      prompt_hashes:body.messages.map(m=>({role:m.role,sha256:sha(m.content)})),
      original_upstream_modified:false,
      round_kind:round,
      backend:"OPEN_ROUTER"
    });
    await save("cf-effective-request.json",{
      target_endpoint:recorded.actual_endpoint,actual_model:CF_MODEL,
      body:cfBody,body_sha256:recorded.translated_body_sha256,
      source_request_sha256:recorded.request_sha256,
      no_credentials_serialized:true
    });
    let raw;
    if(mode==="mock"){
      raw={success:true,result:{response:{
        specs:{startTime:0,stopTime:1/6,dt:0.005,timeUnits:"Hour",integrationMethod:"Euler"},
        variables:[
          {name:"Arrivals",type:"flow",units:"items/hour",inflows:[],outflows:[],
           equation:"1.7",uniflow:true,graphicalFunction:{points:[]},documentation:"Offline input."},
          {name:"Completions",type:"flow",units:"items/hour",inflows:[],outflows:[],
           equation:"MIN(2, Backlog / 1)",uniflow:true,graphicalFunction:{points:[]},documentation:"Offline completion."},
          {name:"Backlog",type:"stock",units:"items",inflows:[],outflows:[],
           equation:"0",uniflow:false,graphicalFunction:{points:[]},documentation:"Offline outstanding."},
          {name:"Completed",type:"stock",units:"items",inflows:["Completions"],outflows:[],
           equation:"0",uniflow:false,graphicalFunction:{points:[]},documentation:"Offline total."}
        ],
        relationships:[
          {from:"Arrivals",to:"Backlog",reasoning:"Material inflow",polarity:"+",polarityReasoning:"Adds."},
          {from:"Completions",to:"Backlog",reasoning:"Material outflow",polarity:"-",polarityReasoning:"Subtracts."},
          {from:"Completions",to:"Completed",reasoning:"Material inflow",polarity:"+",polarityReasoning:"Adds."}
        ],
        explanation:"OFFLINE FIXTURE NOT BUFFALO INFERENCE",title:"Offline stub"
      },usage:{prompt_tokens:0,completion_tokens:0,total_tokens:0}}};
      recorded.inference_source="OFFLINE_WORKERS_AI_PROTOCOL_FIXTURE";
    }else{
      const account=process.env.CLOUDFLARE_ACCOUNT_ID;
      const token=process.env.CLOUDFLARE_API_TOKEN;
      if(!token)fail("EV01_MISSING_CLOUDFLARE_SECRETS");
      const endpoint=cloudflareUrl(account);
      recorded.provider_calls++;
      recorded.inference_source="REAL_CLOUDFLARE_WORKERS_AI";
      await save("cf-call-started.json",{model:CF_MODEL,
        calls_started:recorded.provider_calls,
        effective_body_sha256:recorded.translated_body_sha256,
        timestamp:new Date().toISOString()});
      const response=await originals.fetch(endpoint,{
        method:"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},
        body:JSON.stringify(cfBody),signal:AbortSignal.timeout(EV01_TIMEOUT_MS)
      });
      recorded.http_status=response.status;
      const rawText=await response.text();
      try{raw=JSON.parse(rawText)}catch{
        await save("cf-nonjson-error.json",{http_status:response.status,
          body_sha256:sha(rawText),size:rawText.length});
        fail("EV01_CLOUDFLARE_NON_JSON");
      }
      await save("provider-raw.json",raw);
      recorded.raw_provider_saved=true;
      if(!response.ok)fail("EV01_CLOUDFLARE_HTTP_"+response.status);
    }
    recorded.provider_usage=raw?.result?.usage??raw?.usage??null;
    recorded.provider_finish_reason=raw?.result?.choices?.[0]?.finish_reason??null;
    const envelope=responseToOpenRouter(raw,recorded.request_sha256);
    recorded.compatibility_envelope_synthesized=true;
    recorded.generated_content_sha256=sha(envelope.choices[0].message.content);
    await save("openrouter-compat-envelope.json",envelope);
    return new Response(JSON.stringify(envelope),{status:200,
      headers:{"content-type":"application/json"}});
  };
  process.env.OPEN_ROUTER_API_KEY="IGC_LOCAL_ONLY_NOT_REAL_OPENROUTER_KEY";
  const {default:Engine}=await import(pathToFileURL(join(root,"engines/quantitative/engine.js")).href);
  const engine=new Engine();
  const parameters={
    underlyingModel:OR_SLUG,
    supportsArrays:false,supportsModules:false,supportsSubTypes:false,mentorMode:false,
    problemStatement:visible.question,
    backgroundKnowledge:JSON.stringify({construction:visible.construction,
      observability:visible.observability,
      own_feedback:ownFeedback?.diagnostic??null}),
    maxTokens:EV01_CAP,timeoutMinutes:7
  };
  const output=await engine.generate(userPrompt,parentModel,parameters);
  await save("native-engine-result.json",output);
  recorded.result_sha256=sha(output);
  recorded.model_returned=output?.success===undefined &&
    Array.isArray(output?.model?.variables)&&
    Array.isArray(output?.model?.relationships);
  recorded.native_error=output?.err??null;
  if(recorded.model_returned){
    recorded.variable_count=output.model.variables.length;
    recorded.relationship_count=output.model.relationships.length;
    recorded.inferred_inflow_by_buffalo=output.model.variables.find(
      v=>v.name==="Backlog")?.inflows??null;
    recorded.status=mode==="mock"?
       "ORIGINAL_ENGINE_OFFLINE_PATH_PASS":
       "ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED";
  }else{
    recorded.status="ORIGINAL_ENGINE_NO_NATIVE_MODEL";
  }
  recorded.llm_wrapper_schema_was_sent=recorded.quant_schema_seen;
  recorded.output_horizon_hours=output?.model?.specs?.stopTime??null;
  recorded.horizon_matches_case=recorded.model_returned?
    Math.abs(recorded.output_horizon_hours-1/6)<1e-8:false;
  if(recorded.model_returned&&!recorded.horizon_matches_case)
    recorded.status="EV01_NATIVE_HORIZON_NOT_COMPARABLE";
  recorded.upstream_source_modified=false;
  if(mode==="mock" &&
     !recorded.inferred_inflow_by_buffalo?.includes("Arrivals"))
    fail("EV01_ORIGINAL_UPSTREAM_POSTPROCESS_NOT_EXERCISED");
}catch(err){
  recorded.runner_error=String(err?.message??err).slice(0,450);
  if(recorded.status==="STARTED")recorded.status="RUNNER_FAILURE";
}finally{
  globalThis.fetch=originals.fetch;
  Object.assign(recorded,classifyEv01NativeResult(recorded));
  await save("receipt.json",recorded);
  console.log(JSON.stringify({status:recorded.status,mode:recorded.mode,
    transport:recorded.transport,backend:recorded.backend,
    provider_calls:recorded.provider_calls,model_returned:recorded.model_returned,
    runner_error:recorded.runner_error,http_status:recorded.http_status??null}));
  if(!recorded.model_returned||recorded.runner_error||
     recorded.status==="EV01_NATIVE_HORIZON_NOT_COMPARABLE")process.exitCode=1;
}
