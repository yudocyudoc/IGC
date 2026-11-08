"""CT-01: byte verification of historical Actions ZIPs without replay.

Run with --artifact-dir <dir> holding github-actions-artifact-<id>.zip.
Missing archives are NOT_MOUNTED, never fabricated or treated as model failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "experiments/cafeteria/CT01_VERIFIED_ARCHIVE_DIGESTS_2026-11-07.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_archives(directory: Path, manifest: dict) -> dict:
    if manifest.get("schema") != "igc-ct01-authentic-actions-artifact-digests/1.0":
        raise ValueError("CT01_UNEXPECTED_DIGEST_MANIFEST")
    results = []
    for x in manifest["archives"]:
        artifact_id = x["artifact_id"]
        path = directory / f"github-actions-artifact-{artifact_id}.zip"
        if not path.is_file():
            results.append({"artifact_id": artifact_id, "capability": x["capability"],
                            "status": "ARTIFACT_NOT_MOUNTED", "verified_entries": 0})
            continue
        if sha(path.read_bytes()) != x["zip_sha256"]:
            results.append({"artifact_id": artifact_id, "capability": x["capability"],
                            "status": "ZIP_SHA256_MISMATCH", "verified_entries": 0})
            continue
        try:
            with ZipFile(path) as z:
                names = z.namelist()
                if len(names) != x["entry_count"] or len(names) != len(set(names)):
                    raise ValueError("CT01_ZIP_ENTRY_COUNT_OR_DUPLICATES")
                for name, expected in x["entries"].items():
                    if name not in names or sha(z.read(name)) != expected:
                        raise ValueError("CT01_INNER_ENTRY_SHA_MISMATCH:" + name)
        except (BadZipFile, KeyError, ValueError) as err:
            results.append({"artifact_id": artifact_id, "capability": x["capability"],
                            "status": "INNER_ARCHIVE_VERIFY_FAILED", "reason": str(err),
                            "verified_entries": 0})
            continue
        results.append({"artifact_id": artifact_id, "capability": x["capability"],
                        "status": "DOWNLOADED_ZIP_AND_SELECTED_ENTRY_BYTES_VERIFIED",
                        "verified_entries": len(x["entries"])})
    return {"schema": "igc-ct01-artifact-byte-verification/1.0",
            "artifacts": results,
            "passed": sum(r["status"] == "DOWNLOADED_ZIP_AND_SELECTED_ENTRY_BYTES_VERIFIED"
                          for r in results),
            "missing": sum(r["status"] == "ARTIFACT_NOT_MOUNTED" for r in results),
            "no_reexecuted_experiments": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-dir", required=True, type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = check_archives(args.artifact_dir, manifest)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 1 if any(r["status"] not in (
        "ARTIFACT_NOT_MOUNTED", "DOWNLOADED_ZIP_AND_SELECTED_ENTRY_BYTES_VERIFIED")
                    for r in report["artifacts"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
