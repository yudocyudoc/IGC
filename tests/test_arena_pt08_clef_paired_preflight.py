"""No provider or solver: verify PT08 paired design against original real T2 CSVs."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from scripts.arena_pt08_clef_paired_preflight import build,emit,MAX_CALLS,PAIRS

T1=os.environ.get("ARENA_PT08_ORIGINAL_T1")
T23=os.environ.get("ARENA_PT08_ORIGINAL_T23")
CAT=Path("experiments/e0/catalog.json")

@unittest.skipUnless(T1 and T23,"requires original OpenModelica archive")
class PairedOriginalEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public,cls.private,cls.manifest=build(T1,T23,json.loads(CAT.read_text()))

    def test_only_note_differs_within_each_pair(self):
        a,b,m=self.public,self.private,self.manifest
        self.assertEqual(len(a["requests"]),MAX_CALLS)
        self.assertEqual(len(b["private"]),MAX_CALLS)
        self.assertEqual(m["source_candidate_run_id"],40578550337)
        self.assertEqual(len(m["source_27_candidate_csv_sha256"]),27)
        self.assertEqual(m["provider_requests_planned"],6)
        self.assertEqual(m["new_provider_calls_now"],0)
        self.assertEqual(m["new_solver_calls_now"],0)
        self.assertEqual(m["future_provider_authorization"],"NOT_GRANTED")
        self.assertEqual(m["independence"],"THREE_INFORMATION_TREATMENTS_OF_ONE_PUBLIC_SYNTHETIC_WORLD")
        for i in range(PAIRS):
            control,extra=a["requests"][2*i:2*i+2]
            s0=json.loads(control["body"]["state"])
            s1=json.loads(extra["body"]["state"])
            self.assertEqual(control["condition"],"NUMERIC_ONLY")
            self.assertEqual(extra["condition"],"NUMERIC_PLUS_NOTE")
            self.assertEqual(control["paired_case"],extra["paired_case"])
            self.assertEqual(control["body"]["questions"],extra["body"]["questions"])
            self.assertEqual(s0["observed_deliveredTotal_at_hours"],s1["observed_deliveredTotal_at_hours"])
            self.assertEqual(s0["fixed_27_physical_candidate_curves_at_same_hours"],
                             s1["fixed_27_physical_candidate_curves_at_same_hours"])
            self.assertEqual(len(s0["fixed_27_physical_candidate_curves_at_same_hours"]),27)
            self.assertEqual(s0["operational_note"],"NOT_PROVIDED")
            self.assertNotEqual(s1["operational_note"],"NOT_PROVIDED")
            self.assertEqual([p["t"] for p in s0["observed_deliveredTotal_at_hours"]],
                             [0,0.05,0.10,0.15])
            self.assertEqual(len(control["body"]["questions"]),3)
            for k in ("world_material_class","true_topology","source_parameters",
                      "paired-oracle","note_based_compatibility","C01_is_truth"):
                self.assertNotIn(k,json.dumps(control["body"]))
                self.assertNotIn(k,json.dumps(extra["body"]))
        self.assertEqual(b["private"][0]["note_based_compatibility"],["C00","C01","C02"])
        self.assertEqual(b["private"][3]["note_based_compatibility"],["C01","C02"])
        self.assertEqual(b["private"][5]["note_based_compatibility"],["C01"])

    def test_immutability_and_separate_private_oracle(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"pt08"
            freeze=emit(out,T1,T23,json.loads(CAT.read_text()))
            self.assertEqual(freeze["provider_requests_planned"],6)
            public=json.loads((out/"public-six-requests-NOT-SENT.json").read_text())
            self.assertNotIn("note_based_compatibility",json.dumps(public))
            self.assertNotIn("paired-oracle-NOT-FOR_PROVIDER",json.dumps(public))
            priv=json.loads((out/"researcher-private/paired-oracle-NOT-FOR_PROVIDER.json").read_text())
            self.assertEqual(len(priv["private"]),6)
            with self.assertRaisesRegex(ValueError,"PT08_PAIR_OUTPUT_ALREADY_EXISTS"):
                emit(out,T1,T23,json.loads(CAT.read_text()))

if __name__=="__main__":
    unittest.main()
