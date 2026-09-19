import unittest,tempfile,json
from pathlib import Path
import numpy as np
from evfair.data import Session,Revision,normalize
from evfair.control import Observation,Controller,waterfill
from evfair.simulate import replay,offline_energy
from evfair.metrics import metrics

class Model:
    def survival(self,a,t,d,u,horizon=96):
        return np.r_[1.,np.exp(-np.arange(1,horizon)/8)]
    def cohort(self,u):return 'regular'

def session(sid='a',user='u',arrival=100,departure=116,energy=12):
    return Session(sid,user,sid,'test',arrival,departure,(Revision(arrival,energy,departure),))

class CoreTests(unittest.TestCase):
    def test_power_caps(self):
        rng=np.random.default_rng(1)
        for n in [1,2,20]:
            for _ in range(20):
                upper=rng.uniform(0,8,n);cap=float(rng.uniform(0,upper.sum()))
                p=waterfill(upper,cap,rng.uniform(.1,5,n))
                self.assertTrue(np.all(p>=0));self.assertTrue(np.all(p<=upper+1e-9));self.assertLessEqual(p.sum(),cap+1e-8)
                self.assertAlmostEqual(p.sum(),min(cap,upper.sum()),places=7)
    def test_energy_conservation_and_departure(self):
        ss=[session(),session('b','v',102,112,6)]
        f,d,l=replay(ss,Controller('equal',Model()),4,trace=True)
        for s in ss:
            acts=[a for a in l['actions'] if a['sid']==s.sid]
            self.assertTrue(all(s.arrival<=a['t']<s.departure for a in acts))
            self.assertAlmostEqual(sum(a['battery_kwh'] for a in acts),f.set_index('sid').loc[s.sid,'delivered'])
        self.assertLessEqual(d['max_violation'],1e-7)
    def test_future_events_do_not_change_earlier_actions(self):
        base=session(departure=120)
        future=session('later','other',110,125,8)
        changed=Session(base.sid,base.user,base.station,base.site,base.arrival,130,base.revisions)
        for name in ['history','point','pf_mpc','equal','edf','maxmin']:
            _,_,a=replay([base],Controller(name,Model(),horizon=12),4,trace=True)
            _,_,b=replay([changed,future],Controller(name,Model(),horizon=12),4,trace=True)
            aa=[r for r in a['actions'] if r['t']<110];bb=[r for r in b['actions'] if r['t']<110]
            self.assertEqual(aa,bb)
    def test_revision_boundary(self):
        s=session(energy=15);r=Session(s.sid,s.user,s.station,s.site,s.arrival,s.departure,s.revisions+(Revision(108,25,130),))
        self.assertEqual(r.request_at(107).energy,15);self.assertEqual(r.request_at(108).energy,25)
        _,_,a=replay([s],Controller('history',Model(),horizon=12),3,True)
        _,_,b=replay([r],Controller('history',Model(),horizon=12),3,True)
        self.assertEqual([x for x in a['actions'] if x['t']<108],[x for x in b['actions'] if x['t']<108])
    def test_late_request_no_backfill(self):
        s=session();s=Session(s.sid,s.user,s.station,s.site,s.arrival,s.departure,(Revision(105,12,116),))
        _,_,a=replay([s],Controller('equal',Model()),4,True)
        self.assertTrue(all(x['t']>=105 for x in a['actions']))
    def test_request_decrease_preserves_energy(self):
        s=session();s=Session(s.sid,s.user,s.station,s.site,s.arrival,s.departure,s.revisions+(Revision(108,1,116),))
        f,_,a=replay([s],Controller('equal',Model()),4,True)
        self.assertGreater(f.excess.iloc[0],0)
        self.assertTrue(all(x['t']<108 for x in a['actions']))
        self.assertEqual(f.shortfall.iloc[0],0)
    def test_history_update_once_after_departure(self):
        ss=[session('a','u',100,104,20),session('b','u',105,109,20)]
        _,_,a=replay(ss,Controller('debt_share',Model(),lam=4,rho=.2),2,True)
        self.assertEqual([r[0] for r in a['updates']],[104,109])
        self.assertTrue(all(x['debt']==0 for x in a['actions'] if x['t']<104))
        self.assertTrue(all(0<=r[-1]<=1 for r in a['updates']))
        _,_,b=replay(ss,Controller('debt_share',Model(),lam=4,rho=.2),2,True)
        self.assertEqual(a,b)
    def test_solver_failure_fallback(self):
        c=Controller('history',Model(),horizon=12);c.force_failure=True
        f,d,l=replay([session()],c,2,True)
        self.assertEqual(d['fallbacks'],d['decisions']);self.assertGreater(d['fallbacks'],0)
        self.assertLessEqual(d['max_violation'],1e-7)
    def test_oracle_bound_and_analytic_single_car(self):
        ss=[session(energy=20)]
        v=offline_energy(ss,2)['delivered_bound']
        self.assertAlmostEqual(v,16*.25*.92*2)
        for name in ['equal','point','history','pf_mpc']:
            f,_,_=replay(ss,Controller(name,Model(),horizon=12),2)
            self.assertLessEqual(f.delivered.sum(),v+1e-7)
    def test_expectation_equals_enumeration(self):
        durations=np.arange(1,6);prob=np.array([.1,.3,.2,.1,.3]);x=np.array([1.,.5,.3,.2,.1]);r=4
        S=np.array([prob[durations>k].sum() for k in range(5)])
        explicit=sum(p*max(0,r-x[:d].sum()) for d,p in zip(durations,prob))
        self.assertAlmostEqual(explicit,r-S@x)
    def test_malformed_and_empty_data_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.json'
            for content in ['{"_items":[','{"_items":[]}']:
                p.write_text(content)
                with self.assertRaises(ValueError):normalize(p)
    def test_nonfinite_action_rejected(self):
        from evfair.control import Decision
        class Bad(Controller):
            def act(self,*args):return Decision(np.array([float('nan')]),'bad')
        with self.assertRaises(AssertionError):replay([session()],Bad('equal',Model()),2)


class AdditionalChecks(unittest.TestCase):
    def test_forecast_free_policy_never_reads_model(self):
        class RejectForecast(Model):
            def survival(self,*args,**kwargs):raise AssertionError('forecast accessed')
        for name in ['equal','maxmin','debt_share','fcfs','edf']:
            a,_,_=replay([session()],Controller(name,RejectForecast()),2)
            self.assertGreater(a.delivered.sum(),0)
    def test_synthetic_split_is_temporal_and_newcomers_held_out(self):
        from evfair.synthetic import generate
        from evfair.experiment import split
        ss=generate(11);p=json.loads(Path('config/protocol.json').read_text());parts=split(ss,p)
        blocks=list(parts.values())
        for left,right in zip(blocks,blocks[1:]):self.assertLess(max(s.departure for s in left),min(s.arrival for s in right))
        train_users={s.user for s in parts['train']}
        new={s.user for s in parts['test']}-train_users
        self.assertEqual(len(new),6)
    def test_conditional_survival_distribution(self):
        from evfair.synthetic import generate
        from evfair.forecast import DepartureModel
        ss=generate(4,days=12,users=12);days=sorted({s.arrival//96 for s in ss});train=[s for s in ss if s.arrival//96 in days[:8]];cal=[s for s in ss if s.arrival//96 in days[8:]]
        m=DepartureModel().fit(train,cal);s=cal[-1]
        for kind in ['hazard','empirical']:
            m.kind=kind;v=m.survival(s.arrival,s.arrival+2,s.revisions[0].deadline,s.user,96)
            self.assertEqual(v[0],1);self.assertTrue(np.all(np.diff(v)<=0));self.assertTrue(np.all((v>=0)&(v<=1)))
            pmf=np.r_[-np.diff(v),v[-1]];self.assertAlmostEqual(pmf.sum(),1)
    def test_boundary_spanning_session_excluded(self):
        from evfair.data import split_sessions,STEP
        import pandas as pd
        edge=int(pd.Timestamp('2025-02-01',tz='America/Los_Angeles').timestamp()/STEP)
        s=session(arrival=edge-2,departure=edge+2)
        parts,n=split_sessions([s],['2025-01-01','2025-02-01','2025-03-01','2025-04-01','2025-05-01'])
        self.assertEqual(n,1);self.assertEqual(sum(len(x) for x in parts.values()),0)

    def test_lexicographic_point_solver_preserves_economic_optimum(self):
        from scripts.check_point_tiebreak import lexicographic
        from scipy.sparse import csr_matrix
        result=lexicographic(-np.ones(96),A_ub=csr_matrix(np.ones((1,96))),b_ub=np.array([4.]),bounds=[(0,1)]*96,method='highs')
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.x.sum(),4-2e-7)
        self.assertTrue(np.allclose(result.x[:4],1,atol=2e-7))
        self.assertLess(result.x[4:].sum(),2e-7)

if __name__=='__main__':unittest.main()
