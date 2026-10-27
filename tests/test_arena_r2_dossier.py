"""PT-01 actual evidence, byte tampering, isolation and no-fabricated-decision tests."""
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.arena_r2_dossier import prepare, save
from scripts.arena_r1_buffalo_postonly import ORIGINAL_NATIVE_SHA, SHARED_SOURCE

ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/"data/synthetic/arena_v0_primary_construction.json").read_text())
ARCHIVE=os.environ.get("ARENA_R1_ARCHIVE_ZIP")
ADJUDICATION=os.environ.get("ARENA_R1_ADJUDICATION_JSON")

@unittest.skipUnless(ARCHIVE and ADJUDICATION,"Real R1 artifacts must be explicitly supplied")
class R2ActualArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(Path(ADJUDICATION).read_text())

    def test_authentic_parent_and_private_packets(self):
        original=copy.deepcopy(self.report)
        data=prepare(SOURCE,Path(ARCHIVE),self.report)
        self.assertEqual(self.report,original)
        self.assertEqual(data["manifest"]["r1_method_attempts"],{"D":6,"M":3,"B":1})
        self.assertEqual(data["manifest"]["source_snapshot_hash"],SHARED_SOURCE)
        self.assertEqual(data["manifest"]["b_parent_native_bytes_sha256"],"sha256:"+ORIGINAL_NATIVE_SHA)
        self.assertEqual(data["manifest"]["producer_calls"],0)
        self.assertEqual(data["manifest"]["solver_calls"],0)
        self.assertIsNone(data["m_own"]["chosen_parent"])
        self.assertEqual(data["m_own"]["r1_decision"]["status"],"ABSTAIN")
        self.assertEqual(data["m_own"]["r2_decision"],"PENDING_NOT_FABRICATED")
        self.assertEqual(data["d_own"]["r2_decision"],"PENDING_NOT_FABRICATED")
        packet=json.dumps(data["b_feedback"])
        self.assertNotIn("congestion_multiplier",packet)
        self.assertNotIn("product_of_capacity_effects",packet)
        self.assertNotIn("rmse",packet.lower())
        self.assertNotIn("C01",packet)
        self.assertNotIn("D-",packet)
        self.assertIn("Failed to build model",packet)
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"dossier"
            save(data,folder)
            self.assertEqual((folder/"b-parent-native.json").read_bytes(),data["b_native_bytes"])
            self.assertTrue((folder/"manifest.json").exists())
            with self.assertRaisesRegex(ValueError,"OUTPUT_EXISTS"):
                save(data,folder)

    def test_reject_tampered_native_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/"tampered.zip"
            with zipfile.ZipFile(ARCHIVE) as src, zipfile.ZipFile(dst,"w") as out:
                for name in src.namelist():
                    value=src.read(name)
                    if name=="r1-b-live/native-output.json":
                        value+=b" "
                    out.writestr(name,value)
            with self.assertRaisesRegex(ValueError,"R2_WRONG_BUFFALO_PARENT_BYTES"):
                prepare(SOURCE,dst,self.report)

    def test_reject_wrong_case_and_adjudication(self):
        changed=copy.deepcopy(SOURCE)
        changed["observations"][1]["delivered"]=9.0
        with self.assertRaisesRegex(ValueError,"R2_PRIMARY_EVIDENCE"):
            prepare(changed,Path(ARCHIVE),self.report)
        old=copy.deepcopy(self.report)
        old["B"]["g3"]=0
        with self.assertRaisesRegex(ValueError,"R2_R1_NOT_NEGATIVE"):
            prepare(SOURCE,Path(ARCHIVE),old)

    def test_reject_false_m_selected_parent(self):
        bad=copy.deepcopy(self.report)
        bad["M"]["decision"]["status"]="SELECTED"
        with self.assertRaisesRegex(ValueError,"R2_HISTORIC_D_M_STATE_TAMPERED"):
            prepare(SOURCE,Path(ARCHIVE),bad)

if __name__=="__main__":
    unittest.main()
