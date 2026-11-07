"""F171-04: scientific and physical denominators remain distinct in repository."""
import json
from pathlib import Path
import unittest

REPORT=Path(__file__).resolve().parents[1]/"experiments/cafeteria/E03_RECONCILED_OPERATIONAL_ACCOUNTING.json"


class OperationalAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads(REPORT.read_text(encoding="utf-8"))

    def test_count_physical_runs_not_just_unique_targets(self):
        r=self.r
        runs=r["source_runs"]
        self.assertEqual(len(runs),3)
        phys=sum(x["new_solver_targets"] for x in runs.values())
        unique=sum(runs[x]["new_solver_targets"] for x in ("D_FIRST","M_INITIAL"))
        self.assertEqual(phys,r["physical_omc_simulate_statements_executed"])
        self.assertEqual(unique,r["scientific_unique_new_solver_targets"])
        self.assertEqual(r["physical_omc_redundant_invocations"],
                         runs["D_REPEAT"]["new_solver_targets"])
        self.assertEqual(r["physical_budget_overrun"],
                         phys-r["original_budget_max_physical_simulations"])
        self.assertEqual(r["scientific_unique_candidate_variants"],
                         runs["D_FIRST"]["candidate_count"]+runs["M_INITIAL"]["candidate_count"])
        self.assertEqual(r["historical_csv_reused"],runs["M_INITIAL"]["reused_historical_csv"])

    def test_repeated_D_not_new_scientific_variant(self):
        a,b=[self.r["source_runs"][k] for k in ("D_FIRST","D_REPEAT")]
        for k in ("manifest_sha256","scores_sha256","solver_script_sha256",
                  "source_snapshot_hash","signal_sha256"):
            self.assertEqual(a[k],b[k])
        self.assertNotEqual(a["omc_log_sha256"],b["omc_log_sha256"])
        self.assertNotEqual(a["run_id"],b["run_id"])
        self.assertEqual(a["csv_count"],b["csv_count"])
        self.assertTrue(self.r["no_new_scientific_candidates_from_duplicate"])

    def test_links_to_all_original_artifacts_and_budget_overrun_persistent(self):
        for k in ("D_FIRST","D_REPEAT","M_INITIAL"):
            x=self.r["source_runs"][k]
            self.assertGreater(x["run_id"],0)
            self.assertGreater(x["artifact_id"],0)
            self.assertRegex(x["sha256_zip"],r"^sha256:[a-f0-9]{64}$")
            self.assertEqual(x["csv_count"],x["candidate_count"])
        self.assertEqual(self.r["schema"],"igc-arena-e03-operational-reconciliation/0.1")
        self.assertEqual(self.r["provider_calls"],0)
        self.assertEqual(self.r["G4"],"NOT_RUN")
        self.assertEqual(self.r["G5"],"NOT_RUN")


if __name__=="__main__":
    unittest.main()
