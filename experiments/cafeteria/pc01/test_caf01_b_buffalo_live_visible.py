#!/usr/bin/env python3
"""CAF-01 Buffalo visible native proposal staging: no provider or solver."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from caf01_g3 import CONTRACT
from caf01_b_producer_admission import build
from caf01_b_buffalo_live_visible import generate,visible_for_original_sd_ai

class TestOriginalBuffaloCAF01Visible(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads(CONTRACT.read_text())

    def test_one_model_own_data_and_no_other_arm(self):
        original=build("CAF01",self.contract)
        v=visible_for_original_sd_ai(original)
        self.assertEqual(v["schema"],"igc-arena-visible-input/0.1")
        self.assertEqual(v["resources"]["max_llm_calls"],1)
        self.assertEqual(v["resources"]["max_model_proposals"],1)
        self.assertEqual(v["resources"]["max_simulations"],0)
        self.assertEqual(len(v["construction"]["observations"]),7)
        self.assertEqual(v["construction"]["input_profile"]["rate"],72)
        self.assertEqual(v["construction"]["input_profile"]["duration"],1/3)
        self.assertIn('"integrationMethod":"Euler"',v["question"])
        self.assertNotIn("D_RK4",json.dumps(v))
        self.assertNotIn("M_G2",json.dumps(v))
        self.assertNotIn("CAFN",json.dumps(v))

    def test_reject_masked_negative_and_model_free_diagnosis(self):
        negative=build("CAFN",self.contract)
        with self.assertRaisesRegex(ValueError,"B_CAF01_ONLY_ONE_NATIVE_MODEL_REQUEST"):
            visible_for_original_sd_ai(negative)
        modified=copy.deepcopy(build("CAF01",self.contract))
        modified["task"]["native_model_required"]=False
        with self.assertRaisesRegex(ValueError,"B_CAF01_ONLY_ONE_NATIVE_MODEL_REQUEST"):
            visible_for_original_sd_ai(modified)

    def test_build_offline_visible_and_source_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"B"
            report=generate(out)
            self.assertEqual(report["provider_calls"],0)
            self.assertEqual(report["OpenModelica_simulations"],0)
            self.assertTrue((out/"b-visible.json").is_file())
            with self.assertRaisesRegex(ValueError,"B_CAF01_VISIBLE_OUTPUT_EXISTS"):
                generate(out)

if __name__=="__main__":
    unittest.main()
