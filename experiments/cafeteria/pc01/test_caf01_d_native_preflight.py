#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path
from caf01_d_native_preflight import CONTRACT, check_script, generate


class TestDNativePreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_three_distinct_loss_free_original_d_graphs(self):
        items, _ = generate(self.contract)
        self.assertEqual([x["stocks"] for x in items], [1, 2, 3])
        self.assertTrue(all(x["loss"] is False for x in items))
        self.assertEqual(len({x["source_structure_hash"] for x in items}), 3)
        self.assertTrue(all("lossRate = 0;" in x["source"] for x in items))

    def test_exact_public_pulse_and_no_fit(self):
        items, manifest = generate(self.contract)
        self.assertTrue(all("pulseDuration = (1.0/3.0);" in x["source"] for x in items))
        self.assertTrue(all("pulseRate = 72;" in x["source"] for x in items))
        self.assertEqual(manifest["modelica_simulations_executed"], 0)
        self.assertEqual(manifest["RK4_executed"], 0)
        self.assertEqual(manifest["RK4_construction_budget"], 18)
        self.assertEqual(manifest["RK4_CAF_N_budget"], 18)

    def test_native_check_uses_existing_absolute_paths_no_simulate(self):
        items, _ = generate(self.contract)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for x in items:
                (folder / (x["model"] + ".mo")).write_text(x["source"])
            mos = check_script(items, folder)
            self.assertEqual(mos.count("checkModel("), 3)
            self.assertEqual(mos.count("loadFile("), 3)
            self.assertNotIn("simulate(", mos)
            for item in items:
                self.assertIn((folder / (item["model"]+".mo")).as_posix(), mos)

    def test_missing_model_file_fails_closed(self):
        items, _ = generate(self.contract)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "D_MODELICA_SOURCE_MISSING"):
                check_script(items, temp)

    def test_changed_known_loss_policy_fails_closed(self):
        cfg = copy.deepcopy(self.contract)
        cfg["methods"]["D"]["loss_variants"] = [False, True]
        with self.assertRaisesRegex(ValueError, "D_BOUNDARY"):
            generate(cfg)

    def test_changed_grid_or_pulse_fails_closed(self):
        for field, value in (("grid", [20, 72, 96]), ("pulse", 100)):
            cfg = copy.deepcopy(self.contract)
            if field == "grid":
                cfg["methods"]["D"]["parameter_grid"]["capacity_items_per_hour"] = value
                expected = "D_PARAMETER"
            else:
                cfg["unit_conversion"]["arrival_construction_rate_items_per_hour"] = value
                expected = "D_UNITS"
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, expected):
                    generate(cfg)


if __name__ == "__main__":
    unittest.main()
