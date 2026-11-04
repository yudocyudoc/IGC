"""WEBA bounded-window safeguards; small timestamp parser fixtures only.

These are NOT fabricated cafeteria physics. Live external-source integration
uses the original SHA-pinned five WEBA files in GitHub Actions.
"""
from __future__ import annotations

from datetime import datetime,timezone,timedelta
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile
import json
import unittest

from scripts.arena_cafe import weba_shift_bounded_windows as w


def dt(day,hour,minute=0,second=0):
    return datetime(2024,3,day,hour,minute,second,tzinfo=timezone.utc)


def shift_fixture(day=8,early=True):
    if day==8:
        s,e=dt(8,13,33),dt(8,17,41)
        dump_start=dt(8,17,37)
        dump_end=dt(8,17,37,2)
    elif day==4:
        s,e=dt(4,13,54),dt(4,17,50)
        dump_start=dt(4,17,50,1)
        dump_end=dt(4,17,50,3)
    else:
        raise ValueError("fixture")
    return {
        "UTC_boundaries_under_UNVERIFIED_local_clock_assumption":[
            s.isoformat(),e.isoformat()],
        "Tapo":{
            "Tapo_snapshot_time_utc_first":dump_start.isoformat(),
            "Tapo_snapshot_time_utc_last":dump_end.isoformat(),
            "total_events_in_snapshot":4,
        },
    }


def pos_workbook():
    ns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    records=[
        ("order_id","order_date","order_time","time_of_day"),
        ("PRIVATE_20240223","20240223","0.75","evening"),
        ("PRIVATE_20240304","20240304","0.7","evening"),
        ("PRIVATE_20240308","20240308","0.7","evening"),
        ("PRIVATE_morning","20240308","0.33","morning"),
    ]
    data=[f'<worksheet xmlns="{ns}"><sheetData>']
    for rownum,vals in enumerate(records,1):
        data.append(f'<row r="{rownum}">')
        for col,v in enumerate(vals):
            letter=chr(65+col)
            data.append(
                f'<c r="{letter}{rownum}" t="inlineStr">'
                f'<is><t>{v}</t></is></c>')
        data.append("</row>")
    data.append("</sheetData></worksheet>")
    file=BytesIO()
    with ZipFile(file,"w") as z:
        z.writestr("xl/worksheets/sheet1.xml","".join(data))
    return file.getvalue()


class BoundedWEBAContract(unittest.TestCase):
    def test_00_overlap_half_open_and_never_negative(self):
        a,b=dt(8,13),dt(8,13,30)
        self.assertEqual(1800,w.overlap_seconds(a,b,a,b))
        self.assertEqual(0,w.overlap_seconds(a,b,b,dt(8,14)))
        self.assertEqual(0,w.overlap_seconds(a,b,dt(8,14),dt(8,15)))
        self.assertEqual(600,w.overlap_seconds(
            a,b,dt(8,13,20),dt(8,14)))
        with self.assertRaisesRegex(ValueError,
                                    "WEBA_BOUNDED_INVALID_INTERVAL"):
            w.overlap_seconds(b,a,a,b)

    def test_01_POS_selection_is_by_date_and_shift_never_device(self):
        found=w.pos_receipt_timestamps(pos_workbook())
        self.assertEqual([1,1,1],
                         [len(found[x]) for x in w.instrument.SHIFTS])
        self.assertEqual(dt(8,15,48),found["20240308_evening"][0][0])
        self.assertEqual(dt(8,16,48),found["20240308_evening"][0][1])
        self.assertNotIn("PRIVATE",repr(found))

    def test_02_category_classification_uses_shift_not_grid(self):
        start,end=dt(8,13,33),dt(8,17,41)
        export=dt(8,17,37,2)
        events=[dt(8,13),start,dt(8,14),dt(8,17,39),
                end,dt(8,18)]
        c=w.classify(events,start,end,export)
        self.assertEqual({
            "before_shift":1,
            "inside_shift_pre_export":2,
            "inside_shift_after_export":1,
            "after_shift":2},c)

    def _shift_report(self,day,events,orders=None):
        shift=shift_fixture(day)
        sensor={key:list(events.get(key,[])) for key in w.SENSORS}
        count=sum(len(s) for s in sensor.values())
        shift["Tapo"]["total_events_in_snapshot"]=count
        if orders is None:
            orders=[]
        with patch.object(w,"tapo_sensor_timestamps",return_value=sensor),\
             patch.object(w.instrument,"tapo_log_audit",
                          return_value={"total_events_in_snapshot":count}):
            return w.shift_report(
                "20240308_evening" if day==8 else "20240304_evening",
                shift,"fixture-tapo",orders)

    def test_03_early_export_censors_shift_tail_without_inferring_idleness(self):
        c=self._shift_report(8,{
            "front_door":[dt(8,15)],
            "front_door_m":[dt(8,15)],
            "zone_1":[dt(8,15)],
            "zone_2":[dt(8,15)]},
            orders=[
                (dt(8,13,35),dt(8,14,35)),
                (dt(8,17,39),dt(8,18,39))])
        self.assertAlmostEqual(3.9666666666667,c[
            "shift_minutes_AFTER_latest_Tapo_export_cannot_have_been_collected"],5)
        self.assertEqual(1,c["POS_received_orders_Budapest_assumption"][
            "inside_shift_after_export"])
        self.assertTrue(c["half_hour_cells"][9][
            "minutes_inside_shift_after_last_Tapo_export_PROVABLY_UNOBSERVED"]>3)
        self.assertEqual("SHIFT_PARTLY_AFTER_TAPO_EXPORT_CANNOT_OBSERVE_TAIL",
                         c["half_hour_cells"][9]["temporal_evidence_status"])
        self.assertFalse(c["Tapo_coverage_continuity_verified"])
        self.assertFalse(c["POS_cross_device_time_sync_verified"])
        self.assertTrue(all(row["no_sensor_signal_does_NOT_mean_IDLE"]
                            for row in c["half_hour_cells"]))
        self.assertEqual(248,c["shift_duration_minutes"])

    def test_04_export_after_end_is_NOT_certification_of_coverage(self):
        c=self._shift_report(4,{"zone_2":[dt(4,13,55)]})
        self.assertEqual(0,c[
            "shift_minutes_AFTER_latest_Tapo_export_cannot_have_been_collected"])
        self.assertFalse(c["Tapo_coverage_continuity_verified"])
        self.assertEqual("OUTSIDE_DECLARED_SHIFT_NOT_IN_SAMPLE",
                         c["half_hour_cells"][0]["temporal_evidence_status"])
        self.assertEqual(9,c["count_half_hour_cells_with_some_declared_shift"])
        self.assertEqual(236,c["shift_duration_minutes"])

    def test_05_zero_sensor_events_never_equates_to_unoccupied(self):
        c=self._shift_report(8,{})
        self.assertEqual(0,c[
            "count_declared_shift_cells_with_Tapo_and_zero_POS"])
        self.assertTrue(any(x["temporal_evidence_status"]==
            "FULL_HALF_HOUR_DECLARED_SHIFT_UNKNOWN_SENSOR_CONTINUITY"
            for x in c["half_hour_cells"]))
        self.assertFalse(c["Tapo_coverage_continuity_verified"])

    def test_06_invalid_event_after_export_is_rejected_not_hidden(self):
        with self.assertRaisesRegex(ValueError,
            "WEBA_BOUNDED_SENSOR_EVENT_AFTER_DUMP_INVALID"):
            self._shift_report(8,{"zone_1":[dt(8,17,39)]})

    def test_07_preserve_original_pos_metadata_and_privacy(self):
        c=self._shift_report(8,{"zone_1":[dt(8,14)]},
            orders=[(dt(8,14),dt(8,15))])
        j=json.dumps(c)
        for forbidden in ('"order_ID":','"device_id":','"case_id":',
                          '"event_id":','"raw_order_time":','"resource_id":'):
            self.assertNotIn(forbidden,j)
        self.assertEqual(10,len(c["half_hour_cells"]))
        self.assertEqual(1,c["POS_received_orders_Budapest_assumption"][
            "inside_shift_pre_export"])
        self.assertEqual(1,c["Tapo_pulses_four_sensors_by_relative_shift_position"][
            "zone_1"]["inside_shift_pre_export"])

    def test_08_shift_boundary_events_excluded_in_half_open_window(self):
        start,end=dt(8,13,33),dt(8,17,41)
        events=[start,end]
        assert w.classify(events,start,end,dt(8,17,37))=={
            "before_shift":0,"inside_shift_pre_export":1,
            "inside_shift_after_export":0,"after_shift":1}
        result=w.binning(events,dt(8,13),dt(8,18),start,end)
        self.assertEqual(1,sum(result))


if __name__=="__main__":
    unittest.main()
