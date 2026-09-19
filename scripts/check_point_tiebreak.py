"""Post-primary optimizer diagnostic: lexicographic earliest-service tie break.
The economic LP value is constrained within 1e-7 dollars of its first optimum.
No changes are made to locked primary runs or parameters.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.sparse import vstack,csr_matrix
from evfair.experiment import prepare,run_one,dumps
import evfair.control as control

original=control.linprog

def lexicographic(c,**kwargs):
    first=original(c,**kwargs)
    if not first.success:return first
    H=96;secondary=np.tile(np.arange(H,dtype=float),len(c)//H)
    kw=dict(kwargs);kw['A_ub']=vstack([kw['A_ub'],csr_matrix(np.asarray(c)[None,:])]);kw['b_ub']=np.r_[kw['b_ub'],first.fun+1e-7]
    second=original(secondary,**kw)
    if second.success and np.dot(c,second.x)<=first.fun+2e-7:return second
    return first

if __name__=='__main__':
    p=json.load(open('config/protocol.json'));lock=json.load(open('results/protocol_lock.json'));rows=[]
    control.linprog=lexicographic
    for seed in p['seeds']:
        parts,model,peak=prepare(seed,p,'results/point_lexicographic')
        score=run_one(parts['test'],model,'point',peak*.35,lock['selected']['point'],Path('results/point_lexicographic')/f'seed_{seed}'/'point_lex')
        rows.append(dict(seed=seed,policy='point_lex',**score));print(seed,score['tail'],flush=True)
    pd.DataFrame(rows).to_csv('results/tables/point_lexicographic_diagnostic.csv',index=False)
    dumps('results/point_lexicographic/interpretation.json',dict(status='post-primary exploratory diagnostic; not validation-selected',
       primary_objective_tolerance_dollars=1e-7,secondary='minimize sum(slot index * planned battery kWh)',
       settings='rolling conditional median, gamma40, no history'))
