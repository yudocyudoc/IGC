from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.compose_molecular_candidates import ContractError, compose, render_modelica
from scripts.verify_molecular_composition_poc import sha256, verify_input_provenance


ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/synthetic/fm_b_serial_chain_plan.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "data/synthetic/fm_a_structural_candidates.json").read_text(encoding="utf-8"))


class FmBMolecularComposerTests(unittest.TestCase):
    def test_three_serial_stages_compose_without_changing_the_composer(self):
        plan = copy.deepcopy(PLAN)
        plan["candidates"] = [{
            "id": "urn:igc:candidate:CS-03",
            "structure_id": "urn:igc:structure:CS-03@0.2",
            "stage_count": 3,
        }]
        document = compose(plan, CATALOG)
        instances = document["structures"][0]["molecule_instances"]
        stage_ids = [item["id"] for item in instances
                     if item["molecule_definition_id"] == plan["roles"]["stage"]]
        self.assertEqual(stage_ids, ["stage0", "stage1", "stage2"])
        self.assertIn("BoundedQueue stage2", render_modelica(plan, document))

    def test_zero_stage_count_is_rejected(self):
        plan = copy.deepcopy(PLAN)
        plan["candidates"][0]["stage_count"] = 0
        with self.assertRaisesRegex(ContractError, "COMPOSITION_STAGE_COUNT"):
            compose(plan, CATALOG)

    def test_incompatible_stage_port_is_rejected(self):
        catalog = copy.deepcopy(CATALOG)
        stage = next(item for item in catalog["molecule_definitions"]
                     if item["id"] == PLAN["roles"]["stage"])
        next(port for port in stage["ports"] if port["name"] == "arrival")["direction"] = "out"
        with self.assertRaisesRegex(ContractError, "COMPOSITION_PORT_INCOMPATIBLE"):
            compose(PLAN, catalog)

    def test_parameter_below_declared_minimum_is_rejected(self):
        plan = copy.deepcopy(PLAN)
        plan["parameter_bindings"]["responseTime"]["value"] = 0
        with self.assertRaisesRegex(ContractError, "COMPOSITION_PARAMETER_BOUNDS"):
            compose(plan, CATALOG)

    def test_candidate_ids_with_colliding_modelica_names_are_rejected(self):
        plan = copy.deepcopy(PLAN)
        plan["candidates"].append({
            "id": "urn:igc:candidate:CS_01",
            "structure_id": "urn:igc:structure:CS-03@0.2",
            "stage_count": 3,
        })
        with self.assertRaisesRegex(ContractError, "COMPOSITION_MODELICA_IDENTIFIER_COLLISION"):
            compose(plan, CATALOG)

    def test_invalid_instance_modelica_identifier_is_rejected(self):
        plan = copy.deepcopy(PLAN)
        plan["instances"]["stage_prefix"] = "stage-"
        with self.assertRaisesRegex(ContractError, "COMPOSITION_MODELICA_IDENTIFIER_INVALID"):
            compose(plan, CATALOG)

    def test_verifier_checks_current_plan_and_catalog_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = root / "plan.json"
            catalog = root / "catalog.json"
            generator = root / "composer.py"
            plan.write_text("plan original", encoding="utf-8")
            catalog.write_text("catalog original", encoding="utf-8")
            generator.write_text("generator original", encoding="utf-8")
            report = {"plan_sha256": sha256(plan), "catalog_sha256": sha256(catalog),
                      "generator_sha256": sha256(generator)}
            verify_input_provenance(report, plan, catalog, generator)
            plan.write_text("plan changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "plan_sha256"):
                verify_input_provenance(report, plan, catalog, generator)
            plan.write_text("plan original", encoding="utf-8")
            catalog.write_text("catalog changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "catalog_sha256"):
                verify_input_provenance(report, plan, catalog, generator)


if __name__ == "__main__":
    unittest.main()
