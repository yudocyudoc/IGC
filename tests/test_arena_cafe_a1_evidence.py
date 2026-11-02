"""A1 O0/O1 projections are engineering controls, not native D/B/M inference."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
import unittest

from scripts.arena_cafe import evidence, ev01
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import (
    ArenaContractError, arm_view, assert_same_evidence, digest,
    validate_visible_input,
)


def fixture():
    raw, snapshots = ev01.trace_generator()  # evaluator-side known synthetic control
    ev01.verify_des_parity(snapshots)
    return (
        obs.project_events(raw, "POS"),
        obs.project_events(raw, "FULL"),
    )


class EvidenceA1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pos, cls.full = fixture()

    def test_disclosures_and_same_evidence_within_condition(self):
        data = evidence.build(self.pos, self.full)
        self.assertEqual("PARTIAL", data["claims"]["A1"])
        self.assertEqual(6, len(data["interface"]["entries"]))
        self.assertEqual("NOT_IMPLEMENTED", data["interface"]["actual_process_cache_ledger_acl"])
        views = data["views"]
        self.assertNotEqual(views["O0"]["source_snapshot_hash"],
                            views["O1"]["source_snapshot_hash"])
        for condition in ("O0", "O1"):
            payload = views[condition]
            validate_visible_input(payload)
            assert_same_evidence([arm_view(payload, a) for a in ("D", "B", "M")])
            self.assertEqual("10", payload["observability"]["cutoff_minutes_exact"])
            self.assertEqual("[0,cutoff)", payload["observability"]["window"])
            self.assertEqual(6, len(payload["construction"]["observation_series"]))
        self.assertNotIn("physical_observation", views["O0"]["construction"])
        physical = views["O1"]["construction"]["physical_observation"]
        self.assertEqual("preparacion", physical["stage_disclosed"])
        self.assertGreater(physical["n_completed_stage_services"], 0)
        self.assertEqual(6, len({r["context_id"] for r in data["interface"]["entries"]}))
        self.assertEqual(2, len({r["common_input_hash"] for r in data["interface"]["entries"]}))
        self.assertEqual({"UNSUPPORTED_DOCUMENTED", "NOT_VERIFIED"},
                         {r["interface_status"] for r in data["interface"]["entries"]})
        self.assertTrue(all(not r["native_method_run"] and not r["used_proven"]
                            for r in data["interface"]["entries"]))

    def test_no_future_info_and_no_truth_fields(self):
        original_pos = deepcopy(self.pos)
        original_full = deepcopy(self.full)
        result = evidence.build(original_pos, original_full, cutoff_minutes_exact="10")
        # Change only already-future timestamps. The cutoff must remove them
        # before hashing, counting or aggregating any data.
        for ev in original_pos + original_full:
            if Fraction(ev["t_minutes_exact"]) >= 10:
                ev["t_minutes_exact"] = str(Fraction(ev["t_minutes_exact"]) + 100)
        again = evidence.build(original_pos, original_full, cutoff_minutes_exact="10")
        self.assertEqual(result, again)
        projected = json.dumps(result, sort_keys=True)
        self.assertNotIn("transferencia_final", projected)
        self.assertNotIn("resource_id", projected)
        self.assertNotIn("SPEC", projected)
        self.assertNotIn("generator_parameters", projected)
        self.assertNotIn("provenance_EVALUATOR_ONLY", projected)

    def test_cumulative_accounting_on_half_open_grid(self):
        result = evidence.build(self.pos, self.full)
        o0 = result["views"]["O0"]["construction"]["observation_series"]
        self.assertEqual(0, o0[0]["orders_created_cumulative"])
        self.assertEqual(0, o0[0]["delivered_cumulative"])
        self.assertEqual(5, o0[1]["orders_created_cumulative"])
        self.assertEqual(15, o0[-1]["orders_created_cumulative"])
        self.assertTrue(all(x["orders_created_cumulative"] >= x["delivered_cumulative"]
                            for x in o0))
        self.assertTrue(all(a["delivered_cumulative"] <= b["delivered_cumulative"]
                            for a, b in zip(o0, o0[1:])))

    def test_no_mutation_of_public_inputs(self):
        pos, full = deepcopy(self.pos), deepcopy(self.full)
        before = digest([pos, full])
        evidence.build(pos, full)
        self.assertEqual(before, digest([pos, full]))

    def test_negative_privacy_temporal_and_integrity_cases(self):
        pos, full = deepcopy(self.pos), deepcopy(self.full)
        pos[0]["stage"] = "transferencia_final"
        with self.assertRaisesRegex(ArenaContractError, "UNAUTHORIZED"):
            evidence.build(pos, full)

        pos, full = deepcopy(self.pos), deepcopy(self.full)
        full[0]["provenance_EVALUATOR_ONLY"] = "truth"
        with self.assertRaisesRegex(ArenaContractError, "UNAUTHORIZED"):
            evidence.build(pos, full)

        pos, full = deepcopy(self.pos), deepcopy(self.full)
        pos[0]["t_minutes_exact"] = "1/4"
        with self.assertRaisesRegex(ArenaContractError, "NOT_SAME_SOURCE"):
            evidence.build(pos, full)

        with self.assertRaisesRegex(ArenaContractError, "INVALID_CUTOFF"):
            evidence.build(self.pos, self.full, sample_times=("0", "2", "12"))
        with self.assertRaisesRegex(ArenaContractError, "INVALID_CUTOFF"):
            evidence.build(self.pos, self.full, sample_times=("0", "10", "10"))

    def test_non_event_data_not_falsely_accepted_by_legacy_common(self):
        from scripts.arena_v0_common_evidence import common, SOURCE_SCHEMA
        result = evidence.build(self.pos, self.full)
        payload = result["views"]["O0"]
        # Legacy source adapter rejects this because it only accepts a
        # declared pulse and a list of (t, delivered) pairs.
        legacy = {
            "schema": SOURCE_SCHEMA,
            "investigation_id": payload["investigation_id"],
            "round_id": payload["round_id"],
            "question": payload["question"],
            "input_profile": {"kind": "observed_arrivals"},
            "observations": payload["construction"]["observation_series"],
            "observability": payload["observability"],
            "iteration_limit": 1, "source_id": "a1-evidence",
        }
        with self.assertRaises(ArenaContractError):
            common(legacy)


if __name__ == "__main__":
    unittest.main()
