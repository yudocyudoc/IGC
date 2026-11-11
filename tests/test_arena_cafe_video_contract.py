"""Contrato observacional v0.1: controles positivos y negativos, sin video."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.arena_cafe.validar_anotaciones_video_v0_1 import (
    ROOT, load_contracts, validate_file, validate_record
)


class VideoAnnotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator, cls.entries, cls.catalog = load_contracts()
        path = ROOT / "ejemplos_p031_p045_v0_1.jsonl"
        cls.path = path
        cls.records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def fails(self, row):
        return validate_record(row, self.validator, self.entries, self.catalog)

    def test_positive_seven(self):
        count, problems = validate_file(self.path)
        self.assertEqual(count, 7)
        self.assertEqual(problems, [])

    def test_kind_mismatch(self):
        row = copy.deepcopy(self.records[0]); row["kind"] = "episodio"
        self.assertTrue(self.fails(row))

    def test_unknown_code(self):
        row = copy.deepcopy(self.records[0]); row["event_code"] = "entrega_a_cliente"
        self.assertTrue(self.fails(row))

    def test_reverse_transition(self):
        row = copy.deepcopy(self.records[-1]); row["time"]["last_state_video_s"] = 2895
        self.assertTrue(self.fails(row))

    def test_missing_transition_image(self):
        row = copy.deepcopy(self.records[-1]); row["evidence"] = row["evidence"][:-1]
        self.assertTrue(self.fails(row))

    def test_incorrect_episode_end(self):
        row = copy.deepcopy(self.records[2]); row["time"]["end_video_s"] = [4000, 4002]
        self.assertTrue(self.fails(row))

    def test_silent_physical_clock_promotion(self):
        row = copy.deepcopy(self.records[2]); row["provenance"]["physical_clock_verified"] = True
        self.assertTrue(self.fails(row))

    def test_missing_minimum_count(self):
        row = copy.deepcopy(self.records[0]); row.pop("count_lower_bound")
        self.assertTrue(self.fails(row))

    def test_no_steam_from_pitcher_position(self):
        row = copy.deepcopy(self.records[2]); row["event_code"] = "vapor_activo_verificado"
        row["kind"] = "transicion"
        self.assertTrue(self.fails(row))

    def test_assembly_requires_object_trace(self):
        row = copy.deepcopy(self.records[-1]); row["event_code"] = "montaje_completo_verificado"
        self.assertTrue(self.fails(row))

    def test_source_sha256_mismatch(self):
        row = copy.deepcopy(self.records[0]); row["provenance"]["source_video_sha256"] = "0" * 64
        self.assertTrue(self.fails(row))

    def test_blank_evidence(self):
        row = copy.deepcopy(self.records[0]); row["evidence"] = []
        self.assertTrue(self.fails(row))


if __name__ == "__main__":
    unittest.main()
