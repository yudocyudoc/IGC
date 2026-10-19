import unittest

from scripts.f0_spike import overall_status, source_and_annotation


class F0SpikeContractTests(unittest.TestCase):
    def test_pending_component_cannot_be_reported_as_pass(self):
        stages = [{"stage": "source", "status": "PASS"},
                  {"stage": "openmodelica", "status": "PENDING"}]
        self.assertEqual(overall_status(stages), "BLOCKED")

    def test_stub_cannot_be_reported_as_pass(self):
        stages = [{"stage": "candidate", "status": "STUB"}]
        self.assertEqual(overall_status(stages), "BLOCKED")

    def test_failure_takes_precedence_over_pending(self):
        stages = [{"stage": "rdf", "status": "PENDING"},
                  {"stage": "source", "status": "FAIL"}]
        self.assertEqual(overall_status(stages), "FAIL")

    def test_only_all_pass_can_report_pass(self):
        self.assertEqual(overall_status([{"status": "PASS"}, {"status": "PASS"}]), "PASS")

    def test_synthetic_claim_has_an_exact_source_anchor(self):
        stages, annotation = source_and_annotation()
        self.assertEqual(stages[0]["status"], "PASS")
        self.assertTrue(stages[0]["synthetic"])
        self.assertEqual(annotation["target"]["selector"]["exact"],
                         annotation["body"]["value"])
        self.assertEqual(stages[1]["status"], "PENDING")


if __name__ == "__main__":
    unittest.main()
