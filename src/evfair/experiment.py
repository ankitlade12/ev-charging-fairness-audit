from pathlib import Path
import json, hashlib, platform, time, pickle
import numpy as np
import pandas as pd
from .synthetic import generate
from .forecast import DepartureModel,forecast_audit
from .control import Controller
from .simulate import replay,offline_energy
from .metrics import metrics,paired_seed_interval
from .data import local_day,save_sessions


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dumps(path,obj):
    def clean(x):
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):return [clean(v) for v in x]
        if isinstance(x,(float,np.floating)) and not np.isfinite(x):return None
        return x
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(clean(obj),indent=2,default=str,allow_nan=False))

def split(sessions,protocol):
    days=sorted({local_day(s.arrival) for s in sessions});idx=protocol['split_day_indices']
    return {name:[s for s in sessions if local_day(s.arrival) in days[l:r]] for name,l,r in zip(['train','calibration','validation','test'],idx,idx[1:])}

def prepare(seed,protocol,out):
    sessions=generate(seed,protocol['days'],protocol['users']);parts=split(sessions,protocol)
    model=DepartureModel().fit(parts['train'],parts['calibration'])
    peak=max(sum(s.pmax for s in parts['train'] if s.arrival<=t<s.departure) for t in range(min(s.arrival for s in parts['train']),max(s.departure for s in parts['train'])))
    path=Path(out)/f'seed_{seed}';path.mkdir(parents=True,exist_ok=True)
    save_sessions(sessions,path/'sessions.json')
    dumps(path/'splits.json',{k:dict(sessions=len(v),users=len({s.user for s in v}),start=local_day(min(s.arrival for s in v)),end=local_day(max(s.departure for s in v))) for k,v in parts.items()})
    return parts,model,peak

def run_one(sessions,model,name,cap,config,out,trace=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    controller=Controller(name,model,**config)
    frame,diagnostics,logs=replay(sessions,controller,cap,trace=trace)
    frame.to_csv(out/'sessions.csv',index=False)
    score=metrics(frame);score.update(diagnostics);dumps(out/'summary.json',score)
    dumps(out/'config.json',dict(name=name,capacity=cap,**config))
    if trace:
        pd.DataFrame(logs['actions']).to_csv(out/'actions.csv.gz',index=False)
        dumps(out/'history.json',logs['updates'])
        import gzip
        with gzip.open(out/'plans.json.gz','wt') as f:json.dump(logs['plans'],f)
    return score

def validate(protocol,out='results'):
    parts,model,peak=prepare(protocol['validation_seed'],protocol,out)
    cap=peak*protocol['primary_capacity_fraction'];rows=[]
    for name in ['equal','fcfs','edf','laxity','maxmin','debt_share','point','stochastic','point_history','history','pf_mpc']:
        configs=[dict(gamma=20.,lam=0.)]
        if name in ['point','stochastic','pf_mpc']:configs=[dict(gamma=g,lam=0.) for g in protocol['gamma_grid']]
        if name in ['point_history','history']:configs=[dict(gamma=g,lam=l) for g in protocol['gamma_grid'] for l in protocol['lambda_grid']]
        if name=='debt_share':configs=[dict(gamma=20.,lam=l) for l in protocol['lambda_grid']]
        for cfg in configs:
            cfg.update(rho=protocol['rho'],horizon=protocol['horizon_steps'])
            label=f"{name}_g{cfg['gamma']}_l{cfg['lam']}"
            print('validation',label,flush=True)
            score=run_one(parts['validation'],model,name,cap,cfg,Path(out)/'validation'/label)
            rows.append(dict(name=name,**cfg,**score))
    df=pd.DataFrame(rows);df.to_csv(Path(out)/'validation_grid.csv',index=False)
    base=df[df.name=='equal'].iloc[0]
    def select(group):
        g=group.copy();g['delivery_deficit']=np.maximum(0,.98-g.delivered/base.delivered)
        feasible=g[(g.delivered>=.98*base.delivered)&(g.cost_per_kwh<=1.03*base.cost_per_kwh)]
        best=feasible.sort_values(['tail','cost_per_kwh','name']).iloc[0] if len(feasible) else g.sort_values(['delivery_deficit','tail','name']).iloc[0]
        return {k:float(best[k]) for k in ['gamma','lam','rho']}|{'horizon':int(best.horizon)}
    selected={name:select(g) for name,g in df.groupby('name')}
    fair=df[df.name.isin(['equal','maxmin','debt_share','pf_mpc'])].copy()
    fair= fair[(fair.delivered>=.98*base.delivered)&(fair.cost_per_kwh<=1.03*base.cost_per_kwh)]
    comparator=fair.sort_values(['tail','cost_per_kwh','name']).iloc[0]['name'] # equal is always feasible
    lock=dict(protocol_sha256=digest('config/protocol.json'),selected=selected,comparator=comparator,training_peak_kw=peak,
      code_hashes={str(p):digest(p) for p in sorted(Path('src').rglob('*.py'))},locked_at=pd.Timestamp.now(tz='UTC').isoformat(),
      note='Locked after validation, before final test; not external preregistration.')
    dumps(Path(out)/'protocol_lock.json',lock)
    print('LOCK',comparator,selected['history'],flush=True)
    return lock

def evaluate(protocol,out='results',seeds=None):
    out=Path(out);lock=json.loads((out/'protocol_lock.json').read_text())
    if lock['protocol_sha256']!=digest('config/protocol.json'):raise ValueError('protocol changed after lock')
    rows=[]
    for seed in seeds or protocol['seeds']:
        parts,model,peak=prepare(seed,protocol,out)
        forecast_audit(model,parts['test']).to_csv(out/f'seed_{seed}'/'forecast.csv',index=False)
        for frac in protocol['capacity_fractions_training_peak']:
            cap=peak*frac
            for name,cfg in lock['selected'].items():
                print('test',seed,frac,name,flush=True)
                directory=out/f'seed_{seed}'/f'cap_{frac}'/name
                score=run_one(parts['test'],model,name,cap,cfg,directory,trace=seed==11 and frac==.35 and name in ['history',lock['comparator']])
                rows.append(dict(seed=seed,capacity_fraction=frac,capacity_kw=cap,policy=name,**score))
            bound=offline_energy(parts['test'],cap)
            dumps(out/f'seed_{seed}'/f'cap_{frac}'/'offline.json',bound)
        pd.DataFrame(rows).to_csv(out/f'test_scores_{seed}.csv',index=False)
    # Merge saved summaries, never rely on partially accumulated loop files.
    allrows=[]
    for seed in protocol['seeds']:
        for frac in protocol['capacity_fractions_training_peak']:
            for name in lock['selected']:
                p=out/f'seed_{seed}'/f'cap_{frac}'/name/'summary.json'
                if p.exists():
                    cfg=json.loads(p.with_name('config.json').read_text())
                    allrows.append(dict(seed=seed,capacity_fraction=frac,capacity_kw=cfg['capacity'],policy=name,**json.loads(p.read_text())))
    pd.DataFrame(allrows).to_csv(out/'test_scores.csv',index=False)
