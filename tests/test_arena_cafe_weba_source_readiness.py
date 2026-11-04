"""WEBA real-source reader tests: parser fixtures, NOT invented cafe worlds."""
from __future__ import annotations

import io
import json
from zipfile import ZipFile
import unittest

from scripts.arena_cafe import weba_source_readiness as weba


def tapo_fixture():
    groups=[
        ("T110","front_door",
         [("Open",1,1708700100),("KeepOpen",2,1708700090),
          ("Close",3,1708700080)]),
        ("T100","front_door_m",[("Motion",11,1708700110)]),
        ("T100","zone_1",[("Motion",21,1708700120)]),
        ("T100","zone_2",[("Motion",31,1708700130)]),
    ]
    rows=[]
    for model,name,entries in groups:
        encoded=", ".join(f"{kind} {{ id: {eid}, timestamp: {stamp} }}"
                          for kind,eid,stamp in entries)
        rows.append(
            f"2024-02-23T17:35:40.000Z INFO > Found {model}"
            f" child device with nickname: {name},"
            " id: SOME_DEVICE_ID, detected: true,"
            " last 50 trigger logs: TriggerLogsResult"
            f" {{ start_id: {entries[0][1]}, sum: {len(entries)},"
            f" logs: [{encoded}] }}"
        )
    return "\n".join(rows)


def inline_xlsx(rows):
    ns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    data=[f'<worksheet xmlns="{ns}"><sheetData>']
    for i,row in enumerate(rows,start=1):
        data.append(f'<row r="{i}">')
        for j,value in enumerate(row):
            if value is None: continue
            letter=chr(ord("A")+j)
            data.append(f'<c r="{letter}{i}" t="inlineStr"><is>'
                        f'<t>{value}</t></is></c>')
        data.append("</row>")
    data.append("</sheetData></worksheet>")
    stream=io.BytesIO()
    with ZipFile(stream,"w") as z:
        z.writestr("xl/worksheets/sheet1.xml","".join(data))
    return stream.getvalue()


class WEBAReaders(unittest.TestCase):
    def test_00_retain_keepopen_as_real_sensor_event_not_mislabelled_delivery(self):
        out=weba.parse_tapo_text(tapo_fixture())
        self.assertEqual(4,out["sensor_count"])
        self.assertEqual(6,out["total_returned_tapo_events"])
        self.assertEqual(1,out["keepopen_events_retained"])
        self.assertEqual(3,out["returned_records_per_selected_sensor"][
            "front_door"])
        self.assertTrue(out["no_per_order_dispatch_finished_event_found"])
        self.assertTrue(out["tapo_returned_sum_not_independently_coverage_certified"])

    def test_01_malformed_or_unknown_tapo_event_is_rejected_not_dropped(self):
        with self.assertRaisesRegex(ValueError,
                                      "WEBA_TAPO_UNPARSED_EVENT_TYPE"):
            weba.parse_tapo_text(tapo_fixture().replace(
                "KeepOpen {","UnknownState {"))
        with self.assertRaisesRegex(ValueError,
                                      "WEBA_TAPO_SENSOR_BLOCK_PARSE_INCOMPLETE"):
            weba.parse_tapo_text(tapo_fixture().replace(
                "sum: 1, logs:","sum: 1, broken_logs:",1))

    def test_02_duplicate_sensor_event_id_is_invalid(self):
        s=tapo_fixture().replace(
            "KeepOpen { id: 2","KeepOpen { id: 1")
        with self.assertRaisesRegex(ValueError,
            "WEBA_TAPO_DUPLICATE_EVENT_ID_IN_SENSOR_BLOCK"):
            weba.parse_tapo_text(s)

    def test_03_unreturned_history_is_not_estimated_as_coverage(self):
        s=tapo_fixture().replace(
            "sum: 3, logs:", "sum: 9, logs:")
        out=weba.parse_tapo_text(s)
        door=next(x for x in out["sensor_groups"]
                  if x["sensor_nickname"]=="front_door")
        self.assertFalse(door["returned_equals_reported_sum"])
        self.assertEqual(3,door["returned_event_records"])

    def test_04_git_blob_hash_and_bytes_are_pinned(self):
        with self.assertRaisesRegex(ValueError,
            "WEBA_SOURCE_NOT_PINNED_GIT_BLOB"):
            weba.verify_pinned("tapo",tapo_fixture().encode())
        with self.assertRaisesRegex(ValueError,"WEBA_UNAUTHORIZED_SOURCE"):
            weba.verify_pinned("body_hr",b"sample")

    def test_05_pos_sheet_counts_without_releasing_ids_or_values(self):
        wb=inline_xlsx([
            ("order_ID","order_time","order_date","time_of_day"),
            ("private1","5:00:00 PM","23/02/2024","evening"),
            ("private2",None,"23/02/2024","evening"),
            ("private3","8:00:00 AM","23/02/2024","morning"),
            ("private4","5:00:00 PM","22/02/2024","evening"),
        ])
        out=weba.inspect_pos_xlsx(wb)
        self.assertEqual(4,out["total_nonempty_order_rows"])
        self.assertEqual(3,out["rows_with_nonempty_order_time"])
        self.assertEqual(2,out["rows_matching_selected_evening_shift"])
        self.assertEqual(1,out["selected_shift_rows_with_order_time"])
        self.assertEqual(1,out["selected_shift_rows_without_order_time"])
        raw=json.dumps(out)
        self.assertNotIn("private1",raw)
        self.assertNotIn("5:00:00 PM",raw)
        self.assertNotIn("ordered_value",out)

    def test_06_excel_serial_dates_and_bad_sheet_are_handled_explicitly(self):
        self.assertEqual("2024-02-23",
           weba._normalize_date(str((__import__("datetime").datetime(
               2024,2,23)-__import__("datetime").datetime(
               1899,12,30)).days)))
        with self.assertRaisesRegex(ValueError,
                                   "WEBA_POS_MISSING_FIRST_WORKSHEET"):
            weba._xlsx_rows(inline_xlsx([]).replace(
                b"xl/worksheets/sheet1.xml",b"xl/worksheets/sheetX.xml"))


if __name__=="__main__":
    unittest.main()
