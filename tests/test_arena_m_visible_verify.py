import unittest
from scripts.arena_m_visible_verify import verify

VISIBLE={"construction":{
 "input_profile":{"kind":"pulse","rate":1.7,"duration":2},
 "observations":[{"t":0,"delivered":0},{"t":1,"delivered":0.35},
                 {"t":2,"delivered":1.1},{"t":4,"delivered":2.5}]}}
def samples():
    rows=[]
    for i in range(81):
        t=i/20
        accepted=1.7*min(t,2)
        delivered=accepted*0.7
        waiting=accepted-delivered
        rows.append({"time":str(t),"deliveredTotal":str(delivered),
                     "inTransit":str(waiting)})
    return rows

class TestMVisibleNumericalVerifier(unittest.TestCase):
    def test_synthetic_trace_is_only_unit_test_not_real_omc(self):
        r=verify(samples(),VISIBLE)
        self.assertLess(r["max_material_balance_residual"],1e-10)
        self.assertEqual(len(r["observations"]),4)
        self.assertEqual(r["g3_heldout"],"NOT_RUN")
        self.assertTrue(r["construction_only"])
    def test_tampered_deliveries_fail_independent_mass_balance(self):
        x=samples()
        x[-1]["deliveredTotal"]="999"
        with self.assertRaisesRegex(ValueError,"GLOBAL_MATERIAL_BALANCE_FAILURE"):
            verify(x,VISIBLE)
    def test_negative_stocks_and_reversed_time_fail(self):
        x=samples()
        x[40]["inTransit"]="-0.5"
        with self.assertRaisesRegex(ValueError,"NEGATIVE_MATERIAL_STOCK"): verify(x,VISIBLE)
        x=samples()
        x[45]["time"]="0.1"
        with self.assertRaisesRegex(ValueError,"TIME_BACKWARDS"): verify(x,VISIBLE)

if __name__=="__main__":
    unittest.main()
