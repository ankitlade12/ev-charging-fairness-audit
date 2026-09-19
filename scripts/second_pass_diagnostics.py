"""Post-primary diagnostics; never modifies the frozen primary protocol or source.
Run from repository root with PYTHONPATH=src. Five process-isolated populations.
"""
from pathlib import Path
import argparse, json, hashlib
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from scipy.sparse import vstack, csr_matrix
from evfair.experiment import prepare, run_one, dumps
from evfair.metrics import paired_seed_interval
import evfair.control as control

OUT=Path('results/second_pass')
POLICIES=['point','point_history','stochastic','history','pf_mpc']
LANDMARKS=[4,12,20,28,36]
LEADS=[2,4,8,16]
ORIGINAL=control.linprog


def lex_solver(policy, stats):
    def solve(c, **kwargs):
        first=ORIGINAL(c, **kwargs);stats['first_calls']+=1
        if not first.success:
            stats['first_failure']+=1
            return first
        H=96; n=len(c)//(H+1 if policy=='pf_mpc' else H)
        secondary=np.r_[np.tile(np.arange(H,dtype=float),n),np.zeros(n if policy=='pf_mpc' else 0)]
        assert len(secondary)==len(c)
        kw=dict(kwargs)
        kw['A_ub']=vstack([kw['A_ub'],csr_matrix(np.asarray(c)[None,:])])
        kw['b_ub']=np.r_[kw['b_ub'],first.fun+1e-7]
        second=ORIGINAL(secondary,**kw)
        if second.success and np.dot(c,second.x)<=first.fun+2e-7:
            stats['second_accepted']+=1
            return second
        stats['second_rejected_first_used']+=1
        return first
    return solve


def forecast_rows(model,sessions,seed):
    rows=[]
    for s in sessions:
        activation=max(s.arrival,s.revisions[0].at)
        for age in LANDMARKS:
            now=activation+age
            if now>=s.departure:continue
            r=s.request_at(now)
            assert r is not None
            for kind,cal in [('empirical',False),('hazard',False),('hazard',True)]:
                model.kind,model.calibrated=kind,cal
                surv=model.survival(s.arrival,now,r.deadline,s.user,max(LEADS)+1)
                for lead in LEADS:
                    p=float(np.clip(1-surv[lead],1e-6,1-1e-6)); y=int(s.departure<=now+lead)
                    rows.append(dict(seed=seed,sid=s.sid,user=s.user,cohort=model.cohort(s.user),landmark_hours=age/4,lead_minutes=lead*15,model=kind+('_cal' if cal else ''),p=p,y=y,brier=(p-y)**2,logloss=-y*np.log(p)-(1-y)*np.log(1-p)))
    model.kind,model.calibrated='hazard',True
    return pd.DataFrame(rows)


def worker(seed):
    p=json.loads(Path('config/protocol.json').read_text()); lock=json.loads(Path('results/protocol_lock.json').read_text())
    parts,model,peak=prepare(seed,p,OUT)
    frame=forecast_rows(model,parts['test'],seed)
    frame.to_csv(OUT/f'seed_{seed}'/'forecast_landmarks.csv.gz',index=False)
    rows=[]
    for policy in POLICIES:
        stats=Counter();control.linprog=lex_solver(policy,stats)
        score=run_one(parts['test'],model,policy,peak*p['primary_capacity_fraction'],lock['selected'][policy],OUT/f'seed_{seed}'/policy)
        control.linprog=ORIGINAL
        dumps(OUT/f'seed_{seed}'/policy/'solver_diagnostic.json',dict(stats))
        rows.append(dict(seed=seed,policy=policy,**score))
        print(seed,policy,'tail',score['tail'],flush=True)
    return rows


def summarize():
    rows=[]
    p=json.loads(Path('config/protocol.json').read_text())
    for seed in p['seeds']:
        for policy in POLICIES:
            rows.append(dict(seed=seed,policy=policy,**json.loads((OUT/f'seed_{seed}'/policy/'summary.json').read_text())))
    scores=pd.DataFrame(rows);scores.to_csv(OUT/'lexicographic_scores.csv',index=False)
    pairs=[]
    for a,b in [('history','pf_mpc'),('history','point_history'),('stochastic','point'),('point_history','point'),('history','stochastic')]:
        aa=scores[scores.policy==a].set_index('seed');bb=scores[scores.policy==b].set_index('seed')
        for metric in ['tail','delivered','cost_per_kwh','new_shortfall']:
            v=100*(aa[metric]-bb[metric]) if metric in ['tail','new_shortfall'] else 100*aa[metric]/bb[metric]
            pairs.append(dict(candidate=a,comparator=b,metric=metric,unit='pp difference' if metric in ['tail','new_shortfall'] else 'percent ratio',**paired_seed_interval(v)))
    pd.DataFrame(pairs).to_csv(OUT/'lexicographic_paired_intervals.csv',index=False)
    f=pd.concat([pd.read_csv(OUT/f'seed_{s}'/'forecast_landmarks.csv.gz') for s in p['seeds']],ignore_index=True)
    by=f.groupby(['seed','model','landmark_hours','lead_minutes']).agg(n=('y','size'),events=('y','sum'),p_mean=('p','mean'),event_rate=('y','mean'),brier=('brier','mean'),logloss=('logloss','mean')).reset_index()
    by.to_csv(OUT/'forecast_by_landmark.csv',index=False)
    # Average within each session first: later survivors do not get more total weight.
    session=f.groupby(['seed','model','sid','lead_minutes'])[['brier','logloss']].mean().reset_index()
    overall=session.groupby(['seed','model','lead_minutes'])[['brier','logloss']].mean().reset_index()
    overall.to_csv(OUT/'forecast_session_balanced.csv',index=False)
    intervals=[]
    for lead in sorted(overall.lead_minutes.unique()):
        sub=overall[overall.lead_minutes==lead].set_index(['model','seed'])
        for a,b in [('hazard_cal','empirical'),('hazard_cal','hazard')]:
            for metric in ['brier','logloss']:
                intervals.append(dict(lead_minutes=int(lead),candidate=a,comparator=b,metric=metric,**paired_seed_interval(sub.loc[a,metric]-sub.loc[b,metric])))
    pd.DataFrame(intervals).to_csv(OUT/'forecast_paired_intervals.csv',index=False)
    assert len(scores)==25 and not scores.duplicated(['seed','policy']).any()
    assert all(scores.repeated_users>=30)
    dumps(OUT/'verification.json',dict(runs=25,forecast_rows=len(f),primary_source_hashes_unchanged=all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in json.loads(Path('results/protocol_lock.json').read_text())['code_hashes'].items()),status='post-primary exploratory, all five populations previously inspected'))
    print(scores.groupby('policy').tail if False else scores.groupby('policy')[['tail','delivered']].mean())

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--summarize',action='store_true');args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if not args.summarize:
        lockpath=OUT/'analysis_lock.json'
        payload=dict(status='post-primary exploratory; locked before these new runs, after primary and earlier point diagnostic observed',seeds=[11,22,33,44,55],policies=POLICIES,capacity_fraction=.35,landmarks_slots=LANDMARKS,leads_slots=LEADS,forecast_weighting='equal within-session landmark mean, then equal sessions within seed; paired five-seed t intervals',solver='economic objective including original tiny time preference; secondary earliest planned energy; objective allowance 1e-7 dollars, acceptance 2e-7; existing feasibility fallback retained',selection='unchanged original validation-selected settings; no retuning; not a fresh confirmatory test',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if lockpath.exists():assert json.loads(lockpath.read_text())==payload,'diagnostic changed after lock'
        else:dumps(lockpath,payload)
        with ProcessPoolExecutor(max_workers=3) as pool:list(pool.map(worker,payload['seeds']))
    summarize()
