"""CAF-08B: verify identical CAF-07B policy with only the prediction bank swapped."""
import json
from pathlib import Path
import tempfile
import unittest

import caf08b_selector_fluid_bank as x
import caf07b_umbral_secuencial as b


SOURCE_SHA = "a" * 40


class FluidSelectorComparatorTests(unittest.TestCase):
    def test_quantization_predeclared_half_up(self):
        self.assertEqual([x.snap_count(v) for v in
                          (0, 0.01, 0.49, 0.5, 1.49, 1.5, 2.5)],
                         [0, 0, 0, 1, 1, 2, 3])
        for v in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                x.snap_count(v)

    def test_fluid_predicts_same_channels_and_hypotheses(self):
        rows = b.bank(False)
        fl = x.fluid_predictions(rows)
        self.assertEqual(set(fl), {r["id"] for r in rows})
        for h in rows:
            fields = fl[h["id"]]
            self.assertEqual(set(fields), {"baseline"} | {
                action["id"] for action in b.ACTIONS})
            self.assertEqual(len(fields["baseline"]), 1)
            for action in b.ACTIONS:
                values = fields[action["id"]]
                self.assertEqual(len(values), len(action["channels"]))
                self.assertTrue(all(type(v) is int and v >= 0 for v in values))

    def test_observation_operator_and_stage_stock(self):
        observed = {
            "delivered": 23.5,
            "waiting": [5.49, 1.5, 0],
            "serving": [1.0, 1.0, 1.0],
        }
        self.assertEqual(x.measure_vector(observed, [
            ("delivered", None), ("waiting", "preparacion"),
            ("waiting", "despacho"), ("stage_stock", "despacho")
        ]), [24, 5, 2, 3])
        with self.assertRaises(ValueError):
            x.measure_vector(observed, [("waiting", "nada")])

    def test_selector_is_imported_unchanged(self):
        self.assertIs(x.b.choose_second, b.choose_second)
        self.assertIs(x.b.evaluate_case, b.evaluate_case)
        self.assertEqual(b.BUDGET, 8)
        self.assertEqual(b.TOLERANCE, 1)
        self.assertEqual(b.MIN_GUARANTEED_PER_SURVIVING_CLASS, 1)
        self.assertEqual(b.FIRST_ACTION_ID, "delivered_15_t20")
        self.assertEqual(len(b.scenarios()), 11)

    def test_frozen_comparison_preserves_worlds_and_audit(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "review"
            result = x.run(out, SOURCE_SHA)
            self.assertEqual(result["checkout_sha"], SOURCE_SHA)
            self.assertEqual(result["n_worlds"], 11)
            self.assertEqual(result["n_banks"], 2)
            self.assertEqual(result["n_model_arms"], 2)
            self.assertEqual(result["n_comparisons"], 44)
            self.assertEqual(result["n_paired_comparisons"], 22)
            self.assertFalse(result["selector_implementation_changed"])
            self.assertFalse(result["sensor_or_tolerance_changed"])
            self.assertFalse(result["deployment_validated"])
            self.assertFalse(result["scientific_identifiability_validated"])
            self.assertEqual(result["promotion_gate"],
                             "BLOCKED_RETROSPECTIVE_NOT_BLINDED")
            for p in result["paired_differences"]:
                self.assertTrue(p["same_initial_and_fixed_first_measurement"])
            self.assertTrue(all(e["cost_spent"] <= 8 for e in result["evaluations"]))
            # 44 decision records pre-written before second DES.
            self.assertEqual(len(list(out.glob("01_CHOICE_*.json"))), 44)
            plan = json.loads((out / "00_PLAN_ANTES_DE_EVALUAR.json").read_text())
            self.assertEqual(plan["tolerance"], 1)
            self.assertTrue(plan["posthoc_known_worlds"])
            self.assertEqual(plan["quantization"], "nearest_integer_half_up")
            manifest = json.loads((out / "03_MANIFIESTO.json").read_text())
            self.assertEqual(manifest["checkout_sha"], SOURCE_SHA)
            for name, sha in manifest["files"].items():
                import hashlib
                self.assertEqual(sha, "sha256:" + hashlib.sha256(
                    (out / name).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError, "CAF08B_OUTPUT_EXISTS"):
                x.run(out, SOURCE_SHA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
