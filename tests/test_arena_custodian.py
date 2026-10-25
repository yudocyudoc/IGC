"""Private SQLite custodian tests; no real private reserve distributed via CI."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_custodian import (CustodyError, register, consume, read_receipt)
from scripts.arena_round import prepare,lock_round
from test_arena_round import fixture,submissions


class CustodianTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/"private-custody.sqlite"
        self.spec,self.primary,self.reserve=fixture()
        v=prepare(self.spec,self.primary)
        self.lock=lock_round(self.spec,v,submissions(v,self.spec),run_ref="actions/synthetic")

    def tearDown(self):
        self.tmp.cleanup()

    def test_private_salted_commitment_does_not_expose_gold(self):
        commitment=register(self.db,self.reserve)
        self.assertEqual(commitment["status"],"PREREGISTERED_PRIVATE_COMMITMENT")
        self.assertNotIn("values",commitment)
        self.assertNotIn(str(self.reserve["values"]),json.dumps(commitment))
        self.assertEqual(commitment["timing_attestation"],"LOCAL_CLOCK_ONLY_NOT_INDEPENDENT")

    def test_registration_refuses_duplicate_round_or_reserve(self):
        register(self.db,self.reserve)
        with self.assertRaisesRegex(CustodyError,"ALREADY_REGISTERED"):
            register(self.db,self.reserve)
        second=copy.deepcopy(self.reserve)
        second["reserve_id"]="RESERVE-02"
        with self.assertRaisesRegex(CustodyError,"ALREADY_REGISTERED"):
            register(self.db,second)

    def test_private_reserve_consumed_once_even_across_connections(self):
        register(self.db,self.reserve)
        report=consume(self.db,self.lock,self.reserve,custodian_ref="external-evaluator")
        self.assertEqual(report["consumption"],"HOLDOUT_CONSUMED_FOR_THIS_ROUND")
        self.assertEqual(report["blindness"],"NOT_ESTABLISHED_BY_SOFTWARE")
        receipt=read_receipt(self.db,self.reserve["reserve_id"])
        self.assertEqual(receipt["lock_hash"],self.lock["lock_hash"])
        self.assertEqual(receipt["status"],"HOLDOUT_CONSUMED")
        with self.assertRaisesRegex(CustodyError,"ALREADY_CONSUMED"):
            consume(self.db,self.lock,self.reserve,custodian_ref="different-evaluator")

    def test_unregistered_reserve_cannot_be_evaluated(self):
        with self.assertRaisesRegex(CustodyError,"NOT_PREREGISTERED"):
            consume(self.db,self.lock,self.reserve,custodian_ref="someone")

    def test_tampered_reserve_after_registration_refused(self):
        register(self.db,self.reserve)
        changed=copy.deepcopy(self.reserve)
        changed["values"][-1] = 999
        with self.assertRaisesRegex(CustodyError,"TAMPERED"):
            consume(self.db,self.lock,changed,custodian_ref="someone")
        # Failed evaluation does not consume legitimate reserve.
        consume(self.db,self.lock,self.reserve,custodian_ref="someone")

    def test_wrong_round_refused_before_evaluation(self):
        register(self.db,self.reserve)
        changed=copy.deepcopy(self.lock)
        changed["round_id"]="ANOTHER-ROUND"
        with self.assertRaisesRegex(ValueError, "LOCK_TAMPERED"):
            consume(self.db,changed,self.reserve,custodian_ref="someone")

    def test_receipt_is_available_only_after_consumption(self):
        register(self.db,self.reserve)
        with self.assertRaisesRegex(CustodyError,"UNKNOWN_OR_UNCONSUMED"):
            read_receipt(self.db,self.reserve["reserve_id"])

    def test_private_nonce_changes_commitment_for_equal_data(self):
        reserve2=copy.deepcopy(self.reserve)
        reserve2["round_id"]="ANOTHER-ROUND"
        reserve2["reserve_id"]="RESERVE-02"
        first=register(self.db,self.reserve)
        second=register(self.db,reserve2)
        self.assertNotEqual(first["commitment"],second["commitment"])


if __name__=="__main__":
    unittest.main()
