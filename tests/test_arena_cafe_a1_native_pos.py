"""A1 full native model emission: no DES/private spec or empirical parameter fitting."""
import unittest
import hashlib
from copy import deepcopy
from fractions import Fraction
from scripts.arena_cafe import ev01,evidence,native_pos_scenario as native
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError


class NativePOSScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw,snaps=ev01.trace_generator()
        ev01.verify_des_parity(snaps)
        cls.views=evidence.build(obs.project_events(raw,"POS"),
                                 obs.project_events(raw,"FULL"))["views"]

    def test_event_times_public_and_censored_not_latent(self):
        for condition in ("O0","O1"):
            v=self.views[condition]
            events=v["construction"]["pos_arrival_events"]
            self.assertEqual(15,len(events))
            self.assertEqual(Fraction(1,5),Fraction(events[0]["t_minutes_exact"]))
            self.assertTrue(all(Fraction(x["t_minutes_exact"])<10 for x in events))
            self.assertTrue(all(set(x)=={"case_id","t_minutes_exact"} for x in events))
            self.assertNotIn("resource_id",str(events))
            self.assertNotIn("transferencia_final",str(v))

    def test_native_D_M_same_public_mass_reconstruction_and_original_methods(self):
        for condition in ("O0","O1"):
            visible=self.views[condition]
            bins=native.bins_from_pos(visible,condition)
            self.assertEqual(20,len(bins))
            self.assertEqual(15,sum(x["orders"] for x in bins))
            self.assertEqual("1/2",bins[0]["end_minutes_exact"])
            emitted=[]
            for arm in ("D","M"):
                mo,mos,meta=native.build(visible,arm,condition)
                self.assertEqual("sha256:"+hashlib.sha256(mo.encode()).hexdigest(),
                                 meta["modelica_sha256"])
                self.assertEqual("sha256:"+hashlib.sha256(mos.encode()).hexdigest(),
                                 meta["mos_sha256"])
                self.assertEqual(15,meta["total_reconstructed_orders"])
                self.assertEqual("UNIFORM_MASS_PER_HALF_MINUTE_BIN_NOT_OBSERVED_RATE",
                                 meta["stimulus_semantics"])
                self.assertEqual(visible["source_snapshot_hash"],meta["source_snapshot_hash"])
                self.assertEqual(bins,meta["reconstruction_bins"])
                self.assertEqual("NOT_ESTABLISHED",meta["scientific_inference"])
                self.assertEqual("NOT_RUN_AT_EMISSION",meta["G2"])
                self.assertNotIn("transferencia_final",mo)
                self.assertNotIn("SPEC",mo)
                self.assertIn("numberOfIntervals=1000",mos)
                self.assertIn("native.mo",mos)
                self.assertIn('fileNamePrefix="native"',mos)
                self.assertIn("inputRate =",mo) if arm=="D" else self.assertIn("connect(stimulus.y,",mo)
                if arm=="D":
                    self.assertEqual("minute",meta["time_unit"])
                    self.assertEqual(2,len(meta["candidate"]["structure"]["stocks"]))
                    self.assertEqual(4,mo.count("der("))
                    self.assertIn("capacity = 0.333333333333",mo)
                else:
                    self.assertEqual("hour",meta["time_unit"])
                    self.assertEqual("E1_ORIGINAL_FIXED_REGISTRY_NOT_FITTED",
                                     meta["candidate"]["parameters_origin"])
                    self.assertIn("IGCMolecules.BoundedQueue",mo)
                    self.assertIn("package ArenaCafeM",mo)
                    self.assertNotIn("der(",mo)
                emitted.append(meta)
            self.assertEqual(emitted[0]["reconstruction_bins"],
                             emitted[1]["reconstruction_bins"])

    def test_pos_timeline_integrity_gate_before_simulation(self):
        v=deepcopy(self.views["O0"])
        v["construction"]["pos_arrival_events"][1]["t_minutes_exact"]="99"
        with self.assertRaisesRegex(ArenaContractError,
                                    "A1_POS_ARRIVALS_TIME_OR_ID"):
            native.build(v,"D","O0")
        v=deepcopy(self.views["O0"])
        v["construction"]["pos_arrival_events"][1]["t_minutes_exact"]="1"
        with self.assertRaisesRegex(ArenaContractError,
                                    "A1_POS_ARRIVALS_COUNT_PARITY|A1_SOURCE_DIGEST_MISMATCH"):
            native.build(v,"M","O0")
        with self.assertRaisesRegex(ArenaContractError,"A1_CROSS_CONDITION"):
            native.build(self.views["O0"],"D","O1")


if __name__=="__main__":unittest.main()
