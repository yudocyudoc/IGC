"""Unit guards for real-source WEBA temporal binning, no synthetic cafeteria.

Small parser fixtures probe time-boundary semantics; the CI integration test
separately fetches the actual pinned POS workbook and Tapo log from WEBA.
"""
from __future__ import annotations

from datetime import datetime, timedelta, time, timezone
from decimal import Decimal
import io
import json
from unittest.mock import patch
from zipfile import ZipFile
import unittest

from scripts.arena_cafe import weba_temporal_windows as w
from scripts.arena_cafe import weba_source_readiness as source


def tiny_excel():
    ns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    r=(f'<worksheet xmlns="{ns}"><sheetData>'
       '<row r="1">'
       '<c r="A1" t="inlineStr"><is><t>order_id</t></is></c>'
       '<c r="B1" t="inlineStr"><is><t>order_date</t></is></c>'
       '<c r="C1" t="inlineStr"><is><t>order_time</t></is></c>'
       '<c r="D1" t="inlineStr"><is><t>time_of_day</t></is></c>'
       '</row>'
       '<row r="2">'
       '<c r="A2" t="inlineStr"><is><t>privateID</t></is></c>'
       '<c r="B2" t="inlineStr"><is><t>20240223</t></is></c>'
       '<c r="C2" t="inlineStr"><is><t>14:30:00</t></is></c>'
       '<c r="D2" t="inlineStr"><is><t>evening</t></is></c>'
       '</row></sheetData></worksheet>')
    buf=io.BytesIO()
    with ZipFile(buf,"w") as z:
        z.writestr("xl/worksheets/sheet1.xml",r)
    return buf.getvalue()


def toy_tapo():
    lines=[]
    for i,name in enumerate(w.SENSORS):
        model="T110" if name=="front_door" else "T100"
        kind="Open" if name=="front_door" else "Motion"
        stamp=int(w.START.timestamp())+(i+1)*1800
        lines.append(
            f"2024-02-23T17:35:40.000Z INFO > Found {model}"
            f" child device with nickname: {name},"
            " id: SOME_DEVICE, detected: true,"
            " last 50 trigger logs: TriggerLogsResult"
            f" {{ start_id: {i+1}, sum: 1, logs:"
            f" [{kind} {{ id: {i+1}, timestamp: {stamp} }}] }}"
        )
    return "\n".join(lines)


class TemporalContracts(unittest.TestCase):
    def test_00_parse_hhmmss_numeric_excel_and_12h(self):
        self.assertEqual(time(14,30),w.parse_pos_clock("14:30"))
        self.assertEqual(time(14,30,9),w.parse_pos_clock("14:30:09"))
        self.assertEqual(time(14,30),w.parse_pos_clock("2:30 PM"))
        self.assertEqual(time(12),w.parse_pos_clock("0.5"))
        self.assertEqual(time(6),w.parse_pos_clock("0.25"))

    def test_01_unknown_pos_clock_not_force_guessed(self):
        for value in ("", "bad-clock", "1.2", "-0.5", "100000", "NaN"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    ValueError,"WEBA_TEMPORAL_POS_CLOCK_"):
                    w.parse_pos_clock(value)

    def test_02_budapest_primary_is_declared_assumption_not_UTC(self):
        local=time(14,30)
        primary=w.from_pos_clock(
            local,interpretation="BUDAPEST_LOCAL_ASSUMPTION")
        alternate=w.from_pos_clock(
            local,interpretation="UTC_AS_WRITTEN_SENSITIVITY")
        self.assertEqual(datetime(2024,2,23,13,30,tzinfo=timezone.utc),
                         primary)
        self.assertEqual(datetime(2024,2,23,14,30,tzinfo=timezone.utc),
                         alternate)
        self.assertEqual(timedelta(hours=1),alternate-primary)
        with self.assertRaisesRegex(
            ValueError,"WEBA_TEMPORAL_UNAPPROVED_CLOCK_INTERPRETATION"):
            w.from_pos_clock(local,interpretation="OPTIMIZED_POSTHOC")

    def test_03_half_open_30minute_bin_boundaries(self):
        dt=lambda h,m:datetime(2024,2,23,h,m,tzinfo=timezone.utc)
        self.assertEqual(0,w.window_index(dt(13,0)))
        self.assertEqual(0,w.window_index(dt(13,29)))
        self.assertEqual(1,w.window_index(dt(13,30)))
        self.assertEqual(9,w.window_index(dt(17,30)))
        self.assertIsNone(w.window_index(dt(18,0)))
        self.assertIsNone(w.window_index(dt(12,59)))
        got,out=w._bins([dt(13,0),dt(13,30),dt(18,0)])
        self.assertEqual(1,got[0])
        self.assertEqual(1,got[1])
        self.assertEqual(1,out)

    def test_04_selected_pos_subset_not_constructed_from_unrelated_rows(self):
        with self.assertRaisesRegex(ValueError,
                                    "WEBA_TEMPORAL_POS_33_ORDERS_CHANGED"):
            w.pos_shift_clock_times(tiny_excel())

    def test_05_sensor_type_kept_distinct_from_physical_case(self):
        raw=w.raw_sensor_times(toy_tapo())
        sensors,logaudit=raw
        self.assertEqual(4,logaudit["sensor_count"])
        self.assertEqual(4,len(sensors))
        self.assertEqual(1,len(sensors["front_door"]))
        self.assertEqual("Open",sensors["front_door"][0][0])
        self.assertEqual("Motion",sensors["zone_1"][0][0])
        self.assertEqual(w.START+timedelta(minutes=30),
                         sensors["front_door"][0][1])

    def test_06_fixed_windows_coactivity_only_never_claims_event_matching(self):
        times=[time(14,31)]*33
        fixture={
            "schema":"previous-real-source-readiness-fixture",
            "upstream_git_commit":source.UPSTREAM_COMMIT,
            "source_files_verified_by_git_blob_sha1_and_sha256":{
                "pos":{"sha256":"sha256:pos-fixture"},
                "tapo":{"sha256":"sha256:tapo-fixture"}},
            "pos":{"selected_shift_rows_with_order_time":33},
        }
        with patch.object(w.src,"build",return_value=fixture),\
             patch.object(w,"pos_shift_clock_times",return_value=times):
            result=w.compare(b"fixture-pos",toy_tapo().encode())
        self.assertEqual(33,result["pos_orders_selected"])
        self.assertEqual(33,result["pos_orders_in_primary_windows"])
        self.assertEqual(33,result["sensor_rows_per_window_with_pos_assumed_local"][0][
            "pos_orders_assuming_Budapest_local_clock"])
        self.assertEqual(0,result["pos_orders_outside_primary_windows"])
        self.assertTrue(result["no_pos_order_tapo_event_pairing_attempted"])
        self.assertTrue(result["no_causality_or_service_event_inferred"])
        self.assertFalse(result["cross_clock_offset_calibrated"])
        self.assertFalse(result["POS_clock_timezone_from_raw_metadata_certified"])
        self.assertEqual("NOT_RUN",result["G5"])
        self.assertEqual("NOT_CREATED",result["F5_reserve"])
        body=json.dumps(result)
        for forbidden_key in ("case_id","order_ID","event_id","resource_id",
                              "device_id","raw_order_time"):
            self.assertNotIn(json.dumps(forbidden_key)+":",body)

    def test_07_sensor_count_change_cannot_fake_raw_audit(self):
        corrupted=toy_tapo().replace("sum: 1, logs:", "sum: 2, logs:",1)
        # Mismatch of reported snapshot sum is a diagnostic, not by itself
        # proof of event loss; the original parser makes it observable.
        sensors,meta=w.raw_sensor_times(corrupted)
        self.assertFalse(meta["sensor_groups"][0]["returned_equals_reported_sum"])
        self.assertEqual(4,len(sensors))


if __name__=="__main__":
    unittest.main()
