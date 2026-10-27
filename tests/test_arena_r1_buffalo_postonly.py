import copy
import unittest
from scripts.arena_r1_buffalo_postonly import diagnose

def original_shape_fixture():
    names=["congestion multiplier","product of capacity effects",
           "capacity constrained throughput","completion rate","pulse gate"]
    vs=[{"name":name,"type":"variable","equation":"0"}
        for name in names]
    vs.extend({"name":f"unused {i}","type":"variable","equation":"0"} for i in range(12))
    by={x["name"]:x for x in vs}
    by["congestion multiplier"]["equation"]="product_of_capacity_effects"
    by["product of capacity effects"]["equation"]="congestion_multiplier"
    by["capacity constrained throughput"]["equation"]="max_completion_capacity * MIN(1, work_in_process / 2)"
    by["completion rate"]["equation"]="work_in_process / processing_time"
    by["pulse gate"]["equation"]="MIN(1, MAX(0, (time_active_end - TIME) / 1))"
    return {"model":{"variables":vs}}

class NativeR1PostOnly(unittest.TestCase):
    def test_unanchored_cycle_and_unused_capacity_identified(self):
        r=diagnose(original_shape_fixture())
        self.assertEqual(r["g1_status"],"FAIL_UNANCHORED_ALGEBRAIC_IDENTITY")
        self.assertEqual(r["mathematical_underdetermination"][0]["variables"],
                         ["congestion_multiplier","product_of_capacity_effects"])
        self.assertEqual(r["pulse_shape_discrepancy"]["native_gate_at_t_1_5_given_end_t_2"],0.5)
        self.assertIn("NO_PATH",r["unused_claimed_capacity_mechanism"]["status"])
        self.assertEqual(r["g2_status"],"FAILED_TO_BUILD_ORIGINAL_MODEL_NOT_PHYSICALLY_EVALUATED")
    def test_does_not_alter_native_model(self):
        native=original_shape_fixture()
        before=copy.deepcopy(native)
        diagnose(native)
        self.assertEqual(native,before)
    def test_fail_closed_on_changed_alias_pair(self):
        native=original_shape_fixture()
        native["model"]["variables"][1]["equation"]="1"
        with self.assertRaisesRegex(ValueError,"CYCLE_NOT_FOUND"):
            diagnose(native)
    def test_fail_closed_on_capacity_connected_to_completion(self):
        native=original_shape_fixture()
        native["model"]["variables"][3]["equation"]="capacity_constrained_throughput"
        with self.assertRaisesRegex(ValueError,"CAPACITY_ALREADY_CONNECTED"):
            diagnose(native)

if __name__=="__main__":
    unittest.main()
