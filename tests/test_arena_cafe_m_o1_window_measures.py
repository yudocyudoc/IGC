"""F3 evaluator-only finite-window event-count versus native E1 fluid-mass audit.

Fixtures prove bookkeeping, not provenance of native computation, sensor
accuracy, a time-alignment model, or a discrete-event observation law.
F3 separately reaudits the real OpenModelica CSV before it calls this helper.
"""
from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from fractions import Fraction as Q
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import (
    ev01,evidence,native_pos_scenario,
    m_o1_capacity_certificate as cap,
    m_o1_window_measures as windows)
from scripts.arena_cafe.native_handoff import need
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError


class WindowEventMeasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw,snaps=ev01.trace_generator()
        ev01.verify_des_parity(snaps)
        full=obs.project_events(raw,"FULL")
        cls.full=[
            {**row,"event_seq":i}
            for i,row in enumerate(r for r in full
                if Q(r["t_minutes_exact"])<Q(10))]
        cls.views=evidence.build(
            obs.project_events(raw,"POS"),
            obs.project_events(raw,"FULL"))["views"]
        cls.o1=cls.views["O1"]
        _,_,manifest=native_pos_scenario.build(cls.o1,"M","O1")
        cls.candidate=manifest["candidate"]
        cls.certificate=cap.certificate(cls.o1,cls.candidate)

    def _write_csv(self,path,completed_per_hour="20"):
        source=[x["id"] for x in self.candidate["ast"]["instances"]
                if x["role"]=="source"][0]
        prep=[x["id"] for x in self.candidate["ast"]["instances"]
              if x["role"]=="preparation"][0]
        cols=["time","deliveredTotal",source+".outflow",prep+".completed"]
        rows=[{
            "time":format(t/60,".17g"),
            "deliveredTotal":str(t/2),
            source+".outflow":"60",
            prep+".completed":(completed_per_hour(t)
                if callable(completed_per_hour) else completed_per_hour),
        } for t in range(11)]
        with Path(path).open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=cols)
            writer.writeheader()
            writer.writerows(rows)
        return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def _run(self,path,sha,full=None,visible=None,cert=None):
        return windows.compare(
            visible or self.o1,full if full is not None else self.full,
            self.candidate,cap.REGISTRY,path,sha,
            self.certificate if cert is None else cert)

    def test_00_actual_known_ev01_counts_and_five_window_fluid_integrals(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            r=self._run(path,sha)
        self.assertEqual(5,len(r["windows"]))
        self.assertEqual([["0","2"],["2","4"],["4","6"],
                          ["6","8"],["8","10"]],
                         [x["window_minutes_half_open"] for x in r["windows"]])
        self.assertEqual(9,r["physical_total_completed_pre_cutoff"])
        self.assertEqual(9,sum(x["observed_discrete_prep_completions"]
                               for x in r["windows"]))
        self.assertAlmostEqual(10/3,r["native_continuous_prep_integral_numeric"],
                               places=7)
        self.assertTrue(all(x["nominal_E1_max_mass_exact"]=="2/3"
                            for x in r["windows"]))
        self.assertTrue(all(abs(x[
            "native_e1_integrated_continuous_readyorder_mass_numeric"]-2/3)<1e-7
            for x in r["windows"]))
        self.assertGreater(r["physical_censored_in_service_at_cutoff"],0)

    def test_01_accurately_separates_physical_ledger_and_unverified_fluid_bridge(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            r=self._run(path,sha)
        self.assertFalse(r["unit_identity_empirically_verified"])
        self.assertFalse(r["exact_cutoff_mass_equality_empirically_verified"])
        self.assertFalse(r["temporal_alignment_uncertainty_calibrated"])
        self.assertTrue(r["difference_is_not_sensor_error_or_model_fit"])
        self.assertFalse(r["operator_sufficient_for_scientific_G3"])
        self.assertFalse(r["M_native_model_generated_or_selected_from_O1"])
        self.assertEqual("NOT_ESTABLISHED",r["G3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertEqual("NOT_TRIGGERED_EV01",r["PM14"])

    def test_02_window_boundaries_are_half_open_no_future_event(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            fake=deepcopy(self.full)
            extra={**fake[-1],"event_seq":len(fake),
                   "t_minutes_exact":"10"}
            fake.append(extra)
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_FUTURE_EVENTS_NOT_ALLOWED"):
                self._run(path,sha,full=fake)

    def test_02b_interior_boundaries_go_to_next_half_open_window(self):
        # The historical EV01 physical completions never fall exactly
        # on 2,4,6,8, so directly test the binning operator at the edge.
        exact=[Q(0),Q(2),Q(4),Q(6),Q(8),Q(10)-Q(1,100)]
        self.assertEqual(
            [1,1,1,1,2],
            windows.count_completed_by_half_open_windows(exact))
        self.assertEqual(
            [0,1,0,0,0],
            windows.count_completed_by_half_open_windows([Q(2)]))
        with self.assertRaisesRegex(ArenaContractError,
                                    "F3M_WINDOW_EVENT_OUTSIDE_HALF_OPEN_HORIZON"):
            windows.count_completed_by_half_open_windows([Q(10)])
        with self.assertRaisesRegex(ArenaContractError,
                                    "F3M_WINDOW_INVALID_GRID"):
            windows.count_completed_by_half_open_windows(
                [Q(1)],(Q(0),Q(2),Q(2)))

    def test_02c_censored_preparation_without_entry_is_rejected(self):
        # Remove ONLY the entry of a case in service but not completed
        # at t10. The completed-case O1 mean/count remain unchanged, so
        # the case-level censor audit—not O1 aggregation—must reject it.
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            fake=deepcopy(self.full)
            finished={r["case_id"] for r in fake
                      if r["event_type"]=="servicio_fin"
                      and r.get("stage")=="preparacion"}
            active=next(r["case_id"] for r in fake
                        if r["event_type"]=="servicio_inicio"
                        and r.get("stage")=="preparacion"
                        and r["case_id"] not in finished)
            fake=[r for r in fake
                  if not (r["case_id"]==active and
                          r["event_type"]=="etapa_entrada" and
                          r.get("stage")=="preparacion")]
            for i,r in enumerate(fake):r["event_seq"]=i
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_CENSOR_STATES_INVALID"):
                self._run(path,sha,full=fake)

    def test_02d_over_capacity_native_flux_is_rejected(self):
        # An authenticated CSV hash is not enough: a fabricated 30/h
        # constant signal must fail the original bounded-queue 20/h cap.
        with TemporaryDirectory() as temp:
            path=Path(temp)/"over-cap.csv"
            sha=self._write_csv(path,"30")
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_MODEL_FLUX_EXCEEDS_FIXED_E1_CAP"):
                self._run(path,sha)

    def test_02e_negative_flow_rejected_by_native_parser_first(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"negative.csv"
            sha=self._write_csv(path,"-5")
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_TRACE_NEGATIVE_MATERIAL"):
                self._run(path,sha)

    def test_02f_linearly_rising_flow_has_exact_piecewise_trapezoid_mass(self):
        # In contrast to the constant 20/h engineering fixture, this
        # independent ramp (2*t units/hour) exercises numeric integration
        # across different rates; it is NOT the OMC scientific trajectory.
        with TemporaryDirectory() as temp:
            path=Path(temp)/"linear-ramp.csv"
            sha=self._write_csv(path,lambda t:str(2*t))
            result=self._run(path,sha)
        expected=[Q(1,15),Q(1,5),Q(1,3),Q(7,15),Q(3,5)]
        actual=[w["native_e1_integrated_continuous_readyorder_mass_numeric"]
                for w in result["windows"]]
        for observed,reference in zip(actual,expected):
            self.assertAlmostEqual(observed,float(reference),places=7)
        self.assertAlmostEqual(
            result["native_continuous_prep_integral_numeric"],
            float(Q(5,3)),places=7)
        self.assertEqual([0,3,2,2,2],
            [w["observed_discrete_prep_completions"]
             for w in result["windows"]])
        self.assertFalse(result["exact_cutoff_mass_equality_empirically_verified"])

    def test_03_tampered_physical_times_rejected_by_original_o1_mean(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            fake=deepcopy(self.full)
            row=next(x for x in fake if x["event_type"]=="servicio_fin"
                     and x.get("stage")=="preparacion")
            row["t_minutes_exact"]=str(Q(row["t_minutes_exact"])+Q(1,100))
            with self.assertRaisesRegex(ArenaContractError,
                "F3M_WINDOW_PHYSICAL_COMPLETION_AGGREGATE_NOT_O1"):
                self._run(path,sha,full=fake)

    def test_04_wrong_native_csv_hash_is_rejected(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";self._write_csv(path)
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_UNVERIFIED_NATIVE_CSV_HASH"):
                self._run(path,"sha256:"+"0"*64)

    def test_05_uncertified_or_falsely_validated_bridge_is_rejected(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            counterfeit=deepcopy(self.certificate)
            counterfeit["bridge_empirically_verified"]=True
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_INVALID_OR_FALSELY_VALIDATED_BRIDGE"):
                self._run(path,sha,cert=counterfeit)
            counterfeit=deepcopy(self.certificate)
            counterfeit["semantic_bridge_audit"]["bridge_readiness"]="READY"
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_INVALID_OR_FALSELY_VALIDATED_BRIDGE"):
                self._run(path,sha,cert=counterfeit)

    def test_06_creation_time_changed_without_changing_O0_bin_is_rejected(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            fake=deepcopy(self.full)
            case=next(r["case_id"] for r in fake
                      if r["event_type"]=="pedido_creado")
            for row in fake:
                if row["case_id"]==case and row["event_type"] in (
                        "pedido_creado","pago_confirmado"):
                    row["t_minutes_exact"]=str(
                        Q(row["t_minutes_exact"])+Q(1,100))
            # O0/O1 aggregate checkpoints have not changed, but the
            # exact authorized POS case arrival and its identity did.
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_CASES_OR_TIMES_CHANGED"):
                self._run(path,sha,full=fake)

    def test_06b_delivery_moved_across_bin_fails_original_O1_counts(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            fake=deepcopy(self.full)
            row=next(r for r in fake if r["event_type"]=="pedido_entregado")
            self.assertLess(Q(row["t_minutes_exact"]),Q(19,2))
            row["t_minutes_exact"]="19/2"
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_WINDOW_FULL_POS_NOT_SAME_O1"):
                self._run(path,sha,full=fake)

    def test_07_no_private_timestamps_or_case_ids_in_public_summary(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            r=self._run(path,sha)
        serialized=json.dumps(r)
        self.assertNotIn("O001",serialized)
        self.assertNotIn("case_id",serialized)
        self.assertNotIn("resource_id",serialized)
        self.assertNotIn("servicio_inicio",serialized)
        self.assertTrue(r["no_private_case_timestamps_in_output"])
        self.assertTrue(r["no_full_event_log_given_to_native_M"])
        self.assertEqual("KNOWN_SYNTHETIC_EV01_EVALUATOR_ONLY_DEVELOPMENT",
                         r["origin"])

    def test_08_o0_cannot_inherit_the_o1_private_counts(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path)
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_CROSS_CONDITION"):
                self._run(path,sha,visible=self.views["O0"])

    def test_09_no_scientific_score_for_arbitrary_smoothing_or_rounded_masses(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.csv";sha=self._write_csv(path,"15")
            r=self._run(path,sha)
        self.assertAlmostEqual(Q(5,2),r["native_continuous_prep_integral_numeric"],
                               places=7)
        self.assertEqual("EXISTING_HJ_TRAPEZOID_ON_ORIGINAL_OMC_OUTPUT_NO_ROUNDING",
                         r["native_numeric_integration"])
        self.assertTrue(all(type(x[
            "native_e1_integrated_continuous_readyorder_mass_numeric"]) is float
            for x in r["windows"]))
        self.assertFalse(r["operator_sufficient_for_scientific_G3"])


if __name__=="__main__":
    unittest.main()
