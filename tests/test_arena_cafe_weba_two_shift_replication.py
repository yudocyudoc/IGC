"""WEBA cross-shift replication contracts; synthetic parser fixtures only."""
from __future__ import annotations

from datetime import datetime, time, timezone, timedelta
from unittest.mock import patch
from zipfile import ZipFile
from io import BytesIO
import json
import unittest

from scripts.arena_cafe import weba_two_shift_replication as r


def tiny_workbook():
    ns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    data=[f'<worksheet xmlns="{ns}"><sheetData><row r="1">']
    headings=("order_id","order_date","order_time","time_of_day")
    for j,val in enumerate(headings):
        col=chr(65+j)
        data.append(f'<c r="{col}1" t="inlineStr"><is><t>{val}</t></is></c>')
    data.append("</row>")
    records=[
        ("private1","20240304","14:31:00","evening"),
        ("private2","20240304","","evening"),
        ("private3","20240308","14:40:00","evening"),
        ("private4","20240308","09:00:00","morning"),
        ("private5","20240223","14:11:00","evening"),
    ]
    for i,values in enumerate(records,start=2):
        data.append(f'<row r="{i}">')
        for j,val in enumerate(values):
            col=chr(65+j)
            data.append(
                f'<c r="{col}{i}" t="inlineStr"><is><t>{val}</t></is></c>')
        data.append("</row>")
    data.append("</sheetData></worksheet>")
    raw=BytesIO()
    with ZipFile(raw,"w") as z:
        z.writestr("xl/worksheets/sheet1.xml","".join(data))
    return raw.getvalue()


def fake_log():
    rows=[]
    for i,name in enumerate(r.SENSORS):
        model="T110" if name=="front_door" else "T100"
        kind="Open" if name=="front_door" else "Motion"
        ts=1709568000-i*60
        rows.append(
            f"2024-03-04T17:00:00Z INFO > Found {model} child"
            f" device with nickname: {name}, id: redacted,"
            " last 50 trigger logs: TriggerLogsResult"
            f" {{ start_id: {i+1}, sum: 1,"
            f" logs: [{kind} {{ id: {i+1}, timestamp: {ts} }}] }}"
        )
    return "\n".join(rows).encode()


class ReplicationContracts(unittest.TestCase):
    def test_00_metadata_selection_and_frozen_dates(self):
        self.assertEqual(("20240304_evening","20240308_evening"),
             tuple(x["name"] for x in r.SHIFTS))
        self.assertEqual("d6841669e544579547c94b7ce1e8613bbd6b3a39",
                         r.UPSTREAM_COMMIT)
        self.assertEqual(30,r.WINDOW_MINUTES)
        self.assertEqual(10,r.N_BINS)
        for x in r.SHIFTS:
            self.assertEqual("evening",x["name"].split("_")[-1])
            self.assertTrue(x["date"]<"2024-03-31")

    def test_01_missing_or_changed_selected_external_files_fails(self):
        with self.assertRaisesRegex(ValueError,
            "WEBA_SOURCE_NOT_PINNED_GIT_BLOB"):
            r.verify_sources(b"not-verified",{x["name"]:b"x" for x in r.SHIFTS})
        with patch.object(r.src,"verify_pinned",return_value={}):
            with self.assertRaisesRegex(ValueError,
                "WEBA_REPL_SELECTION_NOT_PREDECLARED"):
                r.verify_sources(b"synthetic",{
                    "20240308_evening":b"x","20240313_evening":b"x"})
            with self.assertRaisesRegex(ValueError,
                "WEBA_REPL_SOURCE_HASH_OR_SIZE_CHANGED"):
                r.verify_sources(b"synthetic",{
                    x["name"]:b"mutated sensor bytes" for x in r.SHIFTS})

    def test_02_pos_rows_include_missing_clocks_not_other_shifts(self):
        found=r.pos_time_fields(tiny_workbook())
        self.assertEqual(2,found["20240304_evening"]["total"])
        self.assertEqual(1,found["20240304_evening"]["missing"])
        self.assertEqual([time(14,31)],found["20240304_evening"]["clocks"])
        self.assertEqual(1,found["20240308_evening"]["total"])
        self.assertEqual(1,len(found["20240308_evening"]["clocks"]))
        serialized=json.dumps({
            k:{"total":v["total"],"missing":v["missing"]}
            for k,v in found.items()})
        self.assertNotIn("private",serialized)

    def test_03_exact_half_open_boundaries_and_outside_are_conserved(self):
        first=datetime(2024,3,4,13,tzinfo=timezone.utc)
        self.assertEqual(0,r.index_for(first,first))
        self.assertEqual(1,r.index_for(first+timedelta(minutes=30),first))
        self.assertEqual(9,r.index_for(first+timedelta(minutes=299),first))
        self.assertIsNone(r.index_for(first+timedelta(hours=5),first))
        self.assertIsNone(r.index_for(first-timedelta(seconds=1),first))
        bins,out=r.histogram([
            first,first+timedelta(minutes=30),
            first+timedelta(hours=5)],first)
        self.assertEqual([1,1]+[0]*8,bins)
        self.assertEqual(1,out)
        with self.assertRaisesRegex(ValueError,"WEBA_REPL_NAIVE_TIMESTAMP"):
            r.index_for(datetime(2024,3,4,13),first)

    def test_04_without_clock_calibration_no_Poisson_or_service_claim(self):
        shift=r.SHIFTS[0]
        data={
            "total":1,"missing":0,
            "clocks":[time(14,31)]}
        item=r.characterize_shift(shift,data,fake_log())
        self.assertEqual(1,item["pos_local_assumption_in_windows"])
        self.assertEqual(1,item["pos_UTC_as_written_sensitivity_in_windows"])
        self.assertEqual(0,item["pos_rows_without_clock"])
        self.assertFalse(item["pos_tapo_independent_clock_calibration_proven"])
        self.assertFalse(item["case_to_sensor_event_link_proven"])
        self.assertFalse(item["sensor_event_as_customer_arrival_or_service_finish"])
        self.assertEqual(10,len(item["half_hour_windows"]))
        self.assertEqual(1,item["pos_rows_in_shift"])
        self.assertNotIn("private",json.dumps(item))

    def test_05_empty_pos_is_not_replaced_with_another_turn(self):
        item=r.characterize_shift(
            r.SHIFTS[1],{"total":0,"missing":0,"clocks":[]},fake_log())
        self.assertEqual(0,item["pos_rows_in_shift"])
        self.assertEqual(0,item["bins_with_POS_orders"])
        self.assertTrue(item["bins_with_sensor_pulses_but_zero_pos_orders"]>0)

    def test_06_wrong_clock_ordinal_cannot_be_fit_by_switching_timezone(self):
        shift=r.SHIFTS[0]
        item=r.characterize_shift(shift,{
            "total":1,"missing":0,"clocks":[time(18,30)]},fake_log())
        self.assertEqual(1,item["pos_local_assumption_in_windows"])
        self.assertEqual(0,item["pos_UTC_as_written_sensitivity_in_windows"])
        self.assertEqual(1,item["pos_UTC_as_written_sensitivity_outside_windows"])

    def test_07_aggregate_output_contains_no_case_device_or_event_ids(self):
        with patch.object(r,"verify_sources",return_value={
            x["name"]:{"git_blob_sha1":"verified-fixture","bytes":1}
            for x in r.SHIFTS}):
            with patch.object(r,"pos_time_fields",return_value={
                x["name"]:{"total":1,"missing":0,"clocks":[time(14,31)]}
                for x in r.SHIFTS}):
                got=r.build(b"fixture",{x["name"]:fake_log()
                                         for x in r.SHIFTS})
        self.assertEqual(2,len(got["results"]))
        self.assertEqual("NOT_RUN",got["G5"])
        self.assertEqual("NOT_CREATED",got["F5_independent_reserve"])
        self.assertTrue(got["no_raw_person_order_device_or_event_identifiers_exported"])
        self.assertTrue(got["source_same_business_as_development_not_independent_business"])
        serialized=json.dumps(got)
        for forbidden in ('"order_ID":','"case_id":','"device_id":',
                          '"resource_id":','"event_id":','"raw_order_time":'):
            self.assertNotIn(forbidden,serialized)


if __name__=="__main__":
    unittest.main()
