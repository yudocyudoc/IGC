"""Regression of the concrete gaps left by the selective main merge.

Numerical CSV fixtures below exercise dispatch and selection; they are synthetic
unit fixtures, never OpenModelica evidence. CI also runs the physical pipeline.
"""
import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_v0_first_round import run
from scripts.arena_v0_common_evidence import prepare as evidence
from scripts.arena_m3_common import prepare, write_models, evaluate
from scripts.arena_m_visible_verify import material_stock_ports
from scripts.arena_atms import project, ATMSError
from scripts.arena_memory import retrieve

ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/'data/synthetic/arena_v0_primary_construction.json').read_text())
CATALOG=json.loads((ROOT/'experiments/e0/catalog.json').read_text())


def fixtures(source, folder):
    visible=evidence(source)['arms']['M']['derived_input']
    prepared=prepare(visible)
    write_models(prepared,folder)
    for i,c in enumerate(prepared['native']['candidates']):
        ports=material_stock_ports({'arm_id':'M','method':'short-e1-one-minimal-molecular-candidate/0.1',
                                   'graph':c['graph']},CATALOG)
        with (folder/(c['id'].lower()+'_res.csv')).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['time','deliveredTotal',*ports])
            writer.writeheader()
            for step in range(81):
                t=step/20
                total=1.7*min(t,2)
                delivered=total*(i+1)/4
                writer.writerow({'time':t,'deliveredTotal':delivered,
                                 **{p:(total-delivered)/len(ports) for p in ports}})
    return visible,prepared


class CommonM3Tests(unittest.TestCase):
    def test_common_round_changes_selection_with_observations_not_case_name(self):
        for factor,chosen in ((.25,'C00'),(.5,'C01'),(0,None)):
            s=copy.deepcopy(SOURCE)
            s['observations']=[{'t':t,'delivered':1.7*min(t,2)*factor} for t in (0,1,2,4)]
            with tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'traces'
                fixtures(s,folder)
                result=run(s,m_csv_root=folder)
                self.assertEqual(result['arms']['M']['evaluation']['chosen_id'],chosen)
                self.assertEqual(result['arms']['B']['status'],'BLOCKED')
                self.assertEqual(result['provider_calls'],0)
                self.assertEqual(result['solver_calls'],0)  # replay, no fresh solver
                self.assertEqual(result['cross_arm_ranking'],'NOT_RUN')
                self.assertEqual(result['holdout'],'NOT_ACCESSED')

    def test_missing_trace_or_changed_model_cannot_be_evaluated(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'traces'
            visible,p=fixtures(SOURCE,folder)
            model=folder/(p['native']['candidates'][0]['class']+'.mo')
            model.write_bytes(model.read_bytes()+b'\n// changed')
            with self.assertRaisesRegex(ValueError,'MODELICA_CHANGED'):
                evaluate(visible,p,folder)
        with tempfile.TemporaryDirectory() as tmp:
            visible=evidence(SOURCE)['arms']['M']['derived_input']
            p=prepare(visible)
            folder=Path(tmp)/'traces';write_models(p,folder)
            with self.assertRaises(FileNotFoundError):evaluate(visible,p,folder)

    def test_budget_does_not_fall_back_to_old_m0(self):
        visible=evidence(SOURCE)['arms']['M']['derived_input']
        visible['resources']['max_simulations']=2
        with self.assertRaisesRegex(ValueError,'THREE_CANDIDATE_BUDGET'):prepare(visible)


class CurrentMemoryArms(unittest.TestCase):
    def test_b_and_m_private_hypotheses_and_historical_snapshot(self):
        at='2026-10-26T10:00:00Z';later='2026-10-26T11:00:00Z'
        events=[];knowledge=[]
        for arm in ('D','B','M'):
            common={'recorded_at':at,'access_policy':'lane:'+arm,'investigation_id':'I'}
            events.extend([{**common,'kind':'assumption','id':arm+'-support'},
                {**common,'kind':'justification','id':arm+'-rule',
                 'antecedents':[arm+'-support'],'consequent':arm+'-model','source_id':'trace'}])
            knowledge.append({**common,'kind':'knowledge','id':arm+'-knowledge',
                'title':'own model','text':'own feedback hypothesis','node_id':arm+'-model','source_id':'trace'})
        for arm in ('D','B','M'):
            engine,_=project(events,as_known_at=at,lane=arm,investigation_id='I')
            self.assertTrue(engine.labels.get(arm+'-model'))
            for other in {'D','B','M'}-{arm}:
                self.assertFalse(engine.labels.get(other+'-model'))
            packet=retrieve(investigation_id='I',lane=arm,as_known_at=at,
                            query='feedback',knowledge_records=knowledge,atms_events=events)
            self.assertIn(arm+'-knowledge',json.dumps(packet))
            for other in {'D','B','M'}-{arm}:self.assertNotIn(other+'-knowledge',json.dumps(packet))
        events.append({**events[2],'recorded_at':later,'active':False})
        old,_=project(events,as_known_at=at,lane='B',investigation_id='I')
        new,_=project(events,as_known_at=later,lane='B',investigation_id='I')
        self.assertTrue(old.labels.get('B-model'));self.assertFalse(new.labels.get('B-model'))
        with self.assertRaises(ATMSError):project(events,as_known_at=at,lane='C')


if __name__=='__main__':unittest.main()
