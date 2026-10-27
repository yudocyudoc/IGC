import unittest
from scripts.arena_v0_atms_support_probe import exercise
from scripts.arena_atms import ATMS, Rule

class ArenaAlternativeSupport(unittest.TestCase):
    def test_selective_retraction_and_shared_premise(self):
        out=exercise()
        self.assertEqual(out["status"],"ATMS_ALTERNATIVE_SUPPORT_AND_SELECTIVE_RETRACTION_PASS")
        self.assertEqual(len(out["before"]),2)
        self.assertEqual(len(out["after_one_support_removed"]),1)
        self.assertEqual(out["after_shared_premise_removed"],[])
        self.assertFalse(out["canonical_mutated"])
    def test_no_cross_path_invention(self):
        e=ATMS({"a","b"},set(),[Rule("a_only",("a",),"claim")],set())
        self.assertEqual(e.what_if(disable_assumptions={"a"})["changed_nodes"]["claim"]["after"],[])
        self.assertTrue(e.explain("claim")["supported"])
if __name__=="__main__":
    unittest.main()
