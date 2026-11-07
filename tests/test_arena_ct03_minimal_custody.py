"""Procedural custody has a hard data projection, NOT independently verified ACL.

CSV and logs used here are synthetic fixtures; no OMC or world chosen for CT03.
"""
import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import digest
from scripts.arena_cafe.ct03_minimal_custody import release
from scripts.arena_cafe.ct03_prospective_lock import PROTOCOL
from scripts.arena_cafe.ct03_world_custody import prepare_private


def prepared(root):
    producer = root/"producer"
    producer.mkdir()
    private = root/"outside-producer-private"
    config = {
        "world_public_id": "FIXTURE_CT03_NOT_REAL",
        "stage_count": 2, "capacity": 2.1, "response_time": .8,
        "custody_nonce": "FIXTURE_NONCE_NOT_SECRET_12345",
        "protocol_sha256": digest(json.loads(PROTOCOL.read_text(encoding="utf-8"))),
    }
    commitment = prepare_private(config, private)
    trace = private/"sealed_world_res.csv"
    with trace.open("w", newline="", encoding="utf-8") as file:
        w = csv.writer(file)
        w.writerow(["time","deliveredTotal"])
        for i in range(65):
            t=i/8
            w.writerow([t,0.3*t])
    (private/"world-omc.log").write_text(
        "SYNTHETIC TEST ONLY, not a solver result. OpenModelica v1.26.5\n")
    return producer,private,commitment


class MinimalCustodyTests(unittest.TestCase):
    def test_release_omits_all_private_parameters_t6_t8_and_original_csv(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            producer,private,commitment=prepared(root)
            dest=root/"public"
            released=release(producer_root=producer,private_dir=private,
                             public_out=dest,commitment=commitment)
            self.assertEqual([o["time"] for o in released["observations"]],[0,1,2,4])
            self.assertEqual(sorted(x.name for x in dest.iterdir()),[
                "construction.json","release-status.json","world-commitment.json"])
            alltext=" ".join(f.read_text() for f in dest.iterdir())
            for forbidden in ("response_time","custody_nonce","stage_count",
                              "private_world.mo","sealed_world_res.csv",
                              '"time":6','"time":8'):
                self.assertNotIn(forbidden,alltext)
            self.assertTrue((private/"sealed_world_res.csv").exists())
            self.assertNotIn("observations",str(commitment))
            self.assertFalse(json.loads((dest/"release-status.json").read_text())[
                "operator_independence_verified"])

    def test_modified_private_csv_or_private_inside_producer_blocks_public_release(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            producer,private,commitment=prepared(root)
            (private/"world-omc.log").unlink()
            with self.assertRaisesRegex(ValueError,"PRIVATE_OMC_OUTPUT_OR_VERSION"):
                release(producer_root=producer,private_dir=private,
                        public_out=root/"bad",commitment=commitment)
            self.assertFalse((root/"bad").exists())
            with self.assertRaisesRegex(ValueError,"PRIVATE_WORLD_INSIDE_PRODUCER"):
                release(producer_root=producer,private_dir=producer,
                        public_out=root/"bad",commitment=commitment)

    def test_subprocess_cli_exports_exact_three_files_and_no_hidden_values(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            producer,private,commitment=prepared(root)
            (root/"public-commitment.json").write_text(json.dumps(commitment))
            out=root/"export"
            repo=Path(__file__).resolve().parents[1]
            argv=[sys.executable,"-m","scripts.arena_cafe.ct03_minimal_custody",
                  "--producer-root",str(producer),"--private-dir",str(private),
                  "--public-out",str(out),"--commitment",
                  str(root/"public-commitment.json")]
            r=subprocess.run(argv,cwd=repo,text=True,capture_output=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(r.stdout)["released_times"],[0,1,2,4])
            r=subprocess.run(argv,cwd=repo,text=True,capture_output=True,timeout=30)
            self.assertNotEqual(r.returncode,0)
            self.assertIn("REFUSE_OVERWRITE",r.stderr)


if __name__=="__main__":
    unittest.main()
