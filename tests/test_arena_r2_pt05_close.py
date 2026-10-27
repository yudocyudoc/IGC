"""PT05 tests: original GitHub Actions evidence, zero new model/solver calls."""
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.arena_r2_pt05_close import inspect,close
from scripts.arena_b_native_series import assess_native,resolve_roles

D=os.environ.get("ARENA_R2_PT01_DIR")
Z7=os.environ.get("ARENA_R2_7K_ZIP")
Z16=os.environ.get("ARENA_R2_16K_ZIP")

@unittest.skipUnless(D and Z7 and Z16,"Need authentic original R1/R2 artifact ZIPs")
class RealPT05(unittest.TestCase):
    def test_native_roles_and_no_original_csv_mutation(self):
        with zipfile.ZipFile(Z16) as z:
            native=json.loads(z.read("r2-b-real/native-output.json"))
            import csv,io
            csv_bytes=z.read("r2-b-physical/BuffaloNative_d3c8b77bb184_res.csv")
            rows=list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
            import hashlib
            before=hashlib.sha256(csv_bytes).hexdigest()
            m=resolve_roles(native,rows[0].keys())["roles"]
            self.assertEqual(m,{"pending_work":"work_in_process",
                                "delivered_work":"cumulative_delivered",
                                "arrivals":"input_rate","completions":"completion_rate"})
            source=json.loads((Path(D)/"b-visible.json").read_text())
            data=assess_native(rows,source,native)
            self.assertAlmostEqual(data["construction_diagnostic"]["rmse_all_observations_items"],
                                   0.355555,places=5)
            self.assertFalse(data["original_csv_mutated"])
            self.assertEqual(hashlib.sha256(csv_bytes).hexdigest(),before)

    def test_fail_closed_ambiguous_graph_and_missing_series(self):
        with zipfile.ZipFile(Z16) as z:
            native=json.loads(z.read("r2-b-real/native-output.json"))
            import csv,io
            rows=list(csv.DictReader(io.StringIO(
                z.read("r2-b-physical/BuffaloNative_d3c8b77bb184_res.csv").decode())))
        with self.assertRaisesRegex(ValueError,"MISSING_NATIVE_CSV_COLUMN"):
            resolve_roles(native,["time"])
        import copy
        wrong=copy.deepcopy(native)
        for v in wrong["model"]["variables"]:
            if v["name"]=="work in process":v["outflows"]=[]
        with self.assertRaisesRegex(ValueError,"AMBIGUOUS_STOCK_ROLES"):
            resolve_roles(wrong,rows[0].keys())

    def test_joint_historic_result_and_b_temporal_support(self):
        r=inspect(D,Z7,Z16)
        self.assertEqual(r["r2"]["D"],"RATIFY_SIX_ALTERNATIVES")
        self.assertEqual(r["r2"]["M"],"RATIFY_ABSTENTION")
        self.assertEqual(r["b16"]["original_auto_verdict"],"G2_OR_G3_REJECTED")
        self.assertEqual(r["b16"]["g2"],"REAL_OPENMODELICA_TRAJECTORY_ON_ALTERED_INPUT")
        self.assertEqual(r["b16"]["g3"],"NOT_ESTABLISHED")
        self.assertFalse(r["b16"]["pulse_fidelity"]["same_stimulus_as_D_M"])
        self.assertAlmostEqual(r["b16"]["pulse_fidelity"]["realized_euler_integral_items"],
                               2.65625)
        self.assertEqual(r["calls"]["additional_calls_in_PT05"],0)
        with tempfile.TemporaryDirectory() as td:
            result=close(Path(td)/"test.sqlite",D,Z7,Z16)
            self.assertTrue(result["ledger"]["d_m_views_unchanged_after_b_result"])
            self.assertTrue(result["ledger"]["b_supported_physical_claim"].endswith(
                "r2-16k-conditional-physical-trajectory"))

if __name__=="__main__":
    unittest.main()
