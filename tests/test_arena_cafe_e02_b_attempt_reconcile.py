"""Original two-provider-attempt archive guards and bitemporal F1a memory."""
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.arena_cafe.e02_b_attempt_reconcile import (
    NO_MODEL, SOURCE_RECEIPT_SHA256, inspect_attempt, reconcile,
)
from scripts.arena_atms import events_from_ledger, project
from scripts.ledger import Ledger
from datetime import datetime,timezone

STAMP=datetime(2026,11,7,0,50,tzinfo=timezone.utc) # replay ingest time, not event


class BAttemptEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        o0=os.getenv('E02_B_ORIGINAL_O0')
        o1=os.getenv('E02_B_ORIGINAL_O1')
        if not o0 or not o1:
            raise unittest.SkipTest('original B O0/O1 GitHub Actions artifacts required')
        cls.sources={'O0':Path(o0),'O1':Path(o1)}
        if not all(x.exists() for x in cls.sources.values()):
            raise ValueError('required source artifacts missing')

    def test_both_real_calls_are_failed_attempts_not_model_abstentions(self):
        results=[inspect_attempt(c,self.sources[c]) for c in ('O0','O1')]
        for r in results:
            self.assertEqual(r['normalized_status'],NO_MODEL)
            self.assertEqual(r['provider_attempt_count'],1)
            self.assertEqual(r['G0'],'NOT_REACHED_NO_NATIVE_MODEL')
            self.assertEqual(r['G3'],'NOT_RUN')
            self.assertFalse(r['model_returned'])
            self.assertEqual(r['provider_billing'],'UNKNOWN_NO_PROVIDER_USAGE_RECEIPT')
            self.assertEqual(r['revision_status'],'NOT_ATTEMPTED_NO_VALID_OWN_NATIVE_PARENT')
            self.assertTrue(r['source_status_is_misleading'])
        self.assertEqual(results[0]['arrival_signal_sha256'],results[1]['arrival_signal_sha256'])
        self.assertNotEqual(results[0]['source_snapshot_hash'],results[1]['source_snapshot_hash'])

    def test_mutated_receipt_is_rejected_against_actual_archived_sha(self):
        path=self.sources['O0']
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'bad'
            target.mkdir()
            if path.is_dir():
                import shutil
                shutil.copytree(path,target,dirs_exist_ok=True)
            else:
                with zipfile.ZipFile(path) as z:
                    z.extractall(target)
            receipt=target/'initial/receipt.json'
            obj=json.loads(receipt.read_text())
            obj['provider_calls']=0
            receipt.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,'LIVE_RECEIPT_SHA256_CHANGED'):
                inspect_attempt('O0',target)

    def test_ledger_and_atms_record_failed_attempt_without_fake_revision(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'ledger.sqlite'
            report=reconcile(self.sources['O0'],self.sources['O1'],db,STAMP)
            self.assertEqual(report['attempted_provider_calls'],2)
            self.assertEqual(report['native_models_returned'],0)
            self.assertEqual(report['revision_calls_attempted'],0)
            self.assertEqual(report['actual_provider_billing'],'UNKNOWN')
            self.assertTrue(report['no_automatic_retries'])
            ledger=Ledger(db,Path(__file__).resolve().parents[1]/'migrations/0001_ledger.sql')
            for c in ('O0','O1'):
                mem=report['memory'][c]
                self.assertFalse(mem['snapshots'][0]['no_native_evaluable'])
                self.assertTrue(mem['snapshots'][1]['no_native_evaluable'])
                self.assertFalse(mem['second_decision_issued'])
                stamp=mem['snapshots'][1]['at']
                records=ledger.snapshot(case_id='E02-B-'+c,as_known_at=stamp)
                engine,_=project(events_from_ledger(records),lane='B',investigation_id='E02-B-'+c,as_known_at=stamp)
                self.assertTrue(engine.explain('E02-B-'+c+':NO_NATIVE_EVALUABLE')['supported'])
                self.assertFalse(engine.explain('E02-B-'+('O1' if c=='O0' else 'O0')+':NO_NATIVE_EVALUABLE')['supported'])

if __name__=='__main__':unittest.main()