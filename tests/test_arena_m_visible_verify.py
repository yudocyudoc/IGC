import unittest
from scripts.arena_m_visible_verify import verify, material_stock_ports
from scripts.arena_m_visible_pulse import build, ROOT
import json

VISIBLE={"construction":{
 "input_profile":{"kind":"pulse","rate":1.7,"duration":2},
 "observations":[{"t":0,"delivered":0},{"t":1,"delivered":0.35},
                 {"t":2,"delivered":1.1},{"t":4,"delivered":2.5}]}}
NATIVE=build(json.loads((ROOT/"data/synthetic/arena_m_v0_visible.json").read_text()))[2]
CATALOG=json.loads((ROOT/"experiments/e0/catalog.json").read_text())

def samples():
    rows=[]
    for i in range(81):
        t=i/20
        accepted=1.7*min(t,2)
        delivered=accepted*0.7
        preparation=accepted*0.2
        dispatch=accepted*0.1
        rows.append({"time":str(t),"deliveredTotal":str(delivered),
                     "inTransit":"0","preparation0.waiting":str(preparation),
                     "dispatch0.waiting":str(dispatch)})
    return rows

class TestMVisibleNumericalVerifier(unittest.TestCase):
    def test_independent_typed_material_stocks_include_early_queues(self):
        ports=material_stock_ports(NATIVE,CATALOG)
        self.assertEqual(set(ports),{"preparation0.waiting","dispatch0.waiting"})
        r=verify(samples(),VISIBLE,NATIVE,CATALOG)
        self.assertLess(r["max_material_balance_residual"],1e-10)
        self.assertEqual(len(r["observations"]),4)
        self.assertEqual(r["g3_heldout"],"NOT_RUN")
        self.assertEqual(r["excluded_non_global_stock_telemetry"],"inTransit")
        self.assertTrue(r["construction_only"])

    def test_tampered_deliveries_fail_independent_mass_balance(self):
        x=samples()
        x[-1]["deliveredTotal"]="999"
        with self.assertRaisesRegex(ValueError,"GLOBAL_MATERIAL_BALANCE_FAILURE"):
            verify(x,VISIBLE,NATIVE,CATALOG)

    def test_negative_stocks_and_reversed_time_fail(self):
        x=samples()
        x[40]["preparation0.waiting"]="-0.5"
        with self.assertRaisesRegex(ValueError,"NEGATIVE_MATERIAL_STOCK"):
            verify(x,VISIBLE,NATIVE,CATALOG)
        x=samples()
        x[45]["time"]="0.1"
        with self.assertRaisesRegex(ValueError,"TIME_BACKWARDS"):
            verify(x,VISIBLE,NATIVE,CATALOG)

    def test_no_silent_drop_of_declared_material_stock(self):
        x=samples()
        for row in x: row.pop("dispatch0.waiting")
        with self.assertRaisesRegex(ValueError,"MISSING_OR_DUPLICATE_COLUMN"):
            verify(x,VISIBLE,NATIVE,CATALOG)

if __name__=="__main__":
    unittest.main()
