"""Adversarial checks for a physically wrong but balance-consistent pulse.

No provider calls, no OpenModelica; generated files are explicitly synthetic.
"""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_s_pilot_physics import (
    COMPOSER, composer_bytes, composer_hash,
    verify_loaded_composer, verify_physical_input)
from scripts.arena_sp_producers import ProviderError
from scripts.compose_molecular_candidates import compose
from scripts.fm_b3_dynamic_evaluation import assess_trace

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((ROOT/p).read_text(encoding="utf-8"))


class PhysicalPilotTests(unittest.TestCase):
    def setUp(self):
        self.plan=read("data/synthetic/fm_b3_dynamic_plan.json")
        self.plan["candidates"]=self.plan["candidates"][:2]
        profile=read("data/synthetic/arena_s_pilot_fit_config.json")["held_out_discrimination"]
        self.plan["external_input"]["value"]=profile["input_amplitude"]
        self.plan["external_input"]["profile"]={
            "kind":"pulse","amplitude":profile["input_amplitude"],"offset":0.0,
            "period":2*profile["stop_time"],
            "width_percent":100*profile["input_duration"]/(2*profile["stop_time"]),
            "start_time":0.0}
        self.plan["simulation"]={"start_time":0.0,
            "stop_time":profile["stop_time"],"intervals":32}
        self.composed=compose(read("data/synthetic/fm_b3_dynamic_plan.json"),
                              read("data/synthetic/fm_a_structural_candidates.json"))

    @staticmethod
    def write(path, wrong=False, with_events=False):
        fields=["time","delivered","acceptedTotal","systemInventory","systemBalanceError",
                "terminalBalanceError","terminalArrivals",
                "waiting_stage0","cumulativeArrivals_stage0",
                "cumulativeCompletions_stage0","queueBalanceError_stage0"]
        rows=[]
        for i in range(33):
            t=i*.5
            accepted=0 if wrong else 3*min(t,2)
            row=dict.fromkeys(fields,0.0)
            row.update(time=t,acceptedTotal=accepted,
                       systemInventory=accepted,
                       waiting_stage0=accepted,
                       cumulativeArrivals_stage0=accepted)
            rows.append(row)
        # Native FM-B3's nominal grid uses 34 rows, including a repeated
        # endpoint sample; event-aware mode can accept additional duplicates.
        rows.append(dict(rows[-1]))
        if with_events:
            rows.extend([dict(rows[4]),dict(rows[4])])
            rows.sort(key=lambda row: row["time"])
        with path.open("w",newline="",encoding="utf-8") as stream:
            writer=csv.DictWriter(stream,fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_zero_input_trace_fails_physical_gate(self):
        with TemporaryDirectory() as folder:
            csv_path=Path(folder)/"fake.csv"
            self.write(csv_path,wrong=True)
            trace=assess_trace(csv_path,["stage0"],0.0,16.,32,
                               allow_extra_event_samples=True)
            self.assertEqual(trace["final_accepted_total"],0.0)
            with self.assertRaisesRegex(ProviderError,"PILOT_INPUT_TRACE_MISMATCH"):
                verify_physical_input(csv_path,self.plan)

    def test_valid_pulse_and_additional_event_rows(self):
        with TemporaryDirectory() as folder:
            csv_path=Path(folder)/"pulse.csv"
            self.write(csv_path,with_events=True)
            trace=assess_trace(csv_path,["stage0"],0.0,16.,32,
                               allow_extra_event_samples=True)
            self.assertEqual(trace["final_accepted_total"],6.0)
            self.assertGreaterEqual(trace["repeated_timestamp_count"],2)
            verify_physical_input(csv_path,self.plan)

    def test_different_composer_rejected_even_with_a_self_consistent_hash(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/COMPOSER
            correct=composer_bytes(self.plan,self.composed)
            path.write_bytes(correct)
            verify_loaded_composer(path,composer_hash(self.plan,self.composed),
                                   self.plan,self.composed)
            path.write_bytes(correct.replace(b"maxThroughput=2",b"maxThroughput=1"))
            with self.assertRaisesRegex(ProviderError,"LOADED_COMPOSER_NOT_CALIBRATED_MODEL"):
                verify_loaded_composer(path,composer_hash(self.plan,self.composed),
                                       self.plan,self.composed)


if __name__ == "__main__":
    unittest.main()
