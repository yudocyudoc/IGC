"""E01/E02 Buffalo preflight: actual case adapter, shared causal input, no provider."""
from copy import deepcopy
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import unittest
from scripts.arena_cafe import buffalo_ev01_visible as b
from scripts.arena_cafe import r2_causal_pos_signal as causal
from scripts.arena_cafe import evidence
from scripts.arena_v0_contract import digest

class BuffaloEV01Stage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=os.environ.get("E01_PUBLIC_DIR") or os.environ.get("RF02_PUBLIC_DIR")
        if not root:
            raise unittest.SkipTest("A1 frozen public O0/O1 artifacts required")
        cls.views={c:json.loads((Path(root)/(c+"_VISIBLE.json")).read_text())
                   for c in ("O0","O1")}

    def test_case_import_and_both_authorized_conditions(self):
        result={}
        for cond,visible in self.views.items():
            staged,receipt=b.stage(visible,cond)
            body=staged["construction"]["declared_input_reconstruction"]
            source=causal.from_visible(visible,cond)["signal"]
            self.assertEqual(body["policy"],causal.POLICY)
            self.assertEqual(body["signal_sha256"],source["event_rate_signal_sha256"])
            self.assertEqual(body["event_times_minutes_exact"],source["event_times_minutes_exact"])
            self.assertEqual(body["mass_before_cutoff_orders_exact"],source["mass_before_cutoff_orders_exact"])
            self.assertEqual(body["mass_deferred_after_cutoff_orders_exact"],source["mass_deferred_after_cutoff_orders_exact"])
            self.assertEqual(body["support_end_minutes_exact"],source["support_end_minutes_exact"])
            self.assertEqual(sum(Q(x["mass_orders_exact"]) for x in body["piecewise_constant_segments"]),15)
            self.assertNotIn("piecewise_constant_bins",body)
            self.assertFalse(receipt["b_live_authorized"])
            self.assertEqual(receipt["ev01_original_engine_max_tokens_opt_in"],16000)
            self.assertEqual(staged["observability"]["public_cutoff_minutes_exact"],"10")
            self.assertEqual(receipt["provider_calls"],0)
            result[cond]=body["signal_sha256"]
        self.assertEqual(result["O0"],result["O1"])

    def test_no_lookahead_event_within_half_minute_bin(self):
        # A POS creation at 0.3 min must contribute no mass at 0.2 min.
        row={"t_minutes_exact":"3/10"}
        sig=causal._signal([Q(row["t_minutes_exact"])],Q(10),Q(1,2))
        self.assertEqual(causal.event_mass_until([Q(3,10)],Q(1,2),Q(1,5)),0)
        self.assertEqual(causal.event_rate_at([Q(3,10)],Q(1,2),Q(1,5)),0)
        self.assertEqual(sig["segments"][0]["rate_orders_per_minute_exact"],"0")

    def test_deliveries_never_change_arrival_signal(self):
        visible=deepcopy(self.views["O0"])
        for item in visible["construction"]["observation_series"]:
            item["delivered_cumulative"]=0
        visible["source_snapshot_hash"]=digest({
            "schema":evidence.SCHEMA,
            "condition":"O0",
            "cutoff_minutes_exact":str(visible["observability"]["cutoff_minutes_exact"]),
            "construction":visible["construction"],
        })
        original=b.stage(self.views["O0"],"O0")[0]["construction"]["declared_input_reconstruction"]
        altered=b.stage(visible,"O0")[0]["construction"]["declared_input_reconstruction"]
        self.assertEqual(original,altered)

if __name__=="__main__":
    unittest.main()
