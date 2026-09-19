"""Evaluator owns event log; immutable observations are the sole controller interface."""
from collections import defaultdict
import time
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix
from .data import DT, local_day
from .control import Observation, tariff


def replay(sessions,controller,capacity,trace=False):
    by_arr=defaultdict(list);by_dep=defaultdict(list)
    for s in sessions:by_arr[s.arrival].append(s);by_dep[s.departure].append(s)
    active={};energy=defaultdict(float);cost=defaultdict(float);debt=defaultdict(float)
    records=[];actions=[];updates=[];plans=[];latency=[];fallbacks=0;max_violation=0.
    for t in range(min(by_arr),max(by_dep)+1):
        for s in sorted(by_dep[t],key=lambda s:s.sid):
            active.pop(s.sid,None);r=s.request_at(t-1)
            if r is None:continue
            short=max(0,1-energy[s.sid]/r.energy);old=debt[s.user]
            debt[s.user]=(1-controller.rho)*old+controller.rho*short
            updates.append((t,s.sid,s.user,old,debt[s.user]))
            records.append(dict(sid=s.sid,user=s.user,day=local_day(s.arrival),requested=r.energy,delivered=energy[s.sid],
                cost=cost[s.sid],shortfall=short,excess=max(0,energy[s.sid]-r.energy),
                dwell_hours=(s.departure-s.arrival)*DT,cohort=controller.model.cohort(s.user),
                individual_unavoidable=max(0,1-(s.departure-max(s.arrival,s.revisions[0].at))*DT*s.eta*s.pmax/r.energy)))
        for s in by_arr[t]:active[s.sid]=s
        current=[s for s in sorted(active.values(),key=lambda s:s.sid) if s.request_at(t) is not None]
        obs=[];ss=[]
        for s in current:
            r=s.request_at(t)
            if energy[s.sid]>=r.energy-1e-9:continue
            ss.append(s);obs.append(Observation(s.sid,s.user,s.arrival,r.energy,energy[s.sid],r.deadline,s.pmax,s.eta,debt[s.user]))
        if not obs:continue
        before=time.perf_counter();decision=controller.act(tuple(obs),t,capacity);latency.append(time.perf_counter()-before)
        p=np.array(decision.power)
        if p.shape!=(len(obs),) or not np.isfinite(p).all():raise AssertionError('invalid action')
        violation=max(0.,float(p.sum()-capacity),float(-p.min()),max(float(pi-o.pmax) for pi,o in zip(p,obs)),
              max(float(pi*o.eta*DT-(o.requested-o.delivered)) for pi,o in zip(p,obs)))
        max_violation=max(max_violation,violation)
        if violation>1e-7:raise AssertionError(f'infeasible applied action: {violation}')
        fallbacks+=decision.status.startswith('fallback')
        for s,o,pi in zip(ss,obs,p):
            increment=float(pi*DT*s.eta);energy[s.sid]+=increment;cost[s.sid]+=float(pi*DT*tariff(t,1)[0])
            if trace:actions.append(dict(t=t,sid=s.sid,power=float(pi),battery_kwh=increment,energy=energy[s.sid],request=o.requested,debt=o.debt,status=decision.status))
        if trace and decision.plan is not None:plans.append((t,[o.sid for o in obs],decision.plan.tolist()))
    diagnostics=dict(fallbacks=int(fallbacks),decisions=len(latency),max_violation=max_violation,
        latency_p50=float(np.quantile(latency,.5)) if latency else 0,latency_p95=float(np.quantile(latency,.95)) if latency else 0)
    return pd.DataFrame(records),diagnostics,dict(actions=actions,updates=updates,plans=plans)


def offline_energy(sessions,capacity):
    """Nondeployable maximum aggregate battery-kWh, all arrivals/departures known.
    Supports fixed requests only, and never claims unique individual entitlements.
    """
    total=0.;upper_by_day={}
    for day in sorted({local_day(s.arrival) for s in sessions}):
        ss=[s for s in sessions if local_day(s.arrival)==day]
        if any(len({r.energy for r in s.revisions})!=1 for s in ss):raise ValueError('offline bound requires fixed requests')
        times=sorted({t for s in ss for t in range(max(s.arrival,s.revisions[0].at),s.departure)})
        tidx={t:j for j,t in enumerate(times)};cols=[(i,t) for i,s in enumerate(ss) for t in range(max(s.arrival,s.revisions[0].at),s.departure)]
        A=lil_matrix((len(times)+len(ss),len(cols)))
        for j,(i,t) in enumerate(cols):A[tidx[t],j]=1/ss[i].eta;A[len(times)+i,j]=1
        b=[capacity*DT]*len(times)+[s.revisions[0].energy for s in ss]
        res=linprog(-np.ones(len(cols)),A_ub=A.tocsr(),b_ub=b,bounds=[(0,ss[i].pmax*ss[i].eta*DT) for i,t in cols],method='highs')
        if not res.success:raise RuntimeError(res.message)
        upper_by_day[day]=float(-res.fun);total-=res.fun
    return dict(delivered_bound=float(total),by_day=upper_by_day)
