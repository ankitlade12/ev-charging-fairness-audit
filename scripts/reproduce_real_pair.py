"""Fresh replay of the primary pair, without loading saved controller outcomes."""
from pathlib import Path
from collections import Counter
import json,pickle,time
import numpy as np
import pandas as pd
from evfair.data import load_sessions
from evfair.simulate import replay
from scripts.real_data_study import OUT, PRIVATE, TracedController, check_lock, check_actions, label
from scripts.second_pass_diagnostics import lex_solver,ORIGINAL
import evfair.control as control

check_lock();lock=json.loads((OUT/'selection_lock.json').read_text())
sessions=load_sessions(PRIVATE/'test_q3.json');cap=json.loads((OUT/'data_audit.json').read_text())['training_peak_kw']*.35
records=[]
for policy in [lock['comparator'],'history']:
    with (PRIVATE/'model.pkl').open('rb') as f:model=pickle.load(f)
    cfg=lock['selected'][policy];controller=TracedController(policy,model,**cfg);stats=Counter()
    if policy=='history':control.linprog=lex_solver(policy,stats)
    start=time.perf_counter()
    try:frame,diag,logs=replay(sessions,controller,cap,trace=True)
    finally:control.linprog=ORIGINAL
    check_actions(frame,pd.DataFrame(logs['actions']),sessions,cap)
    directory=PRIVATE/'runs'/label('test_q3',.35,policy,cfg)
    old=pd.read_csv(directory/'sessions.csv')
    assert frame.sid.equals(old.sid)
    errors={col:float(np.max(np.abs(frame[col]-old[col]))) for col in ['delivered','cost','shortfall','excess']}
    assert max(errors.values())<1e-7
    prior=json.loads((directory/'summary.json').read_text())
    assert diag['fallbacks']==prior['fallbacks'] and dict(stats)==prior['solver_stats']
    assert np.allclose(np.array([u[3:] for u in logs['updates']]),np.array([u[3:] for u in json.loads((directory/'history.json').read_text())]),atol=1e-7,rtol=0)
    records.append(dict(policy=policy,maximum_absolute_errors=errors,seconds=time.perf_counter()-start,fallbacks=diag['fallbacks']))
    print(records[-1],flush=True)
(OUT/'fresh_pair_reproduction.json').write_text(json.dumps({'status':'passed','scope':'Fresh deterministic replay in the same environment and machine; frozen fitted model and source, no refitting or independent replication','runs':records},indent=2))
