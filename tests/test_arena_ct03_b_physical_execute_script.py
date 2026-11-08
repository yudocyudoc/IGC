"""CT03 B executor cannot run via CI: only syntax, deny and source preflight."""
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_b_physical_outcome import preflight
from test_arena_ct03_b_lock_projection import prepare_fixture

SCRIPT=Path("scripts/arena_cafe/ct03_b_physical_execute_once.sh")

class BOriginalOnceTests(unittest.TestCase):
    def test_shell_syntax_and_default_deny_before_any_attempt(self):
        self.assertTrue(SCRIPT.exists())
        subprocess.run(["bash","-n",str(SCRIPT)],check=True)
        with TemporaryDirectory(dir=".") as temp:
            root=Path(temp).relative_to(Path.cwd())
            result=subprocess.run(
                ["bash",str(SCRIPT)],
                capture_output=True,text=True,
                env={**os.environ,
                     "CT03_LIVE_BATCH_AUTH":"",
                     "CT03_B_PHYSICAL_AUTH":"",
                     "GITHUB_EVENT_NAME":"pull_request"},
                timeout=12)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("MANUAL_AUTH_SHA_AND_GLOBAL_BUDGET_REQUIRED",result.stderr)
            self.assertFalse((root/"omc-exit.json").exists())

    def test_integrity_preflight_reads_only_original_native_and_staged_script(self):
        with TemporaryDirectory(dir=".") as temp:
            root=Path(temp).relative_to(Path.cwd())
            native,receipt,plan,feedback,packet,physical=prepare_fixture(root)
            ok=preflight(native=native,receipt=receipt,plan=plan,root=root/"physical")
            self.assertEqual(ok["status"],"B_PHYSICAL_SOURCE_PREFLIGHT_OK_NOT_EXECUTED")
            self.assertEqual(ok["new_omc"],0)
            # Calling the Python CLI with --preflight-only writes no attempt.
            (root/"native.json").write_text(json.dumps(native))
            (root/"receipt.json").write_text(json.dumps(receipt))
            r=subprocess.run([
                "python","-m","scripts.arena_cafe.ct03_b_physical_outcome",
                "--preflight-only",
                "--native",str(root/"native.json"),
                "--receipt",str(root/"receipt.json"),
                "--plan",str(root/"physical/plan.json"),
                "--root",str(root/"physical"),
                "--out",str(root/"physical/no-output.json"),
                "--git-sha","a"*40,"--run-id","98765"],
                capture_output=True,text=True,timeout=12)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertFalse((root/"physical/omc-exit.json").exists())
            self.assertFalse((root/"physical/no-output.json").exists())

if __name__=="__main__":
    unittest.main()
