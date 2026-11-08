"""CT03 new live workflow is prepared, manual and unauthorized by default.

Static integration guard: no network, no solver, no deployment, no provider.
This does NOT certify configured GitHub environment protection or custody.
"""
from pathlib import Path
import subprocess
import unittest
import os

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/".github/workflows/arena-ct03-producer.yml"
INTAKE=ROOT/".github/workflows/arena-ct03-public-intake.yml"
FREEZE=ROOT/".github/workflows/arena-ct03-freeze-predictions.yml"
B=ROOT/"scripts/arena_cafe/ct03_b_producer_rounds_once.sh"
OMC=ROOT/"scripts/arena_cafe/ct03_b_physical_execute_once.sh"

class Ct03GlobalWorkflowTests(unittest.TestCase):
    def test_manual_only_and_fail_closed_budget_custody_provider_separation(self):
        p=WORK.read_text(encoding="utf-8")
        pub=INTAKE.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",p)
        self.assertIn("workflow_dispatch:",pub)
        self.assertNotIn("pull_request:",p)
        self.assertNotIn("schedule:",p)
        self.assertNotIn("push:",p)
        self.assertIn("default: 'no'",p)
        self.assertIn('test "$MAX_OMC" = 19',p)
        self.assertIn('test "$MAX_POST" = 2',p)
        self.assertIn('test "$GITHUB_RUN_ATTEMPT" = 1',p)
        self.assertIn("CT03_APPROVED_FREEZE_SHA",p)
        self.assertIn("CT03_APPROVED_RELEASE_RUN_ID",p)
        self.assertIn("CT03_EXTERNAL_CUSTODIAN_ACK",p)
        self.assertIn("dm-originals-own-feedback-and-revisions:",p)
        self.assertIn("buffalo-original-and-own-review:",p)
        self.assertIn("join-thirteen-public-slots-no-lock-no-evaluator:",p)
        self.assertIn("arena-ct03-dm-budget-count-only",p)
        self.assertIn("test ! -e artifacts/ct03-producer/dm-ten",p)
        self.assertIn("arena-ct03-producer-public-and-forecasts",p)
        self.assertIn("arena-ct03-public-release-",p)
        self.assertIn("scripts.arena_cafe.ct03_public_intake",pub)
        self.assertIn("scripts.arena_cafe.ct03_producer_freeze_handoff",p)
        self.assertNotIn("ct03_minimal_score",p)
        self.assertNotIn("ct03_evaluator_preflight",p)
        self.assertNotIn("private-manifest.json",p)
        self.assertNotIn("sealed_world_res.csv",p)
        self.assertIn("if: always()",p)
        self.assertIn("CLOUDFLARE_API_TOKEN:",p)
        # The provider credential is available ONLY in the B job, not in
        # admission, D/M, or final join steps.
        head=p.split("  buffalo-original-and-own-review:",1)[0]
        tail=p.split("  join-thirteen-public-slots-no-lock-no-evaluator:",1)[1]
        self.assertNotIn("CLOUDFLARE_API_TOKEN",head)
        self.assertNotIn("CLOUDFLARE_API_TOKEN",tail)
        self.assertIn("public_release_run_id",p)
        self.assertIn("path: artifacts/ct03-public",p)

    def test_b_scripts_lexically_valid_and_default_deny(self):
        for script in (B,OMC):
            subprocess.run(["bash","-n",str(script)],check=True)
            denied=subprocess.run(
                ["bash",str(script)],capture_output=True,text=True,
                env={**os.environ,"CT03_LIVE_BATCH_AUTH":"",
                     "GITHUB_EVENT_NAME":"pull_request"},timeout=10)
            self.assertNotEqual(denied.returncode,0)
            self.assertIn("REQUIRED",denied.stderr)

    def test_freeze_is_a_distinct_existing_workflow(self):
        s=FREEZE.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",s)
        self.assertIn("arena-ct03-producer-public-and-forecasts",s)
        self.assertIn("ct03_prospective_lock",s)
        self.assertNotIn("ct03_minimal_score",s)

if __name__=="__main__":
    unittest.main()
