"""Check secondary artifacts against saved trajectories and the primary lock."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from evfair.metrics import metrics
from evfair.experiment import digest,dumps
P=Path('results/second_pass');primary=json.loads(Path('results/protocol_lock.json').read_text())
assert all(digest(path)==h for path,h in primary['code_hashes'].items())
assert digest('config/protocol.json')==primary['protocol_sha256']
lock=json.loads((P/'analysis_lock.json').read_text())
assert digest('scripts/second_pass_diagnostics.py')==lock['script_sha256']
preserved=json.loads((P/'primary_preservation.json').read_text())
assert all(digest(path)==h for path,h in preserved['files'].items())
scores=pd.read_csv(P/'lexicographic_scores.csv');assert len(scores)==25 and not scores.duplicated(['seed','policy']).any()
for _,r in scores.iterrows():
    seed=int(r.seed);directory=P/f'seed_{seed}'/r.policy
    f=pd.read_csv(directory/'sessions.csv');m=metrics(f)
    for key in ['tail','mean_shortfall','delivered','cost','cost_per_kwh','new_shortfall']:
        assert np.isclose(m[key],r[key],rtol=0,atol=1e-7),(seed,r.policy,key)
    assert r.max_violation<=1e-7 and r.repeated_users>=30
    bound=json.loads(Path(f'results/seed_{seed}/cap_0.35/offline.json').read_text())['delivered_bound']
    assert r.delivered<=bound+1e-7
for seed in lock['seeds']:
    f=pd.read_csv(P/f'seed_{seed}'/'forecast_landmarks.csv.gz')
    assert not f.duplicated(['sid','model','landmark_hours','lead_minutes']).any()
    assert set(f.landmark_hours)=={1,3,5,7,9}
    assert set(f.lead_minutes)=={30,60,120,240}
    assert f.p.between(0,1).all() and f.y.isin([0,1]).all()
    assert np.allclose(f.brier,(f.p-f.y)**2,atol=1e-14)
    counts=f.groupby(['sid','landmark_hours','lead_minutes']).agg(n=('model','size'),ys=('y','nunique'))
    assert (counts.n==3).all() and (counts.ys==1).all()
    original=pd.read_csv(f'results/seed_{seed}/forecast.csv')
    early=f[(f.landmark_hours==1)&f.lead_minutes.isin([30,60,120])]
    joined=early.merge(original,on=['sid','model','lead_minutes'],suffixes=('_new','_original'),validate='one_to_one')
    assert len(joined)==len(original) and np.allclose(joined.p_new,joined.p_original,atol=1e-14)
result=dict(status='pass',runs=len(scores),script_lock_verified=True,primary_source_and_protocol_unchanged=True,all_session_metrics_recomputed=True,early_forecasts_match_original=True,applied_power_tolerance=1e-7,max_applied_violation=float(scores.max_violation.max()),total_fallbacks=int(scores.fallbacks.sum()),all_deliveries_below_offline_bounds=True,interpretation='Exploratory reused-population checks; not external replication or official IEEE validation.')
dumps(P/'verification.json',result);print(json.dumps(result,indent=2))
