#!/usr/bin/env python3
import copy
import json
import unittest
import tempfile
from pathlib import Path
from caf01_m_native_preflight import CONTRACT, ROOT, checked_models, render_bundle, resolve_check_only_paths


class TestCAF01MNativePreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(Path(CONTRACT).read_text(encoding="utf-8"))

    def test_nine_models_and_three_structures(self):
        items = checked_models(self.contract)
        self.assertEqual(len(items), 9)
        self.assertEqual({i["structure"] for i in items}, {"C00", "C01", "C02"})
        self.assertEqual({i["transit_count"] for i in items}, {0, 1, 2})
        self.assertEqual({i["capacity"] for i in items}, {20, 72, 100})

    def test_rate_and_horizon_and_zero_simulation_calls(self):
        modelica, mos, manifest = render_bundle(self.contract)
        self.assertEqual(manifest["simulation_budget_spent"], 0)
        self.assertEqual(manifest["native_check_models"], 9)
        self.assertEqual(mos.count("checkModel("), 9)
        self.assertNotIn("simulate(", mos)
        self.assertNotIn("der(", modelica)
        self.assertIn("time < (1.0/3.0)", modelica)
        self.assertEqual(manifest["horizon_hours"], "2/3")

    def test_no_private_world_content_or_results(self):
        _, _, manifest = render_bundle(self.contract)
        self.assertNotIn("truth", json.dumps(manifest).lower())
        self.assertEqual(manifest["status"], "GENERATED_NOT_COMPILED_NOT_SIMULATED")


    def test_absolute_load_files_exist_from_any_cwd(self):
        _, mos, _ = render_bundle(self.contract)
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "caf01-native"
            generated.mkdir()
            (generated / "CAF01MPreflight.mo").write_text("package CAF01MPreflight end CAF01MPreflight;")
            resolved = resolve_check_only_paths(mos, generated)
            self.assertEqual(resolved.count("loadFile("), 3)
            self.assertNotIn('loadFile("CAF01MPreflight.mo")', resolved)
            targets = []
            for line in resolved.splitlines():
                if line.startswith('loadFile("'):
                    target = Path(line[len('loadFile("'):-3])
                    self.assertTrue(target.is_absolute())
                    self.assertTrue(target.is_file())
                    targets.append(target)
            self.assertEqual(targets, [
                (ROOT / "src/modelica/IGCMolecules.mo").resolve(),
                (ROOT / "src/modelica/IGCInformationMolecules.mo").resolve(),
                (generated / "CAF01MPreflight.mo").resolve(),
            ])

    def test_missing_generated_model_fails_closed(self):
        _, mos, _ = render_bundle(self.contract)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "MODELICA_LOAD_FILE_MISSING"):
                resolve_check_only_paths(mos, Path(tmp))

    def test_fail_closed_on_changed_grid(self):
        c = copy.deepcopy(self.contract)
        c["methods"]["M"]["proposed_bounded_capacity_grid_items_per_hour"] = [20, 72.5, 100]
        with self.assertRaisesRegex(ValueError, "M_GRID"):
            checked_models(c)

    def test_fail_closed_on_changed_pulse(self):
        c = copy.deepcopy(self.contract)
        c["worlds"][1]["arrival"]["rate"] = 2
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_RATE"):
            render_bundle(c)


if __name__ == "__main__":
    unittest.main()
