"""Snapshot de evidencia visual: invariantes de datos, no validación de la cámara."""
from __future__ import annotations

import csv
import json
import unittest
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data" / "arena" / "video_barista_v0_1"


def rows(path):
    with (BASE / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class VideoBaristaSnapshotTests(unittest.TestCase):
    def test_original_file_counts(self):
        expected = {
            "pedidos/pedidos.csv": 52,
            "pedidos/items_pedidos.csv": 84,
            "pedidos/resumen_productos.csv": 30,
            "barista/eventos.csv": 200,
            "barista/operaciones.csv": 25,
            "barista/tiempos_pedidos.csv": 52,
            "revisiones/r2_episodios_p004_p006_p045.csv": 5,
            "revisiones/r3_p045_observaciones.csv": 20,
            "revisiones/r4_p031_observaciones.csv": 19,
        }
        for path, count in expected.items():
            with self.subTest(path=path):
                self.assertEqual(len(rows(path)), count)

    def test_units_and_order_references(self):
        orders = rows("pedidos/pedidos.csv")
        items = rows("pedidos/items_pedidos.csv")
        ids = {r["order_id"] for r in orders}
        self.assertEqual(len(ids), 52)
        self.assertEqual(sum(int(r["quantity"]) for r in items), 105)
        self.assertEqual(sum(int(r["product_units"]) for r in orders), 105)
        self.assertTrue(all(r["order_id"] in ids for r in items))
        self.assertEqual({r["order_id"] for r in rows("barista/tiempos_pedidos.csv")}, ids)

    def test_operation_event_pair_integrity(self):
        events = rows("barista/eventos.csv")
        ops = rows("barista/operaciones.csv")
        event_ids = {e["event_id"] for e in events}
        for op in ops:
            with self.subTest(operation=op["event_id"]):
                self.assertIn(op["event_id"] + "-start", event_ids)
                self.assertIn(op["event_id"] + "-end", event_ids)
                if op["status"] == "bounded":
                    s0 = float(op["start_lower_video_s"])
                    s1 = float(op["start_upper_video_s"])
                    e0 = float(op["end_lower_video_s"])
                    e1 = float(op["end_upper_video_s"])
                    self.assertAlmostEqual(float(op["duration_lower_video_s"]), max(0, e0 - s1))
                    self.assertAlmostEqual(float(op["duration_upper_video_s"]), e1 - s0)

    def test_milestone_counts(self):
        types = Counter(r["event_type"] for r in rows("barista/eventos.csv"))
        self.assertEqual(types, {"start": 77, "end": 25, "assembly_end": 46, "last_product_exit": 52})

    def test_contract_and_source_identity(self):
        catalog = json.loads((BASE / "contrato/catalogo_eventos_v0_1.json").read_text(encoding="utf-8"))
        schema = json.loads((BASE / "contrato/schema_anotacion_v0_1.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["entries"]), 23)
        codes = {entry["code"] for entry in catalog["entries"]}
        self.assertEqual(codes, set(schema["properties"]["event_code"]["enum"]))
        self.assertEqual(catalog["source_video_sha256"],
                         "cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5")

    def test_unverified_clock_remains_unverified(self):
        measurements = json.loads((BASE / "barista/mediciones.json").read_text(encoding="utf-8"))
        for prop in ("physical_clock_verified", "continuous_recording_verified", "exhaustive_operation_log"):
            self.assertIs(measurements["summary"][prop], False)


if __name__ == "__main__":
    unittest.main()
