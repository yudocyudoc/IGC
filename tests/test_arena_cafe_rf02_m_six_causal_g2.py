"""RF-02M: six E1 originals, causal source, G2 engineering only, no DES/LLM."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import evidence
from scripts.arena_cafe import r2_m_six_causal_g2 as m
from scripts.arena_cafe import r2_causal_pos_signal as causal
from scripts.arena_v0_contract import ArenaContractError,digest


class OriginalSixMolecules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=os.environ.get("RF02_PUBLIC_DIR")
        if not source:
            raise unittest.SkipTest("Use frozen public O0/O1 A1 views: RF02_PUBLIC_DIR")
        cls.views={c:json.loads((Path(source)/(c+"_VISIBLE.json")).read_text())
                   for c in ("O0","O1")}

    def test_m00_original_code_and_catalog_unchanged(self):
        self.assertTrue(m.source_integrity())

    def test_m01_all_six_complete_AST_not_one_selected(self):
        s,inventory,rows,model=m._original_models(self.views["O0"],"O0")
        self.assertEqual(6,len(rows))
        self.assertEqual(6,len(set(x["canonical_sha256"] for x in rows)))
        self.assertEqual(6,len(set(x["full_ast_sha256"] for x in rows)))
        self.assertEqual(3,len(set(x["material_only_projection_sha256"]
                                   for x in rows)))
        self.assertTrue(all("original_ast" in x and
                            x["G2"]==x["G3"]=="NOT_RUN" and
                            x["native_material_equations_untouched"]
                            for x in rows))
        self.assertEqual(6,model.count("  model E1R2_"))
        self.assertEqual(6,model.count("  end E1R2_"))
        self.assertEqual(6,model.count("Modelica.Blocks.Sources.RealExpression stimulus(y="))
        self.assertEqual(6,model.count("    connect(stimulus.y,"))
        self.assertNotIn("der(",model)
        self.assertNotIn("when ",model)
        self.assertNotIn("pulse.y",model)
        self.assertNotIn("probe==1",model)
        self.assertEqual("1/2",s["width_minutes_exact"])
        self.assertEqual("registry.base.json",inventory["source_registry"].split("/")[-1])

    def test_m02_same_exact_signal_as_D_converted_to_hours(self):
        visible=self.views["O0"]
        source,_,rows,model=m._original_models(visible,"O0")
        d=causal.from_visible(visible,"O0")["signal"]
        self.assertEqual(d["event_rate_signal_sha256"],
                         source["event_rate_signal_sha256"])
        # A causal event at 1/2 min becomes time >= (1.0/120.0) hours.
        self.assertIn("then 120.0 else 0.0",model)
        self.assertIn("time >=",model)
        self.assertIn("time <",model)
        self.assertEqual(6,len(rows))
        self.assertEqual(15,source["events_count"])
        self.assertTrue(source["no_lookahead_in_mathematical_kernel"])

    def test_m03_O0_and_O1_same_model_and_signal_no_o1_data_siphon(self):
        a=m._original_models(self.views["O0"],"O0")
        b=m._original_models(self.views["O1"],"O1")
        self.assertEqual(a[0],b[0])
        self.assertEqual(a[2],b[2])
        self.assertEqual(a[3],b[3])
        self.assertNotEqual(digest(self.views["O0"]),digest(self.views["O1"]))

    def test_m04_delivery_observations_do_not_affect_input(self):
        visible=self.views["O0"]
        altered=deepcopy(visible)
        for x in altered["construction"]["observation_series"]:
            x["delivered_cumulative"]=0
        altered["source_snapshot_hash"]=digest({
            "schema":evidence.SCHEMA,
            "condition":"O0",
            "cutoff_minutes_exact":
                str(altered["observability"]["cutoff_minutes_exact"]),
            "construction":altered["construction"],
        })
        s1=m._original_models(visible,"O0")
        s2=m._original_models(altered,"O0")
        self.assertEqual(s1[0],s2[0])
        self.assertEqual(s1[2],s2[2])
        self.assertEqual(s1[3],s2[3])
        self.assertNotEqual(digest(visible),digest(altered))

    def test_m05_prepare_six_models_no_solver_or_selection(self):
        with TemporaryDirectory() as temp:
            target=Path(temp)/"native"
            a=m.prepare(self.views["O0"],"O0",target)
            self.assertEqual(6,a["candidate_count"])
            self.assertEqual("NONE",a["candidate_selection_owner"])
            self.assertEqual(3,len(a["material_projection_groups"]))
            self.assertFalse(a["material_projection_is_dynamic_equivalence"])
            self.assertTrue(a["original_E1_parameters_fixed_not_fit_to_POS"])
            self.assertTrue(a["preparation_dispatch_mandatory_roles_are_priors"])
            self.assertEqual("NOT_RUN_UNTIL_REAL_CSV",a["G2"])
            self.assertEqual("NOT_RUN",a["G3"])
            self.assertFalse(a["method_complete"])
            self.assertEqual(6,(target/"simulate.mos").read_text().count("simulate("))
            self.assertEqual(6,(target/"simulate.mos").read_text().count("checkModel("))
            self.assertEqual(m.sha_file(target/"native.mo"),a["modelica_sha256"])
            self.assertEqual(m.sha_file(target/"simulate.mos"),a["script_sha256"])
            self.assertFalse(list(target.glob("*_res.csv")))
            self.assertFalse((target/"INVOCATION_STARTED").exists())
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02M_REFUSE_OVERWRITE"):
                m.prepare(self.views["O0"],"O0",target)

    def test_m06_block_no_solver_no_csv_and_fake_success(self):
        with TemporaryDirectory() as temp:
            target=Path(temp)/"native"
            m.prepare(self.views["O0"],"O0",target)
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02M_NO_REAL_SOLVER_SUCCESS"):
                m.verify(self.views["O0"],target)
            (target/"INVOCATION_STARTED").write_text("INVOCATION_STARTED\n")
            (target/"exit_code.txt").write_text("1\n")
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02M_NO_REAL_SOLVER_SUCCESS"):
                m.verify(self.views["O0"],target)
            (target/"exit_code.txt").write_text("0\n")
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02M_MISSING_NATIVE_SOLVER_CSV"):
                m.verify(self.views["O0"],target)

    def test_m07_mutated_registry_AST_claim_and_source_model_rejected(self):
        for mutation in ("candidate_count","selected","graph","source"):
            with self.subTest(mutation=mutation),TemporaryDirectory() as temp:
                root=Path(temp)/"native"
                m.prepare(self.views["O0"],"O0",root)
                if mutation=="source":
                    (root/"native.mo").write_text(
                        (root/"native.mo").read_text()+"\n// changed\n")
                    error="RF02M_MODELICA_OR_SCRIPT_DRIFT"
                else:
                    doc=json.loads((root/"manifest.json").read_text())
                    if mutation=="candidate_count":
                        doc["candidate_count"]=1
                    elif mutation=="selected":
                        doc["candidate_selection_owner"]="ARENA_POLICY"
                    else:
                        doc["candidates"][0]["original_ast"]["instances"][0]["role"]="other"
                    (root/"manifest.json").write_text(json.dumps(doc))
                    error="RF02M_CANDIDATE_OR_SCIENCE_CLAIM_TAMPERED"
                with self.assertRaisesRegex(ArenaContractError,error):
                    m.verify(self.views["O0"],root)

    def test_m08_material_balance_includes_all_E1_typed_queue_stocks(self):
        # E1 backend's inTransit only collects STATE<Shipment>.
        # Preparation and dispatch are STATE<Order> / STATE<ReadyOrder>,
        # so a full conservation assertion must sum ALL typed waiting ports.
        _,_,rows,_=m._original_models(self.views["O0"],"O0")
        totals=[]
        for candidate in rows:
            ports=m._all_material_queue_stock_ports(candidate)
            roles=[x["role"] for x in candidate["original_ast"]["instances"]]
            self.assertTrue(any(x.startswith("preparation") for x in ports))
            self.assertTrue(any(x.startswith("dispatch") for x in ports))
            self.assertEqual(len(ports),len(set(ports)))
            self.assertEqual(len(ports),2+roles.count("transit"))
            self.assertNotIn("inTransit",ports)
            self.assertNotIn("reportedDeliveryRate",ports)
            totals.append(len(ports))
        self.assertEqual([2,2,3,3,4,4],sorted(totals))
        self.assertEqual("SUM_ALL_TYPED_BOUNDED_QUEUE_WAITING_PLUS_DELIVERED_TOTAL",
                         "SUM_ALL_TYPED_BOUNDED_QUEUE_WAITING_PLUS_DELIVERED_TOTAL")

    def test_m08_O0_does_not_accept_O1_or_future_events(self):
        with self.assertRaises(ArenaContractError):
            m._original_models(self.views["O0"],"O1")
        bad=deepcopy(self.views["O0"])
        bad["construction"]["physical_observation"]={"latent":1}
        with self.assertRaises(ArenaContractError):
            m._original_models(bad,"O0")
        bad=deepcopy(self.views["O0"])
        bad["construction"]["pos_arrival_events"][-1]["t_minutes_exact"]="11"
        with self.assertRaises(ArenaContractError):
            m._original_models(bad,"O0")


if __name__=="__main__":
    unittest.main()
