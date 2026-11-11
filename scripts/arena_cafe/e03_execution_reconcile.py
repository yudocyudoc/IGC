"""E03 operational reconciliation from immutable GitHub Actions artifact ZIPs.

No solver, no provider, no scoring, no new data. Reads three original archived
artifacts and the frozen joint summary; verifies complete, comparable native
source identities and per-run exit/candidate counts. Physical executions and
scientific unique targets are separate accounting denominators.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import zipfile

SCHEMA = 'igc-arena-e03-operational-reconciliation/0.1'
RUNS = {
    'M_INITIAL': {'run_id': 42314268694, 'artifact_id': 13549599085, 'arm': 'M'},
    'D_FIRST': {'run_id': 42314519861, 'artifact_id': 13550500454, 'arm': 'D'},
    'D_REPEAT': {'run_id': 42315032070, 'artifact_id': 13550202824, 'arm': 'D'},
}


def _artifact(path, arm, role):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError('E03_ARTIFACT_ZIP_REQUIRED:' + str(path))
    raw_sha = sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        required = {'manifest.json','scores.json','simulate.mos',
                    'exit_code.txt','INVOCATION_STARTED','omc.log'}
        if not required <= names:
            raise ValueError('E03_INCOMPLETE_RUN_ARCHIVE:' + str(required - names))
        m = json.loads(z.read('manifest.json'))
        s = json.loads(z.read('scores.json'))
        declared = m['candidate_count']
        count = m['new_solver_targets']
        reused = m['exact_reused']
        prefix = 'E03D_' if arm == 'D' else 'E03M_'
        csvs = {name for name in names if name.startswith(prefix) and name.endswith('_res.csv')}
        if (m['arm'] != arm or s['arm'] != arm or
            declared != (81 if arm == 'D' else 54) or
            count != (81 if arm == 'D' else 48) or
            reused != (0 if arm == 'D' else 6) or
            len(m['candidates']) != declared or
            s['candidate_count'] != declared or
            s['comparable_count'] != declared or
            len(s['candidate_scores']) != declared or
            len(csvs) != declared or
            z.read('simulate.mos').count(b'simulate(') != count or
            z.read('exit_code.txt').strip() != b'0' or
            z.read('INVOCATION_STARTED').strip() != b'INVOCATION_STARTED' or
            s['status'] != 'FINITE_GRID_COMPLETE'):
            raise ValueError('E03_UNVERIFIED_EXECUTION_OR_INCOMPLETE_DENOMINATOR:' + role)
        if len({x['id'] for x in m['candidates']}) != declared:
            raise ValueError('E03_DUPLICATE_CANDIDATE_ID:' + role)
        # A run with all per-candidate outputs and exit=0 is evidence of
        # executions, but an archive cannot prove physical execution timing.
        identity = [(c['id'], c['parameters'],
                     c.get('modelica_sha256', c.get('full_variant_ast_sha256')))
                    for c in m['candidates']]
        return {'sha256_zip':'sha256:'+raw_sha,
                'manifest_sha256':'sha256:'+sha256(z.read('manifest.json')).hexdigest(),
                'scores_sha256':'sha256:'+sha256(z.read('scores.json')).hexdigest(),
                'omc_log_sha256':'sha256:'+sha256(z.read('omc.log')).hexdigest(),
                'solver_script_sha256':'sha256:'+sha256(z.read('simulate.mos')).hexdigest(),
                'new_solver_targets':count,'reused_historical_csv':reused,
                'candidate_count':declared,'csv_count':len(csvs),
                'source_snapshot_hash':m['source_snapshot_hash'],
                'signal_sha256':m['signal_sha256'],
                'original_input_identity':identity,
                'statuses':{'G3':s['G3'],'G4':s['G4'],'G5':s['G5']}}


def reconcile(m_zip,d_zip,duplicate_d_zip,joint_zip):
    seen = {
        'M_INITIAL': _artifact(m_zip,'M','M_INITIAL'),
        'D_FIRST': _artifact(d_zip,'D','D_FIRST'),
        'D_REPEAT': _artifact(duplicate_d_zip,'D','D_REPEAT')
    }
    if seen['D_FIRST']['original_input_identity'] != seen['D_REPEAT']['original_input_identity'] or \
       seen['D_FIRST']['signal_sha256'] != seen['D_REPEAT']['signal_sha256'] or \
       seen['D_FIRST']['solver_script_sha256'] != seen['D_REPEAT']['solver_script_sha256'] or \
       len({v['source_snapshot_hash'] for v in seen.values()}) != 1 or \
       len({v['signal_sha256'] for v in seen.values()}) != 1:
        raise ValueError('E03_REPEATED_RUN_NOT_IDENTICAL_SCIENTIFIC_TARGETS')
    with zipfile.ZipFile(joint_zip) as z:
        joint=json.loads(z.read('joint-summary.json'))
    if joint['status']!='FINITE_EXTERNAL_GRID_COMPLETE' or \
       joint['budget']['new_OMC'] != 129 or \
       joint['budget']['historical_reused'] != 6:
        raise ValueError('E03_HISTORICAL_JOINT_DIFFERENT_DO_NOT_REWRITE')
    unique_new = (seen['M_INITIAL']['new_solver_targets']+
                  seen['D_FIRST']['new_solver_targets'])
    physical = sum(x['new_solver_targets'] for x in seen.values())
    repeats = seen['D_REPEAT']['new_solver_targets']
    cap = joint['budget']['max_new_OMC']
    if (unique_new,repeats,physical,cap)!=(129,81,210,135):
        raise ValueError('E03_OPERATIONAL_CONSISTENCY_CHANGED')
    return {
        'schema':SCHEMA,
        'status':'RECONCILED_BUDGET_OVERRUN_PRESERVED',
        'study':'EV-01_DEVELOPMENT_EXTERNAL_GRID_NOT_NEW_INDEPENDENT_WORLD',
        'historical_joint_summary_sha256':'sha256:'+sha256(Path(joint_zip).read_bytes()).hexdigest(),
        'scientific_unique_candidate_variants':135,
        'scientific_unique_new_solver_targets':unique_new,
        'historical_csv_reused':seen['M_INITIAL']['reused_historical_csv'],
        'physical_omc_simulate_statements_executed':physical,
        'physical_omc_redundant_invocations':repeats,
        'original_budget_max_physical_simulations':cap,
        'physical_budget_overrun':physical-cap,
        'failed_D_preflight_zero_solver_run':42314268694,
        'no_new_scientific_candidates_from_duplicate':True,
        'no_new_solver_calls_to_reconcile':True,
        'retrospective_historical_results_untouched':True,
        'source_runs':{
            role:{'run_id':RUNS[role]['run_id'],'artifact_id':RUNS[role]['artifact_id'],
                  **{k:v for k,v in meta.items() if k!='original_input_identity'}}
            for role,meta in seen.items()},
        'budget_semantics':{
            'scientific_unique':'distinct candidate parameter signal combination',
            'physical_invocations':'actual verified OMC simulation outputs including rerun',
            'overrun':'physical - budget, no reinterpretation as scientific evidence'},
        'G4':'NOT_RUN','G5':'NOT_RUN','provider_calls':0,
    }


def main():
    parser=argparse.ArgumentParser()
    for key in ('m','d','d_repeat','joint'):
        parser.add_argument('--'+key.replace('_','-'),type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        raise FileExistsError('E03_RECONCILIATION_REFUSE_OVERWRITE')
    r=reconcile(args.m,args.d,args.d_repeat,args.joint)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
    print(json.dumps({'status':r['status'],
                      'physical':r['physical_omc_simulate_statements_executed'],
                      'overrun':r['physical_budget_overrun']},sort_keys=True))

if __name__=='__main__':
    main()