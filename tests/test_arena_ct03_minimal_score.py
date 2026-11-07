"""Post-archive paired scoring exercises ONLY synthetic private trace fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_minimal_score import evaluate,FREEZE_SCHEMA
from scripts.arena_cafe.ct03_minimal_custody import release
from scripts.arena_cafe.ct03_prospective_lock import seal
from test_arena_ct03_prospective_lock import fixture as producer_fixture
from test_arena_ct03_minimal_custody import prepared


def scoped(root):
    producer,private,commitment=prepared(root)
    released=release(producer_root=producer,private_dir=private,
                     public_out=root/"public",commitment=commitment)
    c,w,d,m,entries=producer_fixture(producer)
    # Replace ONLY public case references in synthetic fixture; no secret params.
    c=copy.deepcopy(released)
    entries["world_public_id"]=c["world_public_id"]
    entries["source_snapshot_hash"]=c["source_snapshot_hash"]
    row=next(x for x in entries["rows"] if x["arm"]=="M")
    row["initial"]={
        "status":"PREDICTED",
        "native_sha256":"sha256:"+"a"*64,
        "trace_sha256":"sha256:"+"b"*64,
        "receipt_sha256":"sha256:"+"c"*64,
        "forecast":[{"time":6,"delivered":2.0},{"time":8,"delivered":2.5}],
    }
    row["final"]=copy.deepcopy(row["initial"])
    lock=seal(c,commitment,d,m,entries)
    ack={
        "schema": FREEZE_SCHEMA,
        "lock_sha256":lock["lock_sha256"],
        "github_run_id": 12345678,
        "github_artifact_id": 23456789,
        "frozen_code_sha": "a"*40,
        "verified_by_custodian": "Synthetic test human acknowledgement",
        "archived_before_reveal": True,
        "producer_write_disabled": True,
        "custody_scope": "PROCEDURAL_HUMAN_NO_EXTERNAL_SIGNER",
    }
    return producer,private,c,commitment,lock,ack


class MinimalScoringTests(unittest.TestCase):
    def test_own_prediction_post_lock_error_denominator_and_baselines(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            p,private,c,commitment,lock,ack=scoped(root)
            out=root/"score.json"
            report=evaluate(lock=lock,archive=ack,construction=c,
                            commitment=commitment,producer_root=p,
                            private_dir=private,out=out)
            self.assertTrue(out.exists())
            self.assertEqual(report["candidate_denominator"],13)
            self.assertEqual(report["paired_available"],1)
            self.assertEqual(report["failures_kept_in_denominator"],12)
            self.assertEqual(report["true_reserved"],[
                {"time":6,"delivered":1.8},{"time":8,"delivered":2.4}])
            self.assertAlmostEqual(report["baselines"]["persist_y4"]["mae"],0.9)
            m=next(row for row in report["rows"] if row["pair_comparable"])
            self.assertEqual(m["arm"],"M")
            self.assertAlmostEqual(m["initial_error"]["mae"],0.15)
            self.assertEqual(m["delta_mae"],0)
            self.assertEqual(report["material_groups"]["M"]["total_groups"],3)
            self.assertEqual(report["provider_posts_by_evaluator"],0)

    def test_missing_archive_denies_access_even_if_private_path_missing(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            p,private,c,commitment,lock,ack=scoped(root)
            wrong={**ack,"lock_sha256":"sha256:"+"e"*64}
            with self.assertRaisesRegex(ValueError,"NOT_PROSPECTIVELY_ARCHIVED"):
                evaluate(lock=lock,archive=wrong,construction=c,commitment=commitment,
                         producer_root=p,private_dir=root/"nonexistent",
                         out=root/"should-not-exist.json")
            self.assertFalse((root/"should-not-exist.json").exists())

    def test_missing_prediction_stops_without_opening_private_truth(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            p,private,c,commitment,lock,ack=scoped(root)
            no_preds=copy.deepcopy(lock)
            row=next(x for x in no_preds["rows"] if x["arm"]=="M" and
                     x["initial"]["status"]=="PREDICTED")
            row["initial"]={
                "status":"NOT_EXECUTED","native_sha256":None,
                "trace_sha256":None,"receipt_sha256":None,"forecast":None}
            row["final"]=copy.deepcopy(row["initial"])
            from scripts.arena_v0_contract import digest
            no_preds["lock_sha256"]=digest({k:v for k,v in no_preds.items()
                                           if k!="lock_sha256"})
            ack["lock_sha256"]=no_preds["lock_sha256"]
            with self.assertRaisesRegex(ValueError,"ZERO_ADMISSIBLE_PREDICTIONS"):
                evaluate(lock=no_preds,archive=ack,construction=c,commitment=commitment,
                         producer_root=p,private_dir=root/"nonexistent",
                         out=root/"should-not-exist.json")

    def test_cli_reads_private_only_after_lock_ack_and_writes_one_result(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            p,private,c,commitment,lock,ack=scoped(root)
            for name,data in (("construction",c),("commitment",commitment),
                              ("lock",lock),("archive-record",ack)):
                (root/(name+".json")).write_text(json.dumps(data))
            out=root/"score-from-cli.json"
            args=[sys.executable,"-m","scripts.arena_cafe.ct03_minimal_score",
                  "--construction",str(root/"construction.json"),
                  "--commitment",str(root/"commitment.json"),
                  "--lock",str(root/"lock.json"),
                  "--archive-record",str(root/"archive-record.json"),
                  "--producer-root",str(p),"--private-dir",str(private),
                  "--out",str(out)]
            repo=Path(__file__).resolve().parents[1]
            success=subprocess.run(args,cwd=repo,capture_output=True,text=True,timeout=30)
            self.assertEqual(success.returncode,0,success.stderr)
            self.assertEqual(json.loads(out.read_text())["paired_available"],1)
            again=subprocess.run(args,cwd=repo,capture_output=True,text=True,timeout=30)
            self.assertNotEqual(again.returncode,0)
            self.assertIn("REFUSE_OVERWRITE",again.stderr)


if __name__=="__main__":
    unittest.main()
