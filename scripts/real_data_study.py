"""Chronological real-session replay. Raw/session artifacts remain under data/.
Run with PYTHONPATH=src:. and single-thread BLAS; use --workers for processes.
"""
from pathlib import Path
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import argparse, hashlib, json, pickle, tempfile, datetime, time
import numpy as np
import pandas as pd
from evfair.data import normalize, load_sessions, save_sessions, local_day, STEP
from evfair.forecast import DepartureModel
from evfair.metrics import metrics
from evfair.simulate import replay
from evfair.experiment import dumps, digest
import evfair.control as control
from scripts.audit_revision_order import ordered_input
from scripts.second_pass_diagnostics import lex_solver, forecast_rows, ORIGINAL

OUT=Path('results/real_data')
PRIVATE=Path('data/processed/real_study')
PROTOCOL=Path('config/real_data_protocol.json')
MPC={'point','point_history','stochastic','history','pf_mpc'}

def protocol():return json.loads(PROTOCOL.read_text())

def split_real(sessions, splits):
    result={};assigned=set()
    for name,(left,right) in splits.items():
        lo=int(pd.Timestamp(left,tz='America/Los_Angeles').timestamp()/STEP)
        hi=int(pd.Timestamp(right,tz='America/Los_Angeles').timestamp()/STEP)
        selected=[s for s in sessions if s.arrival>=lo and s.departure<hi]
        assert not assigned.intersection(s.sid for s in selected)
        assigned.update(s.sid for s in selected);result[name]=selected
    return result,len(sessions)-len(assigned)

def audit():
    p=protocol();OUT.mkdir(exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
    acquisition=json.loads((OUT/'acquisition.json').read_text());raw=Path(acquisition['raw_path'])
    assert digest(raw)==acquisition['sha256']
    blob=json.loads(raw.read_text());adjusted,pre=ordered_input(blob)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)/'ordered.json';tmp.write_text(json.dumps(adjusted));ss,norm,_=normalize(tmp,site=p['site'])
    parts,excluded=split_real(ss,p['splits']);rows=[]
    for name,subset in parts.items():
        save_sessions(subset,PRIVATE/(name+'.json'));counts=Counter(s.user for s in subset)
        row={'period':name,'sessions':len(subset),'users':len(counts),'repeat_users':sum(v>=5 for v in counts.values()),'observed_days':len({local_day(s.arrival) for s in subset}),'energy_revision_sessions':sum(len({r.energy for r in s.revisions})>1 for s in subset),'late_request_sessions':sum(s.revisions[0].at>s.arrival for s in subset)}
        rows.append(row)
        if name.startswith('test'):assert row['repeat_users']>=p['minimum_repeated_users_per_test_period'],row
    pd.DataFrame(rows).to_csv(OUT/'coverage.csv',index=False)
    train=parts['train'];events=Counter()
    for s in train:events[s.arrival]+=s.pmax;events[s.departure]-=s.pmax
    peak=0.;current=0.
    for t,delta in sorted(events.items()):current+=delta;peak=max(peak,current)
    result={'source_sha256':digest(raw),'preprocessing':pre,'normalization':norm,'outside_or_crossing_split_boundaries':excluded,'coverage':rows,'training_peak_kw':peak,'normalization_note':'6.6-kW ports and efficiency 0.92 are common modeled assumptions, not measured session power. Excluded sessions supply no background load.'}
    dumps(OUT/'data_audit.json',result);print(json.dumps(result,indent=2),flush=True)

def check_lock(create=False):
    files=[PROTOCOL,Path(__file__),Path('scripts/acquire_real_data.py'),Path('scripts/audit_revision_order.py'),Path('scripts/second_pass_diagnostics.py'),*sorted(Path('src/evfair').glob('*.py'))]
    state={'files':{str(p):digest(p) for p in files},'data_sha256':json.loads((OUT/'acquisition.json').read_text())['sha256'],'normalized_splits':{name:digest(PRIVATE/(name+'.json')) for name in protocol()['splits']}}
    lock=OUT/'protocol_lock.json'
    if lock.exists():
        old=json.loads(lock.read_text());assert old['state']==state,'Real-study source/data/protocol changed after lock'
    else:
        assert create,'Protocol not frozen'
        dumps(lock,{'locked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':state,'status':'Specified after synthetic results and coverage checks, before real-data controller evaluation; not external preregistration'})
    return state

def prepare():
    check_lock(create=True)
    if (PRIVATE/'model.pkl').exists():return
    train=load_sessions(PRIVATE/'train.json');cal=load_sessions(PRIVATE/'calibration.json')
    start=time.perf_counter();model=DepartureModel().fit(train,cal)
    with (PRIVATE/'model.pkl').open('wb') as f:pickle.dump(model,f)
    dumps(OUT/'forecast_fit.json',{'train_sessions':len(train),'calibration_sessions':len(cal),'scale':model.scale,'intercept':model.intercept,'elapsed_seconds':time.perf_counter()-start,'model_sha256':digest(PRIVATE/'model.pkl'),'training_cutoff_slot':model.cutoff})
    print('Forecast fitted on real training/calibration sessions',flush=True)

def label(period,frac,policy,cfg):return f'{period}_c{frac}_{policy}_g{cfg["gamma"]}_l{cfg["lam"]}'

class TracedController(control.Controller):
    def act(self,*args,**kwargs):
        decision=super().act(*args,**kwargs)
        # Keep every applied action but avoid gigabytes of unexecuted horizon plans.
        decision.plan=None
        return decision

def check_actions(frame,actions,sessions,capacity):
    assert not frame.sid.duplicated().any()
    assert np.allclose(frame.shortfall,np.maximum(1-frame.delivered/frame.requested,0),atol=1e-12,rtol=0)
    assert np.allclose(frame.excess,np.maximum(frame.delivered-frame.requested,0),atol=1e-9,rtol=0)
    if not len(actions):assert frame.delivered.sum()==0;return
    assert np.isfinite(actions[['power','battery_kwh','energy']].to_numpy()).all()
    assert actions.power.min()>=-1e-7 and actions.groupby('t').power.sum().max()<=capacity+1e-7
    starts={s.sid:s.arrival for s in sessions};ends={s.sid:s.departure for s in sessions};caps={s.sid:s.pmax for s in sessions};eta={s.sid:s.eta for s in sessions}
    assert (actions.t>=actions.sid.map(starts)).all() and (actions.t<actions.sid.map(ends)).all()
    assert (actions.power<=actions.sid.map(caps)+1e-7).all()
    assert np.allclose(actions.battery_kwh,actions.power*.25*actions.sid.map(eta),atol=1e-10,rtol=0)
    assert (actions.energy<=actions.request+1e-7).all()
    totals=actions.groupby('sid').battery_kwh.sum().reindex(frame.sid,fill_value=0).to_numpy()
    assert np.allclose(totals,frame.delivered,atol=1e-7,rtol=0)

def worker(job):
    period,frac,policy,cfg=job;check_lock()
    directory=PRIVATE/'runs'/label(*job);directory.mkdir(parents=True,exist_ok=True)
    if (directory/'summary.json').exists():return json.loads((directory/'summary.json').read_text())
    with (PRIVATE/'model.pkl').open('rb') as f:model=pickle.load(f)
    sessions=load_sessions(PRIVATE/(period+'.json'))
    cap=json.loads((OUT/'data_audit.json').read_text())['training_peak_kw']*frac
    controller=TracedController(policy,model,**cfg);stats=Counter()
    if policy in MPC:control.linprog=lex_solver(policy,stats)
    start=time.perf_counter()
    try:frame,diag,logs=replay(sessions,controller,cap,trace=True)
    finally:control.linprog=ORIGINAL
    actions=pd.DataFrame(logs['actions']);check_actions(frame,actions,sessions,cap)
    score={'period':period,'capacity_fraction':frac,'capacity_kw':cap,'policy':policy,**cfg,**metrics(frame),**diag,'elapsed_seconds':time.perf_counter()-start,'actions_verified':True,'solver_stats':dict(stats),'private_run':str(directory)}
    frame.to_csv(directory/'sessions.csv',index=False);actions.to_csv(directory/'actions.csv.gz',index=False)
    dumps(directory/'history.json',logs['updates']);dumps(directory/'config.json',dict(zip(['period','fraction','policy','config'],job)))
    dumps(directory/'summary.json',score)
    print(period,frac,policy,cfg,'tail',score['tail'],'seconds',round(score['elapsed_seconds'],1),flush=True)
    return score

def run_jobs(jobs,workers):
    with ProcessPoolExecutor(max_workers=workers) as pool:return list(pool.map(worker,jobs))

def configs(name,p):
    params=[(20.,0.)]
    if name in ['point','stochastic','pf_mpc']:params=[(g,0.) for g in p['gamma_grid']]
    elif name in ['history','point_history']:params=[(g,l) for g in p['gamma_grid'] for l in p['lambda_grid']]
    elif name=='debt_share':params=[(20.,l) for l in p['lambda_grid']]
    return [dict(gamma=g,lam=l,rho=p['rho'],horizon=p['horizon_steps']) for g,l in params]

def select(group,base):
    g=group.copy();g['delivery_deficit']=np.maximum(0,.98-g.delivered/base.delivered)
    feasible=g[(g.delivered>=.98*base.delivered)&(g.cost_per_kwh<=1.03*base.cost_per_kwh)]
    r=feasible.sort_values(['tail','cost_per_kwh','policy']).iloc[0] if len(feasible) else g.sort_values(['delivery_deficit','tail','policy']).iloc[0]
    return {k:float(r[k]) for k in ['gamma','lam','rho']}|{'horizon':int(r.horizon)}

def validate(workers):
    prepare();p=protocol();jobs=[('validation',p['primary_capacity_fraction'],name,cfg) for name in p['policies'] for cfg in configs(name,p)]
    rows=run_jobs(jobs,workers);frame=pd.DataFrame(rows);frame.drop(columns=['solver_stats','private_run']).to_csv(OUT/'validation_grid.csv',index=False)
    base=frame[frame.policy=='equal'].iloc[0];selected={name:select(g,base) for name,g in frame.groupby('policy')}
    fair=frame[frame.policy.isin(['equal','maxmin','debt_share','pf_mpc'])];fair=fair[(fair.delivered>=.98*base.delivered)&(fair.cost_per_kwh<=1.03*base.cost_per_kwh)]
    comparator=fair.sort_values(['tail','cost_per_kwh','policy']).iloc[0].policy
    result={'locked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'comparator':comparator,'selected':selected,'validation_sha256':digest(OUT/'validation_grid.csv'),'protocol_lock_sha256':digest(OUT/'protocol_lock.json')}
    lock=OUT/'selection_lock.json'
    if lock.exists():
        previous=json.loads(lock.read_text());assert previous['selected']==selected and previous['comparator']==comparator
    else:dumps(lock,result)
    print('VALIDATION LOCK',comparator,selected,flush=True)

def evaluate(workers):
    check_lock();p=protocol();lock=json.loads((OUT/'selection_lock.json').read_text())
    assert lock['protocol_lock_sha256']==digest(OUT/'protocol_lock.json')
    jobs=[(period,p['primary_capacity_fraction'],name,lock['selected'][name]) for period in ['test_q3','test_q4'] for name in p['policies']]
    jobs += [('test_q3',frac,name,lock['selected'][name]) for frac in p['sensitivity_capacity_fractions'] for name in p['sensitivity_policies']]
    rows=run_jobs(jobs,workers)
    pd.DataFrame(rows).drop(columns=['solver_stats','private_run']).to_csv(OUT/'test_scores.csv',index=False)
    dumps(OUT/'run_index.json',[{k:r[k] for k in ['period','capacity_fraction','policy','gamma','lam','rho','horizon','actions_verified','solver_stats']} for r in rows])

def block_intervals(a,b,block=5,reps=2000,seed=20260922):
    """Conditional paired observed-day outcome bootstrap; rerank eligible users."""
    aa=a.sort_values('sid').reset_index(drop=True);bb=b.sort_values('sid').reset_index(drop=True)
    assert aa.sid.equals(bb.sid) and aa.user.equals(bb.user) and aa.day.equals(bb.day)
    days=sorted(aa.day.unique());users=sorted(aa.user.unique());n=len(days)
    def matrix(f,col):return f.pivot_table(index='day',columns='user',values=col,aggfunc='sum',fill_value=0).reindex(index=days,columns=users,fill_value=0).to_numpy()
    counts=matrix(aa.assign(one=1),'one');sa=matrix(aa,'shortfall');sb=matrix(bb,'shortfall')
    ea=aa.groupby('day').delivered.sum().reindex(days).to_numpy();eb=bb.groupby('day').delivered.sum().reindex(days).to_numpy()
    ca=aa.groupby('day').cost.sum().reindex(days).to_numpy();cb=bb.groupby('day').cost.sum().reindex(days).to_numpy()
    def tail(s,c):
        v=s[c>=5]/c[c>=5]
        return np.sort(v)[-max(1,int(np.ceil(.1*len(v)))):].mean() if len(v) else np.nan
    rng=np.random.default_rng(seed);values=[]
    for _ in range(reps):
        starts=rng.integers(0,max(1,n-block+1),size=int(np.ceil(n/block)))
        chosen=(starts[:,None]+np.arange(min(block,n))).ravel()[:n];weights=np.bincount(chosen,minlength=n)
        c=weights@counts;da=weights@ea;db=weights@eb
        values.append([100*(tail(weights@sa,c)-tail(weights@sb,c)),100*da/db,100*(weights@ca/da)/(weights@cb/db)])
    values=np.asarray(values);assert np.isfinite(values).all()
    return {metric:{'low':float(np.quantile(values[:,i],.025)),'high':float(np.quantile(values[:,i],.975))} for i,metric in enumerate(['tail_pp','delivery_percent','unit_cost_percent'])}

def frame_for(period,frac,policy,selected):
    return pd.read_csv(PRIVATE/'runs'/label(period,frac,policy,selected[policy])/'sessions.csv')

def summarize():
    check_lock();p=protocol();lock=json.loads((OUT/'selection_lock.json').read_text());sel=lock['selected'];scores=pd.read_csv(OUT/'test_scores.csv');pairs=[]
    for period in ['test_q3','test_q4']:
        a=frame_for(period,.35,'history',sel)
        for other in dict.fromkeys([lock['comparator'],'debt_share','pf_mpc','point_history','stochastic']):
            b=frame_for(period,.35,other,sel);m=metrics(a);n=metrics(b);ci=block_intervals(a,b)
            for key,estimate in [('tail_pp',100*(m['tail']-n['tail'])),('delivery_percent',100*m['delivered']/n['delivered']),('unit_cost_percent',100*m['cost_per_kwh']/n['cost_per_kwh'])]:
                pairs.append(dict(period=period,candidate='history',comparator=other,metric=key,estimate=estimate,**ci[key],block_days=5,reps=2000))
        b=frame_for(period,.35,lock['comparator'],sel)
        if period=='test_q3':
            sensitivity={str(block):block_intervals(a,b,block=block) for block in [2,10]};dumps(OUT/'block_sensitivity.json',sensitivity)
        with (PRIVATE/'model.pkl').open('rb') as f:model=pickle.load(f)
        forecasts=forecast_rows(model,load_sessions(PRIVATE/(period+'.json')),0)
        forecasts.to_csv(PRIVATE/(period+'_forecasts.csv.gz'),index=False)
        balanced=forecasts.groupby(['model','lead_minutes','sid'])[['brier','logloss']].mean().groupby(['model','lead_minutes']).mean().reset_index()
        balanced.to_csv(OUT/(period+'_forecast_balanced.csv'),index=False)
        by=forecasts.groupby(['model','landmark_hours','lead_minutes']).agg(n=('y','size'),events=('y','sum'),brier=('brier','mean'),logloss=('logloss','mean')).reset_index();by.to_csv(OUT/(period+'_forecast_landmarks.csv'),index=False)
    pd.DataFrame(pairs).to_csv(OUT/'paired_intervals.csv',index=False)
    dumps(OUT/'verification.json',{'status':'passed','controller_runs':len(scores),'validation_runs':len(pd.read_csv(OUT/'validation_grid.csv')),'all_runs_actions_verified':bool(scores.actions_verified.all()),'maximum_applied_violation':float(scores.max_violation.max()),'fallbacks':int(scores.fallbacks.sum()),'source_data_protocol_unchanged':True,'scope':'Retrospective replay of observed sessions under modeled charging dynamics; not measured counterfactual delivery, live trial or independent-site inference.'})
    print(scores[scores.capacity_fraction==.35][['period','policy','tail','delivered','fallbacks']].to_string(index=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['audit','prepare','validate','evaluate','summarize']);parser.add_argument('--workers',type=int,default=3);args=parser.parse_args()
    if args.stage in ['validate','evaluate']:globals()[args.stage](args.workers)
    else:globals()[args.stage]()
