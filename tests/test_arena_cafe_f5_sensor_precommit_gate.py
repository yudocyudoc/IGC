"""F5 candidate-sensor freeze and abstention tests.

Synthetic EV01/F4 A and B are ONLY old engineering fixtures. They cannot
promote the t6 dispatch rule into evidence of prospective identification.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import csv
from fractions import Fraction as Q
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import ev01
from scripts.arena_cafe import f4_latent_downstream_symmetry as symmetry
from scripts.arena_cafe import f4_b2_processing_intervention as f4
from scripts.arena_cafe import pilot_event_capture as pilot
from scripts.arena_cafe import f5_sensor_precommit_gate as gate
from scripts.arena_v0_contract import digest


def old_pair_rows(config,*,cutoff=Q(6)):
    """Evaluator-side fixture only, strictly earlier than cutoff."""
    schedule=f4.analytic_intervals(config,ev01.ARRIVALS)
    f4.verify_des_snapshots(config,ev01.ARRIVALS,schedule)
    if config==ev01.config():
        f4.verify_original_full(schedule)
    rows=[]
    def add(case_id,kind,t,stage="",resource=""):
        rows.append({
            "event_id":f"old_fixture_{len(rows)}",
            "case_id":case_id,
            "visit_id":f"{case_id}_{stage}" if stage else "",
            "event_type":kind,
            "stage":stage,
            "resource_id":resource,
            "t_minutes_exact":str(t),
            "source":"instrumentacion_fisica" if stage else "pos",
            "clock_id":"old-evaluator-clock",
            "sensor_id":"old-synthetic-stage" if stage else "old-synthetic-pos",
        })
    for i,t in enumerate(ev01.ARRIVALS):
        if t<cutoff:
            add(f"O{i:03d}","pedido_creado",t)
    for record in schedule["despacho"]:
        for kind,time in (("etapa_entrada",record["entry"]),
                          ("servicio_inicio",record["start"]),
                          ("servicio_fin",record["finish"])):
            if time<cutoff:
                add(record["case_id"],kind,time,"despacho",
                    "" if kind=="etapa_entrada" else record["resource_id"])
    return rows


class FrozenSensorPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=gate.policy()
        cls.a,cls.b=symmetry.private_pair()
        cls.fixtures=[old_pair_rows(cls.a),old_pair_rows(cls.b)]

    def test_00_policy_hash_is_stable_and_prespecified_before_future_data(self):
        self.assertEqual(self.p,gate.policy())
        self.assertEqual(self.p["policy_sha256"],digest({
            k:v for k,v in self.p.items() if k!="policy_sha256"}))
        self.assertEqual(self.p["policy_sha256"],gate.validate_policy(self.p))
        self.assertFalse(self.p["selection_is_prospective_for_existing_EV01"])
        self.assertTrue(self.p["requires_independent_new_data_not_supplied_here"])
        self.assertEqual("despacho",self.p["stage"])
        self.assertEqual("6",self.p["cutoff_minutes_exact"])
        self.assertEqual("[0,6)",self.p["count_window"])

    def test_01_known_A_B_only_as_engineering_smoke(self):
        expected=(4,5)
        for rows,n in zip(self.fixtures,expected):
            r=gate.probe(self.p,rows,source_context="synthetic_fixture")
            self.assertEqual(n,r["physical_services_completed_pre_cutoff"])
            self.assertEqual(
                "CONDITIONAL_CONSISTENCY_WITH_ONE_KNOWN_PAIR_HYPOTHESIS",
                r["two_known_worlds_consistency_status"])
            self.assertEqual(1,len(r["compatible_prior_known_worlds"]))
            self.assertEqual("NOT_ESTABLISHED",
                             r["scientific_identification"])
            self.assertFalse(r["source_world_independent_of_EV01_verified"])
            self.assertFalse(r["pilot_event_capture_completeness_verified"])
            self.assertFalse(r["new_condition_O2_admitted_to_A1_arms"])
            self.assertEqual("NOT_CREATED",r["F5_independent_reserve"])

    def test_02_policy_changed_after_observation_is_rejected(self):
        changes=(
            {"cutoff_minutes_exact":"8"},
            {"stage":"preparacion"},
            {"closed_reference_hypotheses_only":{
                gate.A:5,gate.B:4}},
            {"selection_is_prospective_for_existing_EV01":True},
        )
        for patch in changes:
            with self.subTest(patch=patch):
                forged={**deepcopy(self.p),**patch}
                with self.assertRaisesRegex(
                    ValueError,"F5_SENSOR_POLICY_NOT_EXACT_FROZEN_CANDIDATE"):
                    gate.probe(forged,self.fixtures[0],
                               source_context="synthetic_fixture")

    def test_03_no_false_pos_only_sensor_observation(self):
        rows=[r for r in self.fixtures[0]
              if r["event_type"]=="pedido_creado"]
        out=gate.probe(self.p,rows,source_context="synthetic_fixture")
        self.assertIsNone(out["physical_services_completed_pre_cutoff"])
        self.assertEqual(
            "ABSTAIN_NO_USABLE_DISPATCH_COUNT_OR_SHARED_CLOCK",
            out["two_known_worlds_consistency_status"])
        self.assertEqual([],out["compatible_prior_known_worlds"])

    def test_04_cross_clock_stages_cannot_be_aligned(self):
        rows=deepcopy(self.fixtures[0])
        for r in rows:
            if r["stage"]=="despacho":
                r["clock_id"]="stage-unsynchronized"
        out=gate.probe(self.p,rows,source_context="synthetic_fixture")
        self.assertIsNone(out["physical_services_completed_pre_cutoff"])
        self.assertEqual("WITHHELD_NO_SHARED_CLOCK_OR_PHYSICAL_EVENTS",
                         out["stage_count_ingest_status"])
        self.assertEqual(
            "ABSTAIN_NO_USABLE_DISPATCH_COUNT_OR_SHARED_CLOCK",
            out["two_known_worlds_consistency_status"])

    def test_05_missing_finish_with_later_start_is_rejected_as_overlap(self):
        rows=deepcopy(self.fixtures[0])
        victim=next(r for r in rows
                    if r["stage"]=="despacho" and
                       r["event_type"]=="servicio_fin")
        rows.remove(victim)
        # An unfinished service ties up the resource until cutoff; a
        # subsequent start on that resource contradicts this record.
        with self.assertRaisesRegex(
             ValueError,"PILOT_OVERLAPPING_SERVICE_ON_ONE_RESOURCE"):
            gate.probe(self.p,rows,source_context="synthetic_fixture")

    def test_05b_plausibly_censored_missing_finish_stays_abstention(self):
        rows=deepcopy(self.fixtures[0])
        completions=sorted((Q(r["t_minutes_exact"]),r["case_id"])
                           for r in rows if
                           r["stage"]=="despacho" and
                           r["event_type"]=="servicio_fin")
        last_finish,last_case=completions[-1]
        # Simulate an incomplete, internally consistent observation:
        # the last completion vanishes and the next service no longer
        # starts in the truncated record. POS and queue entrances remain.
        rows=[r for r in rows if not (
            r["stage"]=="despacho" and
            ((r["case_id"]==last_case and
              r["event_type"]=="servicio_fin") or
             (r["event_type"] in ("servicio_inicio","servicio_fin")
              and Q(r["t_minutes_exact"])>=last_finish)))]
        out=gate.probe(self.p,rows,source_context="synthetic_fixture")
        self.assertEqual(3,out["physical_services_completed_pre_cutoff"])
        self.assertEqual("ABSTAIN_NEITHER_KNOWN_HYPOTHESIS_MATCHES",
                         out["two_known_worlds_consistency_status"])
        self.assertTrue(out["no_event_dropouts_identifiable_from_count_alone"])
        self.assertFalse(out["pilot_event_capture_completeness_verified"])

    def test_06_never_read_after_t6_or_boundary_event(self):
        rows=deepcopy(self.fixtures[0])
        rows[0]["t_minutes_exact"]="6"
        with self.assertRaisesRegex(
             ValueError,"PILOT_OUTSIDE_CUTOFF_FUTURE_OR_BOUNDARY"):
            gate.probe(self.p,rows,source_context="synthetic_fixture")
        rows=deepcopy(self.fixtures[0])
        rows[0]["t_minutes_exact"]="61/10"
        with self.assertRaisesRegex(
             ValueError,"PILOT_OUTSIDE_CUTOFF_FUTURE_OR_BOUNDARY"):
            gate.probe(self.p,rows,source_context="synthetic_fixture")

    def test_07_duplicate_or_invalid_physical_event_rejected_by_pilot(self):
        rows=deepcopy(self.fixtures[0])
        rows.append(deepcopy(rows[-1]))
        with self.assertRaisesRegex(ValueError,"PILOT_DUPLICATE_EVENT_ID"):
            gate.probe(self.p,rows,source_context="synthetic_fixture")
        rows=deepcopy(self.fixtures[0])
        row=next(r for r in rows if r["stage"]=="despacho")
        row["source"]="pos"
        with self.assertRaisesRegex(ValueError,
            "PILOT_ONLY_DIRECT_PHYSICAL_STAGE_EVENTS"):
            gate.probe(self.p,rows,source_context="synthetic_fixture")

    def test_08_declared_real_origin_never_attests_independence(self):
        out=gate.probe(self.p,self.fixtures[0],
                       source_context="real_pilot_declared")
        self.assertEqual(4,out["physical_services_completed_pre_cutoff"])
        self.assertEqual("real_pilot_declared",
                         out["source_context_declared_not_verified"])
        self.assertFalse(out["source_origin_independently_attested"])
        self.assertFalse(out["pilot_event_clock_calibration_verified"])
        self.assertFalse(out["source_world_independent_of_EV01_verified"])
        self.assertEqual("NOT_RUN",out["G4"])
        self.assertEqual("NOT_RUN",out["G5"])
        self.assertFalse(out["arm_models_or_inference_executed"])

    def test_09_score_alone_contains_no_private_case_event_records(self):
        out=gate.probe(self.p,self.fixtures[0],
                       source_context="synthetic_fixture")
        serialized=json.dumps(out,sort_keys=True)
        for forbidden in ("case_id","event_id","visit_id","resource_id",
                          "t_minutes_exact","event_type","sensor_id"):
            self.assertNotIn(json.dumps(forbidden)+":",serialized)
        for i in range(15):
            self.assertNotIn(json.dumps(f"O{i:03d}"),serialized)
        self.assertEqual(0,out["provider_calls"])

    def test_10_only_declared_source_context_and_hash_format_allowed(self):
        with self.assertRaisesRegex(ValueError,
                                    "F5_SENSOR_PROBE_SOURCE_CONTEXT_INVALID"):
            gate.probe(self.p,self.fixtures[0],
                       source_context="verified-independent-world")
        with self.assertRaisesRegex(ValueError,
                                    "F5_SENSOR_PROBE_INPUT_FILE_HASH_INVALID"):
            gate.probe(self.p,self.fixtures[0],
                       source_context="synthetic_fixture",
                       event_file_sha256="sha256:fake")

    def test_11_cli_freeze_and_probe_are_distinct_immutable_artifacts(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            policy_file=root/"policy.json"
            gate._write_new(policy_file,self.p)
            self.assertEqual(self.p,json.loads(policy_file.read_text()))
            with self.assertRaisesRegex(ValueError,"F5_SENSOR_REFUSE_OVERWRITE"):
                gate._write_new(policy_file,self.p)
            rows_file=root/"events.csv"
            with rows_file.open("w",encoding="utf-8",newline="") as stream:
                writer=csv.DictWriter(stream,fieldnames=pilot.EVENT_FIELDS)
                writer.writeheader();writer.writerows(self.fixtures[1])
            parsed=pilot.read_rows(rows_file,pilot.EVENT_FIELDS)
            out=gate.probe(json.loads(policy_file.read_text()),
                parsed,source_context="synthetic_fixture")
            result=root/"result.json"
            gate._write_new(result,out)
            self.assertEqual(5,json.loads(result.read_text())[
                "physical_services_completed_pre_cutoff"])
            self.assertEqual("NOT_CREATED",out["F5_independent_reserve"])

    def test_12_scoring_code_has_no_private_evaluator_imports(self):
        source=inspect.getsource(gate)
        tree=ast.parse(source)
        modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                modules += [n.name for n in node.names]
            elif isinstance(node,ast.ImportFrom):
                modules.append(node.module or "")
        self.assertNotIn("scripts.arena_cafe.ev01",modules)
        self.assertNotIn("scripts.arena_physical.des_engine",modules)
        self.assertNotIn("scripts.arena_cafe.f4_latent_downstream_symmetry",
                         modules)
        self.assertIn("scripts.arena_cafe",modules)
        self.assertTrue(self.p["stage_selection_fixed_not_reselected_after_probe"])


if __name__=="__main__":
    unittest.main()
