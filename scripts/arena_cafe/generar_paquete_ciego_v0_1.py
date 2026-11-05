#!/usr/bin/env python3
"""Genera clips ciegos y fotogramas desde un MP4 local verificando su SHA256."""
from __future__ import annotations
import argparse, csv, hashlib, json, subprocess
from pathlib import Path

VIDEO_SHA = "cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5"
WINDOWS = {"A": (2350, 2470), "B": (3750, 3870)}

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for part in iter(lambda: f.read(1024*1024), b""):
            h.update(part)
    return h.hexdigest()

def run(*argv):
    subprocess.run(argv, check=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if sha(args.source) != VIDEO_SHA:
        raise SystemExit("BLOQUEO: MP4 fuente no coincide con el preregistro")
    target = args.output
    target.mkdir(parents=True, exist_ok=True)
    media = target/"media"
    media.mkdir(exist_ok=True)
    samples = media/"fotogramas"
    samples.mkdir(exist_ok=True)
    rows=[]
    for key, (start, stop) in WINDOWS.items():
        filters = [
            "setpts=PTS-STARTPTS",
            "drawbox=x=383:y=0:w=257:h=81:color=black:t=fill",
        ]
        if key == "A":
            filters.append("drawbox=x=465:y=175:w=175:h=185:color=black:t=fill:enable='lt(t,26)'")
        clip=media/f"tramo_{key}_vista_principal.mp4"
        run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
            "-ss",str(start),"-i",str(args.source),"-t","120.10",
            "-an","-vf",",".join(filters),"-c:v","libx264",
            "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
            "-movflags","+faststart",str(clip))
        sampledir=samples/key
        sampledir.mkdir(exist_ok=True)
        for old in sampledir.glob("*.jpg"): old.unlink()
        run("ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
            "-i",str(clip),"-vf","fps=fps=1/2:start_time=0:round=up",
            "-q:v","3",str(sampledir/"frame_%03d.jpg"))
        frames=sorted(sampledir.glob("frame_*.jpg"))
        if len(frames)!=61:
            raise SystemExit(f"BLOQUEO: {key}: {len(frames)} frames; se esperaban 61")
        for i, frame in enumerate(frames):
            t=start+i*2
            final=sampledir/f"{key}_t{t:05d}.jpg"
            frame.rename(final)
            rows.append({"tramo":key,"video_s":t,
                         "archivo":final.relative_to(target).as_posix(),
                         "sha256":sha(final)})
    with (target/"MANIFIESTO_MUESTRAS.csv").open("w",encoding="utf-8",newline="") as f:
        out=csv.DictWriter(f,fieldnames=("tramo","video_s","archivo","sha256"))
        out.writeheader()
        out.writerows(rows)
    manifest = {
        "schema":"igc-arena-video-double-annotation/0.1",
        "source_video_sha256":VIDEO_SHA,
        "windows_video_s":{key:list(value) for key,value in WINDOWS.items()},
        "source_clock":"video_presentation_time_s",
        "physical_clock_verified":False,
        "continuous_recording_verified":False,
        "sampling_video_s":2,
        "sample_count":len(rows),
        "mask_policy":{
            "all":"ORDER oculto con rectángulo x=383..639, y=0..80",
            "A_first_26s":"inserto secundario oculto x=465..639, y=175..359",
            "B":"sin máscara inferior derecha",
            "warning":"región negra es OCLUIDA, nunca vacía",
        },
        "sha256_clips":{key:sha(media/f"tramo_{key}_vista_principal.mp4")
                        for key in WINDOWS},
        "frame_manifest_sha256":sha(target/"MANIFIESTO_MUESTRAS.csv"),
    }
    (target/"MANIFIESTO.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: SHA fuente, 2 clips, 122 muestras y manifiesto verificados")

if __name__=="__main__":
    main()
