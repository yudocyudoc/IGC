"""Reject mock parents, replay-mismatch and contamination of B own review."""
import json
import unittest
from scripts.arena_cafe.e02_b_feedback import build,_model_sha

def example():
    native={"model":{"variables":[{"name":"A","type":"stock"},
        {"name":"B","type":"flow"}],
        "relationships":[],
        "specs":{"startTime":0,"stopTime":1/6,"dt":0.005,
                 "timeUnits":"Hour","integrationMethod":"Euler"}}}
    receipt={"case_id":"EV-01","round_kind":"initial",
             "condition_id":"O0","mode":"live","provider_calls":1,
             "model_returned":True,
             "status":"ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED",
             "result_sha256":_model_sha(native),
             "source_snapshot_hash":"sha256:"+"a"*64}
    return native,receipt

class FeedbackContract(unittest.TestCase):
    def test_real_receipt_and_native_only_no_fabricated_g3(self):
        native,receipt=example()
        f=build(native,receipt)
        self.assertEqual(f["parent_result_sha256"],receipt["result_sha256"])
        self.assertEqual(f["diagnostic"]["scope"],
             "G0_SELF_INSPECTION_ONLY_NO_NATIVE_TRAJECTORY")
        self.assertEqual(f["diagnostic"]["scientific_fit"],
                         "NOT_COMPUTABLE_NO_NATIVE_G2_TRACE")
        self.assertTrue(f["diagnostic"]["native_horizon_matches_public_cutoff"])
        self.assertEqual(f["diagnostic"]["input_kernel_read_by_upstream"],
                         "PROMPT_EXPOSED_NATIVE_USE_NOT_PROVEN")

    def test_mock_never_passing_as_real(self):
        native,receipt=example()
        receipt["mode"]="mock"
        with self.assertRaisesRegex(ValueError,"B_E02_REAL_OWN_PARENT_REQUIRED"):
            build(native,receipt)
        receipt["mode"]="live";receipt["provider_calls"]=0
        with self.assertRaisesRegex(ValueError,"B_E02_REAL_OWN_PARENT_REQUIRED"):
            build(native,receipt)

    def test_mismatched_native_invalidates_parent(self):
        native,receipt=example()
        native["model"]["specs"]["stopTime"]=8
        with self.assertRaisesRegex(ValueError,"B_E02_NATIVE_RECEIPT_HASH_MISMATCH"):
            build(native,receipt)

    def test_revisions_not_fake_initial_parents(self):
        native,receipt=example()
        receipt["round_kind"]="revision"
        with self.assertRaisesRegex(ValueError,"B_E02_REAL_OWN_PARENT_REQUIRED"):
            build(native,receipt)

if __name__=="__main__":unittest.main()
