#!/usr/bin/env python3
"""CAF-15B: sound rational interval exclusion for two independent service durations.

Scientific verdicts are exclusively: verified rational witness, verified
exhaustive box cover, or unresolved. No sampling-based GLOBAL_SEPARATION.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
from functools import lru_cache
from itertools import combinations, product
from hashlib import sha256
import json
from pathlib import Path

import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
import caf14_excitation_temporal_windows as v14
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf15b-certified-two-free-capacity-exclusion/0.1"
PROTOCOL_FIRST="eb2d48d227c7c3dc20fca18fd6a0e320a7afbbb5"
GATE="BLOCKED_DETERMINISTIC_SAME_DES_UNCALIBRATED_SENSOR_NO_EXTERNAL_VALIDATION"
PROGRAMS=("F_R25_T20","F_R25_T25")
TOL=1
MAX_NODES=5000
MAX_DEPTH=32
D_LOW=Q(6,11)
D_HIGH=Q(12,11)
FULL=(("waiting","preparacion"),("waiting","despacho"),("waiting","entrega"),
      ("stage_stock","preparacion"),("stage_stock","despacho"),
      ("stage_stock","entrega"))
FAMILIES=tuple(v11.models())


def need(ok,msg):
    if not ok:
        raise ValueError(msg)


def probe_def(program):
    need(program in PROGRAMS,"CAF15B_PROGRAM_NOT_FROZEN")
    probes=v14.frozen_programs()[program]
    need(len(probes)==3 and tuple(probes[-1]["channels"])==FULL,
         "CAF15B_PROBE_SCHEMA_DRIFT")
    return probes


def stage_service(stages,ds,s):
    return ds[stages.index(s)] if s in stages else Q(1)


@lru_cache(maxsize=120000)
def clock_counts(stages,ds,rate,minute):
    """Independent exact FCFS recurrence; no grids, floats or approximations.

    Monotonicity in each duration is inherited by every event start/end
    because incoming, max and addition preserve coordinate monotonicity.
    """
    need(tuple(stages) in v11.STAGE_SETS,"CAF15B_UNKNOWN_FAMILY")
    need(len(stages)==len(ds) and all(
         D_LOW<=x<=D_HIGH for x in ds),"CAF15B_BAD_DURATION")
    arrivals=des.half_open_arrivals(rate,20)
    inputs=[]; starts=[]; ends=[]
    for s in range(3):
        nservers=1 if s in stages else 2
        service=stage_service(stages,ds,s)
        stage_a=[]; stage_b=[]; stage_f=[]
        for i,when in enumerate(arrivals):
            enter=when if s==0 else ends[s-1][i]
            server_free=stage_f[i-nservers] if i>=nservers else Q(0)
            began=max(enter,server_free)
            stage_a.append(enter)
            stage_b.append(began)
            stage_f.append(began+service)
        inputs.append(stage_a)
        starts.append(stage_b)
        ends.append(stage_f)
    # Event times from the same index are nondecreasing under this scope.
    def cnt(arr):
        return sum(when<=minute for when in arr)
    return {
        "arrivals":tuple(cnt(x) for x in inputs),
        "starts":tuple(cnt(x) for x in starts),
        "ends":tuple(cnt(x) for x in ends),
    }


def signature(stages,ds,program):
    res=[]
    for probe in probe_def(program):
        counts=clock_counts(tuple(stages),tuple(ds),probe["rate"],probe["minute"])
        for field,stage in probe["channels"]:
            if field=="delivered":
                need(stage is None,"CAF15B_BAD_DELIVERY_CHANNEL")
                res.append(counts["ends"][-1])
            else:
                i=b.STAGES.index(stage)
                incoming=counts["arrivals"][i]
                if field=="waiting":
                    val=incoming-counts["starts"][i]
                elif field=="stage_stock":
                    val=incoming-counts["ends"][i]
                else:
                    raise ValueError("CAF15B_BAD_CHANNEL")
                need(val>=0,"CAF15B_NEGATIVE_PHYSICAL_STOCK")
                res.append(val)
    need(len(res)==8,"CAF15B_BAD_SIGNATURE_LENGTH")
    return tuple(res)


def bounds(stages,box,program):
    """Rigorous outer interval for every integer signature coordinate.

    Every event clock is componentwise nondecreasing in duration, so
    the faster corner (all lower durations) and slower corner (all upper)
    rigorously bound each component count. Differences widen safely.
    """
    need(len(stages)==len(box) and
         all(D_LOW<=l<=h<=D_HIGH for l,h in box),"CAF15B_BAD_BOX")
    faster=tuple(l for l,h in box)
    slower=tuple(h for l,h in box)
    result=[]
    for probe in probe_def(program):
        quick=clock_counts(tuple(stages),faster,probe["rate"],probe["minute"])
        slow=clock_counts(tuple(stages),slower,probe["rate"],probe["minute"])
        for field,stage in probe["channels"]:
            if field=="delivered":
                lower=slow["ends"][-1]
                upper=quick["ends"][-1]
            else:
                i=b.STAGES.index(stage)
                arrived_min=slow["arrivals"][i]
                arrived_max=quick["arrivals"][i]
                other="starts" if field=="waiting" else "ends"
                lower=max(0,arrived_min-quick[other][i])
                upper=max(0,arrived_max-slow[other][i])
            need(lower<=upper,"CAF15B_INVALID_BOUNDS")
            result.append((lower,upper))
    need(len(result)==8,"CAF15B_INVALID_BOUNDS_VECTOR")
    return tuple(result)


def exclusion_channel(aa,bb):
    """Returns sound exclusion certificate for one integer channel, or None."""
    need(len(aa)==len(bb)==8,"CAF15B_MISMATCHED_BOUND_LENGTH")
    for j,((al,ah),(bl,bh)) in enumerate(zip(aa,bb)):
        if al>bh+2*TOL:
            return j
        if bl>ah+2*TOL:
            return j
    return None


def close_signatures(a,z):
    need(len(a)==len(z)==8,"CAF15B_BAD_WITNESS_LEN")
    return max(abs(x-y) for x,y in zip(a,z))<=2*TOL


def common_reading(a,z):
    need(close_signatures(a,z),"CAF15B_NO_COMMON_READ")
    y=tuple(max(0,x-TOL,t-TOL) for x,t in zip(a,z))
    need(all(abs(yi-x)<=TOL and abs(yi-t)<=TOL
             for yi,x,t in zip(y,a,z)), "CAF15B_BAD_COMMON_READING")
    return y


def rational_models():
    return [(m["id"],tuple(m["stages"]),m["label"]) for m in FAMILIES]


def initial_boxes(sa,sb):
    return (tuple((D_LOW,D_HIGH) for _ in sa),
            tuple((D_LOW,D_HIGH) for _ in sb))


def endpoints_midpoints(box):
    low=tuple(a for a,z in box)
    mid=tuple((a+z)/2 for a,z in box)
    high=tuple(z for a,z in box)
    return (low,mid,high)


def find_witness(sa,sb,box_a,box_b,pid):
    # Fixed candidate order, not conditioned on evaluator truth.
    samples_a={ds:signature(sa,ds,pid) for ds in endpoints_midpoints(box_a)}
    samples_b={ds:signature(sb,ds,pid) for ds in endpoints_midpoints(box_b)}
    for da,xa in samples_a.items():
        for db,xb in samples_b.items():
            if close_signatures(xa,xb):
                return {
                    "duration_a":[str(v) for v in da],
                    "duration_b":[str(v) for v in db],
                    "capacity_a":[str(Q(60)/v) for v in da],
                    "capacity_b":[str(Q(60)/v) for v in db],
                    "signature_a":list(xa),"signature_b":list(xb),
                    "common_reading":list(common_reading(xa,xb)),
                }
    return None


def split_dim(box_a,box_b,lim_a,lim_b):
    score_a=sum(h-l for l,h in lim_a)
    score_b=sum(h-l for l,h in lim_b)
    which=0 if score_a>=score_b else 1
    box=box_a if which==0 else box_b
    # All dimensions have the same initial domain length.
    index=max(range(len(box)),key=lambda i: (box[i][1]-box[i][0],-i))
    return which,index


def partition_box(box,index,mid):
    need(box[index][0]<mid<box[index][1],"CAF15B_BAD_SPLIT_MID")
    low=list(box);high=list(box)
    low[index]=(box[index][0],mid)
    high[index]=(mid,box[index][1])
    return tuple(low),tuple(high)


def run_pair(sa,sb,program,max_nodes=MAX_NODES,max_depth=MAX_DEPTH):
    need(sa!=sb,"CAF15B_IDENTICAL_PAIR")
    need(tuple(sa) in v11.STAGE_SETS and tuple(sb) in v11.STAGE_SETS,
         "CAF15B_UNKNOWN_PAIR")
    box_a,box_b=initial_boxes(sa,sb)
    stats={"nodes":0,"excluded_leaves":0,"deepest":0,"unresolved_leaves":0}
    witness=None
    # Exact proof tree: X = excluded, S = split, U = unresolved; a witness
    # terminates work because existence is proved regardless of other regions.
    def visit(a,z,depth):
        nonlocal witness
        if witness is not None:
            return {"type":"UNVISITED_AFTER_WITNESS"}
        if stats["nodes"]>=max_nodes:
            stats["unresolved_leaves"]+=1
            return {"type":"U","reason":"NODE_BUDGET"}
        stats["nodes"]+=1
        stats["deepest"]=max(stats["deepest"],depth)
        aa=bounds(sa,a,program)
        bb=bounds(sb,z,program)
        j=exclusion_channel(aa,bb)
        if j is not None:
            stats["excluded_leaves"]+=1
            return {"type":"X","channel":j}
        candidate=find_witness(sa,sb,a,z,program)
        if candidate is not None:
            witness=candidate
            return {"type":"W"}
        if depth>=max_depth or not any(l<h for l,h in a+z):
            stats["unresolved_leaves"]+=1
            return {"type":"U","reason":"MAX_DEPTH_OR_ATOM"}
        which,index=split_dim(a,z,aa,bb)
        box=a if which==0 else z
        lo,hi=box[index]
        mid=(lo+hi)/2
        left,right=partition_box(box,index,mid)
        if which==0:
            first=visit(left,z,depth+1)
            second=visit(right,z,depth+1) if witness is None else {
                "type":"UNVISITED_AFTER_WITNESS"}
        else:
            first=visit(a,left,depth+1)
            second=visit(a,right,depth+1) if witness is None else {
                "type":"UNVISITED_AFTER_WITNESS"}
        return {"type":"S","family":which,"dim":index,
                "mid":str(mid),"left":first,"right":second}
    tree=visit(box_a,box_b,0)
    if witness is not None:
        verdict="CONFUSABLE_WITNESS_CERTIFIED"
    elif stats["unresolved_leaves"]:
        verdict="UNRESOLVED_NOT_CERTIFIED"
    else:
        verdict="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED"
    result={"verdict":verdict,"stats":stats,"witness":witness}
    if verdict=="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED":
        need(verify_exclusion_tree(sa,sb,program,tree),
             "CAF15B_CERTIFICATE_VERIFICATION_FAIL")
        result["certificate_tree"]=tree
        result["independent_tree_verification"]=True
    elif verdict=="UNRESOLVED_NOT_CERTIFIED":
        result["unresolved_reason"]="NODE_BUDGET_OR_DEPTH"
    return result


def verify_exclusion_tree(sa,sb,pid,tree):
    """Independent certificate replay, DOES NOT trust search's exclusions.

    Reconstructs cover recursively from a full closed root. Each leaf X must
    pass re-evaluation of its exact rational bounds. Unknown or witness leaves
    fail certification. Every binary split must strictly bisect declared axis.
    """
    need(tuple(sa) in v11.STAGE_SETS and tuple(sb) in v11.STAGE_SETS,
         "CAF15B_VERIFIER_UNKNOWN_MODEL")
    root_a,root_b=initial_boxes(sa,sb)
    def check(a,z,node):
        kind=node.get("type")
        if kind=="X":
            j=node.get("channel")
            if type(j) is not int or not (0<=j<8):
                return False
            aa=bounds(sa,a,pid)
            bb=bounds(sb,z,pid)
            x=aa[j];y=bb[j]
            return x[0]>y[1]+2*TOL or y[0]>x[1]+2*TOL
        if kind=="S":
            which=node.get("family");i=node.get("dim")
            if type(which) is not int or which not in (0,1) or type(i) is not int:
                return False
            box=a if which==0 else z
            if not(0<=i<len(box)):
                return False
            mid=Q(node["mid"])
            # Exact midpoint convention makes missing or overlapping
            # interior portions impossible to smuggle into the certificate.
            if mid!=(box[i][0]+box[i][1])/2:
                return False
            low,high=partition_box(box,i,mid)
            if which==0:
                return check(low,z,node["left"]) and check(high,z,node["right"])
            return check(a,low,node["left"]) and check(a,high,node["right"])
        return False
    try:
        return check(root_a,root_b,tree)
    except (ValueError,KeyError,TypeError,ZeroDivisionError):
        return False


def physical_signature(stages,ds,pid):
    """Independent native DES observation for all K0/K1/T probes."""
    config={
        "schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
        "stages":[{
            "servers":1 if s in stages else 2,
            "service_minutes":str(stage_service(stages,ds,s)),
        } for s in range(3)]
    }
    des.validate_private_config(config)
    observed=[]
    for p in probe_def(pid):
        arrivals=des.half_open_arrivals(p["rate"],20)
        snap=des.run_toy_engine(config,arrivals,
                               (Q(0),Q(p["minute"])))[-1]
        stock=[a+f for a,f in zip(snap.stage_waiting,snap.stage_in_service)]
        need(snap.accepted_cum_orders==snap.delivered_cum_orders+sum(stock),
             "CAF15B_DES_MASS_BALANCE")
        for field,stage in p["channels"]:
            if field=="delivered":
                observed.append(snap.delivered_cum_orders)
            else:
                i=b.STAGES.index(stage)
                observed.append(snap.stage_waiting[i] if field=="waiting"
                                else stock[i])
    return tuple(observed)


def verify_witness(sa,sb,pid,w):
    try:
        da=tuple(Q(d) for d in w["duration_a"])
        db=tuple(Q(d) for d in w["duration_b"])
        if len(sa)!=len(da) or len(sb)!=len(db):
            return False
        if not all(D_LOW<=x<=D_HIGH for x in da+db):
            return False
        va=signature(sa,da,pid)
        vb=signature(sb,db,pid)
        if list(va)!=w["signature_a"] or list(vb)!=w["signature_b"]:
            return False
        if list(common_reading(va,vb))!=w["common_reading"]:
            return False
        if tuple(Q(z) for z in w["capacity_a"])!=tuple(Q(60)/z for z in da):
            return False
        if tuple(Q(z) for z in w["capacity_b"])!=tuple(Q(60)/z for z in db):
            return False
        return (physical_signature(sa,da,pid)==va
                and physical_signature(sb,db,pid)==vb)
    except (ValueError,KeyError,TypeError,ZeroDivisionError):
        return False


def persist(dest,filename,data):
    return b.lab.write_new(dest,filename,data)


def run(root,checkout_sha,head_sha):
    need(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha)
         and b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha),
         "CAF15B_SHA_REQUIRED")
    root=Path(root).resolve()
    need(not root.exists(),"CAF15B_REFUSE_OVERWRITE")
    root.mkdir(parents=True,exist_ok=False)
    pairinfo=[]
    for x,y in combinations(rational_models(),2):
        pairinfo.append({
            "first":x[2],"second":y[2],
            "first_stages":x[1],"second_stages":y[1],
        })
    persist(root,"00_PLAN_BEFORE_SOLVER.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTOCOL_FIRST,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "programs":PROGRAMS,"model_pairs":pairinfo,
        "continuous_duration_domain":[str(D_LOW),str(D_HIGH)],
        "box_nodes_budget_per_pair":MAX_NODES,
        "box_depth_limit":MAX_DEPTH,
        "tolerance_count":TOL,
        "proof_types":[
            "CONFUSABLE_WITNESS_CERTIFIED",
            "SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED",
            "UNRESOLVED_NOT_CERTIFIED"],
        "all_pairs_frozen_before_solver":True,
        "no_evaluator_worlds":True,
        "no_external_validation":True,
    })
    outcomes=[]
    for pid in PROGRAMS:
        for pair in pairinfo:
            sa=tuple(pair["first_stages"]);sb=tuple(pair["second_stages"])
            result=run_pair(sa,sb,pid)
            if result["verdict"]=="CONFUSABLE_WITNESS_CERTIFIED":
                need(verify_witness(sa,sb,pid,result["witness"]),
                     "CAF15B_NATIVE_WITNESS_PARITY_FAILURE")
            if result["verdict"]=="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED":
                need(result["independent_tree_verification"],
                     "CAF15B_MISSING_CERTIFICATE_CHECK")
            outcomes.append({"program":pid,**pair,**result})
    need(len(outcomes)==30,"CAF15B_BAD_PAIR_COUNT")
    summary={}
    for pid in PROGRAMS:
        sub=[r for r in outcomes if r["program"]==pid]
        summary[pid]={
            "confusable_witness_certified":sum(r["verdict"]=="CONFUSABLE_WITNESS_CERTIFIED" for r in sub),
            "separable_exhaustive_box_certified":sum(r["verdict"]=="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED" for r in sub),
            "unresolved_not_certified":sum(r["verdict"]=="UNRESOLVED_NOT_CERTIFIED" for r in sub),
            "total_nodes":sum(r["stats"]["nodes"] for r in sub),
            "n_pairs":len(sub),
        }
        need(sum(summary[pid][k] for k in (
            "confusable_witness_certified","separable_exhaustive_box_certified",
            "unresolved_not_certified"))==15,"CAF15B_BAD_VERDICT_TOTAL")
    result={
        "schema":SCHEMA,"protocol_first_commit":PROTOCOL_FIRST,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_pairs":30,"summary":summary,"results":outcomes,
        "no_grid_based_negative_certification":True,
        "same_physics_no_external_validation":True,
        "scientific_promotion_gate":GATE,
    }
    persist(root,"01_RESULTADOS.json",result)
    lines=[
        "# CAF-15B — Certificación de exclusión en capacidades continuas independientes",
        "",
        "Las cajas usan aritmética racional exacta. Una no-resolución NO es separación.",
        "El certificado condicional NO valida sistemas fuera del DES homogéneo.",
        "",
        "| Programa | Testigos físicos confirmados | Separaciones globales certificadas | INDETERMINADOS | Nodos visitados |",
        "|---|---:|---:|---:|---:|",
    ]
    for pid in PROGRAMS:
        s=summary[pid]
        lines.append("| "+" | ".join(map(str,(
            pid,s["confusable_witness_certified"],
            s["separable_exhaustive_box_certified"],
            s["unresolved_not_certified"],s["total_nodes"]
        )))+" |")
    lines.extend(["","## Veredictos detallados",
        "| Programa | Familia A | Familia B | Veredicto | Nodos | Testigo (cap A; cap B) |",
        "|---|---|---|---|---:|---|"])
    for r in outcomes:
        w=r["witness"]
        caps=(str(w["capacity_a"])+"; "+str(w["capacity_b"])) if w else "N/A"
        lines.append("| "+" | ".join((
            r["program"],r["first"],r["second"],r["verdict"],
            str(r["stats"]["nodes"]),caps))+" |")
    lines.extend(["",
        "## Límites de la prueba",
        "- A diferencia de CAF-15A, una separación solo existe cuando TODAS las",
        "  cajas terminales están verificadamente excluidas.",
        "- El árbol de certificado es auditable; las ramas con testigos no",
        "  necesitan cubrir el dominio para demostrar existencia.",
        "- No se infieren probabilidades, costos, prevalencias ni políticas.",
        "- Monotonía de clocks requiere FIFO homogéneo y ausencia de bloqueo.",
        "- ±1 es error de conteo no calibrado.",
        "",
        "**GATE:** "+GATE])
    persist(root,"02_INFORME.md","\n".join(lines))
    artifacts=sorted(p for p in root.iterdir() if p.is_file())
    persist(root,"03_MANIFIESTO.json",{
        "schema":SCHEMA,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "files_sha256":{p.name:"sha256:"+sha256(p.read_bytes()).hexdigest()
                        for p in artifacts},
        "no_claim_from_unresolved":True,
    })
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    x=p.parse_args()
    report=run(x.out,x.checkout_sha,x.head_sha)
    print(json.dumps({"n_pairs":report["n_pairs"],
                      "summary":report["summary"],"gate":report["scientific_promotion_gate"]},
                     sort_keys=True))


if __name__=="__main__":
    main()
