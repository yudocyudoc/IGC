"""A3 B one-shot safety: no paid call without NEW explicit manual authorization."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/arena-cafe-a3-b-cloudflare-one-shot.yml"


class BuffaloEV01OneShotGuardTests(unittest.TestCase):
    def test_new_workflow_is_manual_only_once_two_scoped_conditions(self):
        w=WORKFLOW.read_text()
        self.assertTrue(w.startswith("name: A3 Buffalo EV01"))
        self.assertIn("workflow_dispatch:",w)
        self.assertNotIn("  pull_request:",w)
        self.assertNotIn("  push:",w)
        self.assertIn("github.run_number == 1",w)
        self.assertIn("github.run_attempt == 1",w)
        self.assertIn("github.ref == 'refs/heads/main'",w)
        self.assertIn("RUN_EV01_BUFFALO_TWO_LIVE_CALLS_ONCE",w)
        self.assertIn("environment: a3-buffalo-cloudflare",w)
        self.assertIn("condition: [O0, O1]",w)
        self.assertIn("fail-fast: false",w)
        self.assertIn("a3-b-ev01-O0-public-only",w)
        self.assertIn("a3-b-ev01-O1-public-only",w)
        self.assertIn("a3-b-ev01-${{ matrix.condition }}-public-only",w)
        self.assertIn('test "$(find artifacts/reference-public -type f | wc -l)" = 1',w)
        self.assertIn("BUFFALO_EV01_INITIAL: EV01_ONE_SHOT",w)
        self.assertIn("BUFFALO_CF_MODE: live",w)
        self.assertIn("BUFFALO_CF_AUTH: RUN_SINGLE_CF_AI_EV01",w)
        self.assertIn("original Buffalo",w)
        self.assertNotIn("retries:",w)
        self.assertNotIn("actions: write",w)

    def test_no_github_first_dispatch_cannot_start_any_cloudflare_request(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/"blocked"
            env=os.environ.copy()
            for k in ("GITHUB_ACTIONS","GITHUB_EVENT_NAME","GITHUB_REF",
                      "GITHUB_RUN_NUMBER","GITHUB_RUN_ATTEMPT",
                      "CLOUDFLARE_ACCOUNT_ID","CLOUDFLARE_API_TOKEN"):
                env.pop(k,None)
            env.update({
                "BUFFALO_CF_MODE":"live",
                "BUFFALO_EV01_INITIAL":"EV01_ONE_SHOT",
                "BUFFALO_CF_AUTH":"RUN_SINGLE_CF_AI_EV01",
                "BUFFALO_OUTPUT":str(out),
            })
            result=subprocess.run(
                ["node","scripts/arena_b_openrouter_cloudflare.mjs"],
                cwd=ROOT,env=env,capture_output=True,text=True,timeout=15)
            self.assertNotEqual(0,result.returncode)
            receipt=json.loads((out/"receipt.json").read_text())
            self.assertEqual("OPENROUTER_CF_BRIDGE_FAILURE",receipt["status"])
            self.assertEqual("EV01_LIVE_NEW_EXPLICIT_FIRST_DISPATCH_REQUIRED",
                             receipt["error_message"])
            self.assertEqual(0,receipt["live_provider_calls"])
            self.assertEqual(0,receipt["intercepted_http_calls"])
            self.assertFalse((out/"cf-call-started.json").exists())
            self.assertFalse((out/"cloudflare-raw.json").exists())


if __name__=="__main__":
    unittest.main()
