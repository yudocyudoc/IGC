"""No-cloud, no-OMC guards for same-operator CT03 custodial handoff."""
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_private_choose import choose
from scripts.arena_cafe.ct03_prospective_lock import PROTOCOL
from scripts.arena_v0_contract import digest
import json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/arena_cafe/ct03_managed_custody_once.sh"
WORK=ROOT/".github/workflows/arena-ct03-public-intake.yml"
PRODUCER=ROOT/".github/workflows/arena-ct03-producer.yml"
EVALUATE=ROOT/".github/workflows/arena-ct03-evaluate-postlock.yml"


class ManagedCustodyTests(unittest.TestCase):
    def test_private_world_range_and_randomness_no_solver(self):
        protocol = digest(json.loads(PROTOCOL.read_text(encoding="utf-8")))
        configs = [choose() for _ in range(8)]
        for c in configs:
            self.assertIn(c["stage_count"], (2, 3))
            self.assertGreaterEqual(c["capacity"], 1.2)
            self.assertLessEqual(c["capacity"], 2.8)
            self.assertGreaterEqual(c["response_time"], 0.5)
            self.assertLessEqual(c["response_time"], 1.5)
            self.assertEqual(c["protocol_sha256"], protocol)
            self.assertGreaterEqual(len(c["custody_nonce"]), 24)
        self.assertEqual(len({x["world_public_id"] for x in configs}), len(configs))
        self.assertEqual(len({x["custody_nonce"] for x in configs}), len(configs))

    def test_workflow_has_managed_default_but_original_external_mode(self):
        s=WORK.read_text(encoding="utf-8")
        self.assertIn("default: 'managed'",s)
        self.assertIn("if: ${{ inputs.mode == 'managed' }}",s)
        self.assertIn("if: ${{ inputs.mode == 'external' }}",s)
        self.assertIn("environment: arena-ct03-custodian",s)
        self.assertIn("CT03_CUSTODY_ONE_WORLD_AUTH",s)
        self.assertIn("CT03_R2_SECRET_ACCESS_KEY",s)
        self.assertIn("arena-ct03-public-release-",s)
        self.assertIn("artifacts/ct03-public-release/",s)
        self.assertNotIn("pull_request:",s)
        self.assertNotIn("schedule:",s)
        self.assertNotIn("push:",s)
        # Producer has no private R2 key or config/CSV file mounted.
        p=PRODUCER.read_text(encoding="utf-8")
        for term in ("CT03_R2_SECRET_ACCESS_KEY","CT03_R2_ACCESS_KEY_ID",
                     "ct03_managed_custody_once", "world-config.json"):
            self.assertNotIn(term,p)

    def test_postlock_uses_same_custody_but_verifies_archive_before_private_download(self):
        s=EVALUATE.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",s)
        self.assertIn("default: 'no'",s)
        self.assertIn("environment: arena-ct03-custodian",s)
        self.assertIn("CT03_ARCHIVE_VERIFIED_PUBLIC_BEFORE_PRIVATE_ACCESS",s)
        self.assertIn("CT03_PUBLIC_LOCK_ARCHIVED_AND_SCOPED_BEFORE_PRIVATE_READ",s)
        self.assertIn("ct03_minimal_score",s)
        self.assertNotIn("simulate(",s)
        self.assertNotIn("CLOUDFLARE_API_TOKEN",s)
        a=s.index("CT03_PUBLIC_LOCK_ARCHIVED_AND_SCOPED_BEFORE_PRIVATE_READ")
        b=s.index("Fetch full private world only")
        self.assertLess(a,b)
        self.assertIn("arena-ct03-postlock-score-",s)
        self.assertNotIn("actions/upload-artifact@v4\n        with:\n          name: private",s)

    def test_script_default_denied_and_no_private_artifact(self):
        subprocess.run(["bash","-n",str(SCRIPT)],check=True)
        denied=subprocess.run(["bash",str(SCRIPT)],
            env={**os.environ,"GITHUB_EVENT_NAME":"pull_request"},
            text=True,capture_output=True,timeout=10)
        self.assertNotEqual(denied.returncode,0)
        s=SCRIPT.read_text(encoding="utf-8")
        self.assertIn("CT03_ONE_APPROVED_WORLD",s)
        self.assertIn("GITHUB_RUN_ATTEMPT",s)
        self.assertIn("igc-ct03-private-custody",s)
        self.assertIn("s3 sync",s)
        self.assertIn("ct03_minimal_custody",s)
        self.assertIn("--network none",s)
        self.assertIn("world-attempt.log",s)
        self.assertNotIn("actions/upload-artifact",s)


if __name__=="__main__":
    unittest.main()
