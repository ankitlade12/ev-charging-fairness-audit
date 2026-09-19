import numpy as np
import pandas as pd
from scipy.stats import t as student_t

def metrics(frame,min_sessions=5):
    users=frame.groupby('user').shortfall.agg(['mean','count'])
    u=users.loc[users['count']>=min_sessions,'mean']
    tail=float(u.nlargest(max(1,int(np.ceil(.1*len(u))))).mean()) if len(u) else np.nan
    d=float(frame.delivered.sum());cost=float(frame.cost.sum())
    fail=frame.assign(fail=frame.shortfall>.1+1e-9).groupby('user').fail.mean()
    new=frame[frame.cohort=='new']
    return dict(sessions=len(frame),users=len(users),repeated_users=len(u),tail_users=int(np.ceil(.1*len(u))),
       tail=tail,mean_shortfall=float(frame.shortfall.mean()),delivered=d,cost=cost,cost_per_kwh=cost/d if d else np.nan,
       repeat_failure=float((fail.loc[u.index]>=.5).mean()) if len(u) else np.nan,
       new_shortfall=float(new.shortfall.mean()) if len(new) else np.nan,new_sessions=len(new),
       excess_kwh=float(frame.excess.sum()))

def paired_seed_interval(values):
    """Independent generated populations are replication units, not sessions."""
    v=np.array(values,float);n=len(v);mean=float(v.mean())
    half=float(student_t.ppf(.975,n-1)*v.std(ddof=1)/np.sqrt(n)) if n>1 else np.nan
    return dict(mean=mean,low=mean-half,high=mean+half,n=n)

def paired_block_interval(a,b,seed=2026,reps=1000,block=5):
    """Sensitivity only: fixed realized policies/history; rerank users per bootstrap.
    Sample contiguous whole site-day blocks, paired across policies. This is not
    a rerun of history dynamics, nor a population-level guarantee.
    """
    days=sorted(a.day.unique());rng=np.random.default_rng(seed);diff=[]
    for _ in range(reps):
        indices=[]
        while len(indices)<len(days):
            start=int(rng.integers(0,max(1,len(days)-block+1)))
            indices.extend(range(start,min(start+block,len(days))))
        chosen=[days[i] for i in indices[:len(days)]]
        aa=pd.concat([a[a.day==d] for d in chosen]);bb=pd.concat([b[b.day==d] for d in chosen])
        diff.append(metrics(aa)['tail']-metrics(bb)['tail'])
    return dict(low=float(np.nanquantile(diff,.025)),high=float(np.nanquantile(diff,.975)),block_days=block,reps=reps)
