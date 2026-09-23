"""Portable checks possible from the shared aggregate/code package alone."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
root=Path(__file__).resolve().parents[1];out=root/'results/real_data'
lock=json.loads((out/'protocol_lock.json').read_text());checked=0
for name,expected in lock['state']['files'].items():
    path=Path(name)
    # Preserve original lock bytes; map its recorded absolute runner path locally.
    if path.is_absolute():
        assert path.name=='real_data_study.py'
        path=Path('scripts')/path.name
    assert digest(root/path)==expected,path
    checked+=1
selection=json.loads((out/'selection_lock.json').read_text())
assert selection['protocol_lock_sha256']==digest(out/'protocol_lock.json')
assert selection['validation_sha256']==digest(out/'validation_grid.csv')
audit=json.loads((out/'data_audit.json').read_text());coverage=pd.read_csv(out/'coverage.csv')
assert coverage.sessions.sum()==16529 and audit['source_sha256']==lock['state']['data_sha256']
assert coverage.to_dict('records')==audit['coverage']
acq=json.loads((out/'acquisition.json').read_text());assert acq['sha256']==audit['source_sha256']
assert len(acq['windows'])==53 and all(w['complete'] and w['records']==w['expected'] for w in acq['windows'])
assert sum(w['records'] for w in acq['windows'])-acq['exact_duplicates_removed']==acq['raw_records']==17414
scores=pd.read_csv(out/'test_scores.csv');pairs=pd.read_csv(out/'paired_intervals.csv')
assert len(scores)==31 and not scores.duplicated(['period','capacity_fraction','policy']).any()
primary=scores[scores.capacity_fraction==.35].set_index(['period','policy'])
for _,r in pairs.iterrows():
    a=primary.loc[r.period,r.candidate];b=primary.loc[r.period,r.comparator]
    value={'tail_pp':100*(a['tail']-b['tail']),'delivery_percent':100*a.delivered/b.delivered,'unit_cost_percent':100*a.cost_per_kwh/b.cost_per_kwh}[r.metric]
    assert abs(value-r['estimate'])<1e-8
for _,r in scores.iterrows():
    cfg=selection['selected'][r.policy]
    assert all(r[k]==cfg[k] for k in ['gamma','lam','rho','horizon'])
    c=coverage.set_index('period').loc[r.period]
    assert r.sessions==c.sessions and r.repeated_users==c.repeat_users
    assert r.max_violation<=1e-7 and r.actions_verified
summary=json.loads((out/'verification.json').read_text())
assert scores.fallbacks.sum()==summary['fallbacks']
assert abs(scores.max_violation.max()-summary['maximum_applied_violation'])<1e-15
assert selection['comparator']=='maxmin'
report={'status':'passed','source_files_checked':checked,'controller_runs':len(scores),'paired_estimates_recomputed':len(pairs),'scope':'Portable reference code/protocol hashes, aggregate counts, locked configurations and pair arithmetic. Does not recheck raw data, private action logs or bootstrap samples.'}
(out/'public_artifact_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
