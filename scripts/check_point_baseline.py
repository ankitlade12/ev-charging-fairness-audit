"""Post-primary robustness: frozen-at-arrival point deadlines, without retuning.
Added after inspecting weak rolling-point performance; never replaces locked results.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from evfair.experiment import prepare,run_one,dumps
from evfair.metrics import paired_seed_interval

class FrozenPoint:
    def __init__(self,base):self.base=base
    def cohort(self,user):return self.base.cohort(user)
    def survival(self,arrival,now,deadline,user,horizon=96):
        s=self.base.survival(arrival,arrival,deadline,user,96)
        absolute=arrival+max(1,int(np.searchsorted(1-s,.5)))
        # Once predicted deadline passes, treat still-connected request as urgent.
        remain=max(1,absolute-now)
        return (np.arange(horizon)<remain).astype(float)

if __name__=='__main__':
    p=json.load(open('config/protocol.json'));lock=json.load(open('results/protocol_lock.json'));rows=[]
    for seed in p['seeds']:
        parts,model,peak=prepare(seed,p,'results/point_diagnostic')
        name='point_frozen';cfg=lock['selected']['point']
        score=run_one(parts['test'],FrozenPoint(model),'point',peak*.35,cfg,Path('results/point_diagnostic')/f'seed_{seed}'/name)
        rows.append(dict(seed=seed,policy=name,**score));print(seed,score['tail'],flush=True)
    pd.DataFrame(rows).to_csv('results/tables/point_frozen_diagnostic.csv',index=False)
    dumps('results/point_diagnostic/interpretation.json',dict(status='post-primary exploratory implementation sensitivity; not preregistered or validation-selected',
      purpose='Check whether continuously updated point deadlines create avoidable deferral.',settings='gamma40, no history, freeze arrival median; once overdue, assume only current slot remains'))
