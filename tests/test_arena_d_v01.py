"""D engine regression: real base contract, no external inference."""
import csv
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.arena_v0_contract import INPUT_SCHEMA, ArenaContractError, digest
from scripts.arena_d_v01 import (
    DError, topology, lint_structure, generate, modelica, prepare, verify_csv
)


def case():
    return {
        "schema": INPUT_SCHEMA, "investigation_id": "TEST-D",
        "round_id": "R0", "question": "Why cumulative output changes after a finite pulse?",
        "source_snapshot_hash": "sha256:" + "b" * 64,
        "iteration_limit": 2,
        "construction": {
            "input_profile": {"kind": "pulse", "rate": 1.7, "duration": 2.0},
            "nominal_parameters": {"capacity": 2.0, "response_time": 1.0, "loss_time": 3.0},
            "observations": [{"t": 0, "delivered": 0},
                             {"t": 1, "delivered": 0.3},
                             {"t": 4, "delivered": 2.5}]},
        "observability": {"stock_unit": "items", "time_unit": "hour",
                          "observable": "cumulative_delivered"},
        "resources": {"max_stocks": 3, "allow_loss": True,
                      "max_candidates": 6, "max_simulations": 6}
    }


class ArenaDeterministicV01Tests(unittest.TestCase):
    def test_six_distinct_generic_topologies(self):
        data = generate(case())
        candidates = data["candidates"]
        self.assertEqual(len(candidates), 6)
        self.assertEqual(len(set(c["structure_hash"] for c in candidates)), 6)
        self.assertEqual(set(len(c["structure"]["stocks"]) for c in candidates), {1, 2, 3})
        self.assertEqual(set(c["structure"]["loss"] for c in candidates), {False, True})
        self.assertEqual(data["verdict"], "ALTERNATIVES_NOT_IDENTIFIED")

    def test_no_answer_key_or_observation_heuristics(self):
        a = case()
        b = deepcopy(a)
        b["construction"]["observations"][1]["delivered"] = 999
        x, y = generate(a), generate(b)
        self.assertEqual([c["structure_hash"] for c in x["candidates"]],
                         [c["structure_hash"] for c in y["candidates"]])
        self.assertNotEqual(x["input_hash"], y["input_hash"])

    def test_no_reserved_or_cross_arm_fields(self):
        for key in ("gold", "holdout", "other_arm_result"):
            d = case()
            d["construction"][key] = "secret"
            with self.subTest(key=key), self.assertRaises(ArenaContractError):
                generate(d)

    def test_fail_closed_linter(self):
        t = topology(2, True)
        t["edges"].append(t["edges"][-1])
        with self.assertRaisesRegex(DError, "DUPLICATED_MATERIAL"):
            lint_structure(t)
        d = case()
        d["observability"]["observable"] = "generator_id"
        with self.assertRaisesRegex(DError, "BAD_OBSERVABILITY"):
            generate(d)

    def test_physical_conservation_syntax(self):
        data = case()
        for candidate in generate(data)["candidates"]:
            text = modelica(candidate, data["construction"]["input_profile"])
            n = len(candidate["structure"]["stocks"])
            self.assertIn("der(s1) = inputRate - f1 - lossRate;", text)
            self.assertIn(f"der(delivered) = f{n};", text)
            self.assertIn("der(lost) = lossRate;", text)
            if n >= 2:
                self.assertIn("der(s2) = f1 - f2;", text)
            if candidate["structure"]["loss"]:
                self.assertIn("lossRate = max(0, s1/lossTime);", text)
            else:
                self.assertIn("lossRate = 0;", text)
            self.assertNotIn("IGCMolecules", text)

    def test_nominal_not_fitted(self):
        data = case()
        result = generate(data)
        self.assertTrue(all(c["parameter_status"] == "PUBLIC_ASSUMPTIONS_NOT_FITTED"
                            for c in result["candidates"]))
        data["construction"]["nominal_parameters"]["capacity"] = -1
        with self.assertRaisesRegex(DError, "BAD_NOMINAL_PARAMETERS"):
            generate(data)

    def test_publishes_native_artifact_and_nonreasoning_event(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td) / "prepared"
            state = prepare(case(), folder)
            self.assertEqual(state["state"], "G0_G1_ONLY")
            self.assertEqual(len(list(folder.glob("*.mo"))), 6)
            native = json.loads((folder / "candidates.json").read_text())
            sub = json.loads((folder / "submission.json").read_text())
            event = json.loads((folder / "memory-event.json").read_text())
            self.assertEqual(sub["native_artifact_sha256"], digest(native))
            self.assertEqual(event["arm_id"], "D")
            self.assertEqual(event["event_type"], "HYPOTHESIS_PROPOSED")
            self.assertEqual(sub["hypothesis_ids"], state["ids"])
            with self.assertRaises(FileExistsError):
                prepare(case(), folder)

    def test_verifier_rejects_wrong_mass_balance(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "broken.csv"
            p.write_text("time,delivered,lost,s1\n0,0,0,0\n1,1,0,0\n2,1,0,0\n4,1,0,0\n")
            with self.assertRaisesRegex(DError, "MASS_BALANCE_FAIL"):
                verify_csv(p, 1, case()["construction"]["input_profile"])

    def test_budget_and_unknown_topology(self):
        data = case()
        data["resources"].update(max_stocks=2, allow_loss=False, max_candidates=2)
        self.assertEqual(len(generate(data)["candidates"]), 2)
        data["resources"]["max_stocks"] = 100
        with self.assertRaisesRegex(DError, "BAD_BUDGET"):
            generate(data)


if __name__ == "__main__":
    unittest.main()
