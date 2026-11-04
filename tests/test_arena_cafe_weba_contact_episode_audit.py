"""WEBA physical-contact E1 ledger tests; only parser fixtures, not fake cafes."""
from __future__ import annotations

from datetime import datetime,timezone
from unittest.mock import patch
import json
import unittest

from scripts.arena_cafe import weba_contact_episode_audit as contact


def t(iso):
    return int(datetime.fromisoformat(iso.replace("Z","+00:00")).timestamp())


def six_contacts(sample=None):
    keys=tuple(contact.CONTACT_CATEGORIES)
    return {name:list(sample or []) for name in keys}


def bound_shift():
    return {
        "UTC_boundaries_under_UNVERIFIED_local_clock_assumption":[
            "2024-03-08T13:33:00+00:00",
            "2024-03-08T17:41:00+00:00",
        ],
        "Tapo":{
            "Tapo_snapshot_time_utc_last":
                "2024-03-08T17:37:02.167000+00:00",
            "total_events_in_snapshot":27,
        },
    }


class ContactAuditContract(unittest.TestCase):
    def test_00_six_contact_sensors_are_not_zone_motions(self):
        self.assertEqual(5,len(contact.STORAGE))
        self.assertEqual(6,len(contact.CONTACT_CATEGORIES))
        self.assertNotIn("zone_1",contact.CONTACT_CATEGORIES)
        self.assertNotIn("zone_2",contact.CONTACT_CATEGORIES)
        self.assertEqual("ENTRANCE_CONTACT_NON_CUSTOMER_COUNT_CONTROL",
                         contact.CONTACT_CATEGORIES[contact.ENTRANCE])

    def test_01_Open_KeepOpen_Close_is_one_contact_interval(self):
        records=[
            ("Open",100),("KeepOpen",103),("KeepOpen",107),("Close",115),
            ("Open",200),("Close",209)]
        out=contact.reconstruct(records)
        self.assertEqual([(100,115),(200,209)],out["paired_intervals"])
        self.assertEqual(2,out["pair_count"])
        self.assertEqual(2,out["keepopen_while_known_open"])
        self.assertEqual(0,out["unclosed_open_at_snapshot_end"])
        self.assertEqual(0,out["orphan_closes_no_start_known"])

    def test_02_orphan_events_are_censored_not_imputed(self):
        out=contact.reconstruct([
            ("Close",10),("KeepOpen",11),("Open",20),("KeepOpen",21)])
        self.assertEqual(0,out["pair_count"])
        self.assertEqual(1,out["orphan_closes_no_start_known"])
        self.assertEqual(1,out["orphan_keepopen_without_known_open"])
        self.assertEqual(1,out["keepopen_while_known_open"])
        self.assertEqual(1,out["unclosed_open_at_snapshot_end"])
        self.assertEqual([] ,out["paired_intervals"])

    def test_03_ambiguous_nested_or_equal_time_pair_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,"WEBA_CONTACT_NESTED_OPEN_WITHOUT_CLOSE"):
            contact.reconstruct([
                ("Open",100),("Open",110),("Close",120)])
        with self.assertRaisesRegex(
            ValueError,"WEBA_CONTACT_CLOSURE_NOT_AFTER_OPEN"):
            contact.reconstruct([("Open",100),("Close",100)])
        with self.assertRaisesRegex(
            ValueError,"WEBA_CONTACT_INVALID_SOURCE_EVENT"):
            contact.reconstruct([("FinishOrder",100)])

    def test_04_pair_is_bounded_to_shift_and_export_no_imputation(self):
        start=datetime(2024,3,8,13,33,tzinfo=timezone.utc)
        end=datetime(2024,3,8,17,41,tzinfo=timezone.utc)
        export=datetime(2024,3,8,17,37,2,tzinfo=timezone.utc)
        pair=lambda a,b:(t(a),t(b))
        cases={
            "BEFORE_SHIFT":pair(
                "2024-03-08T13:31:00Z","2024-03-08T13:32:00Z"),
            "CROSSES_SHIFT_START":pair(
                "2024-03-08T13:32:55Z","2024-03-08T13:33:02Z"),
            "COMPLETE_WITHIN_DECLARED_SHIFT":pair(
                "2024-03-08T13:33:00Z","2024-03-08T13:33:09Z"),
            "SPANS_BOTH_SHIFT_BOUNDARIES":pair(
                "2024-03-08T13:31:00Z","2024-03-08T17:41:00Z"),
            "CROSSES_SHIFT_END":pair(
                "2024-03-08T17:40:50Z","2024-03-08T17:41:30Z"),
            "AFTER_SHIFT":pair(
                "2024-03-08T17:41:01Z","2024-03-08T17:41:10Z"),
        }
        for expected,p in cases.items():
            with self.subTest(expected=expected):
                if p[1]>int(export.timestamp()):
                    with self.assertRaisesRegex(
                        ValueError,"WEBA_CONTACT_PAIR_LATER_THAN_EXPORT"):
                        contact.classify_pair(p,start,end,export)
                else:
                    self.assertEqual(expected,
                        contact.classify_pair(p,start,end,export))
        self.assertEqual("CROSSES_SHIFT_END",
                         contact.classify_pair(cases["CROSSES_SHIFT_END"],
                          start,end,datetime(2024,3,8,18,tzinfo=timezone.utc)))

    def test_05_full_ledger_reproduces_only_physical_contact_under_fixture(self):
        beginning=t("2024-03-08T13:33:05Z")
        earliest=t("2024-03-08T13:31:00Z")
        raw=six_contacts()
        raw["r_wing_fridge"]=[
            ("Open",earliest),("Close",earliest+7),
            ("Open",beginning),("KeepOpen",beginning+3),
            ("Close",beginning+10),("Open",beginning+90)]
        raw["l_wing_fridge"]=[]
        raw["freezer"]=[("Open",beginning+12),("Close",beginning+15)]
        raw["r_door_cake_display"]=[
            ("Open",beginning+25),("Close",beginning+50)]
        raw["front_door"]=[("Open",beginning),("Close",beginning+8)]
        expected_total=sum(len(v) for v in raw.values())
        shift=bound_shift()
        shift["Tapo"]["total_events_in_snapshot"]=expected_total
        with patch.object(contact,"contact_events",return_value=raw):
            result=contact.run_for_shift(
                "20240308_evening",shift,"not-an-original-source")
        storage=result["storage_contact_summary"]
        self.assertEqual(3,storage[
            "paired_storage_contact_intervals_COMPLETE_WITHIN_shift"])
        self.assertEqual(1,storage[
            "paired_storage_contact_intervals_BEFORE_shift"])
        self.assertEqual(1,storage["storage_contact_open_without_matched_close"])
        self.assertEqual(1,storage[
            "storage_contact_KeepOpen_total_not_new_openings"])
        self.assertEqual(1,result[
            "front_door_control_pairs_complete_within_shift"])
        self.assertFalse(result["human_task_instance_or_completion_confirmed"])
        self.assertFalse(result["POS_order_ID_to_contact_event_link_validated"])
        self.assertFalse(result["sensor_status_and_coverage_independently_validated"])
        self.assertTrue(result["snapshot_ends_before_declared_shift_end"])
        self.assertIsNone(result["sensor_contact_event_ledger"][
            "l_wing_fridge"][
                "paired_contact_open_seconds_median_IN_SHIFT_not_service"])
        self.assertTrue(result["sensor_contact_event_ledger"][
            "l_wing_fridge"]["snapshot_empty_NOT_proof_of_no_real_openings"])
        output=json.dumps(result)
        for private in ("order_ID","case_id","event_id","device_id",
                        "raw_order_time"):
            self.assertNotIn('"'+private+'":',output)

    def test_06_contact_parse_rejects_missing_sensor_or_wrong_model(self):
        # Work at the source boundary without exposing device identifiers.
        mock={
            "sensor_count":10,
            "returned_records_per_selected_sensor":{},
        }
        raw=[
            f"2024-03-08T17:37:00.000Z INFO > Found T110"
            f" child device with nickname: {name}, id: REDACTED,"
            " last 50 trigger logs: TriggerLogsResult"
            " { start_id: 0, sum: 0, logs: [] }"
            for name in contact.CONTACT_CATEGORIES
        ]
        with patch.object(contact.tapo,"parse_tapo_text",return_value=mock):
            self.assertEqual(6,len(contact.contact_events("\n".join(raw))))
            with self.assertRaisesRegex(
                ValueError,"WEBA_CONTACT_INCOMPLETE_SIX_T110_SENSORS"):
                contact.contact_events("\n".join(raw[:-1]))
            with self.assertRaisesRegex(
                ValueError,"WEBA_CONTACT_SENSOR_MODEL_NOT_T110"):
                contact.contact_events("\n".join(raw).replace(
                    "Found T110 child device with nickname: freezer",
                    "Found T100 child device with nickname: freezer"))

    def test_07_task_labels_are_not_emitted_even_for_valid_pairs(self):
        result=contact.reconstruct([
            ("Open",1),("Close",6),("Open",12),("Close",19)])
        self.assertEqual(2,result["pair_count"])
        self.assertNotIn("order_ID",result)
        self.assertNotIn("barista_task",result)
        self.assertNotIn("service_finish",result)

    def test_08_source_hashes_must_precede_any_real_contact_audit(self):
        with self.assertRaisesRegex(ValueError,
                                    "WEBA_SOURCE_NOT_PINNED_GIT_BLOB"):
            contact.build(
                b"fabricated POS bytes",
                b"fabricated shift metadata",
                {k:b"fabricated" for k in contact.source_audit.SHIFTS})


if __name__=="__main__":
    unittest.main()
