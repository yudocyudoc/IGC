"""Only offline structural probes of the fixed CT-02 two-OMC batch.

This does NOT run Docker or OMC and synthetic CSVs must NEVER be uploaded as
physical evidence. Physical tests require explicit manual dispatch and budget.
"""
import csv
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct02_minimal_batch import prepare, verify

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


if __name__=="__main__":
    unittest.main()
