"""EV02 quality gates: declared semantics and clocks, NOT a flow estimator."""
from __future__ import annotations

import csv
from datetime import datetime
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from scripts import arena_operational_ingestion as op
import arena_ev02_ingestion_probe as ev02


class IngestionContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pos,cls.kds=ev02.example_exports()
        cls.pos_spec,cls.kds_spec=ev02.specs()
        cls.key=ev02.SECRET_SYNTHETIC

    def test_strict_named_source_mapping_and_no_physical_relabel(self):
        p=op.ingest_csv(self.pos,self.pos_spec,self.key)
        k=op.ingest_csv(self.kds,self.kds_spec,self.key)
        self.assertEqual((p["n_accepted"],k["n_accepted"]),(45,30))
        self.assertEqual((p["n_quarantined"],k["n_quarantined"]),(0,0))
        self.assertEqual(set(x["activity"] for x in k["events"]),{
            "preparation_started_admin","preparation_completed_admin"})
        for row in p["events"]+k["events"]:
            self.assertEqual(row["event_semantics"],"administrative_milestone")
            self.assertFalse(row["actual_physical_instant_verified"])
            self.assertFalse(row["clock_validation_independently_verified"])
            self.assertNotIn("order_id",row)
            self.assertNotIn("lead_id",row)
            self.assertNotIn("event_id",row)
            self.assertNotIn("email",row)
            self.assertTrue(row["case_ref"].startswith("p_"))

    def test_identity_link_only_by_explicit_namespace_and_secret(self):
        p=op.ingest_csv(self.pos,self.pos_spec,self.key)
        k=op.ingest_csv(self.kds,self.kds_spec,self.key)
        self.assertEqual(set(x["case_ref"] for x in p["events"]),
                         set(x["case_ref"] for x in k["events"]))
        other_spec=op.SourceSpec("kds_export_v1","KDS_EXAMPLE",
           "orders:different","KDS_CLOCK","verified_utc_sync",1,"proof-fixture")
        unlinked=op.ingest_csv(self.kds,other_spec,self.key)
        self.assertTrue(set(x["case_ref"] for x in p["events"]).isdisjoint(
                        set(x["case_ref"] for x in unlinked["events"])))
        self.assertEqual(op.summarize_cases([p,unlinked])["n_cases"],30)
        self.assertNotEqual(
            op.pseudonym(self.key,"case","orders:synthetic","O000"),
            op.pseudonym(b"y"*32,"case","orders:synthetic","O000"))
        with self.assertRaisesRegex(ValueError,"EV02_PRIVATE_PSEUDONYM_SECRET_REQUIRED"):
            op.ingest_csv(self.pos,self.pos_spec,b"bad")

    def test_never_merge_lead_and_order_identifiers_across_entity_types(self):
        with self.assertRaisesRegex(ValueError,
                                    "EV02_SOURCE_PROFILE_NAMESPACE_MISMATCH"):
            op.SourceSpec("crm_export_v1","CRM_EXAMPLE","orders:synthetic",
                          "CRM_CLOCK","unverified",None,"example")
        with self.assertRaisesRegex(ValueError,
                                    "EV02_SOURCE_PROFILE_NAMESPACE_MISMATCH"):
            op.SourceSpec("pos_export_v1","POS_EXAMPLE","crm:synthetic",
                          "POS_CLOCK","verified_utc_sync",1,"example")

    def test_utc_offset_normalization_without_claiming_clock_sync(self):
        self.assertEqual(
            op.utc_iso(op.parse_timestamp("2026-01-01T10:00:00-06:00")),
            "2026-01-01T16:00:00.000000Z")
        self.assertEqual(
            op.parse_timestamp("2026-01-01T16:00:00Z"),
            op.parse_timestamp("2026-01-01T10:00:00-06:00"))
        for value in ("2026-01-01T16:00:00","2026-01-01",
                      "not-a-time","2026-13-01T03:00:00Z"):
            with self.assertRaises(ValueError):
                op.parse_timestamp(value)
        self.assertEqual(
            op.iso_duration_seconds(
                op.parse_timestamp("2026-01-01T00:00:00Z"),
                op.parse_timestamp("2026-01-01T00:00:01.001001Z")),
            "1.001001")

    def test_pos_kds_join_is_only_administrative_timing(self):
        p=op.ingest_csv(self.pos,self.pos_spec,self.key)
        k=op.ingest_csv(self.kds,self.kds_spec,self.key)
        out=op.summarize_cases([p,k])
        self.assertEqual((out["n_cases"],out["n_recorded_events"]),(15,75))
        for row in out["cases"]:
            self.assertEqual(row["cycle_status"],
                             "RECORDED_ADMIN_CYCLE_NOT_PHYSICAL_SOJOURN")
            self.assertEqual(row["admin_interval_status"],
                             "RECORDED_KDS_CLICK_INTERVAL_NOT_PHYSICAL_SERVICE")
            self.assertEqual(row["cross_source_status"],
                             "RECORDED_CROSS_SOURCE_ELAPSED_NOT_PHYSICAL_SERVICE")
            self.assertFalse(row["hidden_stage_inferred"])
            self.assertFalse(row["physical_queue_wait_identified"])
            self.assertFalse(row["physical_service_time_identified"])
            self.assertIn("prep_click_end_to_delivery_click_seconds",row)
        self.assertTrue(out["no_mechanism_discovery_from_click_timestamps"])

    def test_unverified_clock_blocks_cross_source_even_with_iso_offsets(self):
        p=op.ingest_csv(self.pos,self.pos_spec,self.key)
        k=op.ingest_csv(self.kds,ev02.specs("unverified")[1],self.key)
        out=op.summarize_cases([p,k])
        self.assertEqual(out["n_cases"],15)
        for row in out["cases"]:
            self.assertEqual(row["cross_source_status"],
                             "CROSS_SOURCE_TEMPORAL_COMPARISON_BLOCKED")
            self.assertIn("kds_click_interval_seconds",row)
            self.assertNotIn("prep_click_end_to_delivery_click_seconds",row)
        with self.assertRaisesRegex(ValueError,"EV02_VERIFIED_CLOCK_REQUIRES_ACCURACY"):
            op.SourceSpec("pos_export_v1","POS","orders:foo","clk",
                          "verified_utc_sync",None,"evidence")

    def test_quarantine_duplicates_missing_ids_unknown_actions_naive_clocks(self):
        p=op.ingest_csv(ev02.adversarial_export(self.pos),self.pos_spec,self.key)
        self.assertEqual(p["n_accepted"],45)
        self.assertEqual(p["n_quarantined"],4)
        reasons={x["code"] for x in p["quarantine"]}
        self.assertIn("EV02_TIMESTAMP_HAS_NO_UTC_OFFSET",reasons)
        self.assertIn("ROW_DUPLICATE_EVENT_ID",reasons)
        self.assertIn("ROW_UNMAPPED_ACTION",reasons)
        self.assertIn("ROW_EMPTY_REQUIRED_FIELD",reasons)
        self.assertTrue(all(set(x)=={"row_number","code","source_profile"}
                            for x in p["quarantine"]))
        self.assertFalse(any("O000" in str(x) for x in p["quarantine"]))

    def test_extra_pii_header_is_whole_file_blocked(self):
        poisoned=self.pos.replace("clock_id\n","clock_id,email\n",1)
        with self.assertRaisesRegex(ValueError,"EV02_FILE_SCHEMA_REJECTED"):
            op.ingest_csv(poisoned,self.pos_spec,self.key)
        duplicated_header=self.pos.replace("clock_id\n","clock_id,clock_id\n",1)
        with self.assertRaisesRegex(ValueError,"EV02_FILE_SCHEMA_REJECTED"):
            op.ingest_csv(duplicated_header,self.pos_spec,self.key)

    def test_incomplete_and_cross_source_inconsistent_lifecycle_abstains(self):
        rows=list(csv.DictReader(StringIO(self.pos)))
        missing=ev02.csv_rows([r for r in rows
               if not(r["order_id"]=="O000" and r["action"]=="handed_off")])
        p=op.ingest_csv(missing,self.pos_spec,self.key)
        k=op.ingest_csv(self.kds,self.kds_spec,self.key)
        summary=op.summarize_cases([p,k])
        self.assertEqual(sum(x["cycle_status"]=="UNRESOLVED_INCOMPLETE_LIFECYCLE"
                             for x in summary["cases"]),1)
        # Shift one KDS completion beyond the POS delivery recorded clock.
        krows=list(csv.DictReader(StringIO(self.kds)))
        x=next(r for r in krows if
               r["order_id"]=="O000" and r["action"]=="prep_done")
        x["occurred_at"]="2026-01-01T23:59:59.000000-06:00"
        tampered=op.ingest_csv(ev02.csv_rows(krows),self.kds_spec,self.key)
        results=op.summarize_cases([op.ingest_csv(self.pos,self.pos_spec,self.key),
                                     tampered])
        self.assertEqual(sum(
            z["cross_source_status"]=="BLOCKED_INCONSISTENT_OR_MISSING_EVENT_CHAIN"
            for z in results["cases"]),1)

    def test_crm_leads_not_order_resource_or_queue(self):
        spec=op.SourceSpec("crm_export_v1","CRM_EXAMPLE","crm:synthetic",
                           "CRM_CLOCK","unverified",None,"synthetic-example")
        batch=op.ingest_csv(ev02.crm_example(),spec,self.key)
        result=op.summarize_cases([batch])
        self.assertEqual((result["n_cases"],result["n_recorded_events"]),(2,4))
        for c in result["cases"]:
            self.assertEqual(c["cycle_status"],"NOT_APPLICABLE_TO_CRM_ORDER_CYCLE")
            self.assertFalse(c["physical_service_time_identified"])
            self.assertFalse(c["hidden_stage_inferred"])

    def test_end_to_end_artifacts_are_synthetic_and_hash_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"ev02"
            r=ev02.run(path,"a"*40,"b"*40)
            self.assertEqual(r["normal_ingest"]["pos_accepted"],45)
            self.assertEqual(r["normal_ingest"]["kds_accepted"],30)
            self.assertEqual(r["normal_ingest"]["n_valid_cases"],15)
            self.assertEqual(r["unverified_clock"]
                            ["n_cross_source_intervals_blocked"],15)
            self.assertEqual(r["adversarial_quality"]["quarantined"],4)
            self.assertEqual(r["crm_separate_namespace"]["n_leads"],2)
            self.assertEqual(r["n_unknown_topologies_detected"],0)
            self.assertEqual(r["promotion_gate"],op.GATE)
            self.assertTrue(r["no_external_data_used"])
            plan=json.loads((path/"00_PLAN_BEFORE_EVAL.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],ev02.PROTO)
            self.assertEqual(plan["checkout_sha"],"a"*40)
            self.assertEqual(plan["pr_head_sha"],"b"*40)
            manifest=json.loads((path/"03_MANIFEST.json").read_text())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(digest,"sha256:"+
                    sha256((path/name).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"EV02_REFUSE_OVERWRITE"):
                ev02.run(path,"a"*40,"b"*40)


if __name__=="__main__":
    unittest.main(verbosity=2)
