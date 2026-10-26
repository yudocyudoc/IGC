"""Arena B0: original Buffalo quantitative process -> native sd-json -> faithful Modelica.

The generator is a separate LLM using the original, pinned UB SD-AI prompt.
This file only builds the provider-neutral request and validates/translates the
LLM's native response; it NEVER synthesizes a missing stock, flow or equation.

B0 smoke fixture is illustrative and handwritten: not an SD-AI inference run.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
from pathlib import Path

from scripts.arena_v0_contract import (
    SUBMISSION_SCHEMA, arm_view, canonical, digest, trace_event, validate_submission
)

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "data/buffalo-sdai/quantitative_system_scalar.txt"
SOURCE_COMMIT = "5199f7b45f3a7ae4a773cb0dd8542940aabe9edc"
METHOD = "sd-ai-quantitative-scalar-prompt-port/0.1"
SCHEMA = "igc-arena-b-buffalo-native/0.1"
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 ]{0,59}$")
FUNCTIONS = {"MIN": "min", "MAX": "max", "ABS": "abs"}
MAX_VARIABLES = 36


class BuffaloBridgeError(ValueError):
    """Native B model invalid or unsupported by this deliberately bounded adapter."""


def check(condition, code):
    if not condition:
        raise BuffaloBridgeError(code)


def ident(name):
    check(type(name) is str and NAME_RE.fullmatch(name) is not None
          and len(name.split()) <= 5, "INVALID_SD_AI_VARIABLE_NAME")
    return "_".join(name.split())


def encode_expression(equation, declared):
    """Allow arithmetic subset only. Never repair or add an unknown mechanism."""
    check(type(equation) is str and 0 < len(equation) <= 250, "MISSING_OR_LONG_EQUATION")
    normalized = equation.strip().replace("^", "**")
    # Buffalo's quantitative conventions: variable-name references use underscores.
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as exc:
        raise BuffaloBridgeError("UNSUPPORTED_SD_AI_EQUATION_SYNTAX") from exc

    dependencies = set()

    def emit(node):
        if isinstance(node, ast.Constant):
            check(type(node.value) in (int, float) and math.isfinite(node.value),
                  "INVALID_NUMERIC_CONSTANT")
            return repr(node.value)
        if isinstance(node, ast.Name):
            if node.id == "TIME":
                return "time"
            check(node.id in declared, "UNKNOWN_EQUATION_SYMBOL:" + node.id)
            dependencies.add(node.id)
            return node.id
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return ("+" if isinstance(node.op, ast.UAdd) else "-") + "(" + emit(node.operand) + ")"
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult,
                                                               ast.Div, ast.Pow)):
            left, right = emit(node.left), emit(node.right)
            operator = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*",
                        ast.Div: "/", ast.Pow: "^"}[type(node.op)]
            return "(" + left + " " + operator + " " + right + ")"
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id.upper() in FUNCTIONS and not node.keywords):
            count = 1 if node.func.id.upper() == "ABS" else 2
            check(len(node.args) == count, "INVALID_FUNCTION_ARITY")
            return FUNCTIONS[node.func.id.upper()] + "(" + ", ".join(emit(a) for a in node.args) + ")"
        raise BuffaloBridgeError("UNSUPPORTED_SD_AI_EQUATION_EXPRESSION")

    return emit(tree.body), dependencies


def make_request(visible):
    view = arm_view(visible, "B")
    raw = PROMPT_PATH.read_text(encoding="utf-8")
    check("MANDATORY PROCESS - Execute these steps in order:" in raw
          and "STEP 4 - WRITE EQUATIONS:" in raw and "STEP 5 - VERIFY MODEL VALIDITY:" in raw,
          "UPSTREAM_BUFFALO_PROMPT_MISSING")
    # The same EVIDENCE as D and M, not their model candidates or result.
    context = {"construction": visible["construction"],
               "observability": visible["observability"]}
    user = ("Problem statement:\n" + visible["question"] +
            "\n\nBackground knowledge supplied to the modeler:\n" +
            json.dumps(context, ensure_ascii=False, sort_keys=True) +
            "\n\nProduce a stock-flow model in the native SD-AI sd-json "
            "response structure, or explain that evidence is insufficient.")
    return {"schema": SCHEMA, "arm_id": "B", "upstream": "UB-IAD/sd-ai",
            "upstream_commit": SOURCE_COMMIT, "method": METHOD,
            "input_hash": view["input_hash"], "currentModel": {
                "variables": [], "relationships": []},
            "supportsArrays": False, "supportsModules": False,
            "supportsSubTypes": False, "mentorMode": False,
            "prompt": {"system": raw, "user": user},
            "prompt_sha256": "sha256:" + hashlib.sha256(raw.encode()).hexdigest(),
            "provider_status": "NOT_CALLED_PREPARATION_ONLY"}


def validate_model(native):
    """Accept Buffalo sd-json as-is; restrict translator capabilities honestly."""
    check(type(native) is dict and set(native) <= {"variables", "relationships", "specs"}
          and {"variables", "relationships"} <= set(native), "NOT_SD_AI_JSON")
    vs, rs = native["variables"], native["relationships"]
    check(type(vs) is list and 1 <= len(vs) <= MAX_VARIABLES and
          type(rs) is list and len(rs) <= 80, "MODEL_SIZE_OUT_OF_BOUNDS")
    by_name = {}
    slug_names = set()
    stocks, flows = [], []
    for v in vs:
        check(type(v) is dict and {"name", "type", "equation"} <= set(v) and
              set(v) <= {"name", "type", "equation", "units", "uniflow",
                         "inflows", "outflows", "documentation"},
              "UNSUPPORTED_VARIABLE_FEATURE")
        slug = ident(v["name"])
        check(slug not in slug_names and slug != "time", "DUPLICATE_OR_RESERVED_NAME")
        slug_names.add(slug)
        kind = v["type"]
        check(kind in {"stock", "flow", "variable"}, "UNSUPPORTED_VARIABLE_TYPE")
        check(type(v.get("equation")) is str and bool(v["equation"].strip()),
              "MISSING_EQUATION")
        if "units" in v:
            check(type(v["units"]) is str and len(v["units"]) <= 40,
                  "INVALID_UNIT")
        if "uniflow" in v:
            check(kind == "flow" and type(v["uniflow"]) is bool,
                  "UNIFLOW_ONLY_FOR_FLOWS")
        if kind == "stock":
            check(type(v.get("inflows", [])) is list and
                  type(v.get("outflows", [])) is list,
                  "BAD_STOCK_FLOW_PORTS")
            check(set(v.get("inflows", [])).isdisjoint(v.get("outflows", [])),
                  "STOCK_FLOW_DUPLICATED_BOTH_DIRECTIONS")
            check(len(v.get("inflows", [])) + len(v.get("outflows", [])) >= 1,
                  "UNCONNECTED_STOCK")
            check(len(v.get("inflows", [])) == len(set(v.get("inflows", [])))
                  and len(v.get("outflows", [])) == len(set(v.get("outflows", []))),
                  "DUPLICATE_STOCK_FLOW_PORT")
            try:
                initial = float(v["equation"])
            except ValueError as exc:
                raise BuffaloBridgeError("STOCK_INITIAL_VALUE_MUST_BE_NUMERIC") from exc
            check(math.isfinite(initial) and initial >= 0, "NONFINITE_OR_NEGATIVE_INITIAL_STOCK")
            stocks.append(v)
        else:
            check("inflows" not in v and "outflows" not in v,
                  "ONLY_STOCKS_HAVE_FLOW_PORTS")
            if kind == "flow":
                flows.append(v)
        by_name[v["name"]] = v
    check(1 <= len(stocks) <= 8 and 1 <= len(flows) <= 18,
          "STOCK_OR_FLOW_REQUIRED")
    uses = {}
    for stock in stocks:
        for field in ("inflows", "outflows"):
            for flow in stock.get(field, []):
                check(flow in by_name and by_name[flow]["type"] == "flow",
                      "STOCK_REFERS_TO_UNKNOWN_FLOW")
                uses.setdefault(flow, []).append((stock["name"], field))
                # No unit inference and no conversion: incompatible unit strings fail closed.
                if stock.get("units") and by_name[flow].get("units"):
                    check(by_name[flow]["units"] == stock["units"] + "/hour",
                          "STOCK_FLOW_UNIT_INCOMPATIBLE")
    for flow in flows:
        edges = uses.get(flow["name"], [])
        check(1 <= len(edges) <= 2, "UNUSED_OR_MULTI_DUPLICATED_MATERIAL_FLOW")
        if len(edges) == 2:
            check({direction for _, direction in edges} == {"inflows", "outflows"},
                  "DUPLICATED_MATERIAL_FLOW")
    declared = set(slug_names)
    for v in vs:
        if v["type"] != "stock":
            encode_expression(v["equation"], declared)
    for rel in rs:
        check(type(rel) is dict and {"from", "to", "polarity"} <= set(rel) and
              set(rel) <= {"from", "to", "polarity", "reasoning", "polarityReasoning"},
              "INVALID_CAUSAL_RELATIONSHIP")
        check(rel["from"] in by_name and rel["to"] in by_name and
              rel["from"] != rel["to"] and rel["polarity"] in ("+", "-", ""),
              "DANGLING_OR_INVALID_CAUSAL_EDGE")
    specs=native.get("specs", {})
    check(type(specs) is dict and set(specs) <= {"startTime", "stopTime", "timeUnits", "dt"},
          "UNSUPPORTED_SD_AI_SPECS")
    if "startTime" in specs or "stopTime" in specs:
        check(type(specs.get("startTime", 0)) in (int,float) and
              type(specs.get("stopTime", 8)) in (int,float) and
              0 <= specs.get("startTime",0) < specs.get("stopTime",8) <= 96,
              "INVALID_MODEL_TIME_BOUNDS")
    check(specs.get("timeUnits", "Hour") in ("Hour", "Hours", "hour"),
          "UNSUPPORTED_TIME_UNIT")
    if "dt" in specs:
        check(type(specs["dt"]) in (int,float) and 0 < specs["dt"] <= 1,
              "INVALID_MODEL_DT")
    return {"stocks": stocks, "flows": flows, "name_map": {
        v["name"]: ident(v["name"]) for v in vs},
        "variables": vs, "relationships": rs,
        "specs": specs, "status": "G1_BOUNDED_SD_JSON_ACCEPTED_NOT_PHYSICALLY_VALIDATED"}


def render_model(native):
    parsed=validate_model(native)
    digest_id=digest(native)[7:19]
    model_name="BuffaloSFD_" + digest_id
    names=parsed["name_map"]
    decls=[]
    eqs=[]
    stocks=[]
    for v in parsed["variables"]:
        slug=names[v["name"]]
        if v["type"] == "stock":
            decls.append(f"  Real {slug}(start={float(v['equation']):.12g}, fixed=true);")
            stocks.append(v)
        else:
            expr,_=encode_expression(v["equation"], set(names.values()))
            if v["type"] == "flow" and v.get("uniflow") is True:
                expr="max(0, " + expr + ")"
            # Literal constants become parameters to avoid unnecessary DAE unknowns.
            if v["type"] == "variable" and re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",v["equation"].strip()):
                decls.append(f"  parameter Real {slug} = {expr};")
            else:
                decls.append(f"  Real {slug};")
                eqs.append(f"  {slug} = {expr};")
    for stock in stocks:
        inc=[names[x] for x in stock.get("inflows", [])]
        out=[names[x] for x in stock.get("outflows", [])]
        inflow=" + ".join(inc) if inc else "0"
        outflow=" + ".join(out) if out else "0"
        eqs.append(f"  der({names[stock['name']]}) = ({inflow}) - ({outflow});")
    lines=[
        f"model {model_name}",
        "  // Buffalo SD-AI native SFD translation; no molecular decomposition.",
        "  // SOURCE LOGIC: every variable/equation is taken from submitted SD-JSON.",
        *decls,"equation",*eqs, f"end {model_name};",""
    ]
    return model_name, "\n".join(lines)


def accept(visible, response, output):
    """Response must be an actual arm-supplied SD-JSON envelope or fixture marked."""
    view=arm_view(visible,"B")
    check(type(response) is dict and set(response) == {"origin", "model", "source"}
          and response["origin"] in ("UPSTREAM_PROVIDER_OUTPUT", "HANDWRITTEN_SYNTHETIC_FIXTURE"),
          "INVALID_RESPONSE_PROVENANCE")
    check(type(response["source"]) is str and len(response["source"]) <= 160,
          "MISSING_RESPONSE_SOURCE")
    native=response["model"]
    model_name,modelica=render_model(native)
    out=Path(output)
    check(not out.exists(), "OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True,exist_ok=False)
    (out/"sd-ai-native.json").write_bytes(canonical(response)+b"\n")
    (out/(model_name+".mo")).write_text(modelica,encoding="utf-8")
    basis={"native":response,"modelica_hash":"sha256:"+hashlib.sha256(modelica.encode()).hexdigest(),
           "input_hash":view["input_hash"],"upstream_commit":SOURCE_COMMIT}
    (out/"manifest.json").write_bytes(canonical(basis)+b"\n")
    hypid="B-"+digest(native)[7:19]
    submission={"schema":SUBMISSION_SCHEMA,"arm_id":"B",
        "round_id":visible["round_id"],"iteration":0,"parent_revision_id":None,
        "native_artifact_sha256":digest(response),"method_version":METHOD,
        "hypothesis_ids":[hypid],"status":"PROPOSED",
        "unknowns":["STRUCTURAL_IDENTIFICATION_NOT_ESTABLISHED",
                    "MODEL_NOT_VALIDATED_UNDER_INTERVENTIONS"],
        "assumption_ids":["BU_ALGEBRAIC_SUBSET"],
        "evidence_refs":[visible["source_snapshot_hash"]],
        "notes":"Modelica generated from native SD-AI sd-json; not an inference proof."}
    validate_submission(view,submission)
    event=trace_event(arm_id="B",round_id=visible["round_id"],
                      event_type="HYPOTHESIS_PROPOSED",iteration=0,
                      source_hash=view["input_hash"],payload_hash=digest(response))
    (out/"submission.json").write_bytes(canonical(submission)+b"\n")
    (out/"memory-event.json").write_bytes(canonical(event)+b"\n")
    return {"status":"B0_G0_G1_TRANSLATED", "arm":"B", "model":model_name,
            "source_origin":response["origin"], "hypothesis_id":hypid,
            "source_hash":digest(response),
            "proof_limit":"NO_CAUSAL_IDENTIFICATION_NO_PROVIDER_ASSERTION"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["prepare","accept"])
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--response",type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    visible=json.loads(args.input.read_text())
    if args.command=="prepare":
        payload=make_request(visible)
        check(not args.out.exists(),"OUTPUT_ALREADY_EXISTS")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_bytes(canonical(payload)+b"\n")
        print(json.dumps({"status":"B_PROVIDER_NOT_CALLED",
                          "upstream_commit":SOURCE_COMMIT,
                          "request_hash":digest(payload)}))
    else:
        check(args.response is not None, "RESPONSE_REQUIRED")
        result=accept(visible,json.loads(args.response.read_text()),args.out)
        print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
