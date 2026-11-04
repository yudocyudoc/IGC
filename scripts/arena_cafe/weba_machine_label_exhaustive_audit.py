"""Exhaustive, source-pinned WEBA coffee-machine file *format* audit.

Only public upstream machine acceleration is examined. This is not a beverage
detector, not a cycle/finish operator, and never accesses human physiology,
questionnaires, motion sensors, the POS, or any user's private Drive.
All reports are aggregate, with no per-event times, order IDs or raw rows.

IMPORTANT: completeness here is relative to the pinned GitHub tree; four
Drive-vs-GitHub hashes checked separately cannot certify full archive identity.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import re
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

UPSTREAM_REPO = "Department-of-System-Engineering/datasets_WEBA"
UPSTREAM_COMMIT = "d6841669e544579547c94b7ce1e8613bbd6b3a39"
SCHEMA = "igc-weba-machine-format-exhaustive-source-audit/0.1"
TREE_URL = (f"https://api.github.com/repos/{UPSTREAM_REPO}"
            f"/git/trees/{UPSTREAM_COMMIT}?recursive=1")
RAW_ROOT = (f"https://raw.githubusercontent.com/"
            f"{UPSTREAM_REPO}/{UPSTREAM_COMMIT}/")
SHIFT_RE = re.compile(r"^B\.shift_data/(\d{8}_(?:morning|evening))$")
MACHINE_RE = re.compile(
    r"^B\.shift_data/(\d{8}_(?:morning|evening))/"
    r"(5\.coffee_machine_acc|5\.kave)"
    r"(?:/(\d{8}_\d{6}|\d{6}(?:\.coffee_machine_acc)?))?$"
)
CLOCK_RE = re.compile(rb"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?$")
EXPECTED = {
    "shift_folders": 55,
    "machine_signal_files": 209,
    "flat_files": 12,
    "standard_fragments": 185,
    "kave_fragments": 12,
    "machine_shifts": 53,
    "missing_machine_shifts": 2,
}
PRIVATE_FIELDS = {"order_ID", "participant_id", "par_ID", "event_time",
                  "raw_row", "exact_timestamp", "device_id"}


def need(ok: bool, code: str):
    if not ok:
        raise ValueError(code)


def inventory(tree: dict) -> tuple[list[dict], list[str]]:
    need(tree.get("truncated") is False and isinstance(tree.get("tree"), list),
         "WEBA_TREE_TRUNCATED_OR_MALFORMED")
    shifts = set()
    files = []
    for entry in tree["tree"]:
        path = entry.get("path", "")
        if entry.get("type") == "tree" and SHIFT_RE.fullmatch(path):
            shifts.add(SHIFT_RE.fullmatch(path).group(1))
        if entry.get("type") != "blob":
            continue
        found = MACHINE_RE.fullmatch(path)
        if not found:
            continue
        shift, channel, segment = found.groups()
        need(entry.get("size", -1) > 0 and
             re.fullmatch(r"[0-9a-f]{40}", entry.get("sha", "")),
             "WEBA_MACHINE_INVALID_GIT_BLOB_METADATA")
        kind = ("KAVE_FRAGMENT" if channel == "5.kave" else
                "STANDARD_FRAGMENT" if segment else "FLAT_FILE")
        need(channel != "5.kave" or segment is not None,
             "WEBA_UNEXPECTED_KAVE_FILE")
        files.append({
            "path": path, "git_sha1": entry["sha"], "bytes": entry["size"],
            "kind": kind, "shift": shift,
        })
    need(len(shifts) == EXPECTED["shift_folders"],
         "WEBA_UPSTREAM_SHIFT_COUNT_CHANGED")
    need(all(f["shift"] in shifts for f in files),
         "WEBA_MACHINE_OUTSIDE_DECLARED_SHIFT")
    kinds = Counter(f["kind"] for f in files)
    count = {
        "shift_folders": len(shifts),
        "machine_signal_files": len(files),
        "flat_files": kinds["FLAT_FILE"],
        "standard_fragments": kinds["STANDARD_FRAGMENT"],
        "kave_fragments": kinds["KAVE_FRAGMENT"],
        "machine_shifts": len({f["shift"] for f in files}),
        "missing_machine_shifts": len(shifts - {f["shift"] for f in files}),
    }
    need(count == EXPECTED, "WEBA_PINNED_INVENTORY_CHANGED")
    return files, sorted(shifts)


def read_upstream_tree() -> dict:
    request = Request(TREE_URL, headers={
        "User-Agent": "IGC-WEBA-machine-format-retrospective-research",
        "Accept": "application/vnd.github+json",
    })
    with urlopen(request, timeout=45) as response:
        data = response.read()
    return json.loads(data)


def scan_file_bytes(raw: bytes) -> dict:
    """Inspect *every* line: no sampling, no FFT, no activity detection."""
    count = Counter()
    for row in raw.splitlines():
        if not row.strip():
            count["blank_rows"] += 1
            continue
        count["nonblank_rows"] += 1
        fields = row.strip().split(b",")
        if len(fields) != 4:
            count["unexpected_column_count"] += 1
            continue
        if not CLOCK_RE.fullmatch(fields[0].strip()):
            count["unexpected_time_format"] += 1
            continue
        try:
            xyz = tuple(float(x.strip()) for x in fields[1:])
        except ValueError:
            count["nonnumeric_xyz"] += 1
            continue
        if not all(math.isfinite(x) for x in xyz):
            count["nonfinite_xyz"] += 1
            continue
        count["valid_time_and_numeric_xyz"] += 1
    need(count["nonblank_rows"] == (
        count["unexpected_column_count"] + count["unexpected_time_format"] +
        count["nonnumeric_xyz"] + count["nonfinite_xyz"] +
        count["valid_time_and_numeric_xyz"]),
        "WEBA_MACHINE_ROW_MASS_NOT_CONSERVED")
    return dict(count)


def scan_entry(entry: dict, fetch=None) -> dict:
    """Read the entire pinned blob; validate the git object, then each row."""
    if fetch is None:
        fetch = _fetch_raw
    raw = fetch(entry["path"])
    need(len(raw) == entry["bytes"], "WEBA_MACHINE_BLOB_BYTES_DIFFER")
    h = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
    need(h == entry["git_sha1"], "WEBA_MACHINE_BLOB_SHA1_DIFFER")
    stats = scan_file_bytes(raw)
    return {
        "kind": entry["kind"],
        "shift": entry["shift"],
        "bytes": len(raw),
        "sha1_verified": True,
        "rows": stats,
    }


def _fetch_raw(path: str) -> bytes:
    """Bounded retries for transient CDN failures, never a mutable branch."""
    url = RAW_ROOT + quote(path, safe="/")
    for attempt in range(3):
        try:
            request = Request(url, headers={
                "User-Agent": "IGC-WEBA-machine-format-retrospective-research"
            })
            with urlopen(request, timeout=150) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("WEBA_MACHINE_FETCH_NOT_COMPLETED")


def build(files: list[dict], shifts: list[str], worker_count: int = 5) -> dict:
    need(1 <= worker_count <= 8, "WEBA_MACHINE_WORKERS_OUT_OF_RANGE")
    reports = []
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(scan_entry, entry) for entry in files]
        for future in as_completed(futures):
            reports.append(future.result())
            if len(reports) % 25 == 0:
                print("WEBA_MACHINE_VERIFIED_BLOBS", len(reports), flush=True)
    need(len(reports) == len(files) and
         all(report["sha1_verified"] for report in reports),
         "WEBA_MACHINE_INCOMPLETE_BLOB_SCAN")
    by_type = {}
    for category in ("FLAT_FILE", "STANDARD_FRAGMENT", "KAVE_FRAGMENT"):
        records = [r for r in reports if r["kind"] == category]
        rows = Counter()
        for record in records:
            rows.update(record["rows"])
        by_type[category] = {
            "verified_files": len(records),
            "verified_bytes": sum(r["bytes"] for r in records),
            "row_class_counts": dict(sorted(rows.items())),
            "files_with_nonstandard_rows": sum(
                bool(sum(r["rows"].get(key, 0) for key in (
                    "unexpected_column_count", "unexpected_time_format",
                    "nonnumeric_xyz", "nonfinite_xyz"))) for r in records
            ),
        }
    totals = Counter()
    for report in reports:
        totals.update(report["rows"])
    irregular = sum(totals.get(k, 0) for k in (
        "unexpected_column_count", "unexpected_time_format",
        "nonnumeric_xyz", "nonfinite_xyz"))
    verified_shifts = {r["shift"] for r in reports}
    result = {
        "schema": SCHEMA,
        "upstream_repository": UPSTREAM_REPO,
        "upstream_git_commit_fixed": UPSTREAM_COMMIT,
        "source_type": "GITHUB_PUBLIC_MIRROR_ONLY",
        "github_tree_not_truncated": True,
        "shift_folders_verified": len(shifts),
        "machine_shifts_with_files": len(verified_shifts),
        "shifts_without_machine_files": len(set(shifts) - verified_shifts),
        "machine_files_fully_read_and_git_blob_verified": len(reports),
        "machine_bytes_fully_read_and_verified": sum(r["bytes"] for r in reports),
        "by_source_form": by_type,
        "total_rows": dict(sorted(totals.items())),
        "nonstandard_nonblank_rows": irregular,
        "format_annotation_candidate_rows": irregular,
        "all_machine_files_are_pure_time_plus_numeric_XYZ": (
            irregular == 0 and totals["valid_time_and_numeric_xyz"] > 0),
        "all_209_machine_files_scanned": len(reports) == EXPECTED[
            "machine_signal_files"],
        "raw_rows_event_timestamps_or_order_ID_exported": False,
        "machine_cycle_ground_truth_observed": False,
        "per_order_correlation_matching_performed": False,
        "POS_clock_or_completion_link_validated": False,
        "figshare_rar_directly_compared_bytewise": False,
        "google_drive_copy_fully_compared_bytewise": False,
        "retrospective_not_blind": True,
        "G4": "NOT_RUN",
        "G5": "NOT_RUN",
        "F5_independent_reserve": "NOT_CREATED",
        "D_B_M_models_unchanged": True,
    }
    need(not any(key in result for key in PRIVATE_FIELDS),
         "WEBA_MACHINE_PRIVACY_FIELD_IN_REPORT")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--workers", type=int, default=5)
    args = p.parse_args()
    need(not args.out.exists(), "WEBA_MACHINE_REFUSE_OVERWRITE")
    files, shifts = inventory(read_upstream_tree())
    result = build(files, shifts, args.workers)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True,
                                  ensure_ascii=True, indent=2) + "\n")
    print(json.dumps({
        "verified_machine_files": result[
            "machine_files_fully_read_and_git_blob_verified"],
        "verified_machine_bytes": result[
            "machine_bytes_fully_read_and_verified"],
        "nonstandard_nonblank_rows": result["nonstandard_nonblank_rows"],
        "all_time_numeric_XYZ": result[
            "all_machine_files_are_pure_time_plus_numeric_XYZ"],
        "G5": result["G5"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
