"""Transparent designed workloads, not fitted ACN data."""
import numpy as np
import pandas as pd
from .data import Session, Revision, STEP

def generate(seed=11, days=140, users=60, shift=False):
    rng=np.random.default_rng(seed)
    dates=pd.bdate_range('2025-01-06',periods=days,tz='America/Los_Angeles')
    # User effects persistent; type is hidden from forecasters/controllers.
    regular=rng.permutation(np.arange(users))[:users//2]
    regular=set(regular); means=rng.uniform(5.5,8,users)
    energy=rng.uniform(12,28,users); attend=rng.uniform(.3,.55,users)
    out=[]
    for day,date in enumerate(dates):
        shock=rng.normal(0,.45) # shared site-day disturbance
        for u in range(users):
            # Six entrants become observable only in the held-out test period.
            if u>=users-6 and day<110:continue
            if rng.random()>attend[u]:continue
            arr=int(np.clip(round(rng.normal(8.5,.8)*4),27,43))
            sd=.45 if u in regular else 2.0
            dwell=float(np.clip(means[u]+shock+rng.normal(0,sd),1.0,10.5))
            if shift: dwell=max(.75,dwell-1.5)
            duration=max(3,round(dwell*4))
            a=int(date.timestamp()/STEP)+arr
            q=float(np.clip(energy[u]+rng.normal(0,3),6,38))
            # Request reflects intended stay, not realized departure noise.
            intended=max(4,round((means[u]+rng.normal(0,.35))*4))
            out.append(Session(f's{seed}-{day}-{u}',f'u{u:03}',f'port{u:03}',
                 'synthetic_shift' if shift else 'synthetic',a,a+duration,
                 (Revision(a,q,a+intended),)))
    return sorted(out,key=lambda s:(s.arrival,s.sid))
