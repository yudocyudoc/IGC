"""CT-03 M producer preparation: six original graphs, no simulation."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_m_prepare import PUBLIC_INPUT, generated, prepare


class CT03MPreparationTest(unittest.TestCase):
    def test_all_six_full_ast_and_three_material_groups(self):
        rows, groups, modelica, mos = generated()
        self.assertEqual(len(rows), 6)
        self.assertEqual(len({r["canonical_sha256"] for r in rows}), 6)
        self.assertEqual(len(groups), 3)
        self.assertEqual(sorted(map(len, groups.values())), [2, 2, 2])
        self.assertEqual(mos.count("simulate("), 6)
        self.assertEqual(mos.count('method="euler"'), 6)
        self.assertEqual(mos.count("numberOfIntervals=64"), 6)
        self.assertIn("Modelica.Blocks.Sources.RealExpression stimulus(y=if time < 2 then 1.7 else 0);", modelica)
        self.assertNotIn("when ", modelica)

    def test_prepared_artifacts_contain_no_secret_or_observations(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "prepared"
            result = prepare(out)
            self.assertEqual(result["candidate_count"], 6)
            self.assertEqual(result["executed_new_omc"], 0)
            self.assertEqual(result["provider_calls"], 0)
            self.assertFalse(result["construction_observations_read"])
            self.assertFalse(result["reserved_truth_read"])
            self.assertFalse(result["world_selected"])
            self.assertEqual(result["source"], PUBLIC_INPUT)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(manifest["solver_status"], "SCRIPT_ONLY_NO_OMC_RUN")
            self.assertEqual((out / "simulate.mos").read_text().count("simulate("), 6)
            with self.assertRaisesRegex(ValueError, "CT03_REFUSE_OVERWRITE"):
                prepare(out)


if __name__ == "__main__":
    unittest.main()
