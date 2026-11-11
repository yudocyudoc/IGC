#!/usr/bin/env python3
"""CAF-11: exact rational, one-parameter inversion of CAF-01 tandem DES.

A PARAMETRIC CLOCK is a continuous piecewise-affine function of d=60/c.
For deterministic tandem FIFO, identical constant-time parallel servers,
D[s,i](d)=max(arrival[s,i](d),D[s,i-m](d))+service_duration[s](d).
All operations and event-boundary roots are exact Fraction arithmetic.
This narrowly specified family is NOT a general DES solver.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import caf07b_umbral_secuencial as b
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA = "igc-caf11-exact-one-param-des-inverse/0.1"
GATE = "BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE"
CAPACITY_LOW, CAPACITY_HIGH = Fraction(55), Fraction(110)
D_LOW, D_HIGH = Fraction(60, CAPACITY_HIGH), Fraction(60, CAPACITY_LOW)
PROTO_FIRST = "6db736847ca66efc7da363f26e7616f0f899a82a"
STAGE_SETS = ((0,), (1,), (2,), (0,1), (0,2), (1,2))
K0 = {"id":"K0", "rate":b.caf07.T0_RATE, "minute":b.caf07.T0_MINUTE,
      "channels":(("delivered",None),)}
K1 = {"id":"K1", "rate":b.FIRST["rate"], "minute":b.FIRST["minute"],
      "channels":tuple(tuple(c) for c in b.FIRST["channels"])}
PROBES = (K0,K1)
TOLERANCE = b.TOLERANCE


def need(cond,code):
    if not cond:
        raise ValueError(code)


def q(x):
    return str(x)


def clean_knots(knots):
    """Remove redundant collinear vertices without approximating rational data."""
    ks=sorted(knots)
    need(len(ks)>=2 and ks[0][0]==D_LOW and ks[-1][0]==D_HIGH,
         "CAF11_PWL_BAD_DOMAIN")
    need(all(x1<x2 for (x1,_),(x2,_) in zip(ks,ks[1:])),
         "CAF11_PWL_REPEATED_X")
    kept=[]
    for p in ks:
        kept.append(p)
        while len(kept)>=3:
            (x0,y0),(x1,y1),(x2,y2)=kept[-3:]
            if (y1-y0)*(x2-x1)==(y2-y1)*(x1-x0):
                kept.pop(-2)
            else:
                break
    return tuple(kept)


@dataclass(frozen=True)
class Clock:
    knots: tuple[tuple[Fraction,Fraction], ...]

    @classmethod
    def line(cls, a=0, intercept=0):
        a,intercept=Fraction(a),Fraction(intercept)
        return cls(((D_LOW,a*D_LOW+intercept),
                    (D_HIGH,a*D_HIGH+intercept)))

    def at(self,d):
        d=Fraction(d)
        need(D_LOW<=d<=D_HIGH,"CAF11_CLOCK_OUT_OF_DOMAIN")
        xs=[k[0] for k in self.knots]
        i=min(bisect_right(xs,d)-1,len(xs)-2)
        l,vl=self.knots[i]
        r,vr=self.knots[i+1]
        return vl+(d-l)*(vr-vl)/(r-l)

    def add(self,other):
        if not isinstance(other,Clock):
            other=Clock.line(0,other)
        xs=sorted({x for x,_ in self.knots}|{x for x,_ in other.knots})
        return Clock(clean_knots([(x,self.at(x)+other.at(x)) for x in xs]))

    def vmax(self,other):
        if not isinstance(other,Clock):
            other=Clock.line(0,other)
        xs=sorted({x for x,_ in self.knots}|{x for x,_ in other.knots})
        crossings=set()
        for l,r in zip(xs,xs[1:]):
            diff_l=self.at(l)-other.at(l)
            diff_r=self.at(r)-other.at(r)
            if diff_l*diff_r<0:
                x=l+(r-l)*abs(diff_l)/(abs(diff_l)+abs(diff_r))
                need(l<x<r,"CAF11_CROSSING_OUTSIDE_SEGMENT")
                crossings.add(x)
        all_x=sorted(set(xs)|crossings)
        return Clock(clean_knots([
            (x,max(self.at(x),other.at(x))) for x in all_x]))

    def roots_at(self,level):
        """ALL exact d such that Clock(d)=level, including flat segments.

        For a flat segment equal to level, its two endpoints suffice as
        change-point separators; the entire interval will be evaluated.
        """
        level=Fraction(level)
        roots=set()
        for (l,vl),(r,vr) in zip(self.knots,self.knots[1:]):
            if vl==level:
                roots.add(l)
            if vr==level:
                roots.add(r)
            if (vl-level)*(vr-level)<0:
                roots.add(l+(r-l)*(level-vl)/(vr-vl))
        return roots


def clock_tandem(stage_indices,rate):
    """Parametric FCFS tandem: equal-duration parallel servers, exact clocks."""
    arrivals=des.half_open_arrivals(rate,20)
    stages=[]
    zero=Clock.line()
    duration=Clock.line(1,0)
    for s in range(3):
        servers=1 if s in stage_indices else 2
        service=duration if s in stage_indices else Clock.line(0,1)
        endings=[]
        for i,a in enumerate(arrivals):
            arrival=(Clock.line(0,a) if s==0 else stages[s-1][i])
            server_free=(endings[i-servers] if i>=servers else zero)
            end=arrival.vmax(server_free).add(service)
            endings.append(end)
        stages.append(endings)
    return stages[-1]


def certified_regimes(stage_indices):
    """Build exhaustive exact parametric output regimes for K0,K1."""
    outputs={}
    split={D_LOW,D_HIGH}
    for probe in PROBES:
        clocks=clock_tandem(stage_indices,probe["rate"])
        outputs[probe["id"]]=clocks
        for clock in clocks:
            split.update(clock.roots_at(probe["minute"]))
    cuts=sorted(split)
    def readings(d):
        return {
            p["id"]:[sum(clock.at(d)<=p["minute"]
                         for clock in outputs[p["id"]])]
            for p in PROBES
        }
    atoms=[]
    for i,v in enumerate(cuts):
        atoms.append({
            "kind":"point","left":v,"right":v,
            "include_left":True,"include_right":True,
            "pred":readings(v),
        })
        if i+1<len(cuts):
            nxt=cuts[i+1]
            atoms.append({
                "kind":"open","left":v,"right":nxt,
                "include_left":False,"include_right":False,
                "pred":readings((v+nxt)/2),
            })
    need(len(atoms)==2*len(cuts)-1,"CAF11_REGIME_COUNT_WRONG")
    return atoms


def compatible(pred,observed):
    return all(
        len(pred[key])==len(observed[key]) and
        all(abs(x-y)<=TOLERANCE
            for x,y in zip(pred[key],observed[key]))
        for key in ("K0","K1"))


def merge_atoms(atoms, observed):
    """Merge adjacent compatible open intervals and boundary singleton atoms."""
    components=[]
    for atom in atoms:
        if not compatible(atom["pred"],observed):
            continue
        c={
            "left":atom["left"],"right":atom["right"],
            "include_left":atom["include_left"],
            "include_right":atom["include_right"]
        }
        if components and components[-1]["right"]==c["left"] and (
                components[-1]["include_right"] or c["include_left"]):
            prev=components[-1]
            prev["right"]=c["right"]
            prev["include_right"]=c["include_right"]
        else:
            components.append(c)
    return components


def capacity_regions(duration_components):
    """c=60/d reverses boundaries AND inclusion flags exactly."""
    return [{
        "capacity_low":q(60/x["right"]),
        "capacity_high":q(60/x["left"]),
        "low_included":x["include_right"],
        "high_included":x["include_left"],
        "duration_low":q(x["left"]),
        "duration_high":q(x["right"]),
        "duration_low_included":x["include_left"],
        "duration_high_included":x["include_right"],
    } for x in reversed(duration_components)]


def contains_duration(components, value):
    d=Fraction(value)
    return any(
        (x["left"]<d<x["right"]) or
        (d==x["left"] and x["include_left"]) or
        (d==x["right"] and x["include_right"])
        for x in components)


def models():
    return [
        {"id":"M_"+''.join(str(i) for i in stages),
         "stages":stages,
         "label":b.klass([b.STAGES[i] for i in stages])}
        for stages in STAGE_SETS
    ]


def worlds():
    out=[]
    for cap in (68,83,97):
        for stage in (0,1,2):
            out.append({
                "id":f"SINGLE_{cap}_{stage}", "truth_type":"single",
                "truth_class":b.STAGES[stage], "capacity":cap,
                "config":b.make_physical_config((stage,),cap),
            })
    for cap in (69,83,97):
        for i,j in ((0,1),(0,2),(1,2)):
            out.append({
                "id":f"DUAL_{cap}_{i}{j}","truth_type":"double",
                "truth_class":b.klass([b.STAGES[i],b.STAGES[j]]),
                "capacity":cap,
                "config":b.make_physical_config((i,j),cap),
            })
    for cap in (64,86):
        out.append({
            "id":f"EXTRA_{cap}","truth_type":"unknown-extra",
            "truth_class":None, "capacity":cap,
            "config":b.make_physical_config((),cap,extra=True),
        })
    need(len(out)==20 and len({x["id"] for x in out})==20,
         "CAF11_WORLD_CONTRACT_BROKEN")
    return out


def observe_world(config):
    """Truth config goes only to physical reader; NEVER the inverse filter."""
    return {
        p["id"]:b.read_physical(
            config,p["rate"],p["minute"],p["channels"])
        for p in PROBES
    }


def baseline_classes(bank,predictions,observed):
    ids=b.eligible(bank,predictions,{
        "baseline":observed["K0"],
        b.FIRST_ACTION_ID:observed["K1"],
    })
    return b.classes(bank,ids)


def format_atom(atom):
    return {
        "kind":atom["kind"],
        "duration_low":q(atom["left"]),
        "duration_high":q(atom["right"]),
        "low_included":atom["include_left"],
        "high_included":atom["include_right"],
        "counts":atom["pred"],
    }


def analyze(observed, families):
    """Does not accept config/capacity/label. Only observable counts and models."""
    res=[]
    for family in families:
        components=merge_atoms(family["atoms"],observed)
        res.append({
            "id":family["id"],"label":family["label"],
            "nonempty":bool(components),
            "n_components":len(components),
            "regions_capacity":capacity_regions(components),
            # Internal exact duration ranges only for evaluator's containment;
            # avoid publishing mutable internal objects inside the output.
            "_duration_components":components,
        })
    return res


def run(out,checkout_sha,head_sha):
    need(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha) is not None
         and b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha) is not None,
         "CAF11_INVALID_SHA")
    target=Path(out).resolve()
    need(not target.exists(),"CAF11_REFUSE_TO_OVERWRITE")

    defs=models()
    families=[
        {"id":m["id"],"label":m["label"],"stages":m["stages"],
         "atoms":certified_regimes(m["stages"])}
        for m in defs
    ]
    original_bank=b.bank(True)
    original_pred=b.precompute(original_bank)
    evaluation=worlds()
    target.mkdir(parents=True,exist_ok=False)
    def save(filename,content):
        return b.lab.write_new(target,filename,content)
    save("00_PLAN_PRE_EVALUACION.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO_FIRST,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "parameterization":"ONE_COMMON_CONTINUOUS_CAPACITY_FOR_LIMITED_STAGES",
        "capacity_domain":list(map(q,(CAPACITY_LOW,CAPACITY_HIGH))),
        "duration_domain":list(map(q,(D_LOW,D_HIGH))),
        "tolerance":TOLERANCE,
        "probes":PROBES,
        "structural_families":defs,
        "precomputed_rational_regimes":[
            {"id":f["id"],"label":f["label"],
             "n_exact_atomic_regimes":len(f["atoms"]),
             "atoms":[format_atom(x) for x in f["atoms"]]}
            for f in families
        ],
        "point_bank":original_bank,
        "point_bank_DES_predictions":original_pred,
        "evaluator_worlds_EVALUATOR_ONLY":evaluation,
        "new_evaluation_world_DES_calls_before_plan":0,
        "native_DES_not_changed":True,
        "continuous_certification_narrow_tandem_family_only":True,
        "not_calibrated_sensor_error":True,
    })
    cases=[]
    for world in evaluation:
        observed=observe_world(world["config"])
        inverse=analyze(observed,families)
        baseline=baseline_classes(original_bank,original_pred,observed)
        classes=sorted(z["label"] for z in inverse if z["nonempty"])
        truth=world["truth_class"]
        truth_param=Fraction(60,world["capacity"])
        true_family=next((x for x in inverse if x["label"]==truth),None)
        true_contained=(contains_duration(
            true_family["_duration_components"],truth_param)
            if true_family else None)
        # Truth never goes into 'analyze'; only evaluator reads it now.
        public_inverse=[
            {k:v for k,v in x.items() if k!="_duration_components"}
            for x in inverse
        ]
        cases.append({
            "id":world["id"],
            "world_type_EVALUATOR_ONLY":world["truth_type"],
            "true_capacity_EVALUATOR_ONLY":world["capacity"],
            "true_class_EVALUATOR_ONLY":truth,
            "observed":observed,
            "old_point_bank_classes":baseline,
            "continuous_family_classes":classes,
            "continuous_regions":public_inverse,
            "old_point_bank_true_class_covered":
                truth in baseline if truth is not None else None,
            "continuous_true_class_covered":
                truth in classes if truth is not None else None,
            "true_capacity_contained_in_true_family_EVALUATOR_ONLY":
                true_contained,
            "old_point_bank_MODEL_GAP":not baseline,
            "continuous_family_incompatibility":not classes,
        })
    inside=[x for x in cases if x["true_class_EVALUATOR_ONLY"] is not None]
    outside=[x for x in cases if x["true_class_EVALUATOR_ONLY"] is None]
    need(len(inside)==18 and len(outside)==2,
         "CAF11_EVALUATION_DENOMINATORS_CHANGED")
    need(all(x["true_capacity_contained_in_true_family_EVALUATOR_ONLY"]
             for x in inside),"CAF11_FALSE_EXCLUSION_OF_TRUE_CONTINUOUS_PARAMETER")
    summary={
        "in_family_worlds":len(inside),
        "out_of_family_controls":len(outside),
        "point_true_class_coverage":sum(x["old_point_bank_true_class_covered"]
                                        for x in inside),
        "continuous_true_class_coverage":sum(x["continuous_true_class_covered"]
                                             for x in inside),
        "continuous_true_parameter_coverage":sum(
            x["true_capacity_contained_in_true_family_EVALUATOR_ONLY"]
            for x in inside),
        "point_MODEL_GAP_in_family":sum(x["old_point_bank_MODEL_GAP"]
                                        for x in inside),
        "continuous_MODEL_INCONSISTENT_in_family":sum(
            x["continuous_family_incompatibility"] for x in inside),
        "point_false_known_class_out_of_family":sum(
            bool(x["old_point_bank_classes"]) for x in outside),
        "continuous_false_known_class_out_of_family":sum(
            bool(x["continuous_family_classes"]) for x in outside),
        "ambiguous_continuous_in_family":sum(
            len(x["continuous_family_classes"])>1 for x in inside),
        "unique_continuous_class_in_family":sum(
            len(x["continuous_family_classes"])==1 for x in inside),
    }
    report={
        "schema":SCHEMA,"protocol_first_commit":PROTO_FIRST,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "inversion_certification":
            "EXACT_RATIONAL_PIECEWISE_AFFINE_RECURSION_FOR_SPECIFIED_TANDEM_FAMILY",
        "not_general_DES_or_real_world_certified":True,
        "unknown_topology_not_inferred_from_empty_set":True,
        "common_capacity_same_for_K0_and_K1":True,
        "n_models":len(families),"n_worlds":len(evaluation),
        "n_model_world_inversions":len(families)*len(evaluation),
        "summary":summary,"evaluations":cases,
        "promotion_gate":GATE,
        "deployment_validated":False,
    }
    save("01_RESULTADOS.json",report)
    md=[
        "# CAF-11 — Inversión exacta racional de capacidad continua",
        "",
        "**GATE BLOQUEADO:** "+GATE,
        "",
        "El conjunto completo de capacidades es condicional a la subfamilia",
        "DES determinista de tres etapas FCFS, tiempos de servicio idénticos",
        "en cada etapa y un único parámetro común c para etapas limitadas.",
        "No valida otros DES, otras estructuras, variabilidad ni incertidumbre",
        "instrumental real. Banda ±1 es convenio de robustez experimental.",
        "",
        "## Comparación agregada",
        "",
        f"- Mundos in-family: {len(inside)}.",
        f"- Cobertura de clase banco 24: {summary['point_true_class_coverage']}/{len(inside)}.",
        f"- Cobertura de clase continuo: {summary['continuous_true_class_coverage']}/{len(inside)}.",
        f"- Contención de parámetro continuo verdadero: {summary['continuous_true_parameter_coverage']}/{len(inside)}.",
        f"- MODEL_GAP de banco puntual en familia: {summary['point_MODEL_GAP_in_family']}.",
        f"- Incompatibilidad con familias continuas, dentro de familia: {summary['continuous_MODEL_INCONSISTENT_in_family']}.",
        f"- Casos con múltiples clases continuas: {summary['ambiguous_continuous_in_family']}.",
        f"- Controles fuera de familia conservados por alguna estructura: {summary['continuous_false_known_class_out_of_family']}/{len(outside)}.",
        "",
        "## Por mundo",
        "",
        "| Mundo | Clase real (evaluador) | K0 | K1 | Clases banco puntual | Clases continuo | Contiene capacidad verdadera |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for x in cases:
        md.append("| "+ " | ".join((
            x["id"],x["true_class_EVALUATOR_ONLY"] or "fuera de catálogo",
            str(x["observed"]["K0"][0]),str(x["observed"]["K1"][0]),
            ", ".join(x["old_point_bank_classes"]) or "∅",
            ", ".join(x["continuous_family_classes"]) or "∅",
            (str(x["true_capacity_contained_in_true_family_EVALUATOR_ONLY"])
             if x["true_class_EVALUATOR_ONLY"] else "N/A")
        ))+" |")
    md += ["",
           "## Límites de interpretación",
           "",
           "- Ninguna cobertura perfecta dentro del generador común demostraría",
           "  capacidad para diagnosticar un sistema real.",
           "- Un conjunto continuo no vacío no certifica la estructura: puede",
           "  contener muchos mecanismos y capacidades distintas.",
           "- Cuarta etapa oculta no está representada; ajuste de una familia",
           "  conocida a sus conteos no prueba su existencia real.",
           "- Exactitud de regiones se refiere solo a observables de entregas",
           "  K0/K1; el motor DES nativo se verifica por tests de paridad.",
           "- Todas las fronteras son fracciones racionales exactas y cada",
           "  límite de evento se evalúa como singleton, respetando eventos",
           "  DES a t<=horizonte.",
           "",
           "## Próximo falsador, separado de este resultado",
           "",
           "Servicio estocástico, error instrumental justificado, tiempos por",
           "pedido, más de un parámetro continuo, nuevas topologías y un",
           "generador de evaluación independiente.",
           ""]
    save("02_INFORME.md","\n".join(md))
    artifacts=sorted(x for x in target.iterdir() if x.is_file())
    save("03_MANIFIESTO.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,
        "pr_head_sha":head_sha,
        "files_sha256":{
            f.name:"sha256:"+sha256(f.read_bytes()).hexdigest()
            for f in artifacts},
        "evidence_after_plan_written":True,
        "source_run_not_externally_blinded":True,
    })
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    a=p.parse_args()
    r=run(a.out,a.checkout_sha,a.head_sha)
    print(json.dumps({"status":"CAF11_EXACT_INVERSE_EXECUTED",
                      "summary":r["summary"],"promotion_gate":r["promotion_gate"]},
                     sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
