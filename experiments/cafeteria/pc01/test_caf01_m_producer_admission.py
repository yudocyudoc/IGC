#!/usr/bin/env python3
"""Construction-only admission tests, zero RK4/OMC/DES/provider calls."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from caf01_g3 import CONTRACT
from caf01_m_producer_admission import (
    load_public, packet, generate, PUB, published_caf_model_sources,
)
from caf01_m_native_preflight import checked_models

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

    def test_all_nine_final_caf_hashes_match_generated_file_and_six_members(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"M"
            generate(out)
            package_bytes=(out/"CAF01MPreflight.mo").read_bytes()
            package=package_bytes.decode("utf-8")
            manifest=json.loads((out/"M_PRODUCER_PACKET.json").read_text())
            nine=manifest["nine_nominal_model_sources"]
            six=manifest["six_structural_capacity_classes"]
            sources=published_caf_model_sources(
                package,[r["model_name"] for r in nine])
            self.assertEqual(len(sources),9)
            self.assertEqual(len(six),6)
            self.assertEqual(
                manifest["published_CAF01MPreflight_mo_sha256"],
                "sha256:"+hashlib.sha256(package_bytes).hexdigest())
            old={r["name"]:r["model"] for r in checked_models(self.contract)}
            for row in nine:
                name=row["model_name"]
                final_hash="sha256:"+hashlib.sha256(
                    sources[name].encode("utf-8")).hexdigest()
                old_hash="sha256:"+hashlib.sha256(
                    old[name].encode("utf-8")).hexdigest()
                self.assertEqual(row["source_sha256"],final_hash)
                self.assertNotEqual(final_hash,old_hash)
                self.assertIn("publicRate=72;",sources[name])
            for row in six:
                self.assertEqual(
                    row["source_sha256"],
                    "sha256:"+hashlib.sha256(
                        sources[row["class_name"]].encode("utf-8")).hexdigest())

    def test_final_extractor_blocks_e1_or_truncated_package(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"M"
            p=generate(out)
            source=(out/"CAF01MPreflight.mo").read_text()
            names=[x["model_name"] for x in p["nine_nominal_model_sources"]]
            with self.assertRaisesRegex(ValueError,"M_UNREPLACED_E1_STIMULUS"):
                published_caf_model_sources(
                    source.replace("publicRate=72","publicRate=73"),names)
            with self.assertRaisesRegex(ValueError,"M_CAF_MODEL_SOURCE_EXTRACTION_MISMATCH"):
                published_caf_model_sources(source,names[:8])
            with self.assertRaisesRegex(ValueError,"M_CAF_FINAL_PACKAGE_SHAPE_CHANGED"):
                published_caf_model_sources(source[:-1],names)

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
