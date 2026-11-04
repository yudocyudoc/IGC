"""WEBA instrument-coverage and POS-clock quality tests (no fake G5).

The workbook/log inputs are minimal structural fixtures; the CI job downloads
the exact original WEBA source bytes to test the actual three shifts.
"""
from __future__ import annotations

from datetime import datetime,timezone,timedelta
import io
from zipfile import ZipFile
from unittest.mock import patch
import json
import unittest

from scripts.arena_cafe import weba_instrument_integrity as audit


def excel_xml(headers,rows):
    namespace="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    src=[f'<worksheet xmlns="{namespace}"><sheetData>']
    for rownum,items in enumerate((headers,*rows),start=1):
        src.append(f'<row r="{rownum}">')
        for column,value in enumerate(items):
            if value is None:
                continue
            letter=chr(65+column)
            src.append(f'<c r="{letter}{rownum}" t="inlineStr"><is><t>{value}</t></is></c>')
        src.append("</row>")
    src.append("</sheetData></worksheet>")
    buffer=io.BytesIO()
    with ZipFile(buffer,"w") as z:
        z.writestr("xl/worksheets/sheet1.xml","".join(src))
    return buffer.getvalue()


def source_pos_fixture():
    return excel_xml(
        ("order_ID","order_date","order_time","time_of_day"),
        [("privatecase1","20240223","14:01:00","evening"),
         ("privatecase2","20240304","2:04:00 PM","evening"),
         ("privatecase3","20240308",None,"evening")]
    )


def shift_summary_fixture():
    return excel_xml(
        ("par_ID","shift_ID","shift_date","time_of_day",
         "start_time","end_time","total_revenue"),
        [("PRIVATE_PERSON","private-shift-A","20240223","evening",
          "2:00:00 PM","6:00:00 PM","999"),
         ("PRIVATE_PERSON","private-shift-B","20240304","evening",
          "2:00:00 PM","6:00:00 PM","888"),
         ("PRIVATE_PERSON","private-shift-C","20240308","evening",
          "2:00:00 PM","6:00:00 PM","777")]
    )


def tapo_fixture(day="20240223",*,duplicates=False,swapped=False):
    prefix=datetime.strptime(day,"%Y%m%d").strftime("%Y-%m-%d")
    event_clock=int(datetime.strptime(
        prefix+"T14:05:00+0000","%Y-%m-%dT%H:%M:%S%z").timestamp())
    sensors=[
        "r_wing_fridge","l_wing_fridge","freezer","stair",
        "front_door_m","r_door_cake_display","l_door_cake_display",
        "zone_1","zone_2","front_door"
    ]
    out=[]
    for i,name in enumerate(sensors):
        model="T100" if name in ("stair","front_door_m",
                                  "zone_1","zone_2") else "T110"
        kind="Motion" if model=="T100" else "Open"
        ids=(1,1) if duplicates else (2,1)
        a=event_clock+1
        b=event_clock if not swapped else event_clock+2
        out.append(
            f"{prefix}T18:10:00.123Z INFO > Found {model}"
            f" child device with nickname: {name}, id: REDACTED,"
            " last 50 trigger logs: TriggerLogsResult"
            f" {{ start_id: 0, sum: 2, logs: [{kind} {{ id: {ids[0]},"
            f" timestamp: {a} }}, {kind} {{ id: {ids[1]},"
            f" timestamp: {b} }}] }}"
        )
    return "\n".join(out).encode("utf-8")


class InstrumentContract(unittest.TestCase):
    def test_00_source_config_pins_only_three_tapo_logs_and_metadata(self):
        self.assertEqual(3,len(audit.SHIFTS))
        self.assertEqual(set(audit.SHIFTS),set(audit.LOG_FILES))
        self.assertEqual("a8a717c0f0b8292297a71328c2bc6dfc90b6fa82",
                         audit.META_FILE["git_blob_sha1"])
        with self.assertRaisesRegex(ValueError,"WEBA_SOURCE_NOT_PINNED_GIT_BLOB"):
            audit.verify_inputs(
                source_pos_fixture(),shift_summary_fixture(),
                {s:tapo_fixture(s[:8]) for s in audit.SHIFTS})
        with patch.object(audit.source,"verify_pinned",return_value={}):
            with self.assertRaisesRegex(
                ValueError,"WEBA_AUDIT_SHIFT_METADATA_SIZE_CHANGED"):
                audit.verify_inputs(
                    b"pos",shift_summary_fixture(),
                    {s:tapo_fixture(s[:8]) for s in audit.SHIFTS})

    def test_01_wall_clock_parser_rejects_utc_attestation_inference(self):
        pos=audit.pos_clock_audit(source_pos_fixture())
        self.assertEqual(3,pos["nonempty_order_rows"])
        self.assertEqual(2,pos["parseable_order_time_as_wall_clock"])
        self.assertEqual(1,pos["blank_order_time"])
        self.assertEqual(0,pos["order_time_with_explicit_timezone_offset_or_Z"])
        self.assertEqual({"YYYYMMDD_8_DIGITS":3},
                         pos["order_date_raw_encoding_counts"])
        self.assertFalse(pos["timezone_certified_by_source"])
        self.assertFalse(pos["UTC_offset_or_drift_calibrated_against_Tapo"])
        self.assertIn("inlineStr",pos["order_time_OOXML_cells"][
            "cell_storage_types_including_header"])
        encoded=json.dumps(pos)
        for forbidden in ("privatecase1","privatecase2","14:01:00"):
            self.assertNotIn(forbidden,encoded)

    def test_02_shift_metadata_excludes_participant_id_and_revenue(self):
        boundary,total=audit.shift_boundaries(shift_summary_fixture())
        self.assertEqual(3,total)
        self.assertEqual(set(audit.SHIFTS),set(boundary))
        start,end=boundary["20240223_evening"]["interval_for_audit_only"]
        self.assertEqual(
            datetime(2024,2,23,13,tzinfo=timezone.utc),start)
        self.assertEqual(
            datetime(2024,2,23,17,tzinfo=timezone.utc),end)
        serialized=json.dumps({
            s:{k:v for k,v in b.items() if k!="interval_for_audit_only"}
            for s,b in boundary.items()})
        self.assertNotIn("PRIVATE_PERSON",serialized)
        self.assertNotIn("999",serialized)

    def test_03_Tapo_snapshot_has_one_block_per_sensor_and_no_causal_certainty(self):
        bounds,_=audit.shift_boundaries(shift_summary_fixture())
        t=audit.tapo_log_audit(
            "20240223_evening",tapo_fixture().decode(),
            bounds["20240223_evening"])
        self.assertEqual(10,t["sensor_group_count"])
        self.assertEqual(20,t["total_events_in_snapshot"])
        self.assertEqual(0,t["events_before_assumed_recording_shift"])
        self.assertEqual(20,t["events_inside_assumed_recording_shift"])
        self.assertEqual(0,t["events_after_assumed_recording_shift"])
        self.assertTrue(t["not_verified_capture_completeness"])
        self.assertTrue(t["vendor_ID_gaps_not_interpretable_as_missing_count"])
        self.assertFalse(t["Tapo_event_clock_calibrated_against_POS"])

    def test_04_duplicate_vendor_id_detected(self):
        bounds,_=audit.shift_boundaries(shift_summary_fixture())
        with self.assertRaisesRegex(ValueError,
            "WEBA_AUDIT_DUPLICATE_VENDOR_IDS|WEBA_TAPO_DUPLICATE"):
            audit.tapo_log_audit("20240223_evening",
                tapo_fixture(duplicates=True).decode(),
                bounds["20240223_evening"])

    def test_05_reverse_chronology_violation_detected(self):
        bounds,_=audit.shift_boundaries(shift_summary_fixture())
        with self.assertRaisesRegex(ValueError,
                "WEBA_AUDIT_NONREVERSE_CHRONOLOGICAL_TAPO|WEBA_TAPO_TIMESTAMP_ORDER"):
            audit.tapo_log_audit("20240223_evening",
                tapo_fixture(swapped=True).decode(),
                bounds["20240223_evening"])

    def test_06_metadata_duplicated_for_selected_shift_fails(self):
        src=shift_summary_fixture()
        with self.assertRaisesRegex(
            ValueError,"WEBA_AUDIT_DUPLICATE_SHIFT_METADATA"):
            duplicate=excel_xml(
                ("shift_date","time_of_day","start_time","end_time"),
                [("20240223","evening","14:00","18:00"),
                 ("20240223","evening","14:00","18:00"),
                 ("20240304","evening","14:00","18:00"),
                 ("20240308","evening","14:00","18:00")])
            audit.shift_boundaries(duplicate)

    def test_07_report_has_no_event_device_or_participant_records(self):
        with patch.object(audit,"verify_inputs",return_value={"fixture":True}):
            out=audit.build(
                source_pos_fixture(),shift_summary_fixture(),
                {s:tapo_fixture(s[:8]) for s in audit.SHIFTS})
        self.assertEqual("NOT_RUN",out["G5"])
        self.assertEqual("NOT_CREATED",out["F5_independent_reserve"])
        self.assertFalse(out["Tapo_continuous_service_coverage_ESTABLISHED"])
        self.assertFalse(out["POS_and_Tapo_synchronized_ESTABLISHED"])
        self.assertTrue(out["no_individual_order_sensor_or_participant_identifiers_exported"])
        serialized=json.dumps(out)
        for forbidden_key in ('"par_ID":','"order_ID":','"case_id":',
                              '"resource_id":','"event_id":','"device_id":'):
            self.assertNotIn(forbidden_key,serialized)
        for private in ("PRIVATE_PERSON","privatecase1","private-shift-A"):
            self.assertNotIn(private,serialized)


if __name__=="__main__":
    unittest.main()
