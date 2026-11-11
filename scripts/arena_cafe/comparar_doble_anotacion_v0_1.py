#!/usr/bin/env python3
"""Compara dos entregas selladas del experimento visual; no certifica exactitud física."""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import Counter
from pathlib import Path
from statistics import median

VIDEO_SHA="cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5"
WINDOWS={"A":(2350,2470),"B":(3750,3870)}
REGION="barra_frontal_vista_principal"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
    return h.hexdigest()

def load_events(path):
    events=[]
    with open(path,encoding="utf-8-sig") as f:
        for line_no,line in enumerate(f,1):
            if line.strip():
                try: events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSONL inválido, línea {line_no}: {e}") from e
    ids=[row.get("event_id") for row in events]
    if len(ids)!=len(set(ids)):raise ValueError("event_id duplicado")
    for row in events:
        p=row.get("provenance",{})
        if p.get("source_video_sha256")!=VIDEO_SHA:
            raise ValueError("Evento sin procedencia del MP4 preregistrado")
        ts=row.get("time",{})
        nums=(ts.get("samples_video_s",[]) if ts.get("mode")=="sample"
              else ([ts.get("last_state_video_s"),ts.get("first_new_state_video_s")]
                    if ts.get("mode")=="transition" else []))
        for t in nums:
            if t is None or not any(start<=t<=stop for start,stop in WINDOWS.values()):
                raise ValueError("Evento fuera de ventanas preregistradas")
    return events

def closed_package(folder,reviewer):
    folder=Path(folder)
    m=json.loads((folder/"resumen_revisor.json").read_text(encoding="utf-8"))
    if m.get("reviewer_id")!=reviewer or m.get("source_video_sha256")!=VIDEO_SHA:
        raise ValueError("Identidad de revisor o fuente incorrecta")
    if m.get("version_protocolo")!="0.1" or not m.get("timestamp_cierre_utc"):
        raise ValueError("Versión o sello de cierre ausente")
    if m.get("independiente_de_etiquetas_historicas") is not True or m.get("independiente_del_otro_revisor") is not True:
        raise ValueError("No consta declaración de independencia del revisor "+reviewer)
    for key,path in (("cobertura_sha256","cobertura.csv"),("eventos_sha256","eventos.jsonl")):
        if m.get(key)!=sha256(folder/path):
            raise ValueError("Respuesta modificada tras el sello: "+str(folder/path))
    with (folder/"cobertura.csv").open(encoding="utf-8-sig",newline="") as f:
        samples=list(csv.DictReader(f))
    by_key={}
    for row in samples:
        k=(row["tramo"],int(row["video_s"]),row["region_id"])
        if k in by_key:raise ValueError("Muestra repetida: "+str(k))
        by_key[k]=row
        if row["reviewer_id"]!=reviewer or k[2]!=REGION:
            raise ValueError("Revisor o región no preregistrados")
        if k[0] not in WINDOWS or k[1] not in range(WINDOWS[k[0]][0],WINDOWS[k[0]][1]+1,2):
            raise ValueError("Segundo de muestreo fuera del preregistro")
        if row["visibilidad_region"] not in ("completa","parcial","no_evaluable"):
            raise ValueError("Visibilidad regional incompleta: "+str(k))
        if row["barista_visibilidad"] not in ("visible","no_visible","desconocido"):
            raise ValueError("Visibilidad del barista incompleta: "+str(k))
        count=row["minimo_recipientes_con_contenido"].strip()
        if count and not count.isdecimal():raise ValueError("Conteo no entero: "+str(k))
        if not count and row["visibilidad_region"]=="completa" and not row["notas"].strip():
            raise ValueError("Conteo desconocido sin justificar: "+str(k))
    if len(by_key)!=122:raise ValueError(f"Se exigen 122 muestras: hay {len(by_key)}")
    return m,by_key,load_events(folder/"eventos.jsonl")

def interval_distance(a,b):
    return max(0.0,a[0]-b[1],b[0]-a[1])

def event_distance(a,b):
    if (a.get("event_code"),a.get("region_id"),a.get("kind")) != (b.get("event_code"),b.get("region_id"),b.get("kind")):
        return None
    x,y=a["time"],b["time"]
    if x["mode"]!=y["mode"]:return None
    if x["mode"]=="sample":
        return min(abs(i-j) for i in x["samples_video_s"] for j in y["samples_video_s"])
    if x["mode"]=="transition":
        return interval_distance(
            (x["last_state_video_s"],x["first_new_state_video_s"]),
            (y["last_state_video_s"],y["first_new_state_video_s"]))
    if x["mode"]=="episode":
        sx,ex=x["start_video_s"],x["end_video_s"]
        sy,ey=y["start_video_s"],y["end_video_s"]
        if any(v is None for v in (sx,ex,sy,ey)):return None
        return max(interval_distance(sx,sy),interval_distance(ex,ey))
    return None

def match_events(events_a,events_b):
    a=[e for e in events_a if e.get("claim_level")=="OBSERVADO"]
    b=[e for e in events_b if e.get("claim_level")=="OBSERVADO"]
    possibilities=[]
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            d=event_distance(x,y)
            if d is not None and d<=2:possibilities.append((d,i,j))
    taken_a=set();taken_b=set();pairs=[]
    for d,i,j in sorted(possibilities):
        if i in taken_a or j in taken_b:continue
        taken_a.add(i);taken_b.add(j)
        pairs.append({"event_a":a[i]["event_id"],"event_b":b[j]["event_id"],
                      "code":a[i]["event_code"],"difference_video_s":d})
    n=len(pairs)
    return {"positive_a":len(a),"positive_b":len(b),"paired":n,
      "f1_symmetric":(2*n/(len(a)+len(b))) if a or b else None,
      "f1_undefined_if_no_events":not (a or b),
      "pairs":pairs,
      "unmatched_a":[e["event_id"] for i,e in enumerate(a) if i not in taken_a],
      "unmatched_b":[e["event_id"] for i,e in enumerate(b) if i not in taken_b],
      "unknown_a":sum(e.get("claim_level")=="DESCONOCIDO" for e in events_a),
      "unknown_b":sum(e.get("claim_level")=="DESCONOCIDO" for e in events_b)}

def compare_coverage(a,b):
    if a.keys()!=b.keys():raise ValueError("No coinciden las muestras entre hojas")
    keys=sorted(a)
    fields=("visibilidad_region","barista_visibilidad")
    agreement={f:sum(a[k][f]==b[k][f] for k in keys)/len(keys) for f in fields}
    conf=Counter((a[k]["visibilidad_region"],b[k]["visibilidad_region"]) for k in keys)
    diffs=[];missing=[];all_diffs=[]
    for key in keys:
        x=a[key]["minimo_recipientes_con_contenido"].strip()
        y=b[key]["minimo_recipientes_con_contenido"].strip()
        if not x or not y:
            missing.append({"tramo":key[0],"video_s":key[1],"a":x or None,"b":y or None})
        else:
            d=abs(int(x)-int(y));all_diffs.append(d)
            if d:diffs.append({"tramo":key[0],"video_s":key[1],"a":int(x),"b":int(y),"abs_diff":d})
    return {"sample_pairs":len(keys),"agreement":agreement,
      "visibility_confusion":[{"a":x,"b":y,"n":n} for (x,y),n in sorted(conf.items())],
      "counts_both_available":len(all_diffs),
      "count_comparability_fraction":len(all_diffs)/len(keys),
      "count_exact_agreement":sum(d==0 for d in all_diffs)/len(all_diffs) if all_diffs else None,
      "count_median_abs_difference":median(all_diffs) if all_diffs else None,
      "count_disagreements":diffs,
      "counts_uncomparable":missing}

def compare(a_dir,b_dir):
    ma,a,ea=closed_package(a_dir,"A")
    mb,b,eb=closed_package(b_dir,"B")
    return {"status":"EXPLORATORY_AGREEMENT_NOT_PHYSICAL_VALIDATION",
      "source_video_sha256":VIDEO_SHA,
      "reviewer_seals":{"A":{"closed":ma["timestamp_cierre_utc"],
                             "coverage_sha256":ma["cobertura_sha256"],
                             "events_sha256":ma["eventos_sha256"]},
                        "B":{"closed":mb["timestamp_cierre_utc"],
                             "coverage_sha256":mb["cobertura_sha256"],
                             "events_sha256":mb["eventos_sha256"]}},
      "coverage":compare_coverage(a,b),"events":match_events(ea,eb),
      "limitations":["El acuerdo no verifica exactitud, representatividad ni continuidad.",
       "Declaración de independencia no se comprueba automáticamente.",
       "El JSONL debe pasar además el validador semántico oficial v0.1.",
       "No acredita tiempos POS, capacidad física ni acceso a F5/G4/G5."]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--a",required=True,type=Path)
    p.add_argument("--b",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    r=compare(args.a,args.b)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: reporte observacional comparativo",args.out)

if __name__=="__main__":main()
