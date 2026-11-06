"""CAF-L001 evidence and three real native-arm integration tests, no synthetic POS."""
from pathlib import Path
import csv
import tempfile
import unittest

from experiments.cafeteria.l001.reference import METRICS, read_metrics, execute, compare_legacy
from experiments.cafeteria.l001.three_arms import perform, write_artifacts
from scripts.arena_v0_contract import assert_same_evidence, arm_view

class TestL001(unittest.TestCase):
    def test_original_pinned_metrics_and_derived_area(self):
        source=read_metrics()
        self.assertEqual(len(source),9)
        r=execute()
        self.assertEqual(r["source_sha256"],
                         "sha256:f45e12578813f75ae6f201e5390f93e39bf115aed2849edd704072f09544fc28")
        self.assertTrue(r["checks"]["F09"]["derived_not_independent"])
        self.assertEqual([e["pending"] for e in r["trace"]],[2,2,1,0,0])
        self.assertEqual([e["received"] for e in r["trace"]],[0,0,1,2,2])
        self.assertAlmostEqual(r["area_receptacle_video_s"],r["checks"]["F07"]["witness"]+r["checks"]["F08"]["witness"])
        self.assertEqual(r["rejected_in_this_batch_if_measurements_hold"],
            ["TWO_RECEIPTS_EXACTLY_SIMULTANEOUS","BOTH_RECEIVED_AT_PICKUP_END"])

    def test_excludes_master_conflicts(self):
        legacy=compare_legacy(read_metrics())
        self.assertEqual(len(legacy["comparisons"]),2)
        self.assertTrue(all(c["overlap"] is False for c in legacy["comparisons"]))

    def test_inconsistent_bounds_fail_closed(self):
        with METRICS.open(encoding="utf-8-sig",newline="") as f:
            rd=csv.DictReader(f);rows=list(rd);fields=rd.fieldnames
        for row in rows:
            if row["id"]=="F04":
                row["lower"],row["upper"]="20","21"
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"mutated.csv"
            with file.open("w",encoding="utf-8",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            with self.assertRaisesRegex(ValueError,"NO_JOINTLY_FEASIBLE_TRAJECTORY"):
                execute(file,pin=False)

    def test_no_service_distribution_promotion(self):
        with METRICS.open(encoding="utf-8-sig",newline="") as f:
            rd=csv.DictReader(f);rows=list(rd);fields=rd.fieldnames
        rows[0]["usable_as_service_distribution"]="true"
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"mutated.csv"
            with file.open("w",encoding="utf-8",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            with self.assertRaisesRegex(ValueError,"SERVICE_DISTRIBUTION_PROMOTION_PROHIBITED"):
                execute(file,pin=False)

    def test_three_methods_not_fused_or_fabricated(self):
        report,reference,evidence,outputs,support=perform()
        self.assertEqual(set(outputs),{"D","B","M"})
        self.assertEqual(report["arm_status"],{"D":"PARTIAL","B":"BLOCKED","M":"PARTIAL"})
        self.assertEqual(report["D_native_structures_linted"],2)
        self.assertGreater(report["M_short_E1_engineering_graphs_enumerated"],0)
        self.assertEqual(report["B_provider_calls"],0)
        self.assertEqual(report["OpenModelica_runs"],0)
        self.assertEqual(report["selected_hypotheses"],0)
        self.assertTrue(all(x["submission"]["hypothesis_ids"]==[] for x in outputs.values()))
        self.assertFalse(outputs["B"]["native"]["other_arm_results_supplied"])
        self.assertEqual(support["area_conditional"]["minimal_environments"],
                         [["A_ASSOCIATION_OF_TWO_RECEPTACLES_WITH_ONE_LOT"]])

    def test_github_artifacts_and_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"output"
            report=write_artifacts(out)
            self.assertEqual(report["ledger_revisions"],3)
            self.assertEqual(len(list(out.glob("02_*_native.json"))),3)
            self.assertTrue((out/"L001_ledger.sqlite").exists())
            self.assertTrue((out/"03_ATMS.json").exists())

if __name__=="__main__":
    unittest.main()
