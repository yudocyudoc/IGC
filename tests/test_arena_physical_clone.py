"""Regresión de copia física promovida desde CAF-01; no es inferencia nueva."""
from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from scripts.arena_physical import des_engine as des

ORIGINAL_BLOB_SHA1 = "8cadbc1f9489c3e1cd7eecd020009978873822ba"


class ArenaPhysicalPromotionTests(unittest.TestCase):
    def test_exact_original_git_blob(self):
        source = Path(des.__file__).read_bytes()
        header = f"blob {len(source)}".encode("ascii") + bytes([0])
        self.assertEqual(hashlib.sha1(header + source).hexdigest(), ORIGINAL_BLOB_SHA1)

    def test_conservation_fixture(self):
        config = {
            "schema": des.SCHEMA,
            "tie_policy": des.TIE_POLICY,
            "stages": [
                {"servers": 1, "service_minutes": "1"},
                {"servers": 1, "service_minutes": "1"},
            ],
        }
        arrivals = des.half_open_arrivals("1", 3)
        self.assertEqual(len(arrivals), 3)
        series = des.run_toy_engine(config, arrivals, (0, 1, 2, 3, 4, 5))
        self.assertEqual(series[-1].accepted_cum_orders, 3)
        self.assertEqual(series[-1].delivered_cum_orders, 3)
        self.assertEqual(series[-1].pending_orders, 0)
        for s in series:
            self.assertEqual(s.accepted_cum_orders,
                             s.delivered_cum_orders + s.pending_orders)
            self.assertTrue(all(n <= 1 for n in s.stage_in_service))


if __name__ == "__main__":
    unittest.main()
