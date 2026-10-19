import unittest

from scripts.f0_atms_probe import AtmsProbe, run_atms_probe
from scripts.f0_spike import overall_status, run_semantic_pipeline, source_and_annotation


class F0SpikeContractTests(unittest.TestCase):
    def test_atms_alternatives_can_coexist(self):
        atms = AtmsProbe()
        atms.assume("m1")
        atms.assume("m2")
        atms.justify(("m1",), "supports_m1")
        atms.justify(("m2",), "supports_m2")
        context = frozenset({"m1", "m2"})
        self.assertTrue(atms.supported_in("supports_m1", context))
        self.assertTrue(atms.supported_in("supports_m2", context))

    def test_atms_nogood_prunes_inconsistent_environment(self):
        atms = AtmsProbe()
        atms.assume("p")
        atms.assume("not_p")
        atms.justify(("p", "not_p"), "contradiction")
        atms.add_nogood(frozenset({"p", "not_p"}))
        self.assertEqual(atms.labels["contradiction"], set())

    def test_atms_labels_keep_only_minimal_environments(self):
        atms = AtmsProbe()
        atms.assume("a")
        atms.assume("b")
        atms.justify(("a",), "q")
        atms.justify(("a", "b"), "q")
        self.assertEqual(atms.labels["q"], {frozenset({"a"})})

    def test_atms_f0_probe_is_explicitly_prototype(self):
        result = run_atms_probe()
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["production_engine_selected"])

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
        self.assertTrue(annotation["id"].startswith("https://"))
        self.assertEqual(len(stages), 1)

    def test_semantic_spike_roundtrip_provenance_shacl_and_sparql(self):
        _, annotation = source_and_annotation()
        stages = run_semantic_pipeline(annotation)
        statuses = {stage["stage"]: stage["status"] for stage in stages}
        required = [
            "web_annotation_jsonld_roundtrip",
            "rdf_prov_mapping",
            "shacl_positive_and_negative",
            "sparql_query",
            "crminf_crmsci_mapping",
        ]
        self.assertEqual({name: statuses.get(name) for name in required},
                         {name: "PASS" for name in required})
        mapping = next(stage for stage in stages if stage["stage"] == "crminf_crmsci_mapping")
        self.assertEqual(mapping["crminf_version"], "1.2.1")
        self.assertEqual(mapping["crmsci_version"], "3.2")
        self.assertFalse(mapping["crminf_inference_asserted"])
        self.assertFalse(mapping["crmsci_observation_applicable"])


if __name__ == "__main__":
    unittest.main()
