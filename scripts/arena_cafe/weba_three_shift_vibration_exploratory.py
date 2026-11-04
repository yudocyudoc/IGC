"""WEBA three-shift exploratory vibration segmentation.

Retrospective, UNLABELLED: neither coffee cycles nor beverages nor POS service.
Only 12 exact public machine blobs are read (SHA-1 and length pinned).
No biological data, order identifiers, raw traces or event times are exported.

Candidate high-vibration *episodes* are >= 10 s of adjacent 5-s windows
above one threshold fixed on two calendar-earlier training shifts. They are
not physical cycle end points. A third shift is holdout in the weak descriptive
sense ONLY (no independent task labels and no blind F5).
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics

UPSTREAM_REPO = "Department-of-System-Engineering/datasets_WEBA"
UPSTREAM_COMMIT = "d6841669e544579547c94b7ce1e8613bbd6b3a39"
TRAIN = ("20240223_evening", "20240304_evening")
HOLDOUT = "20240308_evening"
SOURCES = [
    ("20240223_evening","20240223_143153",1017789,"ed6e907db552a95a286c20bf0ed08a214945995f"),
    ("20240223_evening","20240223_145204",5591923,"6786195c1d3763a055d22f6eb0f39bcc449ac616"),
    ("20240223_evening","20240223_164253",2028279,"b7ad2de54835fb9bcb65c016128b8529300a6e85"),
    ("20240223_evening","20240223_172309",3412697,"aca8227f1564b65f08efa70c81ace6f2353b1f47"),
    ("20240304_evening","170120",6478804,"831b4108540adbd9d23ce58bef9510fd9e15c4d3"),
    ("20240304_evening","185214.coffee_machine_acc",5559300,"06a1aac6a467122f0fb1b6d3add7c457a2ad3938"),
    ("20240308_evening","20240308_142322",79342,"aa886fe8e110ad507084ba53089741a1e8e79973"),
    ("20240308_evening","20240308_142459",2688358,"2c90e59df3108b74006b27ab76438af4f5363571"),
    ("20240308_evening","20240308_151824",969783,"b9b65d4e2df3f94043b5b139cdf2315b24be49fb"),
    ("20240308_evening","20240308_153744",847476,"94287fea12188ef30ddfd3b399d501a60ab33036"),
    ("20240308_evening","20240308_155437",7978151,"859344ecf8b94fa3e39b801e8f3d3123e2e343c0"),
    ("20240308_evening","20240308_183322",270817,"2bf27512f4763ec98b9ac86937c1174daf691c66"),
]
WINDOW_SECONDS = 5
MIN_SAMPLES = 70
MIN_SPAN = 3.5
MAX_SAMPLE_GAP = 0.3
EPS = 1e-6


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def seconds_of_day(t: str) -> float:
    h, m, s = t.split(":")
    sec = int(h)*3600 + int(m)*60 + float(s)
    if not (0 <= sec < 86400):
        raise ValueError("INVALID_WALL_CLOCK")
    return sec


def windows_of_file(raw: bytes, file_index: int):
    """5s absolute wall-clock bins, never bridged over gaps or file edges."""
    rows = 0
    bad = 0
    gaps = 0
    clock_resets = 0
    dropped = 0
    output = []
    bucket = None
    prior_time = None
    prior_xyz = None
    run_id = 0

    def empty():
        return dict(n=0, s1=[0.,0.,0.], s2=[0.,0.,0.],
                    diff2=0., diffn=0, first=None, last=None,
                    bin=None, run=None)

    def emit():
        nonlocal bucket, dropped
        if not bucket or not bucket["n"]:
            return
        w = bucket
        if (w["n"] >= MIN_SAMPLES and
                w["last"]-w["first"] >= MIN_SPAN and w["diffn"]):
            var = max(0.,sum(max(0., w["s2"][j]/w["n"] -
                (w["s1"][j]/w["n"])**2) for j in range(3)))
            output.append({
                "file_index":file_index, "run":w["run"], "bin":w["bin"],
                "rms":math.sqrt(var),
                "rough":math.sqrt(w["diff2"]/w["diffn"]), "n":w["n"],
            })
        else:
            dropped += 1
        bucket = None

    for row in raw.splitlines():
        if not row.strip():
            continue
        parts = row.decode("ascii").strip().split(",")
        if len(parts) != 4:
            bad += 1
            emit(); prior_time = None; prior_xyz = None; run_id += 1
            continue
        try:
            t = seconds_of_day(parts[0])
            xyz = tuple(float(v) for v in parts[1:])
            if not all(math.isfinite(v) for v in xyz):
                raise ValueError("NONFINITE")
        except ValueError:
            bad += 1
            emit(); prior_time = None; prior_xyz = None; run_id += 1
            continue
        rows += 1
        if prior_time is not None and (
                t <= prior_time or t-prior_time > MAX_SAMPLE_GAP):
            if t <= prior_time:
                clock_resets += 1
            else:
                gaps += 1
            emit(); run_id += 1; prior_xyz = None

        tbin = int(t//WINDOW_SECONDS)
        if bucket is not None and (
                tbin != bucket["bin"] or run_id != bucket["run"]):
            emit()
        if bucket is None:
            bucket=empty()
            bucket["first"]=t
            bucket["bin"]=tbin
            bucket["run"]=run_id
        w=bucket
        w["n"] += 1
        w["last"] = t
        for j in range(3):
            w["s1"][j] += xyz[j]
            w["s2"][j] += xyz[j]**2
        if (prior_xyz is not None and prior_time is not None and
                t > prior_time and t-prior_time <= MAX_SAMPLE_GAP):
            w["diffn"] += 1
            w["diff2"] += sum((xyz[j]-prior_xyz[j])**2
                               for j in range(3))
        prior_time=t
        prior_xyz=xyz
    emit()
    return output, {
        "rows_parsed": rows, "rows_rejected":bad,
        "acquisition_gaps_gt_0_3s":gaps,
        "clock_regressions":clock_resets,
        "partial_windows_dropped":dropped,
    }


def quantile(values, q):
    x=sorted(values)
    if not x:
        raise ValueError("NO_VALID_WINDOWS")
    ix=(len(x)-1)*q
    a=int(ix)
    b=min(a+1,len(x)-1)
    return x[a]+(ix-a)*(x[b]-x[a])


def scaled_mad(values):
    mid=statistics.median(values)
    return statistics.median(abs(x-mid) for x in values)*1.4826


def fit_three_centers(training):
    # The *only* unsupervised model fit. The third shift never updates it.
    raw=[(math.log(w["rms"]+EPS),math.log(w["rough"]+EPS))
         for w in training]
    loc=[statistics.median(v[j] for v in raw) for j in range(2)]
    scale=[max(1e-6,scaled_mad([v[j] for v in raw]))
           for j in range(2)]
    x=[((v[0]-loc[0])/scale[0],(v[1]-loc[1])/scale[1])
       for v in raw]
    sorted_ix=sorted(range(len(x)),key=lambda i:x[i][0])
    centers=[x[sorted_ix[int((len(x)-1)*q)]] for q in (0.15,0.5,0.85)]
    for _ in range(75):
        assignments=[min(range(3), key=lambda j:
            (z[0]-centers[j][0])**2+(z[1]-centers[j][1])**2)
            for z in x]
        new=[]
        for j in range(3):
            members=[z for z,a in zip(x,assignments) if a==j]
            if not members:
                raise ValueError("EMPTY_UNSUPERVISED_CLUSTER")
            new.append((sum(z[0] for z in members)/len(members),
                        sum(z[1] for z in members)/len(members)))
        if max(math.dist(centers[j],new[j]) for j in range(3))<1e-8:
            centers=new
            break
        centers=new
    centers=sorted(centers,key=lambda v:v[0])
    return loc,scale,centers


def cluster_of(w,loc,scale,centers):
    p=((math.log(w["rms"]+EPS)-loc[0])/scale[0],
       (math.log(w["rough"]+EPS)-loc[1])/scale[1])
    return min(range(3),key=lambda j:
        (p[0]-centers[j][0])**2+(p[1]-centers[j][1])**2)


def episode_lengths(windows, flags):
    """Consecutive >threshold windows in one contiguous file/run only."""
    indexed=sorted((w["file_index"],w["run"],w["bin"])
                   for w,high in zip(windows,flags) if high)
    lengths=[]
    last=None
    for x in indexed:
        if (last is not None and x[0]==last[0] and
                x[1]==last[1] and x[2]==last[2]+1):
            lengths[-1]+=5
        else:
            lengths.append(5)
        last=x
    return lengths


def evaluate(root:Path):
    all_windows=[]
    qc_by_shift=defaultdict(Counter)
    for fi,(shift,name,size,sha) in enumerate(SOURCES):
        p=root/(name+".bin")
        content=p.read_bytes()
        if len(content)!=size or blob_sha1(content)!=sha:
            raise ValueError("WEBA_UNVERIFIED_SOURCE_SHA1")
        windows,qc=windows_of_file(content,fi)
        qc_by_shift[shift].update(qc)
        qc_by_shift[shift]["verified_blobs"]+=1
        all_windows.extend(dict(w,shift=shift) for w in windows)
    training=[w for w in all_windows if w["shift"] in TRAIN]
    if len(training)<200:
        raise ValueError("INSUFFICIENT_CALIBRATION_WINDOWS")
    baseline=statistics.median(w["rms"] for w in training)
    sigma=max(1e-6,scaled_mad([w["rms"] for w in training]))
    loc,scale,centers=fit_three_centers(training)

    out={
        "schema":"weba-three-shift-vibration-exploration/0.1",
        "upstream_repo":UPSTREAM_REPO,
        "upstream_git_commit_sha":UPSTREAM_COMMIT,
        "source_data":"12 full machine acceleration files; SHA1+bytes pinned",
        "calibration_shifts":list(TRAIN),
        "descriptive_holdout":HOLDOUT,
        "window_seconds":WINDOW_SECONDS,
        "min_window_samples":MIN_SAMPLES,
        "min_span_seconds":MIN_SPAN,
        "max_gap_seconds":MAX_SAMPLE_GAP,
        "total_verified_machine_files":len(SOURCES),
        "total_valid_windows":len(all_windows),
        "train_median_rms":round(baseline,6),
        "train_scaled_mad_rms":round(sigma,6),
        "threshold_default_train_median_plus_2_5mad":round(
            baseline+2.5*sigma,6),
        "three_centers_learned_train_only":{
            "features":"log(dynamic_rms), log(adjacent_sample_diff_rms)",
            "scaled_centers_low_to_high":[[round(v,3) for v in c]
                                           for c in centers],
            "interpretation":"statistical groups only, not verified physical modes"
        },
        "shifts":[],
        "limitations":[
            "Not externally labeled activity, drink or completed service",
            "5 s bins with >=70 samples, >=3.5s span; no interpolation",
            "Unobserved recording gaps cannot be marked as inactivity",
            "Vibration may be handling, machine operation, sensor noise or impact",
            "A held-out shift without physical labels is not validation",
            "No POS matching or clock offset estimated",
            "No causal attribution or capacity identification",
            "No sample/order/event timestamps or individual traces exported"
        ],
        "task_ground_truth_verified":False,
        "machine_cycle_verified":False,
        "order_to_cycle_match_performed":False,
        "retrospective_not_blind":True,
        "D_B_M_unchanged":True,
        "O2_authorized":False,
        "G4":"NOT_RUN","G5":"NOT_RUN",
        "F5_independent_reserve":"NOT_CREATED",
    }

    for shift in (*TRAIN,HOLDOUT):
        w=[x for x in all_windows if x["shift"]==shift]
        rms=[x["rms"] for x in w]
        rough=[x["rough"] for x in w]
        labels=Counter(cluster_of(x,loc,scale,centers) for x in w)
        probes=[]
        for multiplier in (1.5,2.5,3.5):
            cutoff=baseline+multiplier*sigma
            flags=[x["rms"]>cutoff for x in w]
            lengths=episode_lengths(w,flags)
            episodes=[x for x in lengths if x>=10]
            probes.append({
                "scaled_mad_multiplier":multiplier,
                "threshold_rms":round(cutoff,6),
                "high_windows":sum(flags),
                "high_window_fraction":round(sum(flags)/len(w),4),
                "episodes_ge_10_seconds":len(episodes),
                "episode_durations_ge_10_seconds_total":sum(episodes),
                "median_candidate_duration_seconds":(
                    statistics.median(episodes) if episodes else None),
                "max_candidate_duration_seconds":(
                    max(episodes) if episodes else None),
                "isolated_5s_peaks":len(lengths)-len(episodes),
            })
        out["shifts"].append({
            "shift":shift,
            "role":"TRAIN_DESCRIPTIVE" if shift in TRAIN else "HOLDOUT_DESCRIPTIVE",
            "verified_machine_files":qc_by_shift[shift]["verified_blobs"],
            "rows_parsed":qc_by_shift[shift]["rows_parsed"],
            "rows_rejected":qc_by_shift[shift]["rows_rejected"],
            "sampling_gaps_gt_0_3s":qc_by_shift[shift]["acquisition_gaps_gt_0_3s"],
            "clock_regressions":qc_by_shift[shift]["clock_regressions"],
            "partial_windows_dropped":qc_by_shift[shift]["partial_windows_dropped"],
            "valid_5s_windows":len(w),
            "valid_window_coverage_seconds_non_contiguous":len(w)*5,
            "rms_quantiles_p10_p50_p90":[round(quantile(rms,q),5)
                                         for q in (0.1,0.5,0.9)],
            "roughness_quantiles_p10_p50_p90":[round(quantile(rough,q),5)
                                               for q in (0.1,0.5,0.9)],
            "cluster_counts_by_rms_low_medium_high":[labels[i] for i in range(3)],
            "cluster_fractions_by_rms_low_medium_high":[
                round(labels[i]/len(w),4) for i in range(3)],
            "threshold_sensitivity":probes,
        })
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        raise ValueError("REFUSE_OVERWRITE_PILOT_RESULT")
    result=evaluate(args.root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=True,
                                   indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "verified_machine_blobs":result["total_verified_machine_files"],
        "valid_5s_windows":result["total_valid_windows"],
        "per_shift":[{
            "shift":x["shift"],
            "high_window_fraction_default":
                x["threshold_sensitivity"][1]["high_window_fraction"],
            "candidate_episodes_ge10s_default":
                x["threshold_sensitivity"][1]["episodes_ge_10_seconds"],
        } for x in result["shifts"]],
        "G4":result["G4"],"G5":result["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
