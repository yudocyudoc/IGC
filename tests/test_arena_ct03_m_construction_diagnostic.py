"""CT-02 M handoff: strict source/model/CSV checks and actual own_policy call.

Fixture CSV is synthetic TEST ONLY; no claim of actual OpenModelica success.
"""
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_m_prepare import prepare, PUBLIC_INPUT
from scripts.arena_cafe.ct03_m_construction_diagnostic import (
    build, sha_bytes, RECEIPT_SCHEMA, OBS_SCHEMA,
    _expected_simulation_command,
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
        # OpenModelica native CSV convention (also seen in archived M2 CSV):
        # quoted names, with ROOT name not class-prefixed.
        f.write('"time","deliveredTotal"\n')
        writer = csv.writer(f)
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
        "output_role": "deliveredTotal",
        "model_name": "ArenaCT03M." + parent["class_name"],
        "csv_prefix": parent["csv_prefix"],
        "csv_column": "deliveredTotal",
        "simulate_script_sha256": sha_bytes((target / "simulate.mos").read_bytes()),
        "simulation_command": _expected_simulation_command(parent),
        "csv_filename": csv_path.name}
    return manifest, parent, context, observed, receipt, target / "native.mo", csv_path


class CT03MOwnDiagnosticTests(unittest.TestCase):
    def test_original_parent_csv_receipt_to_own_policy_and_ledger(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, parent, ctx, public, receipt, native, csv_path = make_example(root)
            diag = build(ctx, manifest=manifest, parent=parent,
                construction=public, receipt=receipt,
                modelica_file=native, simulate_script_file=native.parent / "simulate.mos",
                trace_csv=csv_path)
            self.assertEqual(diag["observations"][2]["residual"], .6 - .2)
            self.assertEqual(diag["G3"], "CONSTRUCTION_RESIDUALS_ONLY_NO_HELDOUT")
            self.assertTrue(diag["no_future_truth"])
            self.assertEqual(diag["native_samples"], 65)
            self.assertEqual(diag["native_output_column"], "deliveredTotal")
            self.assertEqual(diag["native_output_filename"], "m00_res.csv")
            self.assertEqual(csv_path.read_text().splitlines()[0],
                             '"time","deliveredTotal"')
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
                      modelica_file=n, simulate_script_file=n.parent / "simulate.mos", trace_csv=s)

    def test_changed_csv_and_parent_is_rejected(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,s = make_example(Path(tmp))
            changed = dict(r)
            changed["csv_sha256"] = "sha256:" + "f"*64
            with self.assertRaisesRegex(ValueError, "RECEIPT_MISMATCH"):
                build(c, manifest=m, parent=p, construction=o, receipt=changed,
                      modelica_file=n, simulate_script_file=n.parent / "simulate.mos", trace_csv=s)
            with self.assertRaisesRegex(ValueError, "PARENT_NOT_FROM_THE_SIX"):
                build(c, manifest=m, parent={**m["candidates"][1], "spurious": True},
                      construction=o, receipt=r, modelica_file=n, simulate_script_file=n.parent / "simulate.mos", trace_csv=s)

    def test_missing_exact_time_is_not_zero_or_interpolated(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,s = make_example(Path(tmp))
            lines=s.read_text().splitlines()
            lines=[line for line in lines if not line.startswith("2.0,")]
            s.write_text("\n".join(lines)+"\n")
            r["csv_sha256"]=sha_bytes(s.read_bytes())
            with self.assertRaisesRegex(ValueError, "EXACT_CONSTRUCTION"):
                build(c, manifest=m, parent=p, construction=o, receipt=r,
                      modelica_file=n, simulate_script_file=n.parent / "simulate.mos", trace_csv=s)

    def test_extra_evaluator_truth_rejected(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,s = make_example(Path(tmp))
            o["heldout_t8"] = 2.9
            with self.assertRaisesRegex(ValueError, "EXTRA_FIELDS_IN_CONSTRUCTION"):
                build(c, manifest=m, parent=p, construction=o, receipt=r,
                      modelica_file=n, simulate_script_file=n.parent / "simulate.mos", trace_csv=s)


    def test_csv_of_another_original_m_candidate_rejected_even_with_updated_sha(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,csv_path = make_example(Path(tmp))
            other = next(x for x in m["candidates"] if
                         x["material_only_projection_sha256"] !=
                         p["material_only_projection_sha256"])
            rows = csv_path.read_text().splitlines()
            old_col = r["csv_column"]
            new_col = "ArenaCT03M." + other["class_name"] + ".deliveredTotal"
            rows[0] = rows[0].replace(old_col, new_col)
            csv_path.write_text("\n".join(rows) + "\n")
            r["csv_sha256"] = sha_bytes(csv_path.read_bytes())
            with self.assertRaisesRegex(ValueError, "WRONG_OR_AMBIGUOUS_CANDIDATE_CSV_COLUMN"):
                build(c,manifest=m,parent=p,construction=o,receipt=r,
                      modelica_file=n,simulate_script_file=n.parent/"simulate.mos",
                      trace_csv=csv_path)
            r["csv_column"] = new_col
            with self.assertRaisesRegex(ValueError, "NATIVE_CSV_OR_RUNTIME_RECEIPT_MISMATCH"):
                build(c,manifest=m,parent=p,construction=o,receipt=r,
                      modelica_file=n,simulate_script_file=n.parent/"simulate.mos",
                      trace_csv=csv_path)


    def test_native_root_column_and_source_command_are_bound_to_this_parent(self):
        """Accept actual OpenModelica variable naming; reject false provenance."""
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,csv_path = make_example(Path(tmp))
            # A true native header does NOT include the class name.
            ok = build(c,manifest=m,parent=p,construction=o,receipt=r,
                       modelica_file=n,simulate_script_file=n.parent/"simulate.mos",
                       trace_csv=csv_path)
            self.assertEqual(ok["native_output_column"], "deliveredTotal")
            self.assertEqual(ok["native_output_filename"], csv_path.name)
            # The same root-variable heading is also valid without CSV quotes.
            csv_path.write_text(csv_path.read_text().replace(
                '"time","deliveredTotal"', 'time,deliveredTotal', 1))
            unquoted_receipt = {**r, "csv_sha256": sha_bytes(csv_path.read_bytes())}
            self.assertEqual(build(c,manifest=m,parent=p,construction=o,
                receipt=unquoted_receipt,modelica_file=n,
                simulate_script_file=n.parent/"simulate.mos",
                trace_csv=csv_path)["native_output_column"], "deliveredTotal")
            variants = [
                ("csv_prefix", "m04"),
                ("csv_filename", "m04_res.csv"),
                ("simulate_script_sha256", "sha256:"+"f"*64),
                ("simulation_command", r["simulation_command"].replace("m00", "m04")),
            ]
            for field, fake in variants:
                forged = {**r, field: fake}
                with self.subTest(field=field),self.assertRaisesRegex(
                        ValueError,"NATIVE_CSV_OR_RUNTIME_RECEIPT_MISMATCH"):
                    build(c,manifest=m,parent=p,construction=o,receipt=forged,
                          modelica_file=n,simulate_script_file=n.parent/"simulate.mos",
                          trace_csv=csv_path)

    def test_reject_prefixed_self_column_ambiguous_root_and_dotted_output(self):
        with TemporaryDirectory() as tmp:
            m,p,c,o,r,n,csv_path = make_example(Path(tmp))
            root_header = csv_path.read_text().splitlines()
            own_prefixed = "ArenaCT03M."+p["class_name"]+".deliveredTotal"
            other = next(x for x in m["candidates"]
                         if x["material_only_projection_sha256"] !=
                            p["material_only_projection_sha256"])
            foreign = "ArenaCT03M."+other["class_name"]+".deliveredTotal"
            for columns in (
                ["time",own_prefixed],
                ["time",foreign],
                ["time","deliveredTotal",foreign],
                ["time","deliveredTotal",own_prefixed],
            ):
                csv_path.write_text(",".join(columns)+"\n"+
                    "\n".join(",".join([line.split(",")[0]]+
                        [line.split(",")[1]]*(len(columns)-1))
                        for line in root_header[1:])+"\n")
                bound = {**r, "csv_sha256": sha_bytes(csv_path.read_bytes())}
                with self.subTest(columns=columns), self.assertRaisesRegex(
                        ValueError,"WRONG_OR_AMBIGUOUS_CANDIDATE_CSV_COLUMN"):
                    build(c,manifest=m,parent=p,construction=o,receipt=bound,
                          modelica_file=n,simulate_script_file=n.parent/"simulate.mos",
                          trace_csv=csv_path)


    def test_cli_accepts_native_fixture_and_rejects_changed_script(self):
        """F172-06: exercise the actual Python -m entry point, not only build()."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, parent, context, construction, receipt, native, csv_path = make_example(root)
            for filename, obj in (
                ("parent.json", parent),
                ("context.json", context),
                ("construction.json", construction),
                ("receipt.json", receipt),
            ):
                (root / filename).write_text(json.dumps(obj), encoding="utf-8")

            script = native.parent / "simulate.mos"
            output = root / "cli-diagnostic.json"
            argv = [
                sys.executable, "-m",
                "scripts.arena_cafe.ct03_m_construction_diagnostic",
                "--manifest", str(native.parent / "manifest.json"),
                "--parent", str(root / "parent.json"),
                "--construction", str(root / "construction.json"),
                "--receipt", str(root / "receipt.json"),
                "--context", str(root / "context.json"),
                "--native", str(native),
                "--simulate-script", str(script),
                "--csv", str(csv_path),
                "--out", str(output),
            ]
            repo = Path(__file__).resolve().parents[1]
            completed = subprocess.run(
                argv, cwd=repo, capture_output=True, text=True, timeout=30
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output.is_file(), completed.stdout)
            direct = build(
                context, manifest=manifest, parent=parent,
                construction=construction, receipt=receipt,
                modelica_file=native, simulate_script_file=script,
                trace_csv=csv_path,
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), direct)
            self.assertEqual(json.loads(completed.stdout)["provider_calls"], 0)
            self.assertEqual(json.loads(completed.stdout)["new_omc"], 0)

            # A different script is not allowed even with valid CSV/manifest.
            script.write_text(script.read_text() + "// tampered script\\n", encoding="utf-8")
            blocked_output = root / "blocked-diagnostic.json"
            blocked = subprocess.run(
                argv[:-1] + [str(blocked_output)],
                cwd=repo, capture_output=True, text=True, timeout=30,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("CT02_M_NATIVE_CSV_OR_RUNTIME_RECEIPT_MISMATCH", blocked.stderr)
            self.assertNotIn("missing 1 required keyword-only argument", blocked.stderr)
            self.assertFalse(blocked_output.exists())


if __name__ == "__main__":
    unittest.main()
