"""A1 H_j probes test numerics on labeled engineering fixtures, NOT native solver runs."""
from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import ev01, evidence, observation_eval, observation_ports
from scripts import arena_event_observability as obs
from scripts.arena_m_short_e1 import get_composer
from scripts.arena_v0_contract import ArenaContractError

REGISTRY=Path("experiments/e1/registry.base.json")


def write_csv(path,rows):
    with Path(path).open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ObservationEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        truth,checkpoints=ev01.trace_generator()
        ev01.verify_des_parity(checkpoints)
        cls.views=evidence.build(obs.project_events(truth,"POS"),
                                 obs.project_events(truth,"FULL"))["views"]
        composer=get_composer()
        cfg,classes,_=composer.load_registry(REGISTRY)
        key,graph=composer.enumerate_graphs(cfg,classes)[0]
        cls.candidate={"canonical_sha256":"sha256:"+key,"ast":graph}
        ids={r:[i["id"] for i in graph["instances"] if i["role"]==r][0]
             for r in ("source","preparation","receipt")}
        cls.ids=ids

    def test_missing_trace_is_true_abstention_for_both_conditions_and_methods(self):
        for condition in ("O0","O1"):
            for arm in ("D","M"):
                visible=self.views[condition]
                port=observation_ports.port(
                    visible,arm,condition,registry=REGISTRY if arm=="M" else None)
                result=observation_eval.evaluate(
                    visible,port,registry=REGISTRY if arm=="M" else None)
                self.assertEqual("ABSTAIN_NO_ADMISSIBLE_NATIVE_TRAJECTORY",result["status"])
                self.assertEqual([],result["comparisons"])
                self.assertEqual("NOT_ESTABLISHED",result["scientific_status"])
                self.assertEqual("NOT_PERFORMED",result["native_generation"])

    def test_numeric_D_fixture_evaluates_same_grid_without_claiming_fit(self):
        visible=self.views["O0"]
        port=observation_ports.d_port(visible,"O0")
        rows=[{"time":str(t),"inputRate":"1","delivered":str(t/2)}
              for t in range(11)]
        with TemporaryDirectory() as temp:
            file=Path(temp)/"fixture.csv";write_csv(file,rows)
            result=observation_eval.evaluate(visible,port,trace_csv=file)
        self.assertEqual("DESCRIPTIVE_HJ_PROBE_ONLY_UNVERIFIED_TRACE",result["status"])
        self.assertEqual(12,len(result["comparisons"]))
        self.assertEqual(11,result["sample_count"])
        arrivals=[x for x in result["comparisons"]
                  if x["observable"]=="orders_created_cumulative"]
        self.assertAlmostEqual(10,arrivals[-1]["native_prediction"])
        self.assertAlmostEqual(-5,arrivals[-1]["residual_orders"])
        self.assertEqual("NOT_ESTABLISHED",result["scientific_status"])

    def _m_rows(self):
        src=self.ids["source"]
        prep=self.ids["preparation"]
        return [
            {"time":format(t/60,".17g"),
             "deliveredTotal":str(t/2),
             src+".outflow":"60",
             prep+".completed":"30"}
            for t in range(11)]

    def test_numeric_M_fixture_uses_real_E1_role_ids_and_minutes_to_hours(self):
        visible=self.views["O1"]
        port=observation_ports.m_port(visible,"O1",REGISTRY)
        with TemporaryDirectory() as temp:
            file=Path(temp)/"fixture.csv";write_csv(file,self._m_rows())
            result=observation_eval.evaluate(
                visible,port,trace_csv=file,candidate=self.candidate,registry=REGISTRY)
        self.assertEqual(13,len(result["comparisons"]))
        source=[r for r in result["comparisons"]
                if r["observable"]=="orders_created_cumulative"]
        self.assertAlmostEqual(10,source[-1]["native_prediction"],places=6)
        prep=[r for r in result["comparisons"]
              if r["observable"]=="n_completed_stage_services"]
        self.assertEqual(1,len(prep))
        self.assertAlmostEqual(5,prep[0]["native_prediction"],places=6)
        self.assertIn("DISCRETE_COMPLETED_SERVICES",prep[0]["limit"])
        self.assertEqual("NOT_ESTABLISHED",result["scientific_status"])

    def test_reject_future_missing_sample_and_negative_rates(self):
        visible=self.views["O0"]
        port=observation_ports.d_port(visible,"O0")
        base=[{"time":str(t),"inputRate":"1","delivered":str(t/2)}
              for t in range(11)]
        with TemporaryDirectory() as temp:
            file=Path(temp)/"fixture.csv"
            for mod,code in (
                (base+[{"time":"11","inputRate":"1","delivered":"6"}],
                 "A1_TRACE_FUTURE_OR_NEGATIVE_TIME"),
                ([r for r in base if r["time"]!="4"],
                 "A1_TRACE_SAMPLE_TIME_MISSING_OR_AMBIGUOUS"),
                ([{**r,"inputRate":"-1"} if r["time"]=="3" else r for r in base],
                 "A1_TRACE_NEGATIVE_MATERIAL"),
                ([{**r,"delivered":"nan"} if r["time"]=="3" else r for r in base],
                 "A1_TRACE_NONFINITE"),
            ):
                write_csv(file,mod)
                with self.assertRaisesRegex(ArenaContractError,code):
                    observation_eval.evaluate(visible,port,trace_csv=file)

    def test_legitimate_rate_discontinuity_uses_left_and_right_event_sides(self):
        visible=self.views["O0"]
        port=observation_ports.d_port(visible,"O0")
        # Stock is continuous through t=5; inputRate legitimately jumps 1→0.
        rows=[
          {"time":"0","inputRate":"1","delivered":"0"},
          {"time":"2","inputRate":"1","delivered":"1"},
          {"time":"4","inputRate":"1","delivered":"2"},
          {"time":"5","inputRate":"1","delivered":"2.5"},
          {"time":"5","inputRate":"0","delivered":"2.5"},
          {"time":"6","inputRate":"0","delivered":"3"},
          {"time":"8","inputRate":"0","delivered":"4"},
          {"time":"10","inputRate":"0","delivered":"5"},
        ]
        with TemporaryDirectory() as temp:
            csvpath=Path(temp)/"event.csv";write_csv(csvpath,rows)
            report=observation_eval.evaluate(visible,port,trace_csv=csvpath)
            self.assertEqual("DESCRIPTIVE_HJ_PROBE_ONLY_UNVERIFIED_TRACE",report["status"])
            result=[r for r in report["comparisons"] if
                    r["observable"]=="orders_created_cumulative"]
            self.assertAlmostEqual(5.0,result[-1]["native_prediction"],places=9)
            # Same-time discontinuity in a *stock* is forbidden.
            changed=deepcopy(rows);changed[4]["delivered"]="3"
            write_csv(csvpath,changed)
            with self.assertRaisesRegex(ArenaContractError,"A1_TRACE_CONFLICTING_DUPLICATE_EVENT"):
                observation_eval.evaluate(visible,port,trace_csv=csvpath)

    def test_e1_structure_sha_does_not_allow_undeclared_parameter_change(self):
        o1=self.views["O1"]
        p=observation_ports.m_port(o1,"O1",REGISTRY)
        with TemporaryDirectory() as temp:
            trace=Path(temp)/"m.csv";write_csv(trace,self._m_rows())
            tampered=deepcopy(self.candidate)
            for inst in tampered["ast"]["instances"]:
                if inst["role"]=="preparation":
                    inst["parameters"]["maxThroughput"]=21
                    break
            # Canonical STRUCTURAL digest remains the same in native E1.
            composer=get_composer()
            self.assertEqual(tampered["canonical_sha256"],
                             "sha256:"+composer.canonical(tampered["ast"]))
            with self.assertRaisesRegex(ArenaContractError,
                                         "A1_M_CANDIDATE_PARAMETERS_NOT_FROZEN"):
                observation_eval.evaluate(o1,p,trace_csv=trace,
                                          candidate=tampered,registry=REGISTRY)

    def test_reject_swapped_port_or_untrusted_M_candidate(self):
        o0=self.views["O0"];o1=self.views["O1"]
        d=observation_ports.d_port(o0,"O0")
        with self.assertRaisesRegex(ArenaContractError,"A1_CROSS_CONDITION"):
            observation_eval.evaluate(o1,d)
        m=observation_ports.m_port(o1,"O1",REGISTRY)
        with TemporaryDirectory() as temp:
            file=Path(temp)/"m.csv";write_csv(file,self._m_rows())
            candidate=deepcopy(self.candidate)
            candidate["canonical_sha256"]="sha256:"+"0"*64
            with self.assertRaisesRegex(ArenaContractError,"A1_M_CANDIDATE_HASH_MISMATCH"):
                observation_eval.evaluate(o1,m,trace_csv=file,candidate=candidate,
                                          registry=REGISTRY)
            with self.assertRaisesRegex(ArenaContractError,
                                        "A1_HJ_M_REQUIRES_NATIVE_GRAPH_AND_REGISTRY"):
                observation_eval.evaluate(o1,m,trace_csv=file,registry=REGISTRY)


if __name__=="__main__":
    unittest.main()
