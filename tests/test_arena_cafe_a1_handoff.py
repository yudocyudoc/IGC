"""Negative A1 input and context controls; exact native sources remain intact."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import evidence, native_handoff, ev01
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError, canonical, digest


class CafeNativeHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw, checkpoints = ev01.trace_generator()
        ev01.verify_des_parity(checkpoints)
        cls.data = evidence.build(
            obs.project_events(raw, "POS"), obs.project_events(raw, "FULL"))

    def test_six_scoped_handoffs_and_no_inferred_use(self):
        observed_scopes = set()
        for condition in ("O0", "O1"):
            visible = self.data["views"][condition]
            input_hash = digest(visible)
            for arm in ("D", "B", "M"):
                receipt = native_handoff.handoff(visible, arm, condition)
                observed_scopes.add(receipt["scope_hash"])
                self.assertEqual(input_hash, receipt["visible_input_hash"])
                self.assertEqual(visible["source_snapshot_hash"], receipt["source_snapshot_hash"])
                self.assertFalse(receipt["native_method_run"])
                self.assertFalse(receipt["prompt_read_proven"])
                self.assertFalse(receipt["native_evidence_use_proven"])
                self.assertEqual("APPLICATION_SCOPED_ONLY_NOT_OS_ACL",
                                 receipt["cross_condition_access_control"])
        self.assertEqual(6, len(observed_scopes))

    def test_actual_d_native_contract_fails_without_invented_pulse(self):
        from scripts.arena_d_v01 import DError, validate_case
        for condition in ("O0", "O1"):
            visible = self.data["views"][condition]
            self.assertIn("BLOCKED", native_handoff.handoff(visible, "D", condition)["status"])
            with self.assertRaises(DError):
                validate_case(visible)

    def test_reject_cross_condition_even_if_visible_hash_would_be_valid(self):
        o0 = self.data["views"]["O0"]
        o1 = self.data["views"]["O1"]
        with self.assertRaisesRegex(ArenaContractError, "A1_CROSS_CONDITION"):
            native_handoff.handoff(o0, "M", "O1")
        with self.assertRaisesRegex(ArenaContractError, "A1_CROSS_CONDITION"):
            native_handoff.handoff(o1, "B", "O0")
        modified = deepcopy(o1)
        modified["observability"]["condition_id"] = "O0"
        with self.assertRaisesRegex(ArenaContractError, "A1_ROUND_CONDITION_MISMATCH"):
            native_handoff.handoff(modified, "B", "O0")

    def test_detect_mutated_aggregate_unless_digest_recomputed(self):
        visible = deepcopy(self.data["views"]["O1"])
        visible["construction"]["physical_observation"]["n_completed_stage_services"] += 1
        with self.assertRaisesRegex(ArenaContractError, "A1_SOURCE_DIGEST_MISMATCH"):
            native_handoff.handoff(visible, "M", "O1")

    def test_reject_extra_private_or_fake_physical_source(self):
        o0 = deepcopy(self.data["views"]["O0"])
        o0["construction"]["hidden_stage"] = "transferencia_final"
        with self.assertRaisesRegex(ArenaContractError, "A1_CONSTRUCTION_SHAPE"):
            native_handoff.handoff(o0, "B", "O0")
        o1 = deepcopy(self.data["views"]["O1"])
        o1["construction"]["physical_observation"]["stage_disclosed"] = "transferencia_final"
        with self.assertRaisesRegex(ArenaContractError, "A1_PHYSICAL_SOURCE_INVALID"):
            native_handoff.handoff(o1, "M", "O1")

    def test_export_one_directory_only_and_refuse_overwrite(self):
        with TemporaryDirectory() as temp:
            for condition in ("O0", "O1"):
                for arm in ("D", "B", "M"):
                    folder = Path(temp) / (condition + "-" + arm)
                    report = native_handoff.export_one(
                        self.data["views"][condition], arm, condition, folder)
                    files = {x.name for x in folder.iterdir()}
                    self.assertEqual({"handoff.json"} if arm == "D"
                                     else {"handoff.json", "visible.json"}, files)
                    self.assertEqual(json.loads((folder / "handoff.json").read_text()), report)
                    if arm != "D":
                        self.assertEqual(
                            json.loads((folder / "visible.json").read_text()),
                            self.data["views"][condition])
                    with self.assertRaisesRegex(ArenaContractError, "A1_REFUSE_OVERWRITE"):
                        native_handoff.export_one(
                            self.data["views"][condition], arm, condition, folder)
            self.assertEqual(6, len(list(Path(temp).iterdir())))


if __name__ == "__main__":
    unittest.main()
