"""RF-02: original grammar and Short E1 inventory, no DES/OMC/LLM.

Reads public O0/O1 from the frozen A1 artifact only. The native D fixture is
its already committed, known-pulse demo and is NOT relabeled as EV-01.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import evidence
from scripts.arena_cafe import r2_observational_contracts as r2
from scripts.arena_v0_contract import ArenaContractError, digest

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"data/synthetic/arena_d_v01_visible.json"
BUDGET={"max_stocks":3,"allow_loss":True,"max_candidates":6,"max_simulations":0}


class RF02ContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get("RF02_PUBLIC_DIR")
        if not path:
            raise unittest.SkipTest(
                "Requires frozen source: RF02_PUBLIC_DIR with O0/O1 A1 views")
        root=Path(path)
        cls.views={cond:json.loads((root/(cond+"_VISIBLE.json")).read_text())
                   for cond in ("O0","O1")}

    def test_DA_legacy_source_preserved_and_full_grammar_intersection(self):
        self.assertTrue(r2.original_source_checks())
        original=json.loads(FIXTURE.read_text())
        cases=0
        for max_stocks in (1,2,3):
            for loss in (False,True):
                for count in (1,3,6):
                    for rate in (0.7,1.7):
                        view=deepcopy(original)
                        view["resources"].update({
                            "max_stocks":max_stocks,
                            "allow_loss":loss,
                            "max_candidates":count,
                            "max_simulations":0,
                        })
                        view["construction"]["input_profile"]["rate"]=rate
                        view["construction"]["observations"][-1]["delivered"]=rate
                        report=r2.legacy_intersection_conformance(view)
                        self.assertEqual("MATCH",
                                         report["order_structure_and_modelica_bytes"])
                        expected=min(count,max_stocks*(2 if loss else 1))
                        self.assertEqual(expected,report["candidate_count"])
                        self.assertEqual(0,report["solver_invocations"])
                        self.assertEqual("NOT_PROVEN",
                                         report["scientific_equivalence_for_POS"])
                        cases+=1
        self.assertEqual(36,cases)

    def test_DB_six_candidates_for_each_condition_and_no_D2_selection(self):
        for condition in ("O0","O1"):
            doc=r2.d_pos_contract(self.views[condition],condition,
                                  resources=BUDGET)
            self.assertEqual(6,doc["candidate_count"])
            self.assertEqual(6,len({x["structure_hash"] for x in doc["candidates"]}))
            self.assertEqual("NO_PARAMETERS_DECLARED",
                             doc["nominal_parameters_state"])
            self.assertFalse(doc["legacy_generate_called_with_pos"])
            self.assertFalse(doc["simulation_authorized"])
            self.assertEqual("NOT_RUN_SIGNAL_POLICY_MISSING",
                             doc["modelica_emission"])
            self.assertEqual(0,doc["solver_invocations"])
            self.assertIsNone(doc["observational_boundary"]["arrival_signal_hash"])
            self.assertEqual("POLICY_NOT_SELECTED_NO_RATE_INFERRED",
                             doc["observational_boundary"]["rate_conversion_policy"])
            self.assertTrue(all(x["selection_owner"]=="NONE" and
                                x["G2"]==x["G3"]=="NOT_RUN" and
                                x["modelica_sha256"] is None
                                for x in doc["candidates"]))
            self.assertEqual(15,
                             doc["observational_boundary"]["events_n"])
            self.assertEqual(15,
                             doc["observational_boundary"]["total_input_orders"])
            self.assertEqual([0,1,1,2,2,3],
                [len(x["structure"]["stocks"]) for x in doc["candidates"]])
            self.assertEqual([False,True]*3,
                [x["structure"]["loss"] for x in doc["candidates"]])
            self.assertFalse(doc["parameter_inference_by_original_D"])

    def test_nominals_require_independent_provenance_and_never_unlock_G2(self):
        params={
            "capacity":{"value":1.2,"unit":"orders/minute","status":"ASSUMED",
                        "actor":"INVESTIGATOR","source_kind":
                        "EXPLICIT_UNVALIDATED_ASSUMPTION","source_ref":"prospective-01"},
            "response_time":{"value":3.2,"unit":"minute","status":"ASSUMED",
                        "actor":"INVESTIGATOR","source_kind":
                        "EXPLICIT_UNVALIDATED_ASSUMPTION","source_ref":"prospective-01"},
            "loss_time":{"value":5.7,"unit":"minute","status":"ASSUMED",
                        "actor":"INVESTIGATOR","source_kind":
                        "EXPLICIT_UNVALIDATED_ASSUMPTION","source_ref":"prospective-01"},
        }
        valid=r2.d_pos_contract(self.views["O0"],"O0",
                                resources=BUDGET,nominal=params)
        self.assertEqual("EXPLICIT_EXTERNAL_VALUES_NOT_FITTED_BY_D",
                         valid["nominal_parameters_state"])
        self.assertFalse(valid["simulation_authorized"])
        self.assertEqual(0,valid["solver_invocations"])
        self.assertTrue(all(x["modelica_sha256"] is None
                            for x in valid["candidates"]))
        bad=deepcopy(params)
        bad["capacity"]["source_ref"]="e1_registry.capacity"
        with self.assertRaisesRegex(ArenaContractError,
                                    "R2_D_NOMINAL_NOT_INDEPENDENT_OR_UNATTRIBUTED"):
            r2.d_pos_contract(self.views["O0"],"O0",resources=BUDGET,nominal=bad)
        bad=deepcopy(params)
        bad["capacity"]["status"]="EXTERNALLY_ESTIMATED"
        with self.assertRaisesRegex(ArenaContractError,
                                    "R2_D_NOMINAL_STATUS_INCONSISTENT"):
            r2.d_pos_contract(self.views["O0"],"O0",resources=BUDGET,nominal=bad)
        bad=deepcopy(params)
        bad["capacity"]["value"]=0
        with self.assertRaisesRegex(ArenaContractError,
                                    "R2_D_NOMINAL_NONPOSITIVE"):
            r2.d_pos_contract(self.views["O0"],"O0",resources=BUDGET,nominal=bad)
        bad=deepcopy(params)
        del bad["loss_time"]
        with self.assertRaisesRegex(ArenaContractError,
                                    "R2_D_NOMINAL_COMPLETE_SCHEMA_REQUIRED"):
            r2.d_pos_contract(self.views["O0"],"O0",resources=BUDGET,nominal=bad)

    def test_DB_budget_respects_D_bounds_order_and_truncation(self):
        view=self.views["O0"]
        for n in (1,2,3):
            for loss in (False,True):
                for count in (1,2,5,6):
                    q={**BUDGET,"max_stocks":n,"allow_loss":loss,
                       "max_candidates":count}
                    out=r2.d_pos_contract(view,"O0",resources=q)
                    self.assertEqual(min(count,n*(2 if loss else 1)),
                                     out["candidate_count"])
                    self.assertEqual([x["structure_hash"] for x in
                        r2._grammar(q)], [x["structure_hash"] for x in
                        out["candidates"]])
        for invalid in (
            {**BUDGET,"max_stocks":4},
            {**BUDGET,"max_candidates":7},
            {**BUDGET,"max_simulations":7},
            {**BUDGET,"max_stocks":True},
            {**BUDGET,"forbidden_field":1},
        ):
            with self.subTest(budget=invalid), self.assertRaises(ArenaContractError):
                r2.d_pos_contract(view,"O0",resources=invalid)

    def test_arrival_source_unchanged_when_delivery_observations_change(self):
        original=self.views["O0"]
        changed=deepcopy(original)
        for row in changed["construction"]["observation_series"]:
            row["delivered_cumulative"]=0
        changed["source_snapshot_hash"]=digest({
            "schema":evidence.SCHEMA,
            "condition":"O0",
            "cutoff_minutes_exact":
                str(changed["observability"]["cutoff_minutes_exact"]),
            "construction":changed["construction"],
        })
        left=r2.d_pos_contract(original,"O0",resources=BUDGET)
        right=r2.d_pos_contract(changed,"O0",resources=BUDGET)
        self.assertNotEqual(left["public_source_snapshot_hash"],
                            right["public_source_snapshot_hash"])
        self.assertEqual(left["observational_boundary"],
                         right["observational_boundary"])
        self.assertEqual([x["structure_hash"] for x in left["candidates"]],
                         [x["structure_hash"] for x in right["candidates"]])
        self.assertEqual(left["candidate_count"],right["candidate_count"])

    def test_DB_rejects_O1_leak_and_future_pos_or_cross_condition(self):
        original=self.views["O0"]
        bad=deepcopy(original)
        bad["construction"]["physical_observation"]={"secret":"stage"}
        with self.assertRaisesRegex(ArenaContractError,"A1_CONSTRUCTION_SHAPE"):
            r2.d_pos_contract(bad,"O0",resources=BUDGET)
        bad=deepcopy(original)
        bad["construction"]["pos_arrival_events"][-1]["t_minutes_exact"]="11"
        with self.assertRaises(ArenaContractError):
            r2.d_pos_contract(bad,"O0",resources=BUDGET)
        with self.assertRaisesRegex(ArenaContractError,"A1_CROSS_CONDITION"):
            r2.d_pos_contract(original,"O1",resources=BUDGET)

    def test_M_base_six_AST_complete_three_structural_projections_only(self):
        for condition in ("O0","O1"):
            m=r2.m_base_universe(self.views[condition],condition)
            self.assertEqual(6,m["graph_count"])
            self.assertEqual(3,m["material_projection_group_count"])
            self.assertEqual([2,2,2],
                sorted(len(x["graph_ids"]) for x in m["material_projection_groups"]))
            self.assertEqual(6,len({x["full_ast_sha256"] for x in m["candidate_graphs"]}))
            self.assertTrue(all("ast" in x and
                                x["native_registry_parameters_preserved"] and
                                x["observational_selection"]=="NOT_RUN"
                                for x in m["candidate_graphs"]))
            self.assertEqual(["source","preparation","dispatch","receipt"],
                             m["mandatory_roles_are_priors"])
            self.assertFalse(m["material_projection_is_dynamic_equivalence"])
            self.assertTrue(m["original_component_complete"])
            self.assertFalse(m["arena_task_complete"])
            self.assertEqual("NONE",m["selection_actor"])
        m0=r2.m_base_universe(self.views["O0"],"O0")
        m1=r2.m_base_universe(self.views["O1"],"O1")
        self.assertEqual([x["full_ast_sha256"] for x in m0["candidate_graphs"]],
                         [x["full_ast_sha256"] for x in m1["candidate_graphs"]])

    def test_Hj_O0_O1_no_forced_stage_and_no_zero_score_for_missing(self):
        o0=r2.comparable_observables(self.views["O0"],"O0")
        o1=r2.comparable_observables(self.views["O1"],"O1")
        self.assertEqual(3,len(o0["operators"]))
        self.assertEqual(6,len(o1["operators"]))
        self.assertNotIn("physical_observation",str(o0))
        self.assertTrue(o1["no_scoring_absent_observables"])
        self.assertTrue(o1["no_native_stage_forced"])
        rows={x["observable"]:x for x in o1["operators"]}
        self.assertEqual("INPUT_NOT_SCORED",
                         rows["orders_created_cumulative"]["role"])
        self.assertEqual("MAY_INCLUDE_STOCKS_AND_LOST",
                         rows["orders_minus_delivered"]["per_arm"]["D"])
        self.assertEqual("NOT_COMPARABLE",
                         rows["mean_wait_minutes_exact"]["per_arm"]["M"])
        self.assertEqual("NO_IDENTIFIED_PREPARATION_STAGE",
                         rows["n_completed_stage_services"]["per_arm"]["D"])
        self.assertEqual("PENDING_REAL_NATIVE_MODEL_AND_TRANSLATION",
                         rows["delivered_cumulative"]["per_arm"]["B"])

    def test_R2_report_no_data_driven_selection_or_futurist_claims(self):
        for cond in ("O0","O1"):
            r=r2.build(self.views[cond],cond,BUDGET)
            self.assertEqual("PARTIAL_CONTRACT_AND_GRAMMAR_NO_NUMERICAL_POLICY",
                             r["R2"])
            self.assertEqual("NOT_SELECTED",r["temporal_input_policy"])
            self.assertEqual("NOT_RUN",r["R3"])
            self.assertEqual("PARTIAL",r["A3"])
            self.assertEqual("NOT_RUN",r["G4"])
            self.assertEqual("NOT_RUN",r["G5"])
            self.assertEqual(0,r["solver_invocations"])
            self.assertEqual(0,r["provider_calls"])
            self.assertEqual("PENDING",r["independent_scientific_review"])
            self.assertFalse(r["D"]["simulation_authorized"])


if __name__=="__main__":
    unittest.main()
