"""Offline gates for 2x2 quantitative System Dynamics prompt vs model-contract trial."""
import json
import unittest
from scripts import arena_sd_system_v21_factorial as ab

class Factorial21Tests(unittest.TestCase):
    def test_exact_manifest_and_order(self):
        man, jobs = ab.build()
        self.assertEqual(man["authorized_provider_calls"], 8)
        self.assertEqual([(x["case_id"], x["variant"]) for x in jobs], ab.ORDER)
        self.assertEqual(len({x["body_hash"] for x in jobs}), 8)
        self.assertEqual(man["retries"], 0)

    def test_user_identical_between_system_variants_for_each_contract_arm(self):
        _, jobs=ab.build()
        for case in ("WC","WD"):
            for flag in ("plain","contract"):
                group=[x for x in jobs if x["case_id"]==case and x["variant"].endswith(flag)]
                self.assertEqual(len(group),2)
                self.assertEqual(len({x["user_hash"] for x in group}),1)

    def test_structural_contract_only_in_contract_arm(self):
        _, jobs=ab.build()
        for job in jobs:
            body=job["body"]
            state=json.loads(body["messages"][1]["content"].removeprefix("State is: "))
            if job["variant"].endswith("_contract"):
                c=state["structural_contract"]
                self.assertEqual(len(c["candidate_equations"]),2)
                self.assertEqual(len(c["admissible_parameter_ranges"]),2)
                self.assertIn("d(delivered)/dt=f2(t)",c["candidate_equations"][1]["equations"])
            else:
                self.assertNotIn("structural_contract",state)
            self.assertNotIn("truth_commitment",body["messages"][1]["content"])
            self.assertEqual(body["max_completion_tokens"],4096)
            self.assertEqual(body["reasoning_effort"],"low")

    def test_parser_enforces_selection_ids_and_schema(self):
        accepted={"selected_candidate_ids":["urn:igc:candidate:CS-01"],
                  "rationale":"Plausible mass balance",
                  "falsifier":"New reset pulse would distinguish curvature",
                  "unknowns":["responseTime"],"next_test":"Early 0.1-hour observations"}
        self.assertEqual(ab.parse(json.dumps(accepted)),accepted)
        bad=dict(accepted,selected_candidate_ids=["CS-03"])
        with self.assertRaises(ValueError):ab.parse(json.dumps(bad))

    def test_physics_contract_conserves_mass_symbolically(self):
        man,_=ab.build()
        c=man["structural_contract"]
        self.assertEqual(c["units"]["u"],"units/hour")
        self.assertEqual(c["units"]["delivered"],"units")
        self.assertIn("dq1/dt=u(t)-f1(t)",c["candidate_equations"][0]["equations"])
        self.assertIn("dq2/dt=f1(t)-f2(t)",c["candidate_equations"][1]["equations"])

if __name__=="__main__":
    unittest.main()
