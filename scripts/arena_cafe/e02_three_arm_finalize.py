"""E02 single three-arm evidence packet: reuse D/M F1a and append actual B failures.

Does not alter original D/M report, historical SQLite or provider artifacts.
No model generation, simulation, native second-decision fabrication or new data.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil

from scripts.arena_v0_contract import canonical
from scripts.ledger import Ledger
from scripts.arena_atms import events_from_ledger, project
from scripts.arena_cafe.e02_b_attempt_reconcile import reconcile, ROOT, RUN_ID

SCHEMA = 'igc-arena-e02-three-arm-evidence-packet/0.1'
SOURCE_DM_RUN = 42322151421
REPLAY_TIME = '2026-11-07T00:50:00+00:00'


def _filehash(path: Path) -> str:
    return 'sha256:' + sha256(path.read_bytes()).hexdigest()


def _dm_snapshot_identity(ledger: Ledger, case: str, at: str) -> str:
    snap=ledger.snapshot(case_id=case,as_known_at=at)
    if len(snap) != 12:
        raise ValueError('E02_D_M_EVIDENCE_RECORD_COUNT_CHANGED:'+case)
    _, proj=project(events_from_ledger(snap),as_known_at=at,
                    investigation_id=case,lane=case.split('-')[1])
    return proj['projection_hash']


def combine(dm_report_path: Path, dm_ledger_path: Path, o0: Path,
            o1: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError('E02_COMBINED_REFUSE_OVERWRITE')
    report=json.loads(dm_report_path.read_text())
    if (report.get('case')!='EV-01' or
        report.get('status')!='E02_PARTIAL_B_NOT_RUN_D_M_POLICY_REVIEW_RECORDED' or
        report.get('OpenModelica_new_invocations')!=0 or
        report.get('OpenModelica_G2_reused')!=12 or
        report.get('Buffalo',{}).get('provider_calls')!=0):
        raise ValueError('E02_D_M_HISTORICAL_REPORT_DRIFT')
    if set(report.get('conditions',{}))!={'O0','O1'}:
        raise ValueError('E02_D_M_CONDITIONS_DRIFT')
    output.mkdir(parents=True)
    final_ledger=output/'combined_ledger.sqlite'
    shutil.copyfile(dm_ledger_path,final_ledger)
    ledger=Ledger(final_ledger,ROOT/'migrations/0001_ledger.sql')
    baseline={}
    for c in ('O0','O1'):
        for arm in ('D','M'):
            case='E02-'+arm+'-'+c
            row=report['conditions'][c][arm]
            if (row.get('candidate_count')!=6 or
                row.get('memory',{}).get('status')!=
                    'SCOPED_ATMS_EVIDENCE_BOUND_REVISION_NOT_EMPIRICAL_LEARNING' or
                row.get('decision',{}).get('author')!=
                    'EXPLICIT_EXPERIMENTAL_POLICY_NOT_ORIGINAL_ENUMERATOR' or
                row.get('decision',{}).get('second_decision',{}).get('status')!=
                    'RATIFY_UNRESOLVED_FULL_SET_WITH_EXPLICIT_LIMITS'):
                raise ValueError('E02_D_M_SCIENTIFIC_STATUS_CHANGED:'+case)
            at=row['memory']['cuts'][-1]['at']
            baseline[case]={'as_known_at':at,
                            'projection_hash':_dm_snapshot_identity(ledger,case,at)}
            if baseline[case]['projection_hash']!=row['memory']['cuts'][-1]['projection_hash']:
                raise ValueError('E02_D_M_LEDGER_AND_REPORT_MISMATCH:'+case)
    attempts=reconcile(o0,o1,final_ledger,
                       datetime.fromisoformat(REPLAY_TIME))
    if attempts['attempted_provider_calls']!=2 or attempts['native_models_returned']!=0:
        raise ValueError('E02_B_PROVIDER_RESULT_CHANGED')
    for case,stamped in baseline.items():
        if (_dm_snapshot_identity(ledger,case,stamped['as_known_at'])!=
                stamped['projection_hash']):
            raise ValueError('E02_B_APPEND_MUTATED_D_M_CASE:'+case)
    combined={
        'schema':SCHEMA,
        'case':'EV-01',
        'status':'E02_THREE_METHODS_ATTEMPTED_B_TIMEOUT_NO_NATIVE_MODEL_PARTIAL',
        'source_development_not_holdout':True,
        'source_dm_workflow_run_id':SOURCE_DM_RUN,
        'source_b_workflow_run_id':RUN_ID,
        'dm_report_sha256':_filehash(dm_report_path),
        'dm_original_ledger_sha256':_filehash(dm_ledger_path),
        'dm_report_unchanged':True,
        'dm_temporal_projections_preserved':baseline,
        'b_immutable_receipt_reconciliation_sha256':
            'sha256:'+sha256(canonical(attempts)).hexdigest(),
        'original_dm_buffalo_status':'BLOCKED_NOT_RUN_NOT_ABSTENTION',
        'updated_buffalo_status':'TWO_REAL_ATTEMPTS_TRANSPORT_TIMEOUT_NO_NATIVE',
        'conditions_assigned':2,
        'arms_assigned':['D','B','M'],
        'producer_condition_assignments':6,
        'producer_condition_attempts':6,
        'native_models_produced_or_original_candidates_comparable':4,
        'producer_condition_attempts_without_native':2,
        'buffalo_actual_provider_calls_attempted':2,
        'buffalo_cost_determined':'UNKNOWN_NO_PROVIDER_USAGE_OR_HTTP_RECEIPT',
        'buffalo_revision_calls_attempted':0,
        'buffalo_second_native_decisions':0,
        'dm_second_decisions':4,
        'dm_second_decision_author':'EXPLICIT_EXPERIMENTAL_POLICY_NOT_ORIGINAL_ENUMERATOR',
        'dm_remaining_candidates_per_condition':{'D':6,'M':6},
        'real_provider_calls_added_by_this_combiner':0,
        'new_omc_simulations_by_this_combiner':0,
        'G4':'NOT_RUN',
        'G5':'NOT_RUN',
        'E04':'D_M_LOCAL_ACTION_MAPPING_GAP_B_NOT_EVALUABLE',
        'E05':'BLOCKED_NO_ADMISSIBLE_LOCAL_ACTION_PREDICTION',
        'no_b_native_fabricated':True,
        'no_causal_O1_advantage_claimed':True,
        'conditions':{},
        'evidence_tiers':{
            'D_M':'ORIGINAL_G2_REUSED_DESCRIPTIVE_HJ_AND_EXTERNAL_POLICY',
            'B':'ORIGINAL_ENGINE_REAL_REQUEST_FAILED_PROVIDER_TRANSPORT',
        },
    }
    for c in ('O0','O1'):
        combined['conditions'][c]={}
        for arm in ('D','M'):
            a=report['conditions'][c][arm]
            combined['conditions'][c][arm]={
                'initial_native_candidates':a['candidate_count'],
                'G2':'HISTORICAL_AUTHENTIC_REAL_OMC_VERIFIED',
                'G3':'DESCRIPTIVE_ONLY_NO_EPSILON_MODEL',
                'feedback_memory':a['memory']['status'],
                'second_decision':a['decision']['second_decision']['status'],
                'decision_author':a['decision']['author'],
            }
        b=attempts['conditions'][c]
        combined['conditions'][c]['B']={
            'initial_provider_calls_attempted':b['provider_attempt_count'],
            'native_model_returned':False,
            'native_status':b['normalized_status'],
            'original_receipt_status':b['source_status_verbatim'],
            'original_receipt_sha256':b['evidence_member_sha256']['receipt'],
            'arrival_signal_sha256':b['arrival_signal_sha256'],
            'G0':b['G0'], 'G1':b['G1'], 'G2':b['G2'], 'G3':b['G3'],
            'second_decision':'NOT_MADE_NO_OWN_NATIVE_PARENT',
            'feedback': 'NOT_SENT_NO_OWN_NATIVE_MODEL',
            'memory_status':attempts['memory'][c]['status'],
            'support_before_after':[x['no_native_evaluable']
                                    for x in attempts['memory'][c]['snapshots']],
        }
    (output/'three_arm_report.json').write_bytes(canonical(combined)+b'\n')
    (output/'b_attempt_reconciliation.json').write_bytes(canonical(attempts)+b'\n')
    return combined


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dm-report',required=True,type=Path)
    p.add_argument('--dm-ledger',required=True,type=Path)
    p.add_argument('--o0',required=True,type=Path)
    p.add_argument('--o1',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    summary=combine(a.dm_report,a.dm_ledger,a.o0,a.o1,a.out)
    print(json.dumps({k:summary[k] for k in
          ('status','producer_condition_attempts','buffalo_actual_provider_calls_attempted',
           'buffalo_second_native_decisions','G4','G5')}))

if __name__=='__main__':main()