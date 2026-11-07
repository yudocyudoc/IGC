"""CT-02 M handoff: strict source/model/CSV checks and actual own_policy call.

Fixture CSV is synthetic TEST ONLY; no claim of actual OpenModelica success.
"""
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_m_prepare import prepare, PUBLIC_INPUT
from scripts.arena_cafe.ct03_m_construction_diagnostic import (
    build, sha_bytes, RECEIPT_SCHEMA, OBS_SCHEMA,
)
from scripts.arena_cafe.ct_feedback_bridge import (
    make_context, record_feedback, own_m_decision, persist_disposition,
)

STAMP = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)


def make_example(root: Path):
    target = root / "ct03-m"
    manifest = prepare(target)
    parent = manifest["candidates"][0]
    src = "sha256:" + "a"*64
    context = make_context(experiment="CT03", world="W1",
        round_id="R0", arm="M", condition="C0", source_hash=src)
    observed = {"schema": OBS_SCHEMA,
        "source_snapshot_hash": src, "world_public_id": "W1",
        "condition_id": "C0", "time_unit": "hours",
        "observable": "cumulative_delivered",
        "observations": [{"time": t, "delivered": y}
                         for t, y in ((0, 0), (1, .1), (2, .2), (4, .4))]}
    csv_path = root / "m00_res.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "ArenaCT03M." + parent["class_name"] + ".deliveredTotal"])
        for i in range(65):
            t = i / 8
            writer.writerow([t, .3 * t])
    receipt = {"schema": RECEIPT_SCHEMA,
        "candidate_canonical_sha256": parent["canonical_sha256"],
        "full_ast_sha256": parent["full_ast_sha256"],
        "source_definition_sha256": manifest["source_definition_sha256"],
        "modelica_sha256": sha_bytes((target / "native.mo").read_bytes()),
        "csv_sha256": sha_bytes(csv_path.read_bytes()),
        "solver": "euler", "start_time": 0, "stop_time": 8,
        "number_of_intervals": 64, "exit_code": 0,
        "output_role": "deliveredTotal"}
    return manifest, parent, context, observed, receipt, target / "native.mo", csv_path


class CT03MOwnDiagnosticTests(unittest.TestCase):
    def test_original_parent_csv_receipt_to_own_policy_and_ledger(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, parent, ctx, public, receipt, native, csv_path = make_example(root)
            diag = build(ctx, manifest=manifest, parent=parent,
                construction=public, receipt=receipt,
                modelica_file=native, trace_csv=csv_path)
            self.assertEqual(diag["observations"][2]["residual"], .6 - .2)
            self.assertEqual(diag["G3"], "CONSTRUCTION_RESIDUALS_ONLY_NO_HELDOUT")
            self.assertTrue(diag["no_future_truth"])
            self.assertEqual(diag["native_samples"], 65)
            db = root / "ct.sqlite"
            record_feedback(db, ctx, parent_hash=diag["parent_hash"],
                diagnostic=diag, recorded_at=STAMP.isoformat())
            decision = own_m_decision(db, ctx, parent_graph=parent["original_ast"],
                as_known_at=(STAMP+timedelta(seconds=1)).isoformat())
            self.assertEqual(decision["status"], "REVISED")
            self.assertEqual(len(decision["parameter_edits"]), 2)
            result = persist_disposition(db, ctx, decision=decision,
                recorded_at=(STAMP+timedelta(seconds=2)).isoformat())
            self.assertEqual(result["model_change_count"], 1)
            self.assertEqual(result["provider_calls"], 0)
            self.assertEqual(result["new_omc"], 0)

    def test_future_construction_point_rejected_before_feedback(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,s = make_example(Path(tmp))
            o["observations"][3]["time"] = 6
            with self.assertRaisesRegex(ValueError, "FOUR_CONSTRUCTION_CUTS_REQUIRED"):
                build(c, manifest=m, parent=p, construction=o, receipt=r,
                      modelica_file=n, trace_csv=s)

    def test_changed_csv_and_parent_is_rejected(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,s = make_example(Path(tmp))
            changed = dict(r)
            changed["csv_sha256"] = "sha256:" + "f"*64
            with self.assertRaisesRegex(ValueError, "RECEIPT_MISMATCH"):
                build(c, manifest=m, parent=p, construction=o, receipt=changed,
                      modelica_file=n, trace_csv=s)
            with self.assertRaisesRegex(ValueError, "PARENT_NOT_FROM_THE_SIX"):
                build(c, manifest=m, parent=m["candidates"][1],
                      construction=o, receipt=r, modelica_file=n, trace_csv=s)

    def test_missing_exact_time_is_not_zero_or_interpolated(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,s = make_example(Path(tmp))
            lines=s.read_text().splitlines()
            lines=[line for line in lines if not line.startswith("2.0,")]
            s.write_text("\n".join(lines)+"\n")
            r["csv_sha256"]=sha_bytes(s.read_bytes())
            with self.assertRaisesRegex(ValueError, "EXACT_CONSTRUCTION"):
                build(c, manifest=m, parent=p, construction=o, receipt=r,
                      modelica_file=n, trace_csv=s)

    def test_extra_evaluator_truth_rejected(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,s = make_example(Path(tmp))
            o["heldout_t8"] = 2.9
            with self.assertRaisesRegex(ValueError, "EXTRA_FIELDS_IN_CONSTRUCTION"):
                build(c, manifest=m, parent=p, construction=o, receipt=r,
                      modelica_file=n, trace_csv=s)


if __name__ == "__main__":
    unittest.main()
