/** CAF-N independent masked identifiability diagnostic on SAME provider model as B.
 * No Buffalo-native model required; this is explicitly a negative-control
 * diagnostic, not the unmodified Buffalo SD-AI quantitative model generator.
 * Provider calls are zero in --dry-run. One live POST maximum, no retries.
 */
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve,join} from "node:path";
import {CF_MODEL} from "../../../scripts/arena_b_cf_protocol_adapter.mjs";

const args=process.argv.slice(2);
const dry=args.includes("--dry-run");
const infile=resolve(process.env.B_CAFN_INPUT??"artifacts/CAFN-only/B_CAFN_PROVIDER_REQUEST.json");
const out=resolve(process.env.B_CAFN_OUTPUT??"artifacts/CAFN-diagnostic");
const hash=x=>"sha256:"+createHash("sha256").update(typeof x==="string"?x:JSON.stringify(x)).digest("hex");
await mkdir(out,{recursive:false});
let receipt={schema:"igc-caf01-b-negative-diagnostic/0.1",
             status:"INITIAL",provider_model:CF_MODEL,case:"CAFN",
             diagnostic_interface:"DIRECT_SAME_PROVIDER_NOT_BUFFALO_NATIVE_GENERATOR",
             provider_calls_started:0,model_required:false,returned_model:null,
             native_simulations:0,evaluation_truth_read:false,other_arm_data_read:false};
const save=async(name,obj)=>writeFile(join(out,name),JSON.stringify(obj,null,2)+"\n");
try{
  const request=JSON.parse(await readFile(infile,"utf8"));
  const obs=request.public_evidence?.observations;
  if(request.schema!=="igc-caf01-b-independent-provider-request/0.1" ||
     request.case!=="CAFN" ||
     request.task?.type!=="independent_identifiability_diagnosis" ||
     request.task?.native_model_required!==false ||
     request.task?.allow_explicit_abstention!==true ||
     request.task?.independent_native_model_max!==0 ||
     request.source_public_snapshot_sha256!=="sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad" ||
     request.original_public_evidence_file_sha256!=="sha256:8112019ffad402ff1f1e0deafa3b4f1786bb37488258d5c7fe16e0404e22d5a1" ||
     !Array.isArray(obs)||obs.length!==2 ||
     obs[0].t_min!==0||obs[1].t_min!==40||
     obs[0].delivered!==0||obs[1].delivered!==24 ||
     request.isolation?.prior_B_native_model_supplied!==false ||
     request.isolation?.other_arms_results_unavailable!==true ||
     request.isolation?.negative_case_intermediate_observations_supplied!==false)
      throw Error("B_CAFN_UNAUTHORIZED_CONTENT_OR_MASK");
  const system="Independently analyze identifiability of stock-flow mechanisms. "+
    "The evidence consists ONLY of a public input pulse and cumulative deliveries "+
    "at t=0 and t=40 min. You have no prior CAF01 model, intermediate history, "+
    "results from another model/arm or evaluation truth. Never invent unseen intermediate "+
    "observations, assume a unique causal structure, fit a model, or produce executable "+
    "stock-flow model JSON. An explicit INSUFFICIENT_EVIDENCE answer is a valid success. "+
    "Explain alternatives and what additional measurements are needed.";
  const prompt=JSON.stringify({
    public_pulse:request.public_evidence.public_pulse,
    endpoints_only:obs,
    question:request.task.diagnostic_questions,
    acceptable_outcomes:request.task.valid_diagnostic_outcomes
  });
  const schema={
    type:"object",additionalProperties:false,
    properties:{
      diagnosis:{type:"string",enum:request.task.valid_diagnostic_outcomes},
      reasoning:{type:"string"},
      identifiable_features:{type:"array",items:{type:"string"}},
      nonidentifiable_dimensions:{type:"array",items:{type:"string"}},
      alternative_explanations:{type:"array",items:{type:"string"}},
      observations_needed:{type:"array",items:{type:"string"}}
    },
    required:["diagnosis","reasoning","identifiable_features",
              "nonidentifiable_dimensions","alternative_explanations","observations_needed"]
  };
  const payload={messages:[{role:"system",content:system},{role:"user",content:prompt}],
    response_format:{type:"json_schema",json_schema:schema},
    max_completion_tokens:2200,reasoning_effort:"low",stream:false};
  receipt.prompt_sha256=hash(prompt);
  receipt.payload_sha256=hash(payload);
  receipt.input_request_sha256=hash(request);
  await save("B_CAFN_REQUEST_AUDIT.json",{
    scenario:dry?"DRY_RUN":"LIVE",request_sha256:receipt.input_request_sha256,
    prompt_sha256:receipt.prompt_sha256,payload_sha256:receipt.payload_sha256,
    observation_times:[0,40],model_required:false,can_abstain:true,
    no_cross_arm_data:true
  });
  if(dry){
    receipt.status="DRY_RUN_VALIDATED_NO_PROVIDER_CALL";
  }else{
    if(process.env.GITHUB_ACTIONS!=="true"||
       process.env.GITHUB_REPOSITORY!=="yudocyudoc/IGC"||
       process.env.GITHUB_REF!=="refs/heads/main"||
       process.env.GITHUB_RUN_NUMBER!=="1"||
       process.env.GITHUB_RUN_ATTEMPT!=="1"||
       process.env.GITHUB_EVENT_NAME!=="workflow_dispatch"||
       process.env.B_CAFN_AUTH!=="RUN_CAF01_B_TWO_INDEPENDENT_ONCE")
        throw Error("B_CAFN_ONLY_FIRST_AUTHORIZED_MAIN_DISPATCH");
    const account=process.env.CLOUDFLARE_ACCOUNT_ID;
    const token=process.env.CLOUDFLARE_API_TOKEN;
    if(!/^[a-fA-F0-9]{32}$/.test(account??"")||!token)
      throw Error("B_CAFN_CLOUDFLARE_SECRETS_NOT_CONFIGURED");
    receipt.provider_calls_started=1;
    receipt.status="LIVE_PROVIDER_POST_STARTED";
    await save("B_CAFN_CALL_STARTED.json",{
      model:CF_MODEL,payload_sha256:receipt.payload_sha256,attempts_started:1,
      GitHub_run:process.env.GITHUB_RUN_ID
    });
    const response=await fetch(
      "https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+CF_MODEL,
      {method:"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},
       body:JSON.stringify(payload),signal:AbortSignal.timeout(160000)});
    const body=await response.text();
    receipt.http_status=response.status;
    receipt.raw_sha256=hash(body);
    let result;
    try{result=JSON.parse(body);}catch{
      throw Error("B_CAFN_PROVIDER_NON_JSON_RESPONSE");
    }
    await save("B_CAFN_PROVIDER_RAW.json",result);
    if(!response.ok||result?.success!==true)throw Error("B_CAFN_PROVIDER_HTTP_OR_BODY_FAILURE");
    let answer=result?.result?.response??result?.result?.choices?.[0]?.message?.content;
    if(typeof answer==="string")answer=JSON.parse(answer);
    if(!answer||typeof answer!=="object"||Array.isArray(answer)||
       !request.task.valid_diagnostic_outcomes.includes(answer.diagnosis) ||
       typeof answer.reasoning!=="string" ||
       !["identifiable_features","nonidentifiable_dimensions",
         "alternative_explanations","observations_needed"].every(
           k=>Array.isArray(answer[k])&&answer[k].every(s=>typeof s==="string")))
      throw Error("B_CAFN_UNEXPECTED_DIAGNOSTIC_SHAPE");
    await save("B_CAFN_DIAGNOSIS.json",answer);
    receipt.status="ONE_LIVE_MASKED_DIAGNOSTIC_VALID";
    receipt.diagnosis=answer.diagnosis;
    receipt.answer_sha256=hash(answer);
  }
}catch(e){
  receipt.status="B_CAFN_DIAGNOSTIC_BLOCKED_OR_FAILED";
  receipt.error_type=e?.name??"Error";
  receipt.error_reason=String(e?.message??e).slice(0,180);
}finally{
  await save("B_CAFN_RECEIPT.json",receipt);
  console.log(JSON.stringify(receipt));
  if(!["ONE_LIVE_MASKED_DIAGNOSTIC_VALID","DRY_RUN_VALIDATED_NO_PROVIDER_CALL"].includes(receipt.status))
    process.exitCode=1;
}
