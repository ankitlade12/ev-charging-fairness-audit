"""Conditional departure distributions; training-only user summaries."""
import numpy as np
from scipy.special import expit, logit
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from .data import DT, STEP
import pandas as pd

class DepartureModel:
    def __init__(self, kind='hazard', calibrated=True):
        self.kind=kind;self.calibrated=calibrated;self.scale=1.;self.intercept=0.;self.cache={};self.calendar={}
    def fit(self, train, calibration):
        self.cutoff=max(s.departure for s in train)
        self.durations=np.array([s.departure-s.arrival for s in train])
        self.hist={}
        for u in {s.user for s in train}:
            v=np.array([s.departure-s.arrival for s in train if s.user==u])
            # Shrink summaries; these describe observed schedules, not sensitive groups.
            w=len(v)/(len(v)+10)
            self.hist[u]=(w*v.mean()+(1-w)*self.durations.mean(),
                          w*v.std()+(1-w)*self.durations.std(),len(v))
        # Training features use population defaults, then prior completed sessions only.
        seen={}; X=[]; y=[]
        for s in sorted(train,key=lambda s:(s.arrival,s.sid)):
            past=[q for q in train if q.user==s.user and q.departure<=s.arrival]
            v=np.array([q.departure-q.arrival for q in past]);w=len(v)/(len(v)+10)
            hist=(w*v.mean()+(1-w)*self.durations.mean(),w*v.std()+(1-w)*self.durations.std(),len(v)) if len(v) else None
            for elapsed in range(s.departure-s.arrival):
                r=s.request_at(s.arrival+elapsed)
                if r is None:continue
                X.append(self.features(s.arrival,elapsed,r.deadline,hist));y.append(int(s.arrival+elapsed+1>=s.departure))
        self.scaler=StandardScaler().fit(X)
        self.lr=LogisticRegression(C=1.,max_iter=500,solver='lbfgs').fit(self.scaler.transform(X),y)
        # Calibration hazard likelihood uses complete risk sets, no class reweighting.
        cx=[];cy=[]
        for s in calibration:
            for e in range(s.departure-s.arrival):
                r=s.request_at(s.arrival+e)
                if r:
                    cx.append(self.features(s.arrival,e,r.deadline,self.hist.get(s.user)))
                    cy.append(int(s.arrival+e+1>=s.departure))
        z=self.lr.decision_function(self.scaler.transform(cx));cy=np.array(cy)
        def loss(v):
            zz=v[0]*z+v[1]
            return np.mean(np.logaddexp(0,zz)-cy*zz)
        opt=minimize(loss,[1.,0.],bounds=[(.1,3),(-3,3)],method='L-BFGS-B')
        if not opt.success: raise RuntimeError('hazard calibration failed')
        self.scale,self.intercept=map(float,opt.x)
        return self
    def features(self,arrival,e,deadline,hist):
        mean,sd,n=hist or (float(self.durations.mean()),float(self.durations.std()),0)
        # UTC index modulo day converted once; DST retained in local calendar.
        if arrival not in self.calendar:
            self.calendar[arrival]=pd.Timestamp(arrival*STEP,unit='s',tz='UTC').tz_convert('America/Los_Angeles')
        t=self.calendar[arrival]
        rem=(deadline-arrival-e) if deadline is not None else mean-e
        return [e/4,(e/4)**2,rem/4, max(-rem/4,0),t.hour+t.minute/60,t.dayofweek,
                mean/4,sd/4,np.log1p(n),float(deadline is None)]
    def survival(self,arrival,now,deadline,user,horizon=96):
        """S[k]=P(connected at beginning of slot now+k | connected now).
        Discrete replay departures occur at slot boundaries; current slot is known active.
        """
        key=(arrival,now,deadline,user,horizon,self.kind,self.calibrated)
        if key in self.cache:return self.cache[key]
        e=now-arrival
        if self.kind=='empirical':
            risk=self.durations[self.durations>e]
            if len(risk)==0:return np.exp(-np.arange(horizon)/4)
            return np.array([np.mean(risk>e+k) for k in range(horizon)])
        X=[self.features(arrival,e+k,deadline,self.hist.get(user)) for k in range(horizon-1)]
        z=self.lr.decision_function(self.scaler.transform(X))
        if self.calibrated:z=self.scale*z+self.intercept
        h=np.clip(expit(z),1e-5,1-1e-5)
        result=np.r_[1.,np.cumprod(1-h)]
        self.cache[key]=result
        return result
    def cohort(self,user):
        if user not in self.hist:return 'new'
        cutoff=np.median([v[1] for v in self.hist.values()])
        return 'variable' if self.hist[user][1]>cutoff else 'regular'


def forecast_audit(model,sessions):
    rows=[]
    for s in sessions:
        # One prespecified landmark per session: one hour after request activation.
        t=max(s.arrival,s.revisions[0].at)+4
        if t>=s.departure:continue
        r=s.request_at(t)
        for kind,cal in [('empirical',False),('hazard',False),('hazard',True)]:
            old=model.kind,model.calibrated;model.kind,model.calibrated=kind,cal
            surv=model.survival(s.arrival,t,r.deadline,s.user,10)
            model.kind,model.calibrated=old
            for lead in [2,4,8]:
                p=float(np.clip(1-surv[lead],1e-6,1-1e-6));y=int(s.departure<=t+lead)
                rows.append(dict(sid=s.sid,user=s.user,day=str(pd.Timestamp(s.arrival*STEP,unit='s',tz='UTC').date()),
                  cohort=model.cohort(s.user),model=kind+('_cal' if cal else ''),lead_minutes=lead*15,p=p,y=y,
                  brier=(p-y)**2,logloss=-y*np.log(p)-(1-y)*np.log(1-p)))
    return pd.DataFrame(rows)
