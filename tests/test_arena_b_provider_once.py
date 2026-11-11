"""No real provider calls in these tests. Genuine calls gated separately."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from scripts.arena_b_provider_once import (
    one_call, request_body, extract_native, ProviderError, MODEL, AUTHORIZATION
)
from scripts.arena_b_sdai_v0 import make_request

ROOT=Path(__file__).resolve().parents[1]
VISIBLE=ROOT/"data/synthetic/arena_b_v0_visible.json"
SAMPLE=ROOT/"data/synthetic/arena_b_v0_handwritten_sdjson.json"

class SimulatedTransport:
    def __init__(self,payload):
        self.payload=payload
        self.calls=0
    def __call__(self,request,timeout):
        self.calls+=1
        assert request.full_url.endswith("/ai/run/"+MODEL)
        assert request.get_header("Authorization")=="Bearer dummy-secret"
        assert timeout==150
        self.request=json.loads(request.data)
        class Stream(io.BytesIO):
            status=200
        return Stream(json.dumps(self.payload).encode())

def env():
    return {"IGC_BUFFALO_B1_AUTHORIZATION":AUTHORIZATION,
            "GITHUB_RUN_ATTEMPT":"1",
            "CLOUDFLARE_ACCOUNT_ID":"0"*32,
            "CLOUDFLARE_API_TOKEN":"dummy-secret"}

def response(body):
    return {"success":True,"result":{"model":MODEL,"id":"test-provider-id",
            "usage":{"prompt_tokens":200,"completion_tokens":100},
            "choices":[{"finish_reason":"stop",
                        "message":{"content":json.dumps(body)}}]}}

class BuffaloProviderOnceTests(unittest.TestCase):
    def test_body_preserves_unmodified_original_method_prompt(self):
        req=make_request(json.loads(VISIBLE.read_text()))
        body=request_body(req)
        self.assertEqual(body["messages"][0]["content"],
                         req["prompt"]["system"])
        self.assertEqual(body["temperature"],0)
        self.assertEqual(body["max_completion_tokens"],4096)
        self.assertNotIn("CS-01",json.dumps(body))

    def test_raw_preserved_and_native_translated_from_fake_sender(self):
        payload=json.loads(SAMPLE.read_text())["model"]
        sender=SimulatedTransport(response(payload))
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"capture"
            state=one_call(visible_path=VISIBLE,output=folder,env=env(),sender=sender)
            self.assertEqual(sender.calls,1)
            self.assertEqual(state["status"],"B1_NATIVE_SFD_TRANSLATED_G2_NOT_YET_TESTED")
            self.assertEqual(state["calls_completed"],1)
            self.assertEqual(state["retries"],0)
            self.assertEqual(json.loads((folder/"response-raw.json").read_text()),response(payload))
            self.assertTrue((folder/"accepted-model"/"submission.json").is_file())
            self.assertEqual(json.loads((folder/"sd-ai-native-provider-output.json").read_text())["model"],payload)

    def test_native_invalid_still_archived_and_never_falls_back_to_fixture(self):
        payload={"variables":[],"relationships":[]}
        sender=SimulatedTransport(response(payload))
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"capture"
            state=one_call(visible_path=VISIBLE,output=folder,env=env(),sender=sender)
            self.assertEqual(sender.calls,1)
            self.assertEqual(state["status"],
                             "B1_NATIVE_SFD_UNSUPPORTED_BY_BOUNDED_MODELICA_ADAPTER")
            self.assertTrue((folder/"response-raw.json").is_file())
            self.assertFalse((folder/"accepted-model").exists())

    def test_transport_is_blocked_without_explicit_gating(self):
        sender=SimulatedTransport(response({}))
        args=env()
        args["IGC_BUFFALO_B1_AUTHORIZATION"]="WRONG"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ProviderError,"CALL_NOT_AUTHORIZED"):
                one_call(visible_path=VISIBLE,output=Path(tmp)/"capture",env=args,sender=sender)
            self.assertEqual(sender.calls,0)

    def test_non_json_provider_response_archived_without_retry(self):
        sender=SimulatedTransport(response({"variables":[],"relationships":[]}))
        sender.payload["result"]["choices"][0]["message"]["content"]="Not valid JSON"
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"capture"
            with self.assertRaisesRegex(ProviderError,"PROVIDER_OR_PARSE_FAILURE_NO_RETRY"):
                one_call(visible_path=VISIBLE,output=folder,env=env(),sender=sender)
            self.assertEqual(sender.calls,1)
            self.assertTrue((folder/"response-raw.json").is_file())
            self.assertFalse((folder/"accepted-model").exists())
            self.assertEqual(json.loads((folder/"receipt.json").read_text())["calls_started"],1)

if __name__=="__main__":
    unittest.main()
