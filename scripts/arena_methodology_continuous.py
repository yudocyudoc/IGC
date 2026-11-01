#!/usr/bin/env python3
"""ARENA MC-01: generic continuous set-membership and falsification contracts.

No CAF/SD imports and NO grid of parameter hypotheses. Boxes are rational
outer *covers*; only a verified rational point is a feasible witness, and
only a fully excluded cover proves emptiness. Supports model-specific backends
that supply rigorous output intervals and pointwise predictions.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol


GATE = "BLOCKED_METHOD_CONTRACT_SYNTHETIC_DES_UNCALIBRATED_ERROR_NO_REAL_DATA"
EMPTY = "CERTIFIED_EMPTY"
WITNESS = "WITNESS_FEASIBLE_WITH_OUTER_COVER"
UNRESOLVED = "UNRESOLVED_WITH_OUTER_COVER"
MAX_BOX_NODES = 256
MAX_DEPTH = 14


def need(ok, code):
    if not ok:
        raise ValueError(code)


@dataclass(frozen=True)
class Family:
    id: str
    parameter_names: tuple[str, ...]
    duration_domains: tuple[tuple[Fraction, Fraction], ...]

    def __post_init__(self):
        need(bool(self.id) and 1 <= len(self.parameter_names) <= 8,
             "MC01_BAD_FAMILY")
        need(len(self.parameter_names) == len(self.duration_domains)
             and len(set(self.parameter_names)) == len(self.parameter_names),
             "MC01_BAD_PARAMETER_NAMES")
        need(all(isinstance(a,Fraction) and isinstance(b,Fraction)
                 and 0 < a < b for a,b in self.duration_domains),
             "MC01_BAD_CONTINUOUS_DOMAIN")


@dataclass(frozen=True)
class Observation:
    program: str
    values: tuple[int, ...]
    error_radius: int
    error_provenance: str
    physical_provenance: str

    def __post_init__(self):
        need(bool(self.program) and bool(self.values),
             "MC01_BAD_OBSERVATION")
        need(all(type(x) is int and x >= 0 for x in self.values),
             "MC01_NONINTEGER_COUNT")
        need(type(self.error_radius) is int and self.error_radius >= 0,
             "MC01_BAD_ERROR_RADIUS")
        need(bool(self.error_provenance) and bool(self.physical_provenance),
             "MC01_ERROR_AND_PHYSICAL_PROVENANCE_REQUIRED")


class BoundedPredictionBackend(Protocol):
    def bounds(self, family: Family,
               box: tuple[tuple[Fraction,Fraction],...],
               program: str) -> tuple[tuple[int,int],...]: ...

    def predict(self, family: Family,
                point: tuple[Fraction,...],
                program: str) -> tuple[int,...]: ...


def check_bounds(bounds, obs):
    need(len(bounds)==len(obs.values),"MC01_OBSERVABLE_SCHEMA_DRIFT")
    need(all(type(l) is int and type(h) is int and 0<=l<=h
             for l,h in bounds),"MC01_UNSOUND_BOUND_FORMAT")


def exclude_channel(bounds, obs):
    """Safe certificate: entire box has outputs outside a declared error band."""
    check_bounds(bounds,obs)
    for index,((l,h),y) in enumerate(zip(bounds,obs.values)):
        if l > y + obs.error_radius or h < y - obs.error_radius:
            return index
    return None


def compatible(prediction,obs):
    need(len(prediction)==len(obs.values),"MC01_OBSERVABLE_SCHEMA_DRIFT")
    return all(type(x) is int and abs(x-y)<=obs.error_radius
               for x,y in zip(prediction,obs.values))


def qpoint(point):
    return [str(t) for t in point]


def qbox(box):
    return [[str(l),str(h)] for l,h in box]


def parse_box(raw):
    return tuple((Fraction(a),Fraction(b)) for a,b in raw)


def point_samples(box):
    """Only points for POSITIVE witness search, NOT a physical grid."""
    return (
        tuple(a for a,b in box),
        tuple((a+b)/2 for a,b in box),
        tuple(b for a,b in box),
    )


def midpoint_split(box):
    widths=[b-a for a,b in box]
    index=max(range(len(widths)),key=lambda i:(widths[i],-i))
    a,b=box[index]
    mid=(a+b)/2
    need(a<mid<b,"MC01_SPLIT_UNSUPPORTED")
    left=list(box);right=list(box)
    left[index]=(a,mid);right[index]=(mid,b)
    return index,mid,tuple(left),tuple(right)


def verify_cover(family,obs,backend,tree,witness):
    """Recompute every exclusion and split from the original continuous root.

    Retained P leaves are SOUND OUTER coverage, not inner feasible regions.
    """
    root=family.duration_domains
    retained=[]
    count_excluded=0
    def check(box,node):
        nonlocal count_excluded
        kind=node.get("type")
        if kind=="X":
            channel=node.get("channel")
            if type(channel) is not int: return False
            intervals=backend.bounds(family,box,obs.program)
            check_bounds(intervals,obs)
            if not(0<=channel<len(intervals)): return False
            l,h=intervals[channel]
            y=obs.values[channel]
            if l>y+obs.error_radius or h<y-obs.error_radius:
                count_excluded+=1
                return True
            return False
        if kind=="P":
            retained.append(qbox(box))
            return True
        if kind=="S":
            dim=node.get("dim")
            if type(dim) is not int or not(0<=dim<len(box)):
                return False
            mid=Fraction(node["mid"])
            if mid!=(box[dim][0]+box[dim][1])/2:
                return False
            lo=list(box);hi=list(box)
            lo[dim]=(box[dim][0],mid)
            hi[dim]=(mid,box[dim][1])
            return check(tuple(lo),node["low"]) and check(tuple(hi),node["high"])
        return False
    try:
        all_valid=check(root,tree)
        if witness is not None:
            point=tuple(Fraction(x) for x in witness["parameter_durations"])
            if not(len(point)==len(root) and all(
                l<=x<=h for x,(l,h) in zip(point,root))):
                return {"valid":False}
            predicted=backend.predict(family,point,obs.program)
            if not compatible(predicted,obs):
                return {"valid":False}
            if list(predicted)!=witness["predicted"]:
                return {"valid":False}
            # Boundary might be shared by two retained boxes; at least one
            # retained box MUST contain the certified positive witness.
            if not any(all(Fraction(r[0])<=x<=Fraction(r[1])
                           for r,x in zip(cell,point)) for cell in retained):
                return {"valid":False}
        return {
            "valid":all_valid,
            "complete_exclusion":all_valid and not retained,
            "retained_outer_boxes":retained,
            "excluded_leaves":count_excluded,
        }
    except (KeyError,ValueError,TypeError,ZeroDivisionError,IndexError):
        return {"valid":False}


def solve(family,obs,backend,
          max_nodes=MAX_BOX_NODES,max_depth=MAX_DEPTH):
    """Sound branch-and-bound, NOT discrete bank classification.

    The true feasible set is defined by the predicate on the entire closed
    continuous domain. This routine computes a rigorous OUTER cover and may
    find an INNER point. Limits produce unresolved, never false emptiness.
    """
    need(type(max_nodes) is int and 1<=max_nodes<=MAX_BOX_NODES and
         type(max_depth) is int and 0<=max_depth<=MAX_DEPTH,
         "MC01_NONPREDECLARED_SOLVER_BUDGET")
    count=0
    first_witness=None
    def visit(box,depth):
        nonlocal count,first_witness
        if count>=max_nodes:
            return {"type":"P","reason":"NODE_BUDGET"}
        count+=1
        limits=backend.bounds(family,box,obs.program)
        channel=exclude_channel(limits,obs)
        if channel is not None:
            return {"type":"X","channel":channel}
        if first_witness is None:
            for point in point_samples(box):
                predicted=backend.predict(family,point,obs.program)
                if compatible(predicted,obs):
                    first_witness={
                        "parameter_durations":qpoint(point),
                        "predicted":list(predicted),
                    }
                    break
        if depth>=max_depth:
            return {"type":"P","reason":"MAX_DEPTH"}
        dim,mid,lo,hi=midpoint_split(box)
        return {
            "type":"S","dim":dim,"mid":str(mid),
            "low":visit(lo,depth+1),
            "high":visit(hi,depth+1),
        }
    tree=visit(family.duration_domains,0)
    verification=verify_cover(family,obs,backend,tree,first_witness)
    need(verification.get("valid") is True,
         "MC01_COVER_VERIFICATION_FAILED")
    if verification["complete_exclusion"]:
        need(first_witness is None,"MC01_CONTRADICTORY_WITNESS")
        state=EMPTY
    elif first_witness is not None:
        state=WITNESS
    else:
        state=UNRESOLVED
    return {
        "family_id":family.id,
        "status":state,
        "parameter_domain":qbox(family.duration_domains),
        "feasibility_predicate":
            "exists d in closed domain: every |predicted_j(d)-observed_j|<=error_radius",
        "witness":first_witness,
        "retained_outer_boxes":verification["retained_outer_boxes"],
        "n_retained_boxes":len(verification["retained_outer_boxes"]),
        "n_excluded_leaves":verification["excluded_leaves"],
        "nodes_visited":count,
        "max_box_nodes":max_nodes,
        "max_depth":max_depth,
        "certificate_verified":True,
        "tree":tree,
        "outer_cover_is_not_exact_feasible_region":True,
    }


def falsify(families,results):
    need(len(families)==len(results),"MC01_FALSIFICATION_MISMATCH")
    ids=[f.id for f in families]
    need(len(set(ids))==len(ids)
         and set(ids)==set(r["family_id"] for r in results),
         "MC01_FALSIFICATION_DUPLICATE_OR_MISSING_CLASS")
    feasible=[r["family_id"] for r in results if r["status"]==WITNESS]
    unresolved=[r["family_id"] for r in results if r["status"]==UNRESOLVED]
    falsified=[r["family_id"] for r in results if r["status"]==EMPTY]
    if len(falsified)==len(families):
        conclusion="KNOWN_FAMILIES_INADEQUATE_UNDER_DECLARED_MODEL_AND_ERROR"
    elif len(feasible)==1 and len(falsified)==len(families)-1:
        conclusion="CONDITIONAL_UNIQUE_WITHIN_DECLARED_FAMILIES"
    else:
        conclusion="INDETERMINATE_MULTIPLE_OR_UNRESOLVED_FAMILIES"
    return {
        "conclusion":conclusion,
        "feasible_witness_families":feasible,
        "unresolved_families":unresolved,
        "certified_falsified_families":falsified,
        "cannot_infer_unknown_topology_from_empty":True,
        "structure_catalog_completeness_not_proven":True,
        "measurement_error_bound_must_be_justified":True,
        "scientific_gate":GATE,
    }


def design_options(candidates,technical_pair_results):
    """Capa 4: decision candidates, not a policy optimizer without costs."""
    results=[]
    for pid in candidates:
        comparisons=technical_pair_results[pid]
        need(len(comparisons)==15,"MC01_UNAPPROVED_APRIORI_SET")
        results.append({
            "program":pid,
            "certified_pair_separations":sum(
                row["verdict"]=="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED"
                for row in comparisons),
            "confusable_pair_witnesses":sum(
                row["verdict"]=="CONFUSABLE_WITNESS_CERTIFIED"
                for row in comparisons),
            "uncertified_pairs":sum(
                row["verdict"]=="UNRESOLVED_NOT_CERTIFIED"
                for row in comparisons),
            "requires_observed_natural_overload_or_nonharmful_opportunity":True,
            "feasibility_verified":False,
            "cost_verified":False,
            "not_an_approved_intervention":True,
        })
    return {
        "status":"DESIGN_NOT_OPTIMIZABLE_MISSING_COST_AND_FEASIBILITY",
        "options":results,
        "ranking":None,
        "autonomous_action":None,
        "reason":"No measured natural-demand window, sensor cost or decision-loss function",
    }
