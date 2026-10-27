import json
import tempfile
import unittest
from pathlib import Path
from scripts.arena_r1_buffalo_finish import pre, from_live
from scripts.arena_r1_buffalo_initial import build

ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/"data/synthetic/arena_v0_primary_construction.json").read_text())

class BuffaloInitialPhysical(unittest.TestCase):
    def test_attempt_blocks_on_unsupported_native_not_repaired(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)
            visible=r/"visible.json"
            visible.write_text(json.dumps(build(SOURCE)))
            live=r/"live"
            live.mkdir()
            receipt={"live_provider_calls":1,"r1_common_initial":True,
                     "common_input_sha256":"sha256:"+"a"*64,
                     "status":"REAL_CLOUDFLARE_NATIVE_BUFFALO_MODEL_RETURNED"}
            (live/"receipt.json").write_text(json.dumps(receipt))
            (live/"cf-request-metadata.json").write_text(
                json.dumps({"parameter_overrides":{"max_completion_tokens":7000}}))
            # This cannot pass strict G0 scope; do not edit provider bytes.
            native={"model":{"specs":{"startTime":0,"stopTime":8,"dt":0.1,
                       "timeUnits":"Hour","integrationMethod":"Euler"},
                       "variables":[],"relationships":[],"modules":[]}}
            (live/"native-output.json").write_text(json.dumps(native))
            out=pre(visible,live,r/"physical")
            self.assertEqual(out["g0_status"],"BLOCKED_UNSUPPORTED_OR_INVALID_NATIVE")
            self.assertIn("NATIVE_SPECS_OUTSIDE_PINNED_G2_SCOPE",out["blocked_reason"])
            self.assertEqual(len(list((r/"physical").glob("*.mo"))),0)
            self.assertEqual(out["provider"]["provider_calls_started"],1)
    def test_reject_more_than_one_call(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)
            visible=r/"visible.json"
            visible.write_text(json.dumps(build(SOURCE)))
            live=r/"live"
            live.mkdir()
            (live/"receipt.json").write_text(json.dumps({
                "live_provider_calls":2,"r1_common_initial":True,
                "common_input_sha256":"sha256:"+"a"*64}))
            with self.assertRaisesRegex(ValueError,"MULTIPLE_PROVIDER_CALLS"):
                from_live(visible,live)

if __name__=="__main__":
    unittest.main()
