"""Ensure BOTH Modelica producers emit exact LF bytes on any OS.

Windows CRLF regression is reproduced by deliberately translating line endings
in a separate file and checking that the strict reader still rejects it.
"""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.arena_s_calibration import main as calibration_main
from scripts.arena_s_pilot_ci import setup
from scripts.arena_s_pilot_physics import (
    composer_bytes, composer_hash, verify_loaded_composer)
from scripts.arena_sp_producers import ProviderError
from scripts.compose_molecular_candidates import compose
from scripts.fm_b5_parameter_identifiability import sample_times, simulate

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((ROOT/p).read_text(encoding="utf-8"))


class CanonicalModelicaBytesTests(unittest.TestCase):
    def test_calibration_cli_emits_identical_canonical_bytes(self):
        plan=read("data/synthetic/fm_b3_dynamic_plan.json")
        plan["candidates"]=plan["candidates"][:2]
        composed=compose(plan,read("data/synthetic/fm_a_structural_candidates.json"))
        fit=read("data/synthetic/arena_s_pilot_fit_config.json")
        fit["parameter_ranges"]["maxThroughput"]={"minimum":1.6,"maximum":1.8,"step":0.2}
        fit["parameter_ranges"]["responseTime"]={"minimum":0.8,"maximum":1.0,"step":0.2}
        cal=fit["calibration"]
        primary={
            "observable_id":"delivered","unit":"units",
            "times":sample_times(cal["stop_time"],cal["observation_interval"]),
            "values":simulate(2,1.8,0.8,cal["input_amplitude"],
                cal["input_duration"],cal["stop_time"],
                cal["observation_interval"],fit["numerics"]["integration_step"]),
            "input_profile":{"kind":"pulse","amplitude":cal["input_amplitude"],
               "duration":cal["input_duration"],"initial_stocks_zero":True}}
        with TemporaryDirectory() as folder:
            root=Path(folder)
            for name,doc in (("base",composed),("plan",plan),("fit",fit),("primary",primary)):
                (root/(name+".json")).write_text(json.dumps(doc),encoding="utf-8")
            argv=["calibration","--composed",str(root/"base.json"),
                  "--plan",str(root/"plan.json"),"--fit-plan",str(root/"fit.json"),
                  "--primary",str(root/"primary.json"),"--out-dir",str(root/"out")]
            with patch.object(sys,"argv",argv):
                calibration_main()
            calibrated=json.loads((root/"out/calibrated-composed.json").read_text())
            eval_plan=json.loads((root/"out/evaluation-plan.json").read_text())
            model=root/"out/GeneratedMolecularCandidates.mo"
            self.assertEqual(model.read_bytes(),composer_bytes(eval_plan,calibrated))
            verify_loaded_composer(model,composer_hash(eval_plan,calibrated),
                                   eval_plan,calibrated)
            with_crlf=root/"old-windows/GeneratedMolecularCandidates.mo"
            with_crlf.parent.mkdir()
            with_crlf.write_bytes(model.read_bytes().replace(b"\n",b"\r\n"))
            with self.assertRaisesRegex(ProviderError,
                                        "LOADED_COMPOSER_NOT_CALIBRATED_MODEL"):
                verify_loaded_composer(with_crlf,composer_hash(eval_plan,calibrated),
                                       eval_plan,calibrated)

    def test_public_ci_setup_emits_identical_canonical_bytes(self):
        with TemporaryDirectory() as folder:
            out=Path(folder)/"public"
            setup(out)
            plan=json.loads((out/"evaluation-plan.json").read_text())
            composed=json.loads((out/"calibrated-composed.json").read_text())
            model=out/"calibration/GeneratedMolecularCandidates.mo"
            self.assertEqual(model.read_bytes(),composer_bytes(plan,composed))
            verify_loaded_composer(model,composer_hash(plan,composed),plan,composed)


if __name__=="__main__":
    unittest.main()
