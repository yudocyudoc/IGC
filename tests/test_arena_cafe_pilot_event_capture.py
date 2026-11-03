"""F5 instrumentation contract only: synthetic EV01 smoke + strict negatives.

These tests are NOT empirical sensor calibration. A synthetic one-clock
fixture validates engineering, not real event accuracy or a F5 reserve.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import csv
from pathlib import Path
import tempfile
import unittest

from scripts.arena_cafe import ev01
from scripts import arena_event_observability as obs
from scripts.arena_cafe import pilot_event_capture as pilot


def known_synthetic_events(cutoff="10"):
    raw,_=ev01.trace_generator()
    visible=obs.project_events(raw,"FULL")
    events=[]
    for i,row in enumerate(visible):
        if Q(row["t_minutes_exact"])>=Q(cutoff):
            continue
        stage=row.get("stage") or ""
        events.append({
            "event_id":f"syn{i}",
            "case_id":row["case_id"],
            "visit_id":f"{row['case_id']}_{stage}" if stage else "",
            "event_type":row["event_type"],
            "stage":stage,
            "resource_id":row.get("resource_id") or "",
            "t_minutes_exact":row["t_minutes_exact"],
            "source":row["source"],
            "clock_id":"synthetic-evaluator-clock",
            "sensor_id":"synthetic-direct" if stage else "synthetic-pos",
        })
    return events


def build(events,cutoff="10",pairs=()):
    return pilot.build(events,cutoff_minutes_exact=cutoff,
                       source_context="synthetic_fixture",pairs=pairs)


class PilotContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events=known_synthetic_events()

    def test_00_observational_ev01_preparation_aggregate_parity(self):
        report=build(self.events)
        self.assertEqual("DESCRIPTIVE_SAME_DECLARED_CLOCK_ONLY",
                         report["stage_aggregates_status"])
        prep=report["stage_completed_only_descriptives"]["preparacion"]
        self.assertEqual(9,prep["completed_services_pre_cutoff"])
        self.assertEqual("15/17",prep["mean_service_minutes_exact"])
        self.assertEqual("1204/765",
                         prep["mean_wait_of_completed_minutes_exact"])
        self.assertEqual(15,report["n_cases_created"])
        self.assertEqual(1,report["observed_entry_route_variants"]["n_variants"])

    def test_01_no_calibration_from_synthetic_exact_timestamps(self):
        report=build(self.events)
        self.assertFalse(report["instrumental_error_calibrated"])
        self.assertIsNone(report["empirical_compatibility_tolerance"])
        self.assertFalse(report["physical_clock_accuracy_known"])
        self.assertFalse(report["clock_resolution_known"])
        self.assertEqual("NO_INDEPENDENT_PAIRED_OBSERVATIONS",
                         report["paired_observation_status"])
        self.assertEqual("ENGINEERING_INGEST_ONLY_NOT_CALIBRATION",
                         report["F5_pilot_capture_status"])
        self.assertEqual("NOT_RUN",report["G4"])
        self.assertEqual("NOT_RUN",report["G5"])

    def test_02_cutoff_censors_incomplete_visits_not_faked_finishes(self):
        rows=known_synthetic_events("4")
        report=build(rows,"4")
        self.assertLess(report["n_delivered_pre_cutoff"],15)
        censored=sum(
            x["censored_waiting_at_cutoff"]+
            x["censored_in_service_at_cutoff"]
            for x in report["stage_completed_only_descriptives"].values())
        self.assertGreater(censored,0)
        self.assertTrue(all(x["selection"]==
            "ONLY_SERVICES_COMPLETED_BEFORE_CUTOFF" for x in
            report["stage_completed_only_descriptives"].values()))

    def test_03_no_future_or_equal_cutoff_event(self):
        rows=deepcopy(self.events)
        rows[0]["t_minutes_exact"]="10"
        with self.assertRaisesRegex(ValueError,"PILOT_OUTSIDE_CUTOFF"):
            build(rows)

    def test_04_missing_service_start_cannot_count_completion(self):
        rows=deepcopy(self.events)
        row=next(x for x in rows if x["event_type"]=="servicio_inicio"
                 and x["stage"]=="preparacion")
        rows.remove(row)
        with self.assertRaisesRegex(ValueError,
                                    "PILOT_INCOMPLETE_VISIT_INVALID_BOUNDARIES"):
            build(rows)

    def test_05_nonphysical_kds_click_not_physical_service(self):
        rows=deepcopy(self.events)
        row=next(x for x in rows if x["event_type"]=="servicio_fin")
        row["source"]="kds_click"
        with self.assertRaisesRegex(ValueError,
                                    "PILOT_ONLY_DIRECT_PHYSICAL_STAGE_EVENTS"):
            build(rows)

    def test_06_resource_collisions_are_not_hidden_by_case_sorting(self):
        rows=deepcopy(self.events)
        # Both caja servers operate concurrently in the original EV01 trace.
        for item in rows:
            if item["resource_id"]=="caja-r2":
                item["resource_id"]="caja-r1"
        with self.assertRaisesRegex(ValueError,
                                    "PILOT_OVERLAPPING_SERVICE_ON_ONE_RESOURCE"):
            build(rows)

    def test_07_cross_clock_data_withhold_stage_means_and_routes(self):
        rows=deepcopy(self.events)
        for row in rows:
            if row["stage"]=="preparacion":
                row["clock_id"]="other-physical-clock"
        report=build(rows)
        self.assertEqual("MULTI_CLOCK_ALIGNMENT_NOT_ESTABLISHED",
                         report["cross_clock_alignment"])
        self.assertEqual("WITHHELD_NO_SHARED_CLOCK_OR_PHYSICAL_EVENTS",
                         report["stage_aggregates_status"])
        self.assertEqual({},report["stage_completed_only_descriptives"])
        self.assertIsNone(report["observed_entry_route_variants"]["n_variants"])
        self.assertEqual("WITHHELD_CLOCK_ALIGNMENT_UNPROVEN",
                         report["observed_entry_route_variants"]["status"])

    def test_08_two_sensor_recordings_are_not_certified_error(self):
        primary=self.events[0]
        pair={
            "pair_id":"p1","primary_event_id":primary["event_id"],
            "secondary_sensor_id":"independent-second-sensor",
            "secondary_clock_id":"another-clock",
            "secondary_t_minutes_exact":
                str(Q(primary["t_minutes_exact"])+Q(1,100)),
        }
        report=build(self.events,pairs=[pair])
        self.assertEqual("1/100",
                         report["paired_max_abs_delta_minutes_exact"])
        self.assertEqual(1,report["paired_observation_count"])
        self.assertEqual("PAIRED_RAW_DIFFERENCES_NOT_ERROR_BOUNDS",
                         report["paired_observation_status"])
        self.assertFalse(report["instrumental_error_calibrated"])
        self.assertIsNone(report["empirical_compatibility_tolerance"])

    def test_09_same_sensor_is_not_independent_pair(self):
        primary=self.events[0]
        pair={
            "pair_id":"p1","primary_event_id":primary["event_id"],
            "secondary_sensor_id":primary["sensor_id"],
            "secondary_clock_id":"same-clock",
            "secondary_t_minutes_exact":primary["t_minutes_exact"],
        }
        with self.assertRaisesRegex(ValueError,
                                    "PILOT_SAME_SENSOR_NOT_INDEPENDENT"):
            build(self.events,pairs=[pair])

    def test_10_repeat_stage_is_valid_if_distinct_visit_id(self):
        def e(event_id,kind,t,visit="",stage="",resource=""):
            return {
                "event_id":event_id,"case_id":"case42","visit_id":visit,
                "event_type":kind,"stage":stage,"resource_id":resource,
                "t_minutes_exact":str(t),
                "source":"pos" if not stage else "instrumentacion_fisica",
                "clock_id":"one-clock","sensor_id":
                    "pos-sensor" if not stage else "physical-sensor",
            }
        rows=[
            e("a","pedido_creado","0"),
            e("b","etapa_entrada","0","v1","preparacion"),
            e("c","servicio_inicio","0","v1","preparacion","r1"),
            e("d","servicio_fin","1","v1","preparacion","r1"),
            e("e","etapa_entrada","1","v2","preparacion"),
            e("f","servicio_inicio","1","v2","preparacion","r1"),
            e("g","servicio_fin","2","v2","preparacion","r1"),
            e("h","pedido_entregado","3"),
        ]
        report=build(rows,"4")
        self.assertEqual(2,report["stage_completed_only_descriptives"][
            "preparacion"]["completed_services_pre_cutoff"])
        self.assertEqual([{"observed_route":["preparacion","preparacion"],
                           "cases":1}],
                         report["observed_entry_route_variants"]["counts"])
        self.assertEqual("NOT_ASSESSED",
                         report["PM_incremental_beyond_B1_B2"])

    def test_11_csv_contract_is_strict_and_lossless(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"events.csv"
            with path.open("w",newline="",encoding="utf-8") as out:
                writer=csv.DictWriter(out,fieldnames=pilot.EVENT_FIELDS)
                writer.writeheader()
                writer.writerows(self.events)
            read=pilot.read_rows(path,pilot.EVENT_FIELDS)
            self.assertEqual(self.events,read)
            with path.open("w",newline="",encoding="utf-8") as out:
                out.write("case_id,event_type\na,b\n")
            with self.assertRaisesRegex(ValueError,
                                        "PILOT_CSV_HEADERS_NOT_EXACT"):
                pilot.read_rows(path,pilot.EVENT_FIELDS)

    def test_12_only_evaluator_sees_physical_events(self):
        report=build(self.events)
        raw=str(report)
        self.assertNotIn("O001",raw)
        self.assertNotIn("event_id",raw)
        self.assertTrue(report["no_parameter_grid_or_new_model_or_pm"])
        self.assertTrue(report["no_provider_calls"])
        self.assertEqual("PARTIAL",report["A3"])


if __name__=="__main__":
    unittest.main()
