#!/usr/bin/env python3
"""Construction-only admission tests, zero RK4/OMC/DES/provider calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from caf01_g3 import CONTRACT
from caf01_m_producer_admission import load_public, packet, generate, PUB

class TestIndependentMProducer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads(CONTRACT.read_text())

    def test_six_from_nine_only_and_no_cross_arm_info(self):
        p=packet(self.contract)
        self.assertEqual(p["allowed_arms"],["M"])
        self.assertEqual(len(p["six_structural_capacity_classes"]),6)
        self.assertEqual(len(p["nine_nominal_model_sources"]),9)
        self.assertEqual({v["structure"] for v in p["six_structural_capacity_classes"]},
                         {"C00","C01","C02"})
        self.assertEqual(
            [(v["capacity_items_per_hour"],v["nominal_capacity_aliases"])
             for v in p["six_structural_capacity_classes"][:2]],
            [(20,[20]),(72,[72,100])])
        self.assertEqual(p["budget"]["M_construction_OpenModelica_used_by_this_packet"],0)
        self.assertEqual(p["G2"],"NOT_RUN")
        self.assertNotIn("D_RK4_SCREEN",json.dumps(p))
        self.assertNotIn("G4_references",json.dumps(p))
        self.assertNotIn("D_G2_VERIFIED",json.dumps(p))

    def test_cafn_has_only_two_points_no_hidden_intermediates(self):
        p=packet(self.contract)
        views=p["public_construction_views"]
        self.assertEqual([x["t_min"] for x in views["CAFN"]["evidence"]["observations"]],
                         [0,40])
        self.assertEqual(len(views["CAF01"]["evidence"]["observations"]),7)
        self.assertEqual(views["CAFN"]["evidence"]["observations"][1]["delivered"],24)

    def test_reject_tampered_input_and_masks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for case in ("CAF01","CAFN"):
                (root/(case+".json")).write_bytes((PUB/(case+".json")).read_bytes())
            first=json.loads((root/"CAFN.json").read_text())
            first["observations"].insert(1,{"t_min":5,"delivered":3})
            (root/"CAFN.json").write_text(json.dumps(first))
            with self.assertRaisesRegex(ValueError,"M_OFFICIAL_CONSTRUCTION_BYTES_CHANGED"):
                load_public("CAFN",self.contract,root)
            with self.assertRaisesRegex(ValueError,"M_UNKNOWN_CONSTRUCTION_CASE"):
                load_public("DES_EVALUATION",self.contract,root)

    def test_frozen_m_parameters_and_source_generation(self):
        invalid=copy.deepcopy(self.contract)
        invalid["methods"]["M"]["proposed_bounded_capacity_grid_items_per_hour"]=[20,48,100]
        with self.assertRaisesRegex(ValueError,"M_METHOD_CONTRACT_CHANGED"):
            packet(invalid)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"m"
            result=generate(out)
            self.assertEqual(result["G2"],"NOT_RUN")
            self.assertTrue((out/"CAF01MPreflight.mo").is_file())
            self.assertEqual(len(list(out.glob("*.mos"))),0)
            with self.assertRaisesRegex(ValueError,"M_OUTPUT_ALREADY_EXISTS"):
                generate(out)

if __name__=="__main__":
    unittest.main()
