"""D1: adversarial finite-grid epistemic and mass-conservation checks."""
import csv
import json
import math
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.arena_v0_contract import INPUT_SCHEMA, ArenaContractError, digest
from scripts.arena_d_v01 import generate
from scripts.arena_d_v1_screen import (
    SCHEMA, ScreenError, assess, compare_omc_csv, integrate, validate_protocol,
    write_evaluation,
)


def fixture():
    profile={"kind":"pulse","rate":1.7,"duration":2.}
    params={"capacity":2.,"response_time":1.,"loss_time":3.}
    times=[0.,0.5,1.,1.5,2.,3.,4.,6.,8.]
    truth=integrate(2, False, params, profile, times, .01)
    observed=[{"t":t,"delivered":round(v+(0.007 if i%2 else -.004),6)}
              for i,(t,v) in enumerate(zip(times, truth))]
    observed[0]["delivered"]=0.
    return {
        "schema":INPUT_SCHEMA,"investigation_id":"D1-TEST","round_id":"R0",
        "question":"How could a pulse produce cumulative deliveries?",
        "source_snapshot_hash":"sha256:"+"3"*64,"iteration_limit":2,
        "construction":{"input_profile":profile,"nominal_parameters":params,
                        "observations":observed},
        "observability":{"stock_unit":"items","time_unit":"hour",
                         "observable":"cumulative_delivered"},
        "resources":{"max_stocks":3,"allow_loss":True,"max_candidates":6,
                     "max_simulations":6},
    }


def protocol():
    return {
        "schema":SCHEMA,"noise_absolute_bound":.035,
        "parameter_grid":{"capacity":[1.5,2.,2.5],
                          "response_time":[.7,1.,1.3],"loss_time":[2.,3.,5.]},
        "max_grid_evaluations":120,"integration_max_step":.02,
        "new_trial_sample_times":[.25,.5,.75,1.,1.5,2.,3.,4.,6.,8.],
    }


class D1Tests(unittest.TestCase):
    def test_genuine_stock_flow_integral_and_initial_zero(self):
        c=fixture()
        out=integrate(2,False,c["construction"]["nominal_parameters"],
                      c["construction"]["input_profile"],[0,.25,1,2,8],.01)
        self.assertAlmostEqual(out[0],0.,places=12)
        self.assertTrue(all(b>=a for a,b in zip(out,out[1:])))
        self.assertLessEqual(out[-1],3.4 + 1e-6)

    def test_search_reproducible_not_truth_claim(self):
        a=assess(fixture(),protocol())
        b=assess(fixture(),protocol())
        self.assertEqual(a,b)
        self.assertEqual(a["grid_evaluations"],108)
        self.assertEqual(a["method"],"FINITE_GRID_CONSTRUCTION_SCREEN_NOT_IDENTIFICATION")
        self.assertTrue(a["no_structural_falsification"])
        self.assertTrue(a["eligible_ids"])
        self.assertTrue(all(x["status"] in {
            "GRID_COMPATIBLE_NOT_IDENTIFIED","UNRESOLVED_GRID_NOT_FALSIFIED"}
            for x in a["results"]))
        self.assertTrue(any(x["stocks"]==2 and x["loss"] is False and
                            x["compatible_grid_points"]>=1 for x in a["results"]))

    def test_no_noise_bound_blocks_claims_of_compatibility(self):
        x=protocol()
        x["noise_absolute_bound"]=None
        r=assess(fixture(),x)
        self.assertEqual(r["conclusion"],"INSUFFICIENT_INSTRUMENT_INFORMATION")
        self.assertEqual(r["eligible_ids"],[])
        self.assertTrue(all(a["status"]=="UNCERTAINTY_UNSPECIFIED" for a in r["results"]))

    def test_grid_failure_does_not_falsify_structure(self):
        c=fixture()
        x=protocol()
        x["noise_absolute_bound"]=0.
        r=assess(c,x)
        self.assertEqual(r["conclusion"],"NO_GRID_FIT_NOT_STRUCTURAL_FALSIFICATION")
        self.assertTrue(all(e["status"]=="UNRESOLVED_GRID_NOT_FALSIFIED" for e in r["results"]))

    def test_physically_inconsistent_instrument_reading_is_flagged_not_used_as_gold(self):
        c=fixture()
        c["construction"]["observations"][-1]["delivered"]=100.
        r=assess(c,protocol())
        self.assertEqual(r["conclusion"],"OBSERVATION_CONTRADICTS_DECLARED_FAMILY_OR_INSTRUMENT_BOUND")
        self.assertIn("DELIVERED_EXCEEDS_INPUT",
                      [x["kind"] for x in r["physical_bound_issues"]])
        self.assertTrue(r["no_structural_falsification"])

    def test_unknown_and_malicious_fields_rejected(self):
        for bad in ("gold","reserve","other_arm_feedback"):
            x=fixture()
            x["construction"][bad]="secret"
            with self.subTest(bad=bad),self.assertRaises(ArenaContractError):
                assess(x,protocol())

    def test_grid_budget_and_invalid_noise_rejected(self):
        x=protocol()
        x["max_grid_evaluations"]=12
        with self.assertRaisesRegex(ScreenError,"GRID_BUDGET_EXCEEDED"):
            assess(fixture(),x)
        x=protocol()
        x["noise_absolute_bound"]=-.1
        with self.assertRaisesRegex(ScreenError,"INVALID_INSTRUMENT_BOUND"):
            assess(fixture(),x)

    def test_next_measurement_heuristic_does_not_claim_identification(self):
        x=protocol()
        x["noise_absolute_bound"]=.9
        r=assess(fixture(),x)
        self.assertGreaterEqual(len(r["eligible_ids"]),2)
        s=r["next_measurement"]
        self.assertEqual(s["kind"],"NEW_INDEPENDENT_RESET_TRIAL")
        self.assertIn(s["suggested_measurement_time"],x["new_trial_sample_times"])
        self.assertIn("Heuristic",s["caveat"])
        self.assertIn("NON_DISCRIMINATING",r["conclusion"])

    def test_event_artifacts_are_hash_linked_not_atms(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"d1"
            results=write_evaluation(fixture(),protocol(),dest)
            self.assertTrue((dest/"screen.json").exists())
            self.assertEqual(len(list(dest.glob("Dfit_*.mo"))),6)
            events=json.loads((dest/"memory-events.json").read_text())
            self.assertEqual(events[0]["event_type"],"HYPOTHESIS_PROPOSED")
            self.assertEqual(events[1]["previous_event_hash"],events[0]["event_hash"])
            self.assertEqual(events[1]["event_type"],"SIMULATION_REPORTED")
            self.assertEqual(events[1]["payload_hash"],digest(results))

    def test_omc_parity_fails_wrong_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"fake.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f)
                w.writerow(["time","delivered"])
                for i in range(12):w.writerow([i, 999.])
            with self.assertRaisesRegex(ScreenError,"MODEL_SIMULATOR_PARITY_FAILED"):
                compare_omc_csv(p,[(0.,0.),(1.,0.5)])

    def test_no_hidden_nonfinite_observations(self):
        c=fixture()
        c["construction"]["observations"][1]["delivered"]=math.inf
        with self.assertRaises(Exception):
            assess(c,protocol())


if __name__ == "__main__":
    unittest.main()
