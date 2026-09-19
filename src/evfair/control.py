"""Causal controllers receive observations, never Session/departure records."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from .data import DT

@dataclass(frozen=True)
class Observation:
    sid: str
    user: str
    arrival: int
    requested: float
    delivered: float
    deadline: int | None
    pmax: float
    eta: float
    debt: float

@dataclass
class Decision:
    power: np.ndarray
    status: str
    plan: np.ndarray | None = None


def waterfill(upper, capacity, weights=None):
    upper=np.asarray(upper,float)
    weights=np.ones(len(upper)) if weights is None else np.asarray(weights,float)
    if not len(upper):return upper.copy()
    if upper.sum()<=capacity:return upper.copy()
    lo=0.;hi=max(upper/np.maximum(weights,1e-12))
    for _ in range(45):
        mid=(lo+hi)/2
        if np.minimum(upper,weights*mid).sum()>capacity:hi=mid
        else:lo=mid
    return np.minimum(upper,weights*lo)


def tariff(now,horizon):
    # Designed two-period tariff, USD/grid-kWh; not a utility tariff claim.
    # UTC 21:00-01:00 corresponds roughly to California afternoon.
    hour=((now+np.arange(horizon))%96)/4
    return np.where((hour>=21)|(hour<1),.30,.12)

class Controller:
    def __init__(self,name,model,gamma=20.,lam=0.,rho=.2,horizon=96,intervention='none',assignment=0):
        self.name=name;self.model=model;self.gamma=gamma;self.lam=lam;self.rho=rho;self.horizon=horizon
        self.intervention=intervention;self.assignment=assignment;self.force_failure=False
    def act(self,obs,now,capacity):
        n=len(obs)
        rem=np.array([max(o.requested-o.delivered,0) for o in obs])
        upper=np.array([min(o.pmax,r/(o.eta*DT)) for o,r in zip(obs,rem)])
        if self.name in ['equal','debt_share','maxmin']:
            if self.name=='equal':p=waterfill(upper,capacity)
            elif self.name=='debt_share':p=waterfill(upper,capacity,[1+self.lam*o.debt for o in obs])
            else:
                # Max-min cumulative request fulfillment after this slot, progressive filling.
                q=np.array([o.requested for o in obs]); e=np.array([o.delivered for o in obs]);eta=np.array([o.eta for o in obs])
                lo=0.;hi=1.
                for _ in range(45):
                    mid=(lo+hi)/2;p=np.minimum(upper,np.maximum(0,(mid*q-e)/(eta*DT)))
                    if p.sum()>capacity:hi=mid
                    else:lo=mid
                p=np.minimum(upper,np.maximum(0,(lo*q-e)/(eta*DT)))
                # Fill residual capacity after some users saturate.
                p+=waterfill(upper-p,max(0,capacity-p.sum()))
            return Decision(p,'heuristic')
        if self.name in ['fcfs','edf','laxity']:
            if self.name=='fcfs':order=sorted(range(n),key=lambda i:(obs[i].arrival,obs[i].sid))
            elif self.name=='edf':order=sorted(range(n),key=lambda i:(obs[i].deadline or now+96,obs[i].sid))
            else:
                keys=[]
                for i,o in enumerate(obs):
                    s=self.model.survival(o.arrival,now,o.deadline,o.user,self.horizon)
                    deadline=max(1,int(np.searchsorted(1-s,.5)))
                    keys.append((deadline*DT-rem[i]/(o.eta*o.pmax),o.sid))
                order=sorted(range(n),key=lambda i:keys[i])
            p=np.zeros(n);cap=capacity
            for i in order:p[i]=min(upper[i],cap);cap-=p[i]
            return Decision(p,'heuristic')
        H=self.horizon
        survival=[]
        for o in obs:
            s=self.model.survival(o.arrival,now,o.deadline,o.user,H).copy()
            # Assignment determined from identity and seed, not outcomes or cohort.
            import hashlib
            treated=int(hashlib.sha256((o.user+str(self.assignment)).encode()).hexdigest()[:8],16)%2==0
            if treated and self.intervention!='none':
                idx=np.arange(H)
                if self.intervention=='late':idx=np.maximum(0,idx-8)
                elif self.intervention=='early':idx=np.minimum(H-1,idx+8)
                elif self.intervention in ['wide','narrow']:
                    median=int(np.searchsorted(1-s,.5)); factor=1.6 if self.intervention=='wide' else .6
                    idx=np.clip(median+(idx-median)/factor,0,H-1)
                s=np.interp(idx,np.arange(H),s);s/=max(s[0],1e-12);s=np.minimum.accumulate(s);s[0]=1
            if self.name in ['point','point_history']:
                median=max(1,min(H,int(np.searchsorted(1-s,.5))))
                s=(np.arange(H)<median).astype(float)
            survival.append(s)
        S=np.array(survival)
        # x in battery-kWh per slot. q - expected energy is nonnegative because
        # every complete planned trajectory is capped at current remaining demand.
        q=np.array([o.requested for o in obs]);eta=np.array([o.eta for o in obs])
        weights=1+self.lam*np.array([o.debt for o in obs])
        cost=(S*tariff(now,H)[None,:]/eta[:,None]).ravel()
        pf=self.name=='pf_mpc'
        nvar=n*H+(n if pf else 0)
        c=np.zeros(nvar);c[:n*H]=cost
        if pf:c[n*H:]=-self.gamma
        else:c[:n*H]-=(self.gamma*weights[:,None]*S/q[:,None]).ravel()
        # Tiny deterministic preference for earlier allocations resolves degeneracy.
        c[:n*H]+=np.tile(np.arange(H)*1e-9,n)
        knots=np.array([.02,.05,.1,.2,.4,.6,.8,1.])
        cols=np.arange(n*H)
        rows=np.r_[np.tile(np.arange(H),n),H+np.repeat(np.arange(n),H)]
        cidx=np.r_[cols,cols]
        vals=np.r_[np.repeat(1/eta,H),np.ones(n*H)]
        b=np.r_[np.full(H,capacity*DT),rem]
        if pf:
            kr=np.arange(n*len(knots)).reshape(n,len(knots))+H+n
            pr=np.repeat(kr.ravel(),H)
            pc=np.repeat(np.arange(n)*H,len(knots)*H)+np.tile(np.arange(H),n*len(knots))
            pv=(-S[:,None,:]/(q[:,None,None]*knots[None,:,None])).ravel()
            rows=np.r_[rows,pr,kr.ravel()]
            cidx=np.r_[cidx,pc,n*H+np.repeat(np.arange(n),len(knots))]
            vals=np.r_[vals,pv,np.ones(n*len(knots))]
            delivered=np.array([o.delivered for o in obs])
            b=np.r_[b,(np.log(knots)[None,:]-1+delivered[:,None]/(q[:,None]*knots[None,:])).ravel()]
        A=coo_matrix((vals,(rows,cidx)),shape=(H+n+(n*len(knots) if pf else 0),nvar)).tocsr()
        bounds=[(0,o.eta*o.pmax*DT) for o in obs for _ in range(H)]
        if pf:bounds.extend([(None,None)]*n)
        try:
            if self.force_failure:raise RuntimeError('injected failure')
            res=linprog(c,A_ub=A.tocsr(),b_ub=b,bounds=bounds,method='highs',options={'time_limit':5.})
            if not res.success or not np.isfinite(res.x).all():raise RuntimeError(str(res.message))
            plan=res.x[:n*H].reshape(n,H)
            p=plan[:,0]/(eta*DT)
            if np.any(p < -1e-7) or np.any(p>upper+1e-7) or p.sum()>capacity+1e-7:raise RuntimeError('infeasible solver action')
            return Decision(np.maximum(0,np.minimum(p,upper)),'optimal',plan)
        except (ValueError,RuntimeError) as e:
            return Decision(waterfill(upper,capacity,np.maximum(rem,1e-9)),'fallback:'+str(e))
