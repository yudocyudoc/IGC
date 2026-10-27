"""Offline gate: R1 may only simulate its original own-arm candidates."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r1_common_physical import (
    checked_d_manifest, d_manifest, prepare_d,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT / "data/synthetic/arena_v0_primary_construction.json").read_text())
ASSUMPTIONS = json.loads((ROOT / "data/synthetic/arena_v0_declared_d_assumptions.json").read_text())


class R1PhysicalPreparationTests(unittest.TestCase):
    def test_d_six_source_models_keep_shared_input_provenance(self):
        original = deepcopy(SOURCE)
        manifest = d_manifest(SOURCE, ASSUMPTIONS)
        self.assertEqual(len(manifest["candidates"]), 6)
        self.assertEqual(len({c["candidate_id"] for c in manifest["candidates"]}), 6)
        self.assertEqual({c["g1_lint"]["status"] for c in manifest["candidates"]},
                         {"G1_STRUCTURE_ADMISSIBLE"})
        self.assertEqual(SOURCE, original)
        self.assertEqual(manifest, d_manifest(SOURCE, ASSUMPTIONS))
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "out"
            prepare_d(SOURCE, ASSUMPTIONS, output)
            self.assertEqual(checked_d_manifest(SOURCE, ASSUMPTIONS, output), manifest)
            self.assertIn("simulate(", (output / "simulate.mos").read_text())
            self.assertEqual(len(list(output.glob("DStockFlow_*.mo"))), 6)

    def test_changed_native_or_assumption_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "out"
            prepare_d(SOURCE, ASSUMPTIONS, root)
            altered = deepcopy(ASSUMPTIONS)
            altered["nominal_parameters"]["capacity"] = 100
            with self.assertRaisesRegex(ValueError, "R1_D_MANIFEST_CHANGED"):
                checked_d_manifest(SOURCE, altered, root)
            first = next(root.glob("DStockFlow_*.mo"))
            first.write_text(first.read_text() + "\n// unauthorized change\n")
            with self.assertRaisesRegex(ValueError, "R1_D_MODEL_CHANGED"):
                checked_d_manifest(SOURCE, ASSUMPTIONS, root)

    def test_fails_closed_without_assumptions_and_overwrite(self):
        with self.assertRaisesRegex(ValueError, "R1_D_NEEDS_EXPLICIT"):
            d_manifest(SOURCE, None)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "out"
            prepare_d(SOURCE, ASSUMPTIONS, root)
            with self.assertRaisesRegex(ValueError, "R1_D_PREPARATION_EXISTS"):
                prepare_d(SOURCE, ASSUMPTIONS, root)

    def test_input_contract_rejects_secret_material(self):
        corrupted = deepcopy(SOURCE)
        corrupted["holdout"] = [0, 1]
        with self.assertRaises(Exception):
            d_manifest(corrupted, ASSUMPTIONS)


if __name__ == "__main__":
    unittest.main()
