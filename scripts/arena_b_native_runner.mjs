/**
 * IGC B-native: invoke ORIGINAL UB-IAD/sd-ai quantitative/engine.js and its
 * ORIGINAL LLMWrapper.js, pinned upstream SHA, without any changes in upstream.
 * A loopback transport bridge ONLY maps bare model alias -> @cf model for
 * Cloudflare compatibility; offline stub mode exercises the same upstream path.
 *
 * This is a scientific smoke test, not structural identification or G2 success.
 */
import { createServer } from "node:http";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";

const ORIGIN="UB-IAD/sd-ai";
const PIN="5199f7b45f3a7ae4a773cb0dd8542940aabe9edc";
const ALIAS="glm-5.3-flash";
const CLOUDFLARE_MODEL="@cf/zai-org/glm-5.3-flash";
const SCHEMA="igc-arena-b-native-engine-proof/0.1";
const sha=x=>"sha256:"+createHash("sha256").update(typeof x==="string"?x:JSON.stringify(x)).digest("hex");
const mode=process.env.BUFFALO_MODE ?? "mock";
const root=resolve(process.env.SDAI_ROOT ?? "");
const artifact=resolve(process.env.BUFFALO_OUTPUT ?? "artifacts/buffalo-node-native");
const input=resolve(process.env.BUFFALO_VISIBLE_INPUT ?? "data/synthetic/arena_b_v0_visible.json");
const results={schema:SCHEMA,origin:ORIGIN,upstream_sha:PIN,engine:"quantitative",
  mode,provider_model:mode==="live"?CLOUDFLARE_MODEL:"OFFLINE_SCHEMA_STUB",
  provider_calls:0,proxy_requests:0,status:"STARTED",native_error:null,
  raw_provider_saved:false,model_returned:false,quant_schema_seen:false,
  no_d_or_m_candidate_inputs:true};
const save=async(name,obj)=>writeFile(join(artifact,name),JSON.stringify(obj,null,2)+"\n");
const fail=(code)=>{throw new Error(code);};
await mkdir(artifact,{recursive:false});
let server;
try {
  if(!["mock","live"].includes(mode))fail("INVALID_MODE");
  if(mode==="live"&&process.env.BUFFALO_LIVE_AUTH!=="ONE_UPSTREAM_CALL")fail("LIVE_NOT_AUTHORIZED");
  const visible=JSON.parse(await readFile(input,"utf8"));
  if(Object.keys(visible).some(k=>/holdout|gold|other.arm/i.test(k)))fail("FORBIDDEN_VISIBLE_FIELDS");
  if(Object.keys(visible.construction??{}).some(k=>/holdout|gold|other.arm/i.test(k)))fail("FORBIDDEN_CONSTRUCTION");
  if(visible.schema!=="igc-arena-visible-input/0.1")fail("INVALID_VISIBLE_INPUT");
  const isEV01=visible.investigation_id==="cafeteria-known-control-a3-b";
  const roundKind=process.env.BUFFALO_ROUND_KIND??"initial";
  if(!["initial","revision"].includes(roundKind))fail("INVALID_ROUND_KIND");
  if(!isEV01&&roundKind!=="initial")fail("LEGACY_REVISION_MODE_FORBIDDEN");
  let ownParent=null, ownFeedback=null;
  if(isEV01){
    const c=visible.construction?.declared_input_reconstruction;
    const cond=visible.observability?.condition_id;
    if(!["O0","O1"].includes(cond) ||
       visible.round_id!=="a3-"+cond.toLowerCase()+"-buffalo-"+roundKind ||
       visible.observability.public_cutoff_minutes_exact!=="10" ||
       c?.policy!=="CAUSAL_RIGHT_RECTANGULAR_EVENT_KERNEL/0.1" ||
       !/^sha256:[a-f0-9]{64}$/.test(c?.signal_sha256??"") ||
       c?.width_minutes_exact!=="1/2" ||
       !Array.isArray(c?.piecewise_constant_segments) ||
       !Array.isArray(c?.event_times_minutes_exact) ||
       c.event_times_minutes_exact.length!==15 ||
       c.mass_not_moved_before_event!==true ||
       c.no_delivery_data_used_to_generate_stimulus!==true)
      fail("EV01_PUBLIC_CAUSAL_INPUT_CONTRACT_MISMATCH");
    results.case_id="EV-01";
    results.condition_id=cond;
    results.round_kind=roundKind;
    results.source_snapshot_hash=visible.source_snapshot_hash;
    results.arrival_signal_sha256=c.signal_sha256;
    results.expected_horizon_hours=1/6;
    results.original_engine_max_tokens=16000;
    if(mode==="live"&&process.env.BUFFALO_EV01_LIVE_AUTH!=="EV01_ONE_ROUND_EXPRESS_AUTH")
      fail("EV01_LIVE_REQUIRES_SEPARATE_AUTHORIZATION");
    if(roundKind==="revision"){
      const parentFile=process.env.BUFFALO_PARENT_NATIVE;
      const receiptFile=process.env.BUFFALO_PARENT_RECEIPT;
      const feedbackFile=process.env.BUFFALO_OWN_FEEDBACK;
      if(!parentFile||!receiptFile||!feedbackFile)fail("EV01_REVISION_PARENT_FEEDBACK_REQUIRED");
      const parent=JSON.parse(await readFile(resolve(parentFile),"utf8"));
      const receipt=JSON.parse(await readFile(resolve(receiptFile),"utf8"));
      const feedback=JSON.parse(await readFile(resolve(feedbackFile),"utf8"));
      const native=parent?.model;
      if(!Array.isArray(native?.variables)||!Array.isArray(native?.relationships) ||
         receipt?.case_id!=="EV-01"||receipt?.condition_id!==cond||
         receipt?.round_kind!=="initial"||
         receipt?.source_snapshot_hash!==visible.source_snapshot_hash||
         receipt?.result_sha256!==sha(parent)||receipt?.model_returned!==true||
         (mode==="live" && (receipt.mode!=="live"||receipt.provider_calls!==1)))
         fail("EV01_PARENT_NOT_OWN_AUTHENTIC_NATIVE_MODEL");
      if(feedback?.schema!=="igc-e02-b-own-feedback/0.1"||
         feedback?.arm!=="B"||feedback?.condition_id!==cond||
         feedback?.source_snapshot_hash!==visible.source_snapshot_hash||
         feedback?.parent_result_sha256!==receipt.result_sha256||
         typeof feedback?.diagnostic!=="object"||feedback.diagnostic===null||
         Object.keys(feedback).some(k=>/holdout|gold|other.arm|private.des/i.test(k)))
         fail("EV01_NOT_OWN_DIAGNOSTIC_FEEDBACK");
      ownParent=parent;
      ownFeedback=feedback;
      results.parent_native_sha256=receipt.result_sha256;
      results.own_feedback_sha256=sha(feedback);
    }
  }else{
    results.original_engine_max_tokens=8000;
    results.round_kind="historical-initial";
  }
  const {default: Engine}=await import(pathToFileURL(join(root,"engines/quantitative/engine.js")).href);
  const {LLMWrapper}=await import(pathToFileURL(join(root,"utilities/LLMWrapper.js")).href);
  const stub={success:true,model:{
    specs:{startTime:0,stopTime:isEV01?1/6:8,dt:isEV01?0.005:0.1,timeUnits:"Hour",integrationMethod:"Euler"},
    variables:[
      {name:"Arrivals",type:"flow",units:"items/hour",inflows:[],outflows:[],
       equation:"1.7",uniflow:true,graphicalFunction:{points:[]},documentation:"New items."},
      {name:"Completions",type:"flow",units:"items/hour",inflows:[],outflows:[],
       equation:"MIN(2, Backlog / 1)",uniflow:true,graphicalFunction:{points:[]},
       documentation:"Items completed."},
      {name:"Backlog",type:"stock",units:"items",inflows:[],outflows:[],
       equation:"0",uniflow:false,graphicalFunction:{points:[]},documentation:"Unfinished work."},
      {name:"Completed",type:"stock",units:"items",inflows:["Completions"],outflows:[],
       equation:"0",uniflow:false,graphicalFunction:{points:[]},documentation:"Finished work."}
    ],
    relationships:[
      {from:"Arrivals",to:"Backlog",reasoning:"Material inflow",polarityReasoning:"Increase",polarity:"+"},
      {from:"Completions",to:"Backlog",reasoning:"Material outflow",polarityReasoning:"Decrease",polarity:"-"},
      {from:"Completions",to:"Completed",reasoning:"Material inflow",polarityReasoning:"Increase",polarity:"+"}
    ],explanation:"Offline stub only.",title:"Offline test"}};
  server=createServer(async(req,res)=>{
    results.proxy_requests++;
    if(req.url!=="/v1/chat/completions"||req.method!=="POST"){
      res.writeHead(404);res.end("NOT_FOUND");return;
    }
    if(results.proxy_requests>1){
      res.writeHead(400);res.end(JSON.stringify({error:{message:"ONE_CALL_GATE",type:"invalid_request_error"}}));return;
    }
    try {
      const parts=[];
      for await(const block of req)parts.push(block);
      const body=JSON.parse(Buffer.concat(parts).toString("utf8"));
      if(body.model!==ALIAS)fail("WRONG_ORIGINAL_ENGINE_MODEL_ROUTE");
      if(body.response_format?.type!=="json_schema")fail("ORIGINAL_STRUCTURED_SCHEMA_ABSENT");
      const desc=body.response_format.json_schema?.schema;
      if(!desc?.properties?.variables||!desc?.properties?.relationships)fail("QUANTITATIVE_SCHEMA_ABSENT");
      results.quant_schema_seen=true;
      results.request_sha256=sha(body);
      await save("request-metadata.json",{
        method:"UB-IAD quantitative/engine.js.generate -> original LLMWrapper",
        schema_type:body.response_format.type,
        request_sha256:results.request_sha256,
        prompt_hashes:body.messages.map(m=>({role:m.role,sha256:sha(m.content)})),
        schema_sha256:sha(desc),original_alias_model:body.model,
        requested_engine_max_tokens:results.original_engine_max_tokens,
        case_id:results.case_id??"LEGACY",round_kind:results.round_kind
      });
      let raw;
      if(mode==="mock"){
        raw={id:"LOCAL-STUB-ONLY",object:"chat.completion",model:ALIAS,
          usage:{prompt_tokens:0,completion_tokens:0,total_tokens:0},
          choices:[{index:0,finish_reason:"stop",message:{role:"assistant",content:JSON.stringify(stub.model)}}]};
      }else{
        const account=process.env.CLOUDFLARE_ACCOUNT_ID, token=process.env.CLOUDFLARE_API_TOKEN;
        if(!/^[a-fA-F0-9]{32}$/.test(account??"")||!token)fail("MISSING_CLOUDFLARE_SECRETS");
        const upstream={...body,model:CLOUDFLARE_MODEL};
        results.provider_calls++;
        // Never retry; only this loopback transport changes model name.
        const response=await fetch(
          "https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/v1/chat/completions",
          {method:"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},
           body:JSON.stringify(upstream),signal:AbortSignal.timeout(135000)}
        );
        results.http_status=response.status;
        const payload=await response.text();
        try{raw=JSON.parse(payload)}catch{raw={provider_error_type:"NON_JSON_RESPONSE",response_excerpt:payload.slice(0,350)}}
        await save("provider-raw.json",raw);
        results.raw_provider_saved=true;
        if(!response.ok)fail("PROVIDER_HTTP_"+response.status);
      }
      results.provider_finish_reason=raw?.choices?.[0]?.finish_reason??null;
      results.provider_usage=raw?.usage??null;
      res.writeHead(200,{"content-type":"application/json"});
      res.end(JSON.stringify(raw));
    } catch(err){
      results.bridge_error=String(err.message??err).slice(0,400);
      res.writeHead(400,{"content-type":"application/json"});
      res.end(JSON.stringify({error:{message:"BRIDGE_FAILURE",type:"invalid_request_error"}}));
    }
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const port=server.address().port;
  process.env.LM_STUDIO_BASE_URL="http://127.0.0.1:"+port;
  const instance=new Engine();
  const parameters={
    underlyingModel:ALIAS,supportsArrays:false,supportsModules:false,
    supportsSubTypes:false,mentorMode:false,
    problemStatement:visible.question,
    backgroundKnowledge:JSON.stringify({construction:visible.construction,
                                         observability:visible.observability,
                                         own_feedback:ownFeedback?ownFeedback.diagnostic:null}),
    maxTokens:results.original_engine_max_tokens,timeoutMinutes:3
  };
  // Upstream Engine.generate receives its OWN native model on revision.
  // Never substitute another arm's or the evaluator's structure.
  const currentModel=ownParent?ownParent.model:{variables:[],relationships:[]};
  const output=await instance.generate(visible.question,currentModel,parameters);
  await save("native-engine-result.json",output);
  results.result_sha256=sha(output);
  results.model_returned=output?.success===undefined &&
    Array.isArray(output?.model?.variables)&&Array.isArray(output?.model?.relationships);
  // Original Engine.generate returns {supportingInfo,model}, not REST success.
  if(output.err)results.native_error=String(output.err).slice(0,450);
  if(results.model_returned){
    results.variable_count=output.model.variables.length;
    results.relationship_count=output.model.relationships.length;
    results.inferred_inflow_by_buffalo=output.model.variables.find(v=>v.name==="Backlog")?.inflows??null;
    results.status=mode==="mock"?"ORIGINAL_ENGINE_OFFLINE_PATH_PASS":"ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED";
  }else{
    results.status="ORIGINAL_ENGINE_NO_NATIVE_MODEL";
  }
  results.llm_wrapper_schema_was_sent=results.quant_schema_seen;
  results.output_horizon_hours=output?.model?.specs?.stopTime??null;
  results.horizon_matches_case=(isEV01?
      Math.abs(results.output_horizon_hours-1/6)<1e-8:
      null);
  if(isEV01 && !results.horizon_matches_case){
    // Never rewrite upstream model output to force the desired horizon.
    results.status="EV01_NATIVE_HORIZON_NOT_COMPARABLE";
  }
  results.upstream_source_modified=false;
  if(mode==="mock" && !results.inferred_inflow_by_buffalo?.includes("Arrivals"))
    fail("BUFFALO_ORIGINAL_POSTPROCESS_NOT_EXERCISED");
} catch(err) {
  results.runner_error=String(err.message??err).slice(0,450);
  if(results.status==="STARTED")results.status="RUNNER_FAILURE";
}finally{
  if(server)await new Promise(done=>server.close(done));
  await save("receipt.json",results);
  console.log(JSON.stringify({status:results.status,mode:results.mode,
    model_returned:results.model_returned,quant_schema_seen:results.quant_schema_seen,
    provider_calls:results.provider_calls,variable_count:results.variable_count,
    native_error:results.native_error,runner_error:results.runner_error,
    bridge_error:results.bridge_error,provider_http_status:results.http_status}));
  if(!results.model_returned||results.runner_error||results.status==='EV01_NATIVE_HORIZON_NOT_COMPARABLE')process.exitCode=1;
}
