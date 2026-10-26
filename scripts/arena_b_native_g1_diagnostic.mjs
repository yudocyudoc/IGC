/**
 * G1 preflight for *unmodified* Buffalo quantitative native output.
 * Advisory diagnostics only: never rewrites, repairs or marks a model executable.
 * Usage: node scripts/arena_b_native_g1_diagnostic.mjs native-output.json [report.json]
 */
import {readFile,writeFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
const sha=x=>"sha256:"+createHash("sha256").update(JSON.stringify(x)).digest("hex");
const id=s=>typeof s==="string"&&/^[A-Za-z][A-Za-z0-9_ ]*$/.test(s);
const unit=s=>typeof s==="string"?s.trim().toLowerCase().replace(/\s+/g,"").replace(/per/g,"/").replace(/hours/g,"hour"):"";
// Deliberately bounded dimensional check: items and hours only; never infer unknown units.
const dim=s=>{const u=unit(s);return ({items:[1,0],item:[1,0],hour:[0,1],"items/hour":[1,-1],"item/hour":[1,-1],dimensionless:[0,0],"1":[0,0]})[u]??null};
const symbols=s=>(s.match(/[A-Za-z_][A-Za-z0-9_]*/g)||[]);
const fns=new Set(["MIN","MAX","ABS","EXP","LN","LOG","SQRT","SIN","COS","TAN","IF","THEN","ELSE","TIME","PI","PULSE","STEP","DELAY","SMOOTH","AND","OR","NOT"]);
export function diagnose(document){
 const model=document?.model??document;
 const issues=[],variables=Array.isArray(model?.variables)?model.variables:[];
 const relationships=Array.isArray(model?.relationships)?model.relationships:[];
 const add=(code,path,detail,category="G1")=>issues.push({code,path,detail,category});
 if(!Array.isArray(model?.variables))add("VARIABLES_MISSING","model.variables","Expected array");
 if(!Array.isArray(model?.relationships))add("RELATIONSHIPS_MISSING","model.relationships","Expected array");
 const names=new Map(),normalized=new Map();
 for(let i=0;i<variables.length;i++){
  const v=variables[i],p=`model.variables[${i}]`;
  if(!id(v?.name)){add("INVALID_NAME",p+".name",String(v?.name));continue;}
  if(names.has(v.name))add("DUPLICATE_NAME",p+".name",v.name);
  names.set(v.name,v);normalized.set(v.name.replace(/ /g,"_"),v.name);
  if(!["stock","flow","variable"].includes(v.type))add("INVALID_TYPE",p+".type",String(v.type));
  if(typeof v.equation!=="string"||!v.equation.trim())add("MISSING_EQUATION",p+".equation","No usable expression");
  if(v.type==="stock"&&!Number.isFinite(Number(v.equation)))add("NON_NUMERIC_STOCK_INITIAL",p+".equation",String(v.equation));
 }
 for(let i=0;i<variables.length;i++){
  const v=variables[i],p=`model.variables[${i}]`; if(!v||typeof v.equation!=="string")continue;
  const e=v.equation.trim();
  if(e.includes("//"))add("ZERO_SAFE_DIVISION_REQUIRES_ADAPTER",p+".equation",e,"ADAPTER");
  if(/\/\*|\*\//.test(e))add("UNSUPPORTED_COMMENT_SYNTAX",p+".equation",e);
  if(/\b(profile over time|TBD|unknown|placeholder)\b/i.test(e))add("PROSE_OR_PLACEHOLDER",p+".equation",e);
  if(v.type!=="stock"){
   // Buffalo explicitly defines // as zero-safe division: it is NOT an upstream syntax error.
   const mul=e.match(/^([A-Za-z][A-Za-z0-9_]*)\s*\*\s*([A-Za-z][A-Za-z0-9_]*)$/);
   if(mul){const left=names.get(normalized.get(mul[1])),right=names.get(normalized.get(mul[2]));
    const l=dim(left?.units),r=dim(right?.units),expected=dim(v.units);
    if(l&&r&&expected&&(l[0]+r[0]!==expected[0]||l[1]+r[1]!==expected[1]))
      add("DIMENSIONAL_PRODUCT_MISMATCH",p+".equation",`${mul[1]} [${left.units}] * ${mul[2]} [${right.units}] is inconsistent with ${v.units}`);
   }
   if(!/^[A-Za-z0-9_ .,+*\/%^()<>!=?:-]+$/.test(e))add("UNSUPPORTED_EXPRESSION_CHARACTERS",p+".equation",e);
   for(const s of symbols(e)){if(normalized.has(s)||fns.has(s.toUpperCase()))continue;
    add("UNRESOLVED_SYMBOL",p+".equation",s);
   }
  }
  if(v.type==="stock"){
   for(const direction of ["inflows","outflows"]){
    if(v[direction]!==undefined&&!Array.isArray(v[direction])){add("INVALID_FLOW_PORTS",p+"."+direction,"Expected array");continue;}
    for(const name of v[direction]||[]){
     const flow=names.get(name);
     if(!flow||flow.type!=="flow"){add("UNRESOLVED_FLOW_PORT",p+"."+direction,String(name));continue;}
     const su=unit(v.units),fu=unit(flow.units);
     if(su&&fu&&fu!==su+"/hour"&&fu!==su+"/hours"&&fu!==su+"/h")
      add("STOCK_FLOW_UNIT_MISMATCH",p+"."+direction,`${v.name} [${v.units}] ← ${name} [${flow.units}]`);
    }
   }
  }
 }
 for(let i=0;i<relationships.length;i++){
  const r=relationships[i];
  if(!names.has(r?.from)||!names.has(r?.to))add("DANGLING_RELATIONSHIP",`model.relationships[${i}]`,`${r?.from} → ${r?.to}`);
 }
 return {schema:"igc-b-native-g1-preflight/0.1",source_sha256:sha(document),
  variable_count:variables.length,relationship_count:relationships.length,
  stock_count:variables.filter(v=>v?.type==="stock").length,
  flow_count:variables.filter(v=>v?.type==="flow").length,
  status:issues.some(i=>i.category==="G1")?"G1_ISSUES_FOUND":(issues.length?"ADAPTER_LIMITATIONS_ONLY":"PREFLIGHT_NO_OBVIOUS_ISSUES_NOT_G1_PASS"),
  g1_certified:false,g2_executed:false,g3_supported:false,
  limitations:["Expression checks are lexical; dimensional product check only handles known items/hour units.",
   "Buffalo // is defined as zero-safe division; a Modelica adapter must preserve that semantics.",
   "A clean preflight does not imply translator compatibility, physical consistency or valid causal mechanism.",
   "Native document is never modified."],issues};
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
 const source=process.argv[2],out=process.argv[3];
 if(!source){console.error("Usage: node scripts/arena_b_native_g1_diagnostic.mjs native-output.json [report.json]");process.exit(2);}
 const raw=JSON.parse(await readFile(source,"utf8"));const result=diagnose(raw);
 if(out)await writeFile(out,JSON.stringify(result,null,2)+"\n");
 console.log(JSON.stringify(result,null,2));
}
