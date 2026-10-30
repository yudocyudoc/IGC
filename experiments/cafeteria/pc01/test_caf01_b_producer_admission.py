#!/usr/bin/env python3
"""Independent Buffalo intake: test two masked fixtures, no provider contact."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from caf01_g3 import CONTRACT
from caf01_b_producer_admission import FILES, PUB, build, case_evidence, generate

class TestBIndependentInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_each_provider_receives_only_its_own_case(self):
        a=build("CAF01",self.contract)
        b=build("CAFN",self.contract)
        self.assertEqual(len(a["public_evidence"]["observations"]),7)
        self.assertEqual([x["t_min"] for x in b["public_evidence"]["observations"]],[0,40])
        self.assertEqual(a["method"],b["method"])
        self.assertNotEqual(a["evidence_semantic_sha256"],b["evidence_semantic_sha256"])
        self.assertEqual(a["budget"]["provider_inferences_from_this_preparation"],0)
        self.assertEqual(b["budget"]["native_simulations_from_this_preparation"],0)
        for row in (a,b):
            self.assertFalse(row["isolation"]["prior_B_native_model_supplied"])
            self.assertFalse(row["isolation"]["evaluation_truth_supplied"])
            self.assertEqual(row["task"]["required_native_solver_specs"]["stopTime"],2/3)
            self.assertEqual(row["native_adapter"]["native_G2"],"NOT_RUN")
            self.assertNotIn("D_RK4_SCREEN",json.dumps(row))
            self.assertNotIn("M_PRODUCER_PACKET",json.dumps(row))

    def test_negative_independence_requires_fresh_no_history(self):
        c=copy.deepcopy(self.contract)
        c["methods"]["B"]["negative_control_no_prior_history"]=False
        with self.assertRaisesRegex(ValueError,"B_CONTRACT_PROVIDER_SCOPE_DRIFT"):
            build("CAFN",c)

    def test_fails_closed_on_pulse_or_mask_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            tmp=Path(d)
            for case in ("CAF01","CAFN"):
                (tmp/(case+".json")).write_bytes((PUB/(case+".json")).read_bytes())
            item=json.loads((tmp/"CAFN.json").read_text())
            item["observations"].insert(1,{"t_min":5,"delivered":3})
            (tmp/"CAFN.json").write_text(json.dumps(item))
            with self.assertRaisesRegex(ValueError,"B_PUBLIC_EVIDENCE_BYTES_CHANGED"):
                case_evidence("CAFN",self.contract,tmp)
            with self.assertRaisesRegex(ValueError,"B_UNKNOWN_REQUEST_CASE"):
                case_evidence("EVALUATION",self.contract,tmp)

    def test_output_never_contains_provider_output_or_unmasked_negative(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"b"
            out=generate(target)
            self.assertEqual(set(out),{"CAF01","CAFN"})
            self.assertEqual(sorted(p.name for p in target.glob("*.json")),
                             ["B_CAF01_PROVIDER_REQUEST.json","B_CAFN_PROVIDER_REQUEST.json"])
            assert (target/"NOT_SENT.txt").is_file()
            self.assertNotIn("CAF01", (target/"B_CAFN_PROVIDER_REQUEST.json").read_text().replace("caf01","").replace("CAF-N",""))
            with self.assertRaisesRegex(ValueError,"B_OUTPUT_EXISTS"):
                generate(target)

if __name__=="__main__":
    unittest.main()
