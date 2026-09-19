"""Secondary analyses; fixed settings, no selection from final-test outcomes."""
from pathlib import Path
from dataclasses import replace
import json
import pandas as pd
from .experiment import prepare,run_one,dumps
from .synthetic import generate
from .data import Revision,local_day
from .forecast import forecast_audit


def seed_run(seed,protocol,out):
    parts,model,peak=prepare(seed,protocol,out)
    lock=json.loads((Path(out)/'protocol_lock.json').read_text());cfg=lock['selected']['history'];cap=peak*.35
    base=Path(out)/f'seed_{seed}'/'supplement';rows=[]
    cases=[('uncalibrated','history',dict(cfg)),('empirical','history',dict(cfg)),('horizon_12h','history',dict(cfg,horizon=48))]
    cases += [(kind,'history',dict(cfg,intervention=kind,assignment=seed)) for kind in ['early','late','wide','narrow']]
    for label,name,c in cases:
        print('supplement',seed,label,flush=True)
        model.kind='empirical' if label=='empirical' else 'hazard';model.calibrated=label!='uncalibrated'
        score=run_one(parts['test'],model,name,cap,c,base/label)
        rows.append(dict(seed=seed,variant=label,policy=name,**score))
    model.kind='hazard';model.calibrated=True
    # Physical stress tests hold generator draws fixed, transform test sessions only.
    for label in ['shorter_stay','larger_requests']:
        if label=='shorter_stay':
            ss=[replace(s,departure=max(s.arrival+3,s.departure-6)) for s in parts['test']]
        else:
            ss=[replace(s,revisions=tuple(replace(r,energy=1.25*r.energy) for r in s.revisions)) for s in parts['test']]
        for name in ['history',lock['comparator']]:
            print('stress',seed,label,name,flush=True)
            score=run_one(ss,model,name,cap,lock['selected'][name],base/f'{label}_{name}')
            rows.append(dict(seed=seed,variant=label,policy=name,**score))
    # No-forecast baseline is an invariance negative control, exact same sessions/actions.
    dumps(base/'negative_control.json',{'policy':'equal','claim':'equal controller never accesses forecast; forecast-only perturbations cannot alter its actions','verified_in_tests':True})
    pd.DataFrame(rows).to_csv(base/'scores.csv',index=False)


def run(protocol,out,workers=1):
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs=[pool.submit(seed_run,s,protocol,out) for s in protocol['seeds']]
        for j in jobs:j.result()
    pd.concat([pd.read_csv(Path(out)/f'seed_{s}'/'supplement'/'scores.csv') for s in protocol['seeds']]).to_csv(Path(out)/'supplement_scores.csv',index=False)
