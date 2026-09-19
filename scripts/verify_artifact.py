from pathlib import Path
import json,hashlib,platform,sys,gzip
import numpy as np
import pandas as pd
from evfair.experiment import digest,dumps

root=Path('.')
lock=json.load(open('results/protocol_lock.json'))
assert digest('config/protocol.json')==lock['protocol_sha256']
for path,h in lock['code_hashes'].items():
    assert digest(path)==h,f'Locked source changed: {path}'
scores=pd.read_csv('results/test_scores.csv')
assert len(scores)==220
assert not scores.duplicated(['seed','capacity_fraction','policy']).any()
assert (scores.max_violation<=1e-7).all()
assert (scores.repeated_users>=30).all()
tracechecks=[]
for name in ['history',lock['comparator']]:
    d=Path('results/seed_11/cap_0.35')/name
    f=pd.read_csv(d/'sessions.csv').set_index('sid');a=pd.read_csv(d/'actions.csv.gz')
    cap=json.load(open(d/'config.json'))['capacity']
    assert a.groupby('t').power.sum().max()<=cap+1e-7
    bysid=a.groupby('sid').battery_kwh.sum().reindex(f.index,fill_value=0)
    assert np.allclose(bysid,f.delivered,atol=1e-7,rtol=0)
    h=json.load(open(d/'history.json'));assert len(h)==len(f);assert len({r[1] for r in h})==len(f)
    assert all(0<=r[-1]<=1 for r in h)
    with gzip.open(d/'plans.json.gz','rt') as stream:plans=json.load(stream)
    for t,sids,x in plans:
        x=np.array(x)
        assert x.min()>=-1e-7
        assert (x/.92).sum(axis=0).max()<=cap*.25+1e-7
    tracechecks.append(name)
assert json.load(open('results/reproduction/verification.json'))['passed']
manifest={str(p):digest(p) for top in ['src','scripts','config','docs','figures','manuscript','notebooks','tests'] for p in sorted(Path(top).rglob('*')) if p.is_file() and p.suffix not in ['.pyc','.aux','.log','.out']}
manifest.update({str(p):digest(p) for p in sorted(Path('results').rglob('*')) if p.is_file() and p.name not in ['artifact_manifest.json','package_verification.json'] and p.suffix not in ['.log']})
for name in ['pyproject.toml','requirements.lock','requirements-review.lock','README.md','.gitignore']:manifest[name]=digest(name)
dumps('results/artifact_manifest.json',dict(files=manifest,python=platform.python_version(),platform=platform.platform(),
    note='Artifact integrity manifest; source-specific provenance in docs and data/raw. No independent human review implied.'))
dumps('results/package_verification.json',dict(locked_core_code_unchanged=True,primary_runs=220,primary_constraints_pass=True,
    trace_ledger_checks=tracechecks,clean_environment_reproduction=True,manuscript_pdf_exists=Path('manuscript/main.pdf').exists(),
    independent_human_review=False,external_submission=False,real_data_fairness_gate_pass=False))
print('Artifact verification passed')
