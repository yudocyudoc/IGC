"""One canonical E02 ledger with D/M and real failed B attempts, zero new calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.e02_three_arm_finalize import combine
from scripts.ledger import Ledger


class E02ThreeArmFinalizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths=[os.getenv('E02_DM_REPORT'),os.getenv('E02_DM_LEDGER'),
               os.getenv('E02_B_ORIGINAL_O0'),os.getenv('E02_B_ORIGINAL_O1')]
        if not all(paths):
            raise unittest.SkipTest('immutable D/M and B original CI artifacts required')
        cls.paths=[Path(x) for x in paths]
        if not all(p.exists() for p in cls.paths):
            raise ValueError('pinned artifact files missing')

    def test_single_ledger_six_assignments_and_no_model_for_B(self):
        with TemporaryDirectory() as d:
            out=Path(d)/'combined'
            r=combine(*self.paths,out)
            self.assertEqual(r['producer_condition_assignments'],6)
            self.assertEqual(r['producer_condition_attempts'],6)
            self.assertEqual(r['native_models_produced_or_original_candidates_comparable'],4)
            self.assertEqual(r['producer_condition_attempts_without_native'],2)
            self.assertEqual(r['buffalo_actual_provider_calls_attempted'],2)
            self.assertEqual(r['buffalo_second_native_decisions'],0)
            self.assertTrue(r['dm_report_unchanged'])
            self.assertEqual(r['G4'],r['G5'])
            self.assertEqual(r['G4'],'NOT_RUN')
            db=Ledger(out/'combined_ledger.sqlite',Path(__file__).resolve().parents[1]/'migrations/0001_ledger.sql')
            for c in ('O0','O1'):
                for arm in ('D','M','B'):
                    self.assertTrue(db.snapshot(case_id=f'E02-{arm}-{c}',
                        as_known_at=('2026-11-07T00:50:00+00:00' if arm=='B'
                         else r['dm_temporal_projections_preserved'][f'E02-{arm}-{c}']['as_known_at'])))
                b=r['conditions'][c]['B']
                self.assertEqual(b['G0'],'NOT_REACHED_NO_NATIVE_MODEL')
                self.assertEqual(b['support_before_after'],[False,True])
                self.assertEqual(b['second_decision'],'NOT_MADE_NO_OWN_NATIVE_PARENT')
                self.assertEqual(r['conditions'][c]['D']['decision_author'],
                                 'EXPLICIT_EXPERIMENTAL_POLICY_NOT_ORIGINAL_ENUMERATOR')

    def test_prior_dm_b_status_remains_preserved_as_source_not_overwritten(self):
        with TemporaryDirectory() as d:
            result=combine(*self.paths,Path(d)/'out')
            self.assertEqual(result['original_dm_buffalo_status'],
                             'BLOCKED_NOT_RUN_NOT_ABSTENTION')
            self.assertEqual(result['updated_buffalo_status'],
                             'TWO_REAL_ATTEMPTS_TRANSPORT_TIMEOUT_NO_NATIVE')
            original=json.loads(self.paths[0].read_text())
            self.assertEqual(original['Buffalo']['provider_calls'],0)
            self.assertEqual(original['Buffalo']['status'],
                             'BLOCKED_NOT_RUN_NOT_ABSTENTION')

    def test_changed_original_dm_provenance_fails_closed(self):
        with TemporaryDirectory() as d:
            test_report=Path(d)/'damaged_report.json'
            body=json.loads(self.paths[0].read_text())
            body['conditions']['O0']['D']['memory']['cuts'][-1]['projection_hash']='invalid'
            test_report.write_text(json.dumps(body))
            with self.assertRaisesRegex(ValueError,'E02_D_M_LEDGER_AND_REPORT_MISMATCH'):
                combine(test_report,self.paths[1],self.paths[2],self.paths[3],Path(d)/'out')


if __name__=='__main__':unittest.main()