"""Only offline structural probes of the fixed CT-02 two-OMC batch.

This does NOT run Docker or OMC and synthetic CSVs must NEVER be uploaded as
physical evidence. Physical tests require explicit manual dispatch and budget.
"""
import csv
import json
import math
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct02_minimal_batch import prepare, verify, verify_arm

class CT02TwoOnly(unittest.TestCase):
    def test_preparation_is_exactly_original_d0_and_short_e1_m_with_no_solver(self):
        with TemporaryDirectory(dir=".") as tmp:
            out=Path(tmp).relative_to(Path.cwd())/"two"
            x=prepare(out)
            self.assertEqual(x["planned_omc_runs"],2)
            self.assertEqual(x["actual_omc_runs"],0)
            self.assertEqual(x["provider_calls"],0)
            self.assertFalse(x["world_selected"])
            self.assertFalse(x["reserved_truth_opened"])
            self.assertEqual([a["arm"] for a in x["items"]], ["D","M"])
            for arm in ("D","M"):
                script=(out/(arm+"-single.mos")).read_text()
                self.assertEqual(script.count("simulate("),1)
                self.assertIn("numberOfIntervals=64",script)
                self.assertIn('method="euler"',script)
                self.assertIn("stopTime=8",script)
            m=json.loads((out/"M/manifest.json").read_text())
            d=json.loads((out/"D/manifest.json").read_text())
            self.assertEqual(m["candidate_count"],6)
            self.assertEqual(d["candidate_count"],6)
            self.assertEqual(x["items"][1]["parent_ast_sha256"],
                             m["candidates"][0]["full_ast_sha256"])
            self.assertEqual((out/"M-single.mos").read_text().count("simulate("),1)
            self.assertNotIn("CT03SealedWorld",str(x))

    def test_missing_real_native_csv_and_log_fail_closed(self):
        with TemporaryDirectory(dir=".") as tmp:
            out=Path(tmp).relative_to(Path.cwd())/"two"
            prepare(out)
            with self.assertRaisesRegex(ValueError,"NO_ACTUAL_TRACE_OR_SOLVER_LOG"):
                verify(out,git_sha="a"*40,run_id="12345678")
            self.assertFalse((out/"conformity.json").exists())

    def test_tampered_script_prevents_verification_even_with_forged_log(self):
        with TemporaryDirectory(dir=".") as tmp:
            out=Path(tmp).relative_to(Path.cwd())/"two"
            prepare(out)
            (out/"D-single.mos").write_text(
                (out/"D-single.mos").read_text()+"\nsimulate(FORGED);\n")
            with self.assertRaisesRegex(ValueError,"SCRIPT_CHANGED_OR_MULTIPLE"):
                verify(out,git_sha="a"*40,run_id="12345678")
            self.assertFalse((out/"conformity.json").exists())

    def test_unpinned_head_and_nonrelative_output_rejected(self):
        with TemporaryDirectory(dir=".") as tmp:
            with self.assertRaisesRegex(ValueError,"RELATIVE_ARTIFACT_PATH"):
                prepare(Path(tmp).resolve()/"two")
            out=Path(tmp).relative_to(Path.cwd())/"two"
            prepare(out)
            with self.assertRaisesRegex(ValueError,"FROZEN_SHA_REQUIRED"):
                verify(out,git_sha="NOT_A_SHA",run_id="123")
            with self.assertRaisesRegex(ValueError,"RUN_ID_REQUIRED"):
                verify(out,git_sha="a"*40,run_id="unknown")


    def test_physical_workflow_stops_after_bad_D_before_mock_M_is_attempted(self):
        """Execute the actual workflow Bash block with a fake local Docker command.

        This fixture never executes Docker/OMC/provider and is NOT solver evidence.
        A nonempty but mass-invalid D CSV must stop M in the workflow itself.
        """
        workflow=(Path(__file__).resolve().parents[1] /
                  ".github/workflows/arena-ct02-minimal-physical.yml").read_text()
        marker="      - name: Execute exactly one D then one M, no retry, preserve stdout/stderr\n"
        after="      - name: Verify native originals, delivered outputs and conserved mass"
        self.assertIn(marker,workflow)
        step=workflow.split(marker,1)[1].split(after,1)[0]
        self.assertIn("        run: |\n",step)
        script="\n".join(line[10:] if line.strip() else ""
                         for line in step.split("        run: |\n",1)[1].splitlines())
        self.assertIn('for arm in D M; do',script)
        self.assertIn('verify-arm',script)
        self.assertTrue(script.index('verify-arm') < script.index('\ndone'))
        mock_docker=textwrap.dedent("""\
            #!/usr/bin/env python3
            import csv
            import os
            import sys
            from pathlib import Path
            path=sys.argv[-1]
            arm="D" if path.endswith("/D-single.mos") else "M"
            out=Path("artifacts/ct02-exact-two")
            field=["time","delivered","lost","s1"] if arm=="D" else ["time","deliveredTotal"]
            with (out/("d00_res.csv" if arm=="D" else "m00_res.csv")).open(
                    "w",encoding="utf-8",newline="") as f:
                writer=csv.writer(f)
                writer.writerow(field)
                for i in range(65):
                    t=i/8
                    mass=1.7*min(t,2)
                    delivered=.1*min(t,2)
                    if arm=="D":
                        stock=(0.0 if os.environ.get("MOCK_BAD_D")=="1"
                               else mass-delivered)
                        writer.writerow([t,delivered,0,stock])
                    else:
                        writer.writerow([t,delivered])
            print("OpenModelica v1.26.5 SYNTHETIC FIXTURE ONLY no solver")
            """)
        repo=Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            exe=root/"bin"
            exe.mkdir()
            docker=exe/"docker"
            docker.write_text(mock_docker,encoding="utf-8")
            docker.chmod(0o755)
            base={**os.environ,"PYTHONPATH":str(repo),
                  "PATH":str(exe)+os.pathsep+os.environ["PATH"],
                  "GITHUB_RUN_ID":"12345678",
                  "GITHUB_SHA":"a"*40,
                  "RUNNER_TEMP":str(root/"tmp")}
            for bad in (True,False):
                out=root/"artifacts/ct02-exact-two"
                if out.exists():
                    import shutil
                    shutil.rmtree(out)
                setup=subprocess.run(
                    [sys.executable,"-m","scripts.arena_cafe.ct02_minimal_batch",
                     "prepare","--out","artifacts/ct02-exact-two"],
                    cwd=root,env=base,text=True,capture_output=True,timeout=30)
                self.assertEqual(setup.returncode,0,setup.stderr)
                env={**base,"MOCK_BAD_D":"1" if bad else "0"}
                run=subprocess.run(["bash","-c",script],cwd=root,env=env,
                                   text=True,capture_output=True,timeout=30)
                attempts=(out/"attempts.log").read_text().splitlines()
                if bad:
                    self.assertNotEqual(run.returncode,0)
                    self.assertIn("MASS_BALANCE_FAIL",run.stderr)
                    self.assertEqual(len(attempts),1)
                    self.assertTrue(attempts[0].startswith("D attempted;"))
                    self.assertFalse((out/"m00_res.csv").exists())
                    self.assertFalse((out/"M-omc.log").exists())
                    self.assertFalse((out/"conformity.json").exists())
                else:
                    self.assertEqual(run.returncode,0,run.stderr)
                    self.assertEqual(len(attempts),2)
                    self.assertTrue(attempts[0].startswith("D attempted;"))
                    self.assertTrue(attempts[1].startswith("M attempted;"))
                    # The aggregate report still belongs to the success step.
                    done=verify(out,git_sha="a"*40,run_id="12345678")
                    self.assertEqual(len(done["outputs"]),2)
                    self.assertEqual(done["attempted_omc"],2)


if __name__=="__main__":
    unittest.main()
