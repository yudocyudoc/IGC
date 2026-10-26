"""M3 negative and non-leakage tests, no remote provider or solver required."""
from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.arena_m3_prepare import ROOT, family, prepare
from scripts.arena_m3_select import decide, validate_case, validate_manifest, sample


class M3EvidenceSelectionTests(unittest.TestCase):
    def test_reuses_original_e1_six_graphs_three_observable_material_paths(self):
        cfg,classes,paths=family()
        self.assertEqual(set(paths),{0,1,2})
        self.assertEqual([sum(x["role"]=="transit" for x in paths[i][1]["instances"])
                          for i in (0,1,2)],[0,1,2])
        self.assertTrue(all(sum(x["role"]=="report" for x in v[1]["instances"])==0
                            for v in paths.values()))
        self.assertEqual([len(paths[i][1]["instances"]) for i in (0,1,2)],[4,5,6])

    def test_emits_five_original_backend_simulations_and_hides_source_key(self):
        # Preparation under repo root is required for trusted absolute Modelica
        # mount paths. The ephemeral test is deleted at context exit.
        with tempfile.TemporaryDirectory(prefix="m3test-",dir=ROOT) as temp:
            out=Path(temp)/"sample"
            prepare(out)
            manifest=json.loads((out/"candidate-manifest.json").read_text())
            candidates=validate_manifest(manifest)
            self.assertEqual(len(candidates),3)
            self.assertEqual(manifest["candidate_simulations"],3)
            self.assertEqual(manifest["world_simulations"],2)
            self.assertEqual(manifest["excluded_information_only_aliases"],3)
            text=(out/"M3Generated.mo").read_text()
            self.assertNotIn("der(",text)
            self.assertNotIn("when ",text)
            self.assertEqual(text.count("  model M3"),5)
            cmds=(out/"simulate.mos").read_text()
            self.assertEqual(cmds.count("simulate(ArenaM3Generated."),5)
            self.assertNotIn("expected_candidate_id",(out/"candidate-manifest.json").read_text())
            self.assertIn("expected_candidate_id",
                          (out/"grading"/"sealed-source-key.json").read_text())

    @staticmethod
    def scores(a,b,c):
        return [{"id":"C00","material_queues":2,"rmse_items":a},
                {"id":"C01","material_queues":3,"rmse_items":b},
                {"id":"C02","material_queues":4,"rmse_items":c}]

    def test_real_evidence_switches_structure_not_just_parameters(self):
        a=decide(self.scores(.003,.30,.65))
        b=decide(self.scores(.30,.003,.30))
        self.assertEqual(a["status"],"SELECTED_CONDITIONALLY")
        self.assertEqual(b["status"],"SELECTED_CONDITIONALLY")
        self.assertEqual((a["chosen_id"],b["chosen_id"]),("C00","C01"))

    def test_no_false_identification_when_not_discriminated_or_out_of_family(self):
        ambiguous=decide(self.scores(.012,.019,.4))
        self.assertEqual(ambiguous["status"],"ABSTAIN")
        self.assertEqual(ambiguous["reason"],"OBSERVATIONS_DO_NOT_DISCRIMINATE_FIXED_E1_PATHS")
        unknown=decide(self.scores(.25,.3,.5))
        self.assertEqual(unknown["status"],"ABSTAIN")
        self.assertEqual(unknown["reason"],"ALL_FIXED_E1_STRUCTURES_MISS_CONSTRUCTION_TOLERANCE")

    def test_blind_case_rejects_source_identity_reserved_or_rival(self):
        case={"schema":"igc-arena-m3-blind-construction-case/0.1",
              "case_id":"case-alpha",
              "construction_observations":[{"t":t,"delivered":v} for t,v in
                   zip([0,1,2,3],[0,.1,.3,.6])],
              "source_snapshot_hash":"sha256:"+"1"*64,
              "synthetic_measurement":True,
              "observability":"cumulative_delivered_items"}
        self.assertEqual(len(validate_case(case)),4)
        for key in ("generating_graph","reserved_observations","other_arm","holdout",
                    "world_class"):
            altered=copy.deepcopy(case)
            altered[key]="leak"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,
                    "M3_CASE_NOT_BLIND_OR_UNRECOGNIZED"):
                validate_case(altered)
        broken=copy.deepcopy(case)
        broken["construction_observations"][2]["delivered"]=float("nan")
        with self.assertRaisesRegex(ValueError,"M3_INVALID_OBSERVATIONS"):
            validate_case(broken)

    def test_omc_pulse_boundary_duplicate_event_rows_are_continuous(self):
        rows=[{"time":"1.0","deliveredTotal":"0.4"},
              {"time":"2.0","deliveredTotal":"1.2"},
              {"time":"2.000000000004","deliveredTotal":"1.200000000002"},
              {"time":"2.000000000004","deliveredTotal":"1.200000000002"},
              {"time":"3.0","deliveredTotal":"2.0"},
              {"time":"6.0","deliveredTotal":"3.4"},
              {"time":"6.0","deliveredTotal":"3.4"}]
        self.assertEqual(len(sample(rows,[1,2,3,6])),4)
        rows[2]["deliveredTotal"]="1.5"
        with self.assertRaisesRegex(ValueError,
                "M3_CONFLICTING_EVENT_TIME_DELIVERIES"):
            sample(rows,[2])

    def test_no_posthoc_threshold_edits(self):
        with tempfile.TemporaryDirectory(prefix="m3test-",dir=ROOT) as temp:
            out=Path(temp)/"out"
            prepare(out)
            original=json.loads((out/"candidate-manifest.json").read_text())
            for edit,val in [("predeclared_min_gap_rmse_items",0.0),
                             ("predeclared_max_best_rmse_items",1.0),
                             ("universe_count",3)]:
                altered=copy.deepcopy(original)
                altered[edit]=val
                with self.subTest(edit=edit),self.assertRaisesRegex(ValueError,
                        "M3_PROTOCOL_NOT_PREREGISTERED"):
                    validate_manifest(altered)


if __name__=="__main__":
    unittest.main()
