"""CAF-16 independent stochastic DES, frozen analyst, and sensor noise tests."""
from __future__ import annotations

from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import caf15a_two_capacity_witnesses as v15a
import caf16_stochastic_robustness as s

SHA="a"*40
HEAD="b"*40

class CAF16Tests(unittest.TestCase):
    def test_design_and_probabilities_are_frozen(self):
        self.assertEqual(s.CVS,("CV0","CV25","CV50"))
        self.assertEqual(s.ERRORS,("E0","E1"))
        self.assertEqual(s.PROGRAMS,("HIGH_T20","SHAPED_T14_T20"))
        self.assertEqual(s.REPS,12)
        self.assertEqual(len(s.physical_worlds()),30)
        self.assertEqual(sum(w["truth_class"] is not None
                             for w in s.physical_worlds()),27)
        self.assertEqual(len(s.shaped_arrivals()),34)
        self.assertEqual(s.shaped_arrivals()[0],Q(5,12))
        self.assertTrue(all(a<b for a,b in
                            zip(s.shaped_arrivals(),s.shaped_arrivals()[1:])))
        self.assertTrue(all(t<20 for t in s.shaped_arrivals()))
        self.assertEqual(len(s.arrival_pulse("5/2")),50)
        for cv,mult in s.MULTIPLIERS.items():
            self.assertEqual(sum(mult)/len(mult),Q(1))
            var=sum((z-1)**2 for z in mult)/len(mult)
            self.assertEqual(var,{
                "CV0":Q(0),"CV25":Q(1,16),"CV50":Q(1,4)
            }[cv])

    def test_independent_engine_parity_with_native_DES_CV0(self):
        # Both constant and piecewise arrival patterns; samples across all
        # classes and explicit fourth-stage topology.
        worlds=s.physical_worlds()
        select=[worlds[i] for i in (0,5,9,16,21,26,27,29)]
        for world in select:
            for name,(arrivals,times) in s.scenarios().items():
                independent=s.stochastic_engine(
                    world["config"],arrivals,times,"CV0",333)
                native=s.native_engine_snapshots(world["config"],arrivals,times)
                self.assertEqual(independent,native,(world["id"],name))
                for reading in independent:
                    self.assertEqual(
                        reading["accepted"],
                        reading["delivered"]+
                        sum(reading["waiting"])+sum(reading["in_service"]))

    def test_rng_substreams_reproducible_and_cv_changes_physics(self):
        config=s.physical_worlds()[10]["config"]
        arrivals,times=s.scenarios()["HIGH_T20"]
        first=s.stochastic_engine(config,arrivals,times,"CV50",123456)
        second=s.stochastic_engine(config,arrivals,times,"CV50",123456)
        self.assertEqual(first,second)
        different=s.stochastic_engine(config,arrivals,times,"CV25",123456)
        self.assertNotEqual(first,different)
        self.assertNotEqual(
            s.seed_for("SERVICE","W0",1,"CV25","K0"),
            s.seed_for("SENSOR","W0",1,"CV25","K0"))
        self.assertNotEqual(
            s.seed_for("SERVICE","W0",1,"CV25","K0"),
            s.seed_for("SERVICE","W0",2,"CV25","K0"))
        with self.assertRaisesRegex(ValueError,"CAF16_UNDECLARED_CV"):
            s.stochastic_engine(config,arrivals,times,"CV93",12)

    def test_sensor_E0_E1_paired_without_changing_physical_path(self):
        config=s.physical_worlds()[2]["config"]
        raw=s.physical_signatures(config,"PAIR",0,"CV50")
        self.assertEqual(len(raw["HIGH_T20"]),8)
        self.assertEqual(len(raw["SHAPED_T14_T20"]),14)
        self.assertEqual(raw,s.physical_signatures(config,"PAIR",0,"CV50"))
        for pid in s.PROGRAMS:
            exact=s.with_sensor_error(raw[pid],"PAIR",0,"CV50",pid,"E0")
            noisy=s.with_sensor_error(raw[pid],"PAIR",0,"CV50",pid,"E1")
            self.assertEqual(exact,raw[pid])
            self.assertTrue(all(abs(x-y)<=1 for x,y in zip(exact,noisy)))
            self.assertTrue(all(x>=0 for x in noisy))
            self.assertEqual(noisy,
                s.with_sensor_error(raw[pid],"PAIR",0,"CV50",pid,"E1"))
        with self.assertRaisesRegex(ValueError,"CAF16_UNDECLARED_ERROR"):
            s.with_sensor_error(raw["HIGH_T20"],"PAIR",0,"CV50",
                                "HIGH_T20","E7")

    def test_deterministic_analyst_bank_is_true_CAF15A_and_shaped_DES(self):
        bank=s.analyst_bank()
        self.assertEqual(len(bank),720)
        row_ids={r["id"] for r in bank}
        self.assertEqual(len(row_ids),720)
        for idx in (0,7,25,45,160,250,500,719):
            row=bank[idx]
            config=v15a.config_for(row["stages"],row["capacity_by_stage"])
            base=v15a.native_readings(config)
            self.assertEqual(row["signatures"]["HIGH_T20"],
                             base["F_R25_T20"])
            a,t=s.scenarios()["SHAPED_T14_T20"]
            native=s.native_engine_snapshots(config,a,t)
            shaped=(tuple(base["BASE"])
                    +s.observation(native[1],s.CHANNELS)
                    +s.observation(native[2],s.CHANNELS))
            self.assertEqual(row["signatures"]["SHAPED_T14_T20"],shaped)

    def test_analyst_only_receives_fixed_reading_not_true_topology(self):
        bank=s.analyst_bank()
        known=s.physical_worlds()[11]
        physical=s.physical_signatures(
            known["config"],known["id"],0,"CV0")
        for pid in s.PROGRAMS:
            classes=s.predict_classes(physical[pid],pid,bank)
            self.assertIn(known["truth_class"],classes)
        with self.assertRaisesRegex(ValueError,"CAF16_BAD_SENSOR_DIMENSION"):
            s.predict_classes((0,1),"HIGH_T20",bank)

    def test_full_run_is_reproducible_and_has_strata_without_fake_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"caf16"
            x=s.run(root,SHA,HEAD)
            self.assertEqual((x["n_worlds"],x["n_replicates"],
                              x["n_trajectories_before_sensor_perturbations"],
                              x["n_readings"],x["n_deterministic_candidates"]),
                             (30,12,1080,4320,720))
            self.assertTrue(x["stochastic_generator_independent_of_legacy_DES"])
            self.assertTrue(x["natural_overload_not_observed"])
            self.assertTrue(x["no_external_calibrated_service_or_sensor"])
            self.assertEqual(x["promotion_gate"],s.GATE)
            plan=json.loads((root/"00_PLAN_PRE_EVALUACION.json").read_text())
            self.assertEqual(plan["protocol_first_commit"],s.PROTO_COMMIT)
            self.assertTrue(plan["no_stochastic_world_generated_before_plan"])
            self.assertEqual(plan["n_readings"],4320)
            self.assertEqual(plan["catalog_sha256"],"sha256:"+sha256(
                (root/"00B_CATALOGO_PRE_EVALUACION.json").read_bytes()
            ).hexdigest())
            self.assertEqual(plan["pr_head_sha"],HEAD)
            self.assertEqual(plan["checkout_sha"],SHA)
            for pid in s.PROGRAMS:
                for cv in s.CVS:
                    for e in s.ERRORS:
                        row=x["summary"][pid][cv][e]
                        self.assertEqual((row["n_known"],row["n_unknown"]),(324,36))
                baseline=x["summary"][pid]["CV0"]["E0"]
                self.assertEqual(baseline["known_true_class_covered"],324)
            paired={}
            for r in x["observations"]:
                k=(r["world"],r["replicate"],r["cv"],r["program"])
                paired.setdefault(k,{})[r["sensor_error"]]=r
            self.assertEqual(len(paired),2160)
            for item in paired.values():
                a=item["E0"]; z=item["E1"]
                self.assertEqual(a["trajectory_id"],z["trajectory_id"])
                self.assertEqual(a["raw_physical_signature"],
                                 z["raw_physical_signature"])
                self.assertTrue(all(abs(u-v)<=1 for u,v in zip(
                    a["observed_signature"],z["observed_signature"])))
            manifest=json.loads((root/"03_MANIFIESTO.json").read_text())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual("sha256:"+sha256((root/name).read_bytes()).hexdigest(),digest)
            with self.assertRaisesRegex(ValueError,"CAF16_REFUSE_OVERWRITE"):
                s.run(root,SHA,HEAD)


if __name__=="__main__":
    unittest.main(verbosity=2)
