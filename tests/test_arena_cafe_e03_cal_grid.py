"""E03 negative/positive guards; never assert a scientific winner from fixtures."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import e03_cal_grid as e

class E03Grid(unittest.TestCase):
    def test_original_e02_nominal_failures_justify_grid_not_hidden_estimation(self):
        self.assertEqual(e.D_GRID['capacity_orders_min'],[0.5,1.0,2.0])
        self.assertEqual(e.D_GRID['response_minutes'],[0.25,1.0,4.0])
        self.assertEqual(e.D_GRID['loss_minutes_if_loss'],[2.0,8.0])
        self.assertEqual(e.M_GRID['maxThroughput_orders_hour'],[20,60,100])
        self.assertEqual(e.M_GRID['responseTime_hours'],[0.1,0.5,1.0])
        self.assertEqual(e.BANDS,(0.,1.,2.))
        self.assertEqual(e.OBSERVED,(0,0,2,4,6,8))

    def test_six_cuts_single_parameter_vector_no_marginal_envelope(self):
        # Two different variants each explain only part of a trajectory.
        # No operation may stitch their best coordinates into one candidate.
        a=[0,0,2,0,6,0]
        b=[0,0,0,4,0,8]
        self.assertTrue(any(abs(x-y)>1 for x,y in zip(a,e.OBSERVED)))
        self.assertTrue(any(abs(x-y)>1 for x,y in zip(b,e.OBSERVED)))
        self.assertEqual(e.CUTS,(0.,2.,4.,6.,8.,10.))

    @classmethod
    def setUpClass(cls):
        p=os.environ.get('E03_PUBLIC')
        if not p:
            raise unittest.SkipTest('Requires historical public O0 A1 input')
        cls.visible=e.load_public(Path(p))

    def test_d_full_grid_and_original_source_identity(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/'d'
            m=e.prepare_d(self.visible,out)
            self.assertEqual(m['candidate_count'],81)
            self.assertEqual(m['new_solver_targets'],81)
            self.assertEqual(m['exact_reused'],0)
            self.assertEqual(len(list(out.glob('*.mo'))),81)
            self.assertEqual((out/'simulate.mos').read_text().count('simulate('),81)
            self.assertEqual(len({(r['native_structure_hash'],
                         str(r['parameters'])) for r in m['candidates']}),81)
            self.assertEqual(sum(not r['loss'] for r in m['candidates']),27)
            self.assertEqual(sum(r['loss'] for r in m['candidates']),54)
            self.assertTrue(all('EXTERNAL' in r['origin'] for r in m['candidates']))
            with self.assertRaises(ValueError):
                e.prepare_d(self.visible,out)

    def test_m_only_six_exact_baseline_reused(self):
        p=os.environ.get('E03_M_HIST')
        if not p:
            self.skipTest('Requires original native M G2 artifact')
        with TemporaryDirectory() as tmp:
            m=e.prepare_m(self.visible,Path(tmp)/'m',Path(p))
            self.assertEqual(m['candidate_count'],54)
            self.assertEqual(m['new_solver_targets'],48)
            self.assertEqual(m['exact_reused'],6)
            self.assertEqual((Path(tmp)/'m/simulate.mos').read_text().count('simulate('),48)
            self.assertEqual(len(list((Path(tmp)/'m').glob('*_res.csv'))),6)
            self.assertEqual(sum('HISTORICAL' in x['origin'] for x in m['candidates']),6)
            self.assertEqual(len({x['full_variant_ast_sha256'] for x in m['candidates']}),54)
            self.assertEqual(len({x['native_base_ast_sha256'] for x in m['candidates']}),6)

    def test_g2_evaluator_cannot_claim_success_before_real_solver(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)/'d'
            e.prepare_d(self.visible,root)
            with self.assertRaises(FileNotFoundError):
                e.evaluate('D',self.visible,root)

if __name__=='__main__':
    unittest.main()