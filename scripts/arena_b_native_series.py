"""PT-05: map real Buffalo native material ports to CSV series without edits.

An adapter VIEW only. The original CSV and the historical B assess() contract
remain unchanged. Reject ambiguous graphs rather than guessing name aliases.
"""
from __future__ import annotations
from scripts.arena_b_native_to_modelica import ident
from scripts.arena_b_construction_check import assess

SCHEMA="igc-arena-b-native-series-view/0.1"
ROLES=("pending_work","delivered_work","arrivals","completions")

def require(ok,code):
    if not ok: raise ValueError(code)

def resolve_roles(native, columns):
    model=native.get("model",native) if isinstance(native,dict) else {}
    vs=model.get("variables",[])
    require(isinstance(vs,list) and len(vs)>0,"NATIVE_VARIABLES_MISSING")
    require(len(vs)==len({v.get("name") for v in vs if isinstance(v,dict)}),
            "DUPLICATE_NATIVE_NAME")
    stocks=[v for v in vs if v.get("type")=="stock"]
    flows=[v for v in vs if v.get("type")=="flow"]
    require(len(stocks)==2 and len(flows)==2,"UNSUPPORTED_NATIVE_MATERIAL_GRAPH")
    flow_names={v["name"] for v in flows}
    for s in stocks:
        require(isinstance(s.get("inflows"),list) and
                isinstance(s.get("outflows"),list) and
                all(x in flow_names for x in s["inflows"]+s["outflows"]),
                "INVALID_NATIVE_STOCK_PORTS")
    delivered=[s for s in stocks if len(s["inflows"])==1 and not s["outflows"]]
    pending=[s for s in stocks if len(s["inflows"])==1 and len(s["outflows"])==1]
    require(len(delivered)==len(pending)==1,"AMBIGUOUS_STOCK_ROLES")
    a,b=delivered[0],pending[0]
    completion=a["inflows"][0]
    arrival=b["inflows"][0]
    require(completion==b["outflows"][0] and arrival!=completion and
            {completion,arrival}==flow_names,"AMBIGUOUS_MATERIAL_FLOW_ROLES")
    pairs={"pending_work":b["name"],"delivered_work":a["name"],
           "arrivals":arrival,"completions":completion}
    mapping={role:ident(name) for role,name in pairs.items()}
    require(len(set(mapping.values()))==4,"NATIVE_ROLE_IDENTIFIER_COLLISION")
    require(all(val in columns for val in mapping.values()),"MISSING_NATIVE_CSV_COLUMN")
    return {"schema":SCHEMA,"roles":mapping,"source":"NATIVE_PORT_GRAPH_NOT_COLUMN_GUESS",
            "assumptions":["TWO_STOCK_INFLOW_OUTFLOW_CHAIN",
                           "MODELICA_NATIVE_IDENTIFIER_CONVERSION"],
            "native_equations_changed":False}

def assess_native(rows,visible,native):
    require(isinstance(rows,list) and len(rows)>1,"NATIVE_CSV_ROWS_MISSING")
    mapping=resolve_roles(native,rows[0].keys())
    transformed=[dict(row,**{role:row[column] for role,column
                             in mapping["roles"].items()}) for row in rows]
    result=assess(transformed,visible)
    return {"series_view":mapping,"construction_diagnostic":result,
            "original_csv_mutated":False,"epistemic_status":
            "SUPPLEMENTARY_CONDITIONAL_G2_DESCRIPTIVE_G3_ONLY"}
