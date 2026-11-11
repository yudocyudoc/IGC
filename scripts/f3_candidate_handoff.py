"""Run a synthetic ATMS selection through the OpenModelica handoff."""
from __future__ import annotations

import json
import math
from pathlib import Path

try:
    from .f0_candidate_handoff import ROOT, CANDIDATE_PATH, run_candidate_handoff
    from .f3_candidate_selection import select_candidates
except ImportError:
    from f0_candidate_handoff import ROOT, CANDIDATE_PATH, OUTPUT_DIR, run_candidate_handoff
    from f3_candidate_selection import select_candidates


PROPOSALS_PATH = ROOT / "data" / "synthetic" / "f3_candidate_proposals.json"
ARTIFACT_DIR = ROOT / "artifacts" / "f3"
HANDOFF_DIR = ARTIFACT_DIR / "candidate-handoff"


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    base = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    proposal_set = json.loads(PROPOSALS_PATH.read_text(encoding="utf-8"))
    if proposal_set.get("schema") != "igc-atms-candidate-proposals/0.1" or not proposal_set.get("synthetic"):
        raise SystemExit("unsupported or non-synthetic proposal fixture")

    selection = select_candidates(
        base, proposal_set["proposals"], proposal_set["assumptions"], proposal_set["nogoods"]
    )
    selection_path = ARTIFACT_DIR / "selection.json"
    selection_path.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    if len(selection["selected"]) != 1:
        raise SystemExit(f"expected exactly one ATMS-supported candidate, got {len(selection['selected'])}")

    selected_path = ARTIFACT_DIR / "selected-candidate.json"
    selected_path.write_text(json.dumps(selection["selected"][0]["candidate"],
                                        ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    result = run_candidate_handoff(candidate_path=selected_path, output_dir=HANDOFF_DIR)
    if result.get("status") == "PASS":
        if (not math.isclose(float(result.get("base_final_stock", float("nan"))), 30.0,
                             rel_tol=1e-7, abs_tol=1e-7)
                or not math.isclose(float(result.get("perturbed_final_stock", float("nan"))), 40.0,
                                    rel_tol=1e-7, abs_tol=1e-7)):
            result = {"stage": "atms_selected_candidate_handoff", "status": "FAIL",
                      "reason": "selected parameter did not produce the expected 30/40 trajectory"}
    result["stage"] = "atms_selected_candidate_handoff"
    result["selection"] = str(selection_path.relative_to(ROOT))
    result["selected_candidate_id"] = selection["selected"][0]["candidate"]["candidate_id"]
    result["rejected_candidate_ids"] = [item["candidate_id"] for item in selection["rejected"]]
    report = {"schema": "igc-f3-atms-handoff/0.1",
              "status": "PASS_SYNTHETIC" if result.get("status") == "PASS" else "FAIL",
              "synthetic": True, "selection_result": str(selection_path.relative_to(ROOT)),
              "selected_candidate": str(selected_path.relative_to(ROOT)), "handoff": result}
    report_path = ARTIFACT_DIR / "run.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS_SYNTHETIC" else 2


if __name__ == "__main__":
    raise SystemExit(main())
