"""Verify saved real-session actions, history, costs, aggregates and provenance.
Run from the project root with PYTHONPATH=src:.; never changes frozen outcomes.
"""
from pathlib import Path
from collections import defaultdict
import hashlib, json
import numpy as np
import pandas as pd
from evfair.data import load_sessions
from evfair.metrics import metrics
from scripts.real_data_study import OUT, PRIVATE, check_lock, check_actions


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    check_lock()
    acquisition=json.loads((OUT/'acquisition.json').read_text())
    assert len(acquisition['windows'])==53
    for w in acquisition['windows']:
        path=Path('data/raw/real_study/jpl_windows')/(w['start']+'.json')
        assert digest(path)==w['sha256'] and w['complete']
        assert len(json.loads(path.read_text())['_items'])==w['records']==w['expected']
    assert digest(Path(acquisition['raw_path']))==acquisition['sha256']
    parts={name:load_sessions(PRIVATE/(name+'.json')) for name in ['validation','test_q3','test_q4']}
    summary=[];files={};action_count=0
    for directory in sorted((PRIVATE/'runs').iterdir()):
        score=json.loads((directory/'summary.json').read_text());ss=parts[score['period']]
        frame=pd.read_csv(directory/'sessions.csv');actions=pd.read_csv(directory/'actions.csv.gz')
        check_actions(frame,actions,ss,score['capacity_kw'])
        assert set(frame.sid)=={s.sid for s in ss}
        keyed=frame.set_index('sid');by_sid={s.sid:s for s in ss}
        for s in ss:
            assert abs(keyed.loc[s.sid,'requested']-s.request_at(s.departure-1).energy)<1e-10
        # Reconstruct all policy-specific history from completed outcomes independently.
        debt=defaultdict(float);histories=defaultdict(list);saved=json.loads((directory/'history.json').read_text())
        assert len(saved)==len(ss)
        for s,update in zip(sorted(ss,key=lambda s:(s.departure,s.sid)),saved):
            old=debt[s.user];new=(1-score['rho'])*old+score['rho']*keyed.loc[s.sid,'shortfall']
            assert update[:3]==[s.departure,s.sid,s.user]
            assert np.allclose(update[3:],[old,new],atol=1e-12,rtol=0)
            histories[s.user].append((s.departure,new));debt[s.user]=new
        for sid,g in actions.groupby('sid',sort=False):
            s=by_sid[sid];times=g.t.to_numpy();h=histories[s.user]
            if h:
                ht,hv=np.asarray(h).T;indices=np.searchsorted(ht,times,side='right')-1
                expected=np.where(indices>=0,hv[np.maximum(indices,0)],0.)
            else:expected=np.zeros(len(times))
            assert np.allclose(g.debt,expected,atol=1e-12,rtol=0)
            rev_times=np.array([r.at for r in s.revisions]);ri=np.searchsorted(rev_times,times,side='right')-1
            assert (ri>=0).all()
            assert np.allclose(g.request,np.array([r.energy for r in s.revisions])[ri],atol=1e-12,rtol=0)
            assert np.allclose(g.energy,g.battery_kwh.cumsum(),atol=1e-7,rtol=0)
        # Independent tariff calculation from UTC slots, with grid/battery distinction.
        utc_hour=(actions.t.to_numpy()%96)/4
        charges=actions.power*.25*np.where((utc_hour>=21)|(utc_hour<1),.30,.12)
        costs=charges.groupby(actions.sid).sum().reindex(frame.sid,fill_value=0).to_numpy()
        assert np.allclose(costs,frame.cost,atol=1e-8,rtol=0)
        for k,v in metrics(frame).items(): assert np.isclose(v,score[k],atol=1e-8,rtol=1e-10,equal_nan=True),(directory,k)
        summary.append({k:score[k] for k in ['period','policy','capacity_fraction','actions_verified']})
        for name in ['sessions.csv','actions.csv.gz','history.json','config.json','summary.json']:
            path=directory/name;files[str(path.relative_to(PRIVATE))]=digest(path)
        action_count+=len(actions)
    assert len(summary)==52
    aggregate=pd.read_csv(OUT/'test_scores.csv')
    for _,r in aggregate.iterrows():
        matching=[s for s in summary if s['period']==r.period and s['policy']==r.policy and s['capacity_fraction']==r.capacity_fraction]
        assert len(matching)==1
    assert len(aggregate)==31
    manifest={'status':'passed','controller_runs':len(summary),'validation_runs':21,'test_runs':31,'applied_action_rows':action_count,'checks':['official-window counts and checksums','frozen protocol and implementation','complete session sets','recorded final/current requests','physical action constraints','every policy-specific history update and action history','cumulative battery energy','independent UTC tariff accounting','session-derived metrics'],'private_artifact_hashes':files,'privacy':'Hashes only; raw identities, sessions and traces are not distributed.'}
    (OUT/'independent_verification.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:v for k,v in manifest.items() if k!='private_artifact_hashes'},indent=2))

if __name__=='__main__':main()
