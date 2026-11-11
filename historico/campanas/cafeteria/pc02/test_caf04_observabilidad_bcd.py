#!/usr/bin/env python3
"""CAF-04 tests: actual DES, conservation, sensor search, known-world limits."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf04_observabilidad_bcd as cf
from experiments.cafeteria.pc01 import caf01_des_engine as des


class ObservabilityTest(unittest.TestCase):
    def test_reuses_exact_bcd_worlds_and_declared_sensor_menu(self):
        worlds=cf.defined_worlds()
        self.assertEqual([x["id"] for x in worlds],["B","C","D"])
        self.assertEqual([x["capacity_h"] for x in worlds],[60]*3)
        self.assertEqual(len(cf.RATES),6)
        self.assertEqual(len(cf.TIMES),6)
        self.assertEqual(cf.FIELDS,("waiting","in_service","stage_stock"))
        for i,x in enumerate(worlds):
            ss=des.validate_private_config(x["config"])
            self.assertEqual([n for n,t in ss].index(1),i)
            self.assertEqual([t for n,t in ss],[1,1,1])

    def test_minimal_sensor_search_requires_three_distinct_world_signatures(self):
        mock={
            "B":{"waiting":[3,0,0],"in_service":[1,0,0],
                 "stage_stock":[4,0,0]},
            "C":{"waiting":[0,3,0],"in_service":[0,1,0],
                 "stage_stock":[0,4,0]},
            "D":{"waiting":[0,0,3],"in_service":[0,0,1],
                 "stage_stock":[0,0,4]},
        }
        solution=cf.separating_sets(mock,("waiting",))
        self.assertTrue(solution["separable"])
        self.assertEqual(solution["minimal_sensor_count"],2)
        self.assertEqual(solution["total_minimal_equivalent_solutions"],3)
        indistinguishable={
            k:{**v,"in_service":[1,1,1]} for k,v in mock.items()}
        self.assertIsNone(cf.separating_sets(indistinguishable,
                                            ("in_service",))[
                                                "minimal_sensor_count"])

    def test_actual_des_sweep_and_local_hashes_and_no_retries(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"observability"
            original=des.run_toy_engine
            calls=[]
            def instrument(config,arrivals,times):
                self.assertTrue((folder/"00_PLAN_INSTRUMENTACION.json").is_file())
                self.assertFalse((folder/"02_DIAGNOSTICO_SENSORES.json").exists())
                plan=json.loads((folder/"00_PLAN_INSTRUMENTACION.json").read_text())
                self.assertEqual(plan["DES_executed_before_plan"],0)
                self.assertEqual(tuple(plan["sensor_fields"]),cf.FIELDS)
                calls.append((config,len(arrivals)))
                return original(config,arrivals,times)
            with patch.object(des,"run_toy_engine",side_effect=instrument):
                value=cf.run(folder)
            self.assertEqual(value["DES_runs"],18)
            self.assertEqual(len(calls),18)
            self.assertEqual(value["observations_per_world"],36)
            self.assertEqual(len(value["cases"]),36)
            self.assertEqual(value["worlds"],["B","C","D"])
            self.assertEqual(value["DES_confirmatory_runs"],0)
            self.assertTrue(value["known_worlds_not_independent"])
            self.assertTrue(value["M_D_not_updated_for_new_sensors"])
            self.assertTrue(value["sensor_minima_computed_posthoc"])
            # "Indistinguishable" may apply to an observed sweep, not to
            # every possible flow/control input. Preserve actual flags.
            for c in value["cases"]:
                self.assertEqual(set(c["delivered_by_world"]),set("BCD"))
                self.assertEqual(set(c["stage_waiting_by_world"]),set("BCD"))
                self.assertEqual(set(c["sensors"]),
                                 {"waiting","in_service","stage_stock","all_nine"})
                for arm in "BCD":
                    self.assertEqual(len(c["stage_waiting_by_world"][arm]),3)
                    self.assertEqual(len(c["in_service_by_world"][arm]),3)
                    self.assertEqual(len(c["stage_stock_by_world"][arm]),3)
                for details in c["sensors"].values():
                    if details["separable"]:
                        self.assertIn(details["minimal_sensor_count"],
                                      range(1,10))
                    else:
                        self.assertIsNone(details["minimal_sensor_count"])
            self.assertEqual(len((folder/"03_OBSERVACIONES_ETAPAS.csv").read_text().splitlines()),
                             109)
            self.assertEqual(len((folder/"04_COMPARACION_SENSORES.csv").read_text().splitlines()),
                             37)
            m=json.loads((folder/"06_HASHES.json").read_text())
            self.assertFalse(m["external_custody"])
            for name,digest in m["files_sha256"].items():
                self.assertEqual(cf.lab.sha((folder/name).read_bytes()),digest)
            with self.assertRaisesRegex(ValueError,"CAF04_OUTPUT_ALREADY_EXISTS"):
                cf.run(folder)

    def test_total_pending_is_not_stage_specific(self):
        # If total accepted and total delivered agree, total waiting
        # (including service) necessarily agrees by physical conservation.
        with tempfile.TemporaryDirectory() as tmp:
            r=cf.run(Path(tmp)/"trial")
            for c in r["cases"]:
                if c["delivery_equivalent"]:
                    self.assertTrue(c["total_pending_equivalent"])
                if c["sensors"]["waiting"]["separable"]:
                    chosen=c["sensors"]["waiting"]["minimal_sensors"][0]
                    self.assertTrue(all(x["field"]=="waiting" for x in chosen))


if __name__=="__main__":
    unittest.main()
