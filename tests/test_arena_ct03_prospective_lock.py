"""CT-03 prospective producer prediction lock; all data are synthetic fixtures."""
import copy
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import digest
from scripts.arena_cafe.ct03_d_prepare import prepare as prepare_d
from scripts.arena_cafe.ct03_m_prepare import prepare as prepare_m
from scripts.arena_cafe.ct03_public import PUBLIC_INPUT, OBS_SCHEMA
from scripts.arena_cafe.ct03_world_custody import PUBLIC_SCHEMA
from scripts.arena_cafe.ct03_prospective_lock import (
    INPUT_SCHEMA, registry, seal, verify_locked, PROTOCOL,
)

SRC = "sha256:" + "a" * 64
def H(ch):
    return "sha256:" + ch * 64


def fixture(root):
    d, m = prepare_d(root / "d"), prepare_m(root / "m")
    construction = {
        "schema": OBS_SCHEMA, "world_public_id": "W1", "condition_id": "C0",
        "source_snapshot_hash": SRC, "observable": "cumulative_delivered",
        "time_unit": "hours",
        "observations": [{"time": t, "delivered": y}
                         for t, y in ((0, 0), (1, .1), (2, .2), (4, .4))],
    }
    # A fabricated protocol/custody commitment FOR TESTS. No real world selected.
    commitment = {
        "schema": PUBLIC_SCHEMA, "world_public_id": "W1",
        "source_definition_sha256": digest(PUBLIC_INPUT),
        "private_commitment_sha256": H("b"),
        "protocol_sha256": digest(json.loads(PROTOCOL.read_text(encoding="utf-8"))),
        "status": "WORLD_COMMITTED_NOT_EXECUTED_NO_PUBLIC_CONSTRUCTION_YET",
        "evaluator_boundary": "PROCEDURAL_JOB_ISOLATION_NOT_OS_ACL_PROOF",
        "omc_executed": 0, "provider_calls": 0,
    }
    rows = []
    for (arm, candidate_id), meta in registry(d, m).items():
        empty = {"status": "NOT_EXECUTED", "native_sha256": None,
                 "trace_sha256": None, "receipt_sha256": None, "forecast": None}
        policy = {"D": "D-CT03-EXPLICIT-FIXED-SET/1.0",
                  "M": "M-E1-OWN-FEEDBACK-SET/1.0",
                  "B": "UB-IAD/sd-ai::Engine.generate"}[arm]
        rows.append({
            "arm": arm, "candidate_id": candidate_id,
            "parent_hash": meta["parent_hash"], "material_group": meta["group"],
            "initial": copy.deepcopy(empty),
            "decision": {"status": "NOT_EXECUTED", "policy": policy,
                         "feedback_hash": None, "retrieved_item_id": None,
                         "new_model_sha256": None},
            "final": copy.deepcopy(empty),
        })
    entries = {"schema": INPUT_SCHEMA, "world_public_id": "W1",
               "source_snapshot_hash": SRC, "condition_id": "C0", "rows": rows}
    return construction, commitment, d, m, entries


class ProspectiveLockTests(unittest.TestCase):
    def test_seals_all_original_candidates_but_never_claims_execution(self):
        with TemporaryDirectory() as tmp:
            lock = seal(*fixture(Path(tmp)))
            self.assertEqual(lock["candidate_count"], 13)
            self.assertEqual(lock["material_groups"], {"D": 6, "M": 3, "B": 1})
            self.assertEqual(verify_locked(lock), lock["lock_sha256"])
            self.assertFalse(lock["authentic_solver_runs_proven"])
            self.assertFalse(lock["reserved_truth_opened"])
            self.assertEqual(lock["provider_calls_triggered"], 0)

    def test_missing_extra_duplicate_cross_parent_and_future_truth_rejected(self):
        with TemporaryDirectory() as tmp:
            c, world, d, m, entries = fixture(Path(tmp))
            wrong = copy.deepcopy(entries)
            wrong["rows"].pop()
            with self.assertRaisesRegex(ValueError, "ALL_THIRTEEN"):
                seal(c, world, d, m, wrong)
            wrong = copy.deepcopy(entries)
            wrong["rows"].append(copy.deepcopy(wrong["rows"][0]))
            with self.assertRaisesRegex(ValueError, "DUPLICATE_CANDIDATE"):
                seal(c, world, d, m, wrong)
            wrong = copy.deepcopy(entries)
            wrong["rows"][0]["material_group"] = H("e")
            with self.assertRaisesRegex(ValueError, "PARENT_OR_GROUP"):
                seal(c, world, d, m, wrong)
            wrong = copy.deepcopy(entries)
            wrong["rows"][0]["true_t8"] = 2
            with self.assertRaisesRegex(ValueError, "UNKNOWN_ROW"):
                seal(c, world, d, m, wrong)
            bad_commitment = {**world, "protocol_sha256": H("c")}
            with self.assertRaisesRegex(ValueError, "CUSTODY_COMMITMENT_INVALID"):
                seal(c, bad_commitment, d, m, entries)
            wrong = copy.deepcopy(c)
            wrong["observations"].append({"time": 8, "delivered": 2})
            with self.assertRaisesRegex(ValueError, "FOUR_CONSTRUCTION"):
                seal(wrong, world, d, m, entries)
            wrong = copy.deepcopy(entries)
            wrong["rows"][0]["decision"]["status"] = "REVISED"
            with self.assertRaisesRegex(ValueError, "DECISION_NOT_OWN"):
                seal(c, world, d, m, wrong)

    def test_forecasts_are_own_predictions_not_hidden_truth_or_fake_zero(self):
        with TemporaryDirectory() as tmp:
            c, world, d, m, entries = fixture(Path(tmp))
            row = next(row for row in entries["rows"] if row["arm"] == "M")
            row["initial"] = {"status": "PREDICTED", "native_sha256": H("d"),
                              "trace_sha256": H("e"), "receipt_sha256": H("f"),
                              "forecast": [{"time": 6, "delivered": .8},
                                           {"time": 8, "delivered": 1.2}]}
            row["final"] = copy.deepcopy(row["initial"])
            row["decision"] = {
                "status": "RATIFIED", "policy": "M-E1-OWN-FEEDBACK-SET/1.0",
                "feedback_hash": H("a"),
                "retrieved_item_id": ("ct-CT03-W1-R0-M-C0-parent-" +
                                      row["parent_hash"][7:] + ":FEEDBACK"),
                "new_model_sha256": None}
            self.assertEqual(seal(c, world, d, m, entries)["candidate_count"], 13)
            row["decision"]["retrieved_item_id"] = "ct-CT03-W2-R0-M-C0-parent-" + row["parent_hash"][7:] + ":FEEDBACK"
            with self.assertRaisesRegex(ValueError, "WITHOUT_OWN_RETRIEVAL"):
                seal(c, world, d, m, entries)
            row["decision"]["retrieved_item_id"] = "ct-CT03-W1-R0-M-C0-parent-" + row["parent_hash"][7:] + ":FEEDBACK"
            row["initial"]["forecast"][1]["true_y8"] = 3.4
            row["final"] = copy.deepcopy(row["initial"])
            with self.assertRaisesRegex(ValueError, "UNKNOWN_FORECAST_FIELDS"):
                seal(c, world, d, m, entries)

    def test_cli_seal_is_equal_to_pure_call_and_cannot_be_overwritten(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            c, world, d, m, entries = fixture(root)
            for name, obj in (("construction", c), ("commitment", world),
                              ("entries", entries)):
                (root / (name + ".json")).write_text(json.dumps(obj))
            dest = root / "seal.json"
            cmd = [sys.executable, "-m", "scripts.arena_cafe.ct03_prospective_lock",
                   "--construction", str(root / "construction.json"),
                   "--commitment", str(root / "commitment.json"),
                   "--d-manifest", str(root / "d/manifest.json"),
                   "--m-manifest", str(root / "m/manifest.json"),
                   "--entries", str(root / "entries.json"),
                   "--out", str(dest)]
            repo = Path(__file__).resolve().parents[1]
            first = subprocess.run(cmd, cwd=repo, capture_output=True,
                                   text=True, timeout=30)
            self.assertEqual(first.returncode, 0, first.stderr)
            lock = json.loads(dest.read_text())
            self.assertEqual(lock, seal(c, world, d, m, entries))
            second = subprocess.run(cmd, cwd=repo, capture_output=True,
                                    text=True, timeout=30)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("CT03_LOCK_REFUSE_OVERWRITE", second.stderr)
            lock["rows"][0]["parent_hash"] = H("f")
            with self.assertRaisesRegex(ValueError, "SEAL_TAMPERED"):
                verify_locked(lock)


if __name__ == "__main__":
    unittest.main()
