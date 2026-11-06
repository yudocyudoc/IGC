"""E00 regressions: original metrics, direct hit limits, revision and as-of memory."""
import tempfile
import unittest
from pathlib import Path

from experiments.cafeteria.l001.e00_correction import (
    check_lineage, load_direct_source, relative_direct_bounds,
    write_temporal_revision, OLD, NEW,
)
from experiments.cafeteria.l001.reference import read_metrics, constraints, solve, execute
from scripts.ledger import Ledger
import numpy as np


class TestE00(unittest.TestCase):
    def test_documented_direct_source(self):
        data=load_direct_source()
        self.assertEqual(relative_direct_bounds(data)["H07"],[48.986,49.988])
        self.assertEqual(data["hit_intervals_video_s"]["H01"],[178.414,178.414])
        result=check_lineage(read_metrics())
        self.assertEqual(result["primary_source_verification"],
                         "PENDING_PRIMARY_MASTER_AND_EVENT_EXPORT")
        self.assertEqual({x["id"] for x in result["revisions"]},{"MD-M001","MD-M002"})

    def test_old_h07_witness_excluded_by_direct_hit(self):
        a,b=constraints(read_metrics())
        candidate=np.array([42.0,45.5,47.4,48.585])
        self.assertTrue(np.any(a@candidate>b+1e-8))
        result=execute()
        self.assertGreaterEqual(result["ranges_relative_H01_video_s"]["H07"][0],48.986-1e-6)
        self.assertLessEqual(result["ranges_relative_H01_video_s"]["H07"][1],49.988+1e-6)
        self.assertGreaterEqual(result["one_nonunique_witness"]["H07"],48.986-1e-6)

    def test_direct_contradiction_empty_region(self):
        from experiments.cafeteria.l001.e00_correction import direct_constraint_rows
        source=load_direct_source()
        source["hit_intervals_video_s"]["H07"]=[201.0,202.0]
        da,db=direct_constraint_rows(source)
        a,b=constraints(read_metrics(),direct=False)
        with self.assertRaisesRegex(ValueError,"NO_JOINTLY_FEASIBLE_TRAJECTORY"):
            solve(np.zeros(4),np.vstack((a,da)),np.concatenate((b,db)))

    def test_time_travel_and_unrelated_case_unchanged(self):
        root=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp)/"memory.sqlite",root/"migrations/0001_ledger.sql")
            ledger.append_revision(
                entity_id="OTHER:CLAIM",entity_type="ATMSNode",case_id="UNRELATED",
                actor_id="test",idempotency_key="other-once",
                payload={"kind":"fact","active":True},
                recorded_at="2026-11-06T00:00:00+00:00",
                created_at="2026-11-06T00:00:00+00:00",
                access_policy="construction-visible")
            before=ledger.snapshot(case_id="UNRELATED",as_known_at="2026-11-06T02:00:00+00:00")
            report=write_temporal_revision(ledger,"2026-11-06T01:00:00+00:00")
            after=ledger.snapshot(case_id="UNRELATED",as_known_at="2026-11-06T02:00:00+00:00")
            self.assertEqual([r.integrity_hash for r in before],
                             [r.integrity_hash for r in after])
            self.assertEqual(report["new_ledger_revisions"],5)
            self.assertEqual([x["knowledge_node"] for x in report["snapshots"]],[OLD,NEW])
            self.assertNotEqual(report["snapshots"][0]["projection_hash"],
                                report["snapshots"][1]["projection_hash"])


if __name__=="__main__":
    unittest.main()
