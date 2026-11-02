#!/usr/bin/env python3
"""PC01/0.3: verification only, no provider, no solver, no DES generator.

Offline checks of contract, pricing ceilings, units, negative control, and
pure-reference algorithms. Modelica native port and B parity are NOT certified.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,math,statistics,unittest
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
PATH=HERE/'ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json'
OLD=HERE/'ARENA_PC01_CAF01_CONTRATO_CORREGIDO_v0_2_2026-10-28.json'
OLD_SHA='42300b47158c7514de0a919c79aa7b7a02b185fb52027077fb8c1d039e99ea60'

class PC01Error(ValueError):pass

def require(pred,reason):
    if not pred:raise PC01Error(reason)

def arrivals_midpoint(rate_per_min,duration_min=20):
    """Exact rational design event schedule only. NO DES execution."""
    lam=Fraction(str(rate_per_min)); duration=Fraction(duration_min)
    require(lam>0 and duration>0,'INVALID_PULSE')
    result=[]
    j=0
    while True:
        t=(Fraction(j)+Fraction(1,2))/lam
        if t>=duration: break
        result.append(t)
        j+=1
        require(j<=100,'EVENT_BUDGET')
    return result

def ref_scale(times,observed_construction,rate_con,rate_eval,duration=20):
    require(len(times)==len(observed_construction),'MISMATCH_REFERENCE_LENGTH')
    k=rate_eval/rate_con
    require(k>0,'NONPOSITIVE_SCALE')
    return [min(rate_eval*min(t,duration),k*dv)
            for t,dv in zip(times,observed_construction)]

def ref_capacity_from_construction(times,delivered,rate,margin=1.0):
    """Strictly design arrivals, not the richer event sidecar; construction only.

    This is an empirical release rate, NOT physical capacity estimation.
    """
    require(len(times)==len(delivered),'BAD_CAPACITY_INPUT')
    eligible=[]
    for i in range(1,len(times)):
        a,b=times[i-1],times[i]
        if b>20:continue
        require(b>a,'NONINCREASING_TIME')
        if rate*a-delivered[i-1]>margin and rate*b-delivered[i]>margin:
            eligible.append((delivered[i]-delivered[i-1])/(b-a))
    return statistics.median(eligible) if len(eligible)>=2 else None

def verify(c):
    require(c['schema']=='igc-arena-v3-caf01-pc01-protocol-draft/0.3','BAD_VERSION')
    require('NOT_FROZEN' in c['status'] and 'NOT_APPROVED' in c['status'],'PREMATURE_APPROVAL')
    require(c['source_commit']=='6f0ba57d175c10d31f762237287cb1e79cdaea41','SOURCE_DRIFT')
    require(c['source_proposal']['implementation_status']=='NOT_BUILT','DES_NOT_CONFIRMED')
    require(c['source_proposal']['parameters_or_topology']=='TO_BE_SEALED_PRIVATE_BEFORE_CONSTRUCTION','TRUTH_LEAK')
    require(c['boundary']['losses_allowed'] is False and c['boundary']['cancellations_allowed'] is False,'SOURCE_LOSS_DRIFT')
    w=c['worlds']; require(len(w)==2,'WORLD_COUNT')
    require(all(z['start_state']=='EMPTY_RESET' and z['stop_minutes']==40 and
                z['arrival']['kind']=='pulse' and z['arrival']['duration_minutes']==20 for z in w),'PULSE_DRIFT')
    rates=[x['arrival']['rate'] for x in w];require(rates==[1.2,1.5],'RATES_DRIFT')
    arrival_events=[arrivals_midpoint(x) for x in rates]
    require([len(x) for x in arrival_events]==[24,30],'BAD_EVENT_COUNTS')
    require(all(all(0<t<20 for t in seq) and all(b>a for a,b in zip(seq,seq[1:])) for seq in arrival_events),'EVENTS_OUTSIDE_HALF_OPEN_PULSE')
    require(c['source_proposal']['expected_event_counts_given_half_open_pulse']=={'construction':24,'evaluation':30},'DECLARED_COUNTS_DRIFT')
    require(c['source_proposal']['tie_order_at_equal_timestamps'].startswith('REQUIRED_BEFORE'),'UNJUSTIFIED_DES_GATE')
    tm=c['measurement_times_minutes']; require(tm==[0,5,10,15,20,30,40],'TIMES_CHANGED')
    u=c['unit_conversion']
    require(u['arrival_construction_rate_items_per_hour']==72 and u['arrival_evaluation_rate_items_per_hour']==90,'TIME_UNITS_RATE')
    require(math.isclose(u['pulse_duration_hours'],1/3) and math.isclose(u['forecast_horizon_hours'],2/3),'TIME_UNITS_HORIZON')
    require(all(math.isclose(t/60,h,rel_tol=0,abs_tol=1e-13) for t,h in zip(tm,u['observation_times_hours'])),'TIME_UNITS_SAMPLES')
    d=c['methods']['D']; b=c['methods']['B'];m=c['methods']['M'];v=c['budget']
    require(d['loss_variants']==[False] and d['max_topologies']==3 and d['topology_stock_counts']==[1,2,3], 'KNOWN_NO_LOSS_MODELS_MUST_BE_ONLY_ACTIVE_D')
    require('LOSS_TRUE' in d['excluded_legacy_topologies'],'LOSS_MODELS_NOT_ACCOUNTED_AS_EXCLUDED')
    dg=d['parameter_grid']; per_topology=len(dg['capacity_items_per_hour'])*len(dg['response_time_hours'])*len(dg['loss_time_hours'])
    require(per_topology==6 and d['construction_RK4_max']==3*per_topology==18,'D_MAIN_GRID_WRONG')
    require(d['CAF_N_RK4_max']==18 and v['Python_RK4_integrations_D']['CAF01_construction_max']==18 and v['Python_RK4_integrations_D']['CAF_N_masked_max']==18 and v['Python_RK4_integrations_D']['total_max']==36,'D_NEGATIVE_CONTROL_NOT_COSTED')
    require(all(x>0 for x in dg['capacity_items_per_hour']+dg['response_time_hours']+dg['loss_time_hours']),'D_GRID_NONPOSITIVE')
    require(b['current_native_translator_status']=='BLOCKED_NATIVE_SPECS_OUTSIDE_PINNED_G2_SCOPE' and b['local_adapter']=='NOT_IMPLEMENTED_NO_NATIVE_EQUATIONS_CHANGED','B_PARITY_NOT_ESTABLISHED')
    require(b['historical_specs']=={'startTime':0,'stopTime':8,'dt':0.125,'timeUnits':'hour','integrationMethod':'Euler'},'BUFFALO_HISTORIC_SCOPE_DRIFT')
    require(b['provider_calls_max']==2 and b['call_count_purpose']=={'CAF01_original_model_proposal':1,'CAFN_fresh_masked_diagnosis':1},'B_NEGATIVE_CONTROL_NOT_COSTED')
    require(b['negative_control_no_prior_history'] is True and b['negative_control_native_simulations_max']==0,'B_NEGATIVE_CONTROL_LEAK')
    require(m['structural_classes']==['C00','C01','C02'] and m['per_structure_max']==3 and len(m['proposed_bounded_capacity_grid_items_per_hour'])==3,'M_CAPACITY_GRID_COUNT')
    require(all(0.01<=v0<=100 for v0 in m['proposed_bounded_capacity_grid_items_per_hour']),'M_CAPACITY_OUTSIDE_CATALOG')
    require(all(0.1<=v0<=5 for v0 in m['frozen_response_time_hours'].values()),'M_RESPONSE_OUTSIDE_CATALOG')
    require(m['OpenModelica_construction_max']==m['OpenModelica_evaluation_max']==9 and m['CAFN_extra_candidate_solver_runs']==0,'M_RUNS_DRIFT')
    phys=v['OpenModelica_candidate_runs'];require(phys['D_construction_max']==3 and phys['D_evaluation_max']==3 and phys['D_total_max']==6,'D_OM_UNDERCOUNT')
    require(phys['B_construction_max']==phys['B_evaluation_max']==1 and phys['B_total_max']==2,'B_OM_UNDERCOUNT')
    require(phys['M_construction_max']==phys['M_evaluation_max']==9 and phys['M_total_max']==18,'M_OM_UNDERCOUNT')
    require(phys['construction_total_max']==phys['evaluation_total_max']==13 and phys['total_max']==26,'OM_SUM')
    require(v['CAF_N_extra_DES_worlds']==v['CAF_N_extra_OpenModelica']==0,'CAFN_HIDDEN_SOLVER')
    require(v['DES_world_runs']['total_max']==2,'DES_RUNS')
    require(v['provider_inferences']['Buffalo_max']==2 and v['provider_inferences']['Buffalo_CAF_N_max']==1,'B_TOTAL_PROVIDER_CALLS')
    require(v['actual_DES_runs']==v['actual_OpenModelica_runs']==v['actual_RK4_integrations']==v['actual_provider_calls']==0,'EXECUTIONS_NOT_AUTHORIZED')
    require(v['automatic_retries']==0,'NO_RETRIES')
    require('CAF_N' in c and 'CAF_N' not in c['out_of_scope'] and c['CAF_N']['status']=='PREPARATION_ONLY_NOT_EXECUTED','CAF_N_MISSING')
    require('t=0 and t=40min' in c['CAF_N']['mask'],'CAFN_NOT_A_MEASUREMENT_MASK')
    require(c['CAF_N']['methods']['B'].startswith('one independent stateless inference'),'CAFN_B_LEAK')
    require(c['REF_CAF']['actual_arrivals_sidecar_not_a_calibration_privilege'] is True,'REF_RICHER_INFORMATION')
    require('A_actual' in c['common_visible_legacy']['comparison_information_policy'],'INFORMATION_PARITY_UNDOCUMENTED')
    require(math.isclose(c['REF_SCALE']['rate_ratio'],1.25),'SCALING_CONTROL_CHANGED')
    require(len(c['metrics']['primary'])==1 and 'pending' not in c['metrics']['primary'][0].lower(),'DOUBLE_SCORING_DEPENDENT_OUTCOME')
    return {'status':'PC01_V03_OFFLINE_DESIGN_CHECKS_ONLY_NOT_NATIVE_SIMULATION','D_topologies':3,'D_RK4_main':18,'D_RK4_CAFN':18,'D_RK4_total':36,'OpenModelica_total':26,'Buffalo_inferences_budget':2,'DES_total':2,'actual_executions':0,'still_blocked':['B_LOCAL_PARITY','M_NATIVE_LINT','DES_SEAL','PARAMETER_APPROVAL','PREDICTION_SELECTION_LOCK','BUDGET_AUTHORIZATION']}

class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(PATH.read_text())
    def test_original_v02_preserved_unchanged(self):
        self.assertEqual(hashlib.sha256(OLD.read_bytes()).hexdigest(),OLD_SHA)
    def test_positive_contract(self):
        self.assertEqual(verify(self.c)['OpenModelica_total'],26)
    def test_pulse_discrete_total(self):
        self.assertEqual((len(arrivals_midpoint(1.2)),len(arrivals_midpoint(1.5))),(24,30))
        self.assertEqual(arrivals_midpoint(1.2)[0],Fraction(5,12))
        self.assertTrue(arrivals_midpoint(1.5)[-1]<20)
    def test_scale_ratio_without_future_measurement(self):
        t=[0,5,10,15,20,30,40];dc=[0,1,2,3,4,5,6]
        self.assertEqual(ref_scale(t,dc,1.2,1.5),[0,1.25,2.5,3.75,5,6.25,7.5])
    def test_ref_capacity_insufficient_data_abstains(self):
        t=[0,5,10,15,20,30,40]
        d=[1.2*min(x,20) for x in t]
        self.assertIsNone(ref_capacity_from_construction(t,d,1.2))
    def test_ref_capacity_empirical_not_hidden_true_cap(self):
        t=[0,5,10,15,20,30,40];d=[0,.2,1,2,3,6,12]
        self.assertAlmostEqual(ref_capacity_from_construction(t,d,1.2),.2)
    def test_reject_loss_graph_reenabled(self):
        x=copy.deepcopy(self.c);x['methods']['D']['loss_variants']=[False,True]
        with self.assertRaisesRegex(PC01Error,'KNOWN_NO_LOSS'):verify(x)
    def test_reject_missing_mask_budget(self):
        x=copy.deepcopy(self.c);x['budget']['Python_RK4_integrations_D']['CAF_N_masked_max']=0
        with self.assertRaisesRegex(PC01Error,'NEGATIVE_CONTROL'):verify(x)
    def test_reject_old_OM_count(self):
        x=copy.deepcopy(self.c);x['budget']['OpenModelica_candidate_runs']['total_max']=32
        with self.assertRaisesRegex(PC01Error,'OM_SUM'):verify(x)
    def test_reject_provider_one_call(self):
        x=copy.deepcopy(self.c);x['methods']['B']['provider_calls_max']=1
        with self.assertRaisesRegex(PC01Error,'B_NEGATIVE_CONTROL_NOT_COSTED'):verify(x)
    def test_reject_extra_des_run_for_CAF_N(self):
        x=copy.deepcopy(self.c);x['budget']['CAF_N_extra_DES_worlds']=1
        with self.assertRaisesRegex(PC01Error,'CAFN_HIDDEN_SOLVER'):verify(x)
    def test_reject_privileged_ref_arrivals(self):
        x=copy.deepcopy(self.c);x['REF_CAF']['actual_arrivals_sidecar_not_a_calibration_privilege']=False
        with self.assertRaisesRegex(PC01Error,'REF_RICHER_INFORMATION'):verify(x)
    def test_reject_approval_without_gates(self):
        x=copy.deepcopy(self.c);x['status']='APPROVED_FOR_EXECUTION'
        with self.assertRaisesRegex(PC01Error,'PREMATURE_APPROVAL'):verify(x)
    def test_reject_manipulated_assumptions(self):
        x=copy.deepcopy(self.c);x['methods']['M']['proposed_bounded_capacity_grid_items_per_hour']=[20,72,101]
        with self.assertRaisesRegex(PC01Error,'M_CAPACITY_OUTSIDE_CATALOG'):verify(x)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',default=str(PATH));p.add_argument('--tests',action='store_true');a=p.parse_args()
    c=json.loads(Path(a.contract).read_text())
    print(json.dumps(verify(c),sort_keys=True))
    if a.tests:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
        if not result.wasSuccessful():raise SystemExit(1)
