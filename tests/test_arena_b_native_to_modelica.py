import json
import unittest
from pathlib import Path
from scripts.arena_b_native_to_modelica import generate, TranslationBlocked

class BuffaloNativeTranslatorTests(unittest.TestCase):
    def model(self):
        return {"model": {
            "variables":[
                {"name":"pending work","type":"stock","equation":"0","units":"items",
                 "inflows":["arrivals"],"outflows":["completions"]},
                {"name":"delivered work","type":"stock","equation":"0","units":"items",
                 "inflows":["completions"],"outflows":[]},
                {"name":"arrivals","type":"flow","equation":"arrival_rate * pulse_shape",
                 "units":"items per hour","uniflow":True},
                {"name":"completions","type":"flow","equation":"pending_work // time_reference",
                 "units":"items per hour","uniflow":True},
                {"name":"arrival rate","type":"variable","equation":"1.7","units":"items per hour"},
                {"name":"time reference","type":"variable","equation":"1","units":"hour"},
                {"name":"pulse shape","type":"variable","equation":"TIME","units":"dimensionless",
                 "graphicalFunction":{"points":[{"x":0,"y":1},{"x":2,"y":1},{"x":2.001,"y":0}]}}],
            "relationships": [
                {"from":"arrivals","to":"pending work","polarity":"+"},
                {"from":"completions","to":"delivered work","polarity":"+"}
            ],"modules":[],"specs":{"startTime":0,"stopTime":8,"dt":0.125,"timeUnits":"hour"}}}

    def test_zero_safe_and_lookup_are_rendered_not_discarded(self):
        name,mo,report=generate(self.model())
        self.assertIn("if (time_reference) == 0 then 0",mo)
        self.assertIn("lookup_pulse_shape(time)",mo)
        self.assertIn("elseif x < 2.001",mo)
        self.assertEqual(report["status"],"TRANSLATED_WITH_EXPLICIT_LOOKUP_ASSUMPTIONS")
        self.assertNotIn("G0_FAITHFUL",report["status"])

    def test_negative_unresolved_variable_fails_closed(self):
        doc=self.model()
        doc["model"]["variables"][2]["equation"]="magic_not_declared"
        with self.assertRaisesRegex(TranslationBlocked,"UNKNOWN_SYMBOL"):
            generate(doc)

    def test_negative_bad_table_and_flow_topology_fail_closed(self):
        doc=self.model()
        doc["model"]["variables"][-1]["graphicalFunction"]["points"][1]["x"]=0
        with self.assertRaisesRegex(TranslationBlocked,"NON_MONOTONIC_GRAPHICAL_X"):
            generate(doc)
        doc=self.model()
        doc["model"]["variables"][0]["outflows"]=["arrivals"]
        with self.assertRaisesRegex(TranslationBlocked,"SAME_FLOW_BOTH_STOCK_PORTS"):
            generate(doc)

if __name__=="__main__":
    unittest.main()
