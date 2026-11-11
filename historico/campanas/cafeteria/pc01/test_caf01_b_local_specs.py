#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path

from caf01_b_local_specs import CONTRACT, bridge, check_script, digest
from scripts.arena_b_native_to_modelica import generate as legacy_generate
from scripts.arena_b_native_to_modelica import TranslationBlocked

FIXTURE = Path(__file__).parent / "fixtures/b_caf_local_synthetic_native.json"


class TestBLocalSpecs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def source(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_adapts_only_temporary_solver_specs_without_mutating_source(self):
        document = self.source()
        original = copy.deepcopy(document)
        name, source, report = bridge(document, self.contract)
        self.assertEqual(document, original)
        self.assertEqual(report["original_document_sha256"], digest(original))
        self.assertEqual(report["actual_native_specs"], original["model"]["specs"])
        self.assertEqual(report["historical_specs_used_only_for_translation"]["stopTime"], 8)
        self.assertEqual(report["caf_solver_specs_preserved_for_future_authorized_execution"]["dt"], 1/120)
        self.assertFalse(report["native_equations_modified"])
        self.assertEqual(report["native_simulation_runs"], 0)
        self.assertEqual(report["buffalo_provider_calls"], 0)
        self.assertIn("der(pending_work)", source)
        self.assertIn("lookup_pulse_shape(time)", source)
        self.assertTrue(name.startswith("BuffaloNative_"))

    def test_historical_translator_still_rejects_caf_specs(self):
        with self.assertRaisesRegex(TranslationBlocked, "NATIVE_SPECS_OUTSIDE_PINNED_G2_SCOPE"):
            legacy_generate(self.source())

    def test_delegates_exact_equations_to_historical_renderer(self):
        doc = self.source()
        _, code, report = bridge(doc, self.contract)
        proxy = copy.deepcopy(doc)
        proxy["model"]["specs"] = report["historical_specs_used_only_for_translation"]
        name2, code2, _ = legacy_generate(proxy)
        self.assertEqual(code, code2)
        self.assertEqual(report["modelica_class"], name2)

    def test_wrong_native_specs_rejected(self):
        for key, value in (("stopTime", 1), ("dt", 0.125),
                           ("timeUnits", "minute"), ("integrationMethod", "RK4"),
                           ("startTime", -1), ("dt", True), ("dt", float("nan"))):
            with self.subTest(key=key, value=str(value)):
                doc = self.source()
                doc["model"]["specs"][key] = value
                with self.assertRaisesRegex(TranslationBlocked, "B_LOCAL_|B_NATIVE_SPECS"):
                    bridge(doc, self.contract)

    def test_unknown_native_spec_field_rejected(self):
        doc = self.source()
        doc["model"]["specs"]["randomSeed"] = 17
        with self.assertRaisesRegex(TranslationBlocked, "B_LOCAL_SPECS_FIELDS"):
            bridge(doc, self.contract)

    def test_original_subtypes_still_blocked(self):
        doc = self.source()
        doc["model"]["variables"][0]["subType"] = "conveyor"
        with self.assertRaisesRegex(TranslationBlocked, "UNSUPPORTED_NATIVE_VARIABLE_FIELD"):
            bridge(doc, self.contract)

    def test_material_series_are_only_shape_mapped_not_verified(self):
        _, _, report = bridge(self.source(), self.contract)
        self.assertEqual(report["stocks"], 2)
        self.assertEqual(report["flows"], 2)
        self.assertEqual(report["series_mapping_status"],
                         "SHAPE_MAPPED_CSV_AND_DYNAMICS_UNVERIFIED")
        self.assertEqual(report["series_roles_if_unambiguous"]["pending_work"], "pending_work")

    def test_extra_stock_is_reported_as_series_block_not_translator_failure(self):
        doc = self.source()
        # Add a separate stock and flow to the existing chain. The legacy
        # translator supports it, but the existing read-only series view does not.
        doc["model"]["variables"].append({
            "name":"side stock", "type":"stock", "equation":"0", "units":"items",
            "inflows":["side flow"],"outflows":[]
        })
        doc["model"]["variables"].append({
            "name":"side flow", "type":"flow", "equation":"0",
            "units":"items per hour", "uniflow":True
        })
        _, code, report = bridge(doc, self.contract)
        self.assertIn("der(side_stock)", code)
        self.assertEqual(report["series_mapping_status"],
                         "BLOCKED_SERIES_VIEW_NOT_PROVIDER_MODEL_FAILURE")
        self.assertIn("UNSUPPORTED_NATIVE_MATERIAL_GRAPH", report["series_block_reason"])

    def test_check_script_absolute_path_existing_file_and_no_solver(self):
        name, code, _ = bridge(self.source(), self.contract)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with self.assertRaisesRegex(TranslationBlocked, "B_LOCAL_GENERATED_MODEL_MISSING"):
                check_script(name, folder)
            (folder / (name + ".mo")).write_text(code, encoding="utf-8")
            mos = check_script(name, folder)
            self.assertIn((folder / (name + ".mo")).as_posix(), mos)
            self.assertEqual(mos.count("checkModel("), 1)
            self.assertNotIn("simulate(", mos)

    def test_budget_mutation_refused(self):
        c = copy.deepcopy(self.contract)
        c["methods"]["B"]["candidate_OpenModelica_max"] = 3
        with self.assertRaisesRegex(TranslationBlocked, "B_CAF_BUDGET_CHANGED"):
            bridge(self.source(), c)


if __name__ == "__main__":
    unittest.main()
