"""Exact signed candidate/trace mapping to prospective lock; synthetic only."""
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import digest
from scripts.arena_cafe.ct03_prospective_lock import seal
from scripts.arena_cafe.ct03_prediction_attestation import bind_signed_m_initial
from test_arena_ct03_prospective_lock import fixture as lock_fixture
from test_arena_ct03_execution_boundary import credentials, runner_fixture, signed


def evidence(root):
    _,secret,public,registry,archive_secret,archive_public=credentials(root)
    producer,manifest,parent,receipt,mo,csv,log,statement=runner_fixture(root)
    sources = root/"lock-sources"
    sources.mkdir()
    c,world,d,m,entries=lock_fixture(sources)
    row=next(x for x in entries["rows"] if x["arm"] == "M" and
             x["candidate_id"] == parent["canonical_sha256"])
    row["initial"]={
        "status":"PREDICTED", "native_sha256":statement["modelica_sha256"],
        "trace_sha256":statement["csv_sha256"],
        "receipt_sha256":statement["receipt_sha256"],
        "forecast":[{"time":6,"delivered":0.8},{"time":8,"delivered":1.2}],
    }
    row["final"]=copy.deepcopy(row["initial"])
    row["decision"]={
        "status":"RATIFIED","policy":"M-E1-OWN-FEEDBACK-SET/1.0",
        "feedback_hash":"sha256:"+"c"*64,
        "retrieved_item_id":("ct-CT03-W1-R0-M-C0-parent-" +
                             row["parent_hash"][7:]+":FEEDBACK"),
        "new_model_sha256":None,
    }
    lock=seal(c,world,d,m,entries)
    witness=signed(root,statement,"PHYSICAL_OMC","TEST_RUNNER",secret)
    package={
        "witness":witness,"trust_registry":registry,"public_key":public,
        "producer_root":producer,"manifest":manifest,"parent":parent,
        "receipt":receipt,"modelica_file":mo,
        "script_file":mo.parent/"simulate.mos",
        "csv_file":csv,"solver_log":log,
    }
    return lock,package,(c,world,d,m,entries),row


class SignedPredictionBindingTests(unittest.TestCase):
    def test_original_m_signed_claim_matches_exact_own_locked_trace(self):
        with TemporaryDirectory() as tmp:
            lock,package,_,row=evidence(Path(tmp))
            result=bind_signed_m_initial(lock,[package])
            self.assertEqual(result["linked_original_m_initial_count"],1)
            self.assertEqual(result["links"][0]["parent_hash"],row["parent_hash"])
            self.assertEqual(result["links"][0]["trace_sha256"],
                             row["initial"]["trace_sha256"])
            self.assertFalse(result["authentic_solver_execution_proven"])
            self.assertFalse(result["scientific_g2_granted"])
            self.assertFalse(result["evaluator_reveal_authorized"])
            self.assertEqual(result["new_omc"],0)

    def test_missing_duplicate_or_wrong_world_fails_without_release(self):
        with TemporaryDirectory() as tmp:
            lock,package,_,row=evidence(Path(tmp))
            with self.assertRaisesRegex(ValueError,"MISSING_OR_EXTRA_SIGNED_EXECUTION"):
                bind_signed_m_initial(lock,[])
            with self.assertRaisesRegex(ValueError,"MISSING_OR_EXTRA_SIGNED_EXECUTION"):
                bind_signed_m_initial(lock,[package,package])
            changed=copy.deepcopy(package)
            changed["witness"]=copy.deepcopy(package["witness"])
            changed["witness"]["statement"]["world_public_id"]="W2"
            changed["witness"]["statement_sha256"]=digest(changed["witness"]["statement"])
            with self.assertRaisesRegex(ValueError,"SIGNATURE_NOT_VERIFIED"):
                bind_signed_m_initial(lock,[changed])

    def test_self_consistent_alternate_trace_is_not_same_prospectively_locked_prediction(self):
        with TemporaryDirectory() as tmp:
            lock,package,inputs,row=evidence(Path(tmp))
            c,world,d,m,entries=inputs
            row["initial"]["trace_sha256"]="sha256:"+"f"*64
            row["final"]=copy.deepcopy(row["initial"])
            tampered_lock=seal(c,world,d,m,entries)
            with self.assertRaisesRegex(ValueError,
                     "SIGNED_TRACE_PARENT_OR_WORLD_DIFFERS_FROM_LOCK"):
                bind_signed_m_initial(tampered_lock,[package])

    def test_revision_d_and_b_cannot_reuse_initial_m_witness(self):
        with TemporaryDirectory() as tmp:
            lock,package,inputs,row=evidence(Path(tmp))
            c,world,d,m,entries=inputs
            row["decision"]["status"]="REVISED"
            row["decision"]["new_model_sha256"]="sha256:"+"d"*64
            row["final"]={
                "status":"PREDICTED",
                "native_sha256":"sha256:"+"d"*64,
                "trace_sha256":"sha256:"+"e"*64,
                "receipt_sha256":"sha256:"+"f"*64,
                "forecast":[{"time":6,"delivered":.6},{"time":8,"delivered":1.1}],
            }
            revised=seal(c,world,d,m,entries)
            with self.assertRaisesRegex(ValueError,"REVISED_M_NEEDS_DISTINCT"):
                bind_signed_m_initial(revised,[package])
            # Model A is D, not an M original. A valid D forecast slot
            # cannot be laundered through an M witness.
            row["decision"]={
                "status":"RATIFIED","policy":"M-E1-OWN-FEEDBACK-SET/1.0",
                "feedback_hash":"sha256:"+"c"*64,
                "retrieved_item_id":("ct-CT03-W1-R0-M-C0-parent-" +
                                     row["parent_hash"][7:]+":FEEDBACK"),
                "new_model_sha256":None,
            }
            row["final"]=copy.deepcopy(row["initial"])
            drow=next(x for x in entries["rows"] if x["arm"]=="D")
            drow["initial"]={
                "status":"PREDICTED","native_sha256":"sha256:"+"a"*64,
                "trace_sha256":"sha256:"+"b"*64,
                "receipt_sha256":"sha256:"+"c"*64,
                "forecast":[{"time":6,"delivered":.8},{"time":8,"delivered":1.2}],
            }
            drow["final"]=copy.deepcopy(drow["initial"])
            mixed=seal(c,world,d,m,entries)
            with self.assertRaisesRegex(ValueError,"D_OR_B_NEEDS_SEPARATE"):
                bind_signed_m_initial(mixed,[package])


if __name__=="__main__":
    unittest.main()
