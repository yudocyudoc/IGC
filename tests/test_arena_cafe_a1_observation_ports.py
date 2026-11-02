"""Original-method A1 observation operators, with no inferred stimulus/parameters."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import subprocess
import sys
import unittest

from scripts.arena_cafe import ev01, evidence, observation_ports as ports
from scripts.arena_v0_contract import ArenaContractError, digest
from scripts import arena_event_observability as obs


REGISTRY = Path("experiments/e1/registry.base.json")


class ObservationPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw, checkpoints = ev01.trace_generator()
        ev01.verify_des_parity(checkpoints)
        cls.source = evidence.build(
            obs.project_events(raw, "POS"), obs.project_events(raw, "FULL"))

    def test_D_exact_interval_counts_without_pulse_or_capacity(self):
        for condition in ("O0", "O1"):
            payload = self.source["views"][condition]
            port = ports.d_port(payload, condition)
            self.assertEqual(digest(payload), port["visible_input_hash"])
            self.assertEqual("D", port["arm_id"])
            self.assertFalse(port["native_input_valid"])
            self.assertFalse(port["native_engine_executed_from_port"])
            self.assertEqual("NOT_RUN", port["native_inference_or_selection"])
            self.assertEqual("NOT_MAPPED_TO_GENERIC_D_STOCKS" if condition == "O1"
                             else "NOT_AVAILABLE_O0", port["physical_aggregates"])
            self.assertEqual(
                {"orders_created_cumulative", "delivered_cumulative"},
                {p["observed"] for p in port["observation_operators"]})
            self.assertIn("NO_KNOWN_EXOGENOUS_PULSE", port["blocked_requirements"])
            self.assertNotIn("nominal_parameters", json.dumps(port))
            self.assertNotIn("pulseRate", json.dumps(port))
            bins = port["observed_interval_counts"]
            self.assertEqual(len(payload["construction"]["observation_series"])-1, len(bins))
            self.assertEqual(15, sum(x["arrivals_observed_count"] for x in bins))
            self.assertEqual("0", bins[0]["start_minutes_exact"])
            self.assertEqual("2", bins[0]["end_minutes_exact"])
            self.assertEqual(5, bins[0]["arrivals_observed_count"])
            self.assertTrue(all(x["time_within_bin"] == "UNKNOWN_NOT_A_PULSE"
                                for x in bins))
            self.assertTrue(all(Fraction(x["start_minutes_exact"]) <
                                Fraction(x["end_minutes_exact"]) for x in bins))

    def test_M_roles_are_exact_original_typed_registry_ports(self):
        o0 = ports.m_port(self.source["views"]["O0"], "O0", REGISTRY)
        o1 = ports.m_port(self.source["views"]["O1"], "O1", REGISTRY)
        self.assertEqual(2, len(o0["observation_operators"]))
        self.assertEqual(3, len(o1["observation_operators"]))
        self.assertEqual("UNRESOLVED", o1["candidate_selection"])
        self.assertEqual("NOT_RUN", o1["parameter_fitting"])
        self.assertEqual("NOT_RUN", o1["native_inference_or_selection"])
        self.assertEqual(o0["registry_roles_hash"], o1["registry_roles_hash"])
        source = o0["observation_operators"][0]
        receipt = o0["observation_operators"][1]
        self.assertEqual(("source", "outflow", "FLOW<Order>", "units/hour"),
            (source["target"]["role"], source["target"]["port"],
             source["target"]["type"], source["target"]["native_unit"]))
        self.assertEqual(("receipt", "total", "STATE<Delivered>", "units"),
            (receipt["target"]["role"], receipt["target"]["port"],
             receipt["target"]["type"], receipt["target"]["native_unit"]))
        self.assertEqual("INTEGRAL_FLOW_UP_TO_SAMPLE_T", source["operator"])
        self.assertEqual("SAMPLE_CUMULATIVE_STATE_AT_T", receipt["operator"])
        prep = o1["observation_operators"][2]
        self.assertEqual(("preparation", "completed", "FLOW<ReadyOrder>"),
            (prep["target"]["role"], prep["target"]["port"], prep["target"]["type"]))
        self.assertEqual("FLOW<U>", prep["target"]["catalog_declared_type"])
        self.assertEqual({"T": "Order", "U": "ReadyOrder"},
                         prep["target"]["role_type_bindings"])
        self.assertEqual("CANDIDATE_ROLE_ASSOCIATION_FROM_DISCLOSED_STAGE_NOT_IDENTIFIED",
                         prep["status"])
        self.assertEqual(
            self.source["views"]["O1"]["construction"]["physical_observation"][
                "n_completed_stage_services"], prep["observed_count"])
        self.assertEqual(["mean_wait_minutes_exact", "mean_service_minutes_exact"],
                         o1["unmapped_measurements"])
        self.assertNotIn("maxThroughput", json.dumps(o1))
        self.assertNotIn("responseTime\": 0.5", json.dumps(o1))
        self.assertNotIn("transferencia_final", json.dumps(o1))
        self.assertNotIn("resource_id", json.dumps(o1))

    def test_M_rejects_unapproved_registry_and_wrong_catalog_type(self):
        with TemporaryDirectory() as tmp:
            unknown = Path(tmp) / "registry.base.json"
            unknown.write_text(REGISTRY.read_text())
            with self.assertRaisesRegex(ArenaContractError, "A1_M_UNAPPROVED_REGISTRY"):
                ports.m_port(self.source["views"]["O0"], "O0", unknown)
        path, cfg, classes, catalog = ports._get_registry(REGISTRY)
        bad_classes = deepcopy(classes)
        bad_classes["delivery-counter"]["ports"][1]["type"] = "FLOW<Delivered>"
        with patch.object(ports, "_get_registry", return_value=(path, cfg, bad_classes, catalog)):
            with self.assertRaisesRegex(ArenaContractError, "A1_M_PORT_TYPE_MISMATCH"):
                ports.m_port(self.source["views"]["O0"], "O0", REGISTRY)
        wrong_binding = deepcopy(classes)
        wrong_binding["bounded-queue"]["role_bindings"]["preparation"]["U"] = "Shipment"
        with patch.object(ports, "_get_registry", return_value=(path, cfg, wrong_binding, catalog)):
            with self.assertRaisesRegex(ArenaContractError, "A1_M_PORT_TYPE_MISMATCH"):
                ports.m_port(self.source["views"]["O1"], "O1", REGISTRY)
        bad_cfg = deepcopy(cfg)
        del bad_cfg["roles"]["source"]
        with patch.object(ports, "_get_registry", return_value=(path, bad_cfg, classes, catalog)):
            with self.assertRaisesRegex(ArenaContractError, "A1_M_ROLE_NOT_REGISTERED"):
                ports.m_port(self.source["views"]["O0"], "O0", REGISTRY)

    def test_no_cross_condition_or_unauthorized_injection(self):
        with self.assertRaisesRegex(ArenaContractError, "A1_CROSS_CONDITION"):
            ports.port(self.source["views"]["O0"], "D", "O1")
        with self.assertRaisesRegex(ArenaContractError, "A1_CROSS_CONDITION"):
            ports.port(self.source["views"]["O1"], "M", "O0", registry=REGISTRY)
        with self.assertRaisesRegex(ArenaContractError, "A1_PORT_UNSUPPORTED_ARM"):
            ports.port(self.source["views"]["O0"], "B", "O0")
        with self.assertRaisesRegex(ArenaContractError, "A1_M_REQUIRES_PINNED_REGISTRY"):
            ports.port(self.source["views"]["O0"], "M", "O0")
        with self.assertRaisesRegex(ArenaContractError, "A1_D_DOES_NOT_USE_M_REGISTRY"):
            ports.port(self.source["views"]["O0"], "D", "O0", registry=REGISTRY)
        changed = deepcopy(self.source["views"]["O0"])
        changed["construction"]["observation_series"][1]["orders_created_cumulative"] += 1
        with self.assertRaisesRegex(ArenaContractError, "A1_POS_ARRIVALS_COUNT_PARITY"):
            ports.port(changed, "D", "O0")

    def test_cli_creates_one_sidecar_without_native_model(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            for arm,cond in (("D","O0"), ("M","O1")):
                payload = self.source["views"][cond]
                source = folder / (cond + ".json")
                source.write_text(json.dumps(payload))
                dest = folder / (arm + "-port.json")
                cmd = [sys.executable, "-m", "scripts.arena_cafe.observation_ports",
                       "--input", str(source), "--arm", arm, "--condition", cond,
                       "--out", str(dest)]
                if arm == "M":
                    cmd += ["--registry", str(REGISTRY)]
                run = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(0, run.returncode, run.stderr)
                obj = json.loads(dest.read_text())
                self.assertEqual(arm, obj["arm_id"])
                self.assertEqual(cond, obj["condition_id"])
                self.assertFalse(obj["native_engine_executed_from_port"])
                again = subprocess.run(cmd, capture_output=True, text=True)
                self.assertNotEqual(0, again.returncode)
                self.assertIn("A1_PORT_OUTPUT_EXISTS", again.stderr)


if __name__ == "__main__":
    unittest.main()
