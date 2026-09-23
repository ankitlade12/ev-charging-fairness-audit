"""Checks specific to the real-session extension."""
import unittest
import numpy as np
import pandas as pd
from evfair.data import Session,Revision,STEP
from scripts.real_data_study import split_real,block_intervals,check_actions,select

class RealDataChecks(unittest.TestCase):
    def test_split_uses_local_midnight_and_rejects_spanning_sessions(self):
        boundary=int(pd.Timestamp('2019-07-01',tz='America/Los_Angeles').timestamp()/STEP)
        def session(sid,a,d):return Session(sid,'user','port','jpl',a,d,(Revision(a,10,a+4),))
        rows=[session('before',boundary-8,boundary-4),session('after',boundary,boundary+4),session('spanning',boundary-1,boundary+1)]
        parts,excluded=split_real(rows,{'validation':['2019-06-01','2019-07-01'],'test':['2019-07-01','2019-10-01']})
        self.assertEqual([s.sid for s in parts['validation']],['before'])
        self.assertEqual([s.sid for s in parts['test']],['after']);self.assertEqual(excluded,1)
    def test_paired_blocks_keep_known_constant_difference_and_ratios(self):
        rows=[dict(sid=f'{day}-{u}',user=u,day=f'2019-07-{day+1:02d}',requested=10,delivered=8,cost=1,shortfall=.2,excess=0,cohort='regular') for day in range(10) for u in range(10)]
        b=pd.DataFrame(rows);a=b.assign(shortfall=.1,delivered=9,cost=1.125)
        result=block_intervals(a,b,block=2,reps=30)
        for bound in ['low','high']:
            self.assertAlmostEqual(result['tail_pp'][bound],-10)
            self.assertAlmostEqual(result['delivery_percent'][bound],112.5)
            self.assertAlmostEqual(result['unit_cost_percent'][bound],100)
        with self.assertRaises(AssertionError):block_intervals(a,b.assign(sid='wrong'),reps=2)
    def test_action_check_rejects_post_departure_delivery(self):
        session=Session('s','u','port','jpl',10,12,(Revision(10,10,12),))
        frame=pd.DataFrame([dict(sid='s',requested=10,delivered=1,shortfall=.9,excess=0)])
        action=pd.DataFrame([dict(t=12,sid='s',power=1/(.25*.92),battery_kwh=1,energy=1,request=10)])
        with self.assertRaises(AssertionError):check_actions(frame,action,[session],6.6)
        action['t']=11;check_actions(frame,action,[session],6.6)
    def test_validation_does_not_choose_low_tail_that_breaks_delivery_guardrail(self):
        rows=pd.DataFrame([dict(policy='history',gamma=10,lam=1,rho=.2,horizon=96,tail=.01,delivered=90,cost_per_kwh=.1),dict(policy='history',gamma=40,lam=4,rho=.2,horizon=96,tail=.10,delivered=99,cost_per_kwh=.1)])
        base=pd.Series({'delivered':100,'cost_per_kwh':.1})
        self.assertEqual(select(rows,base)['gamma'],40)
if __name__=='__main__':unittest.main()
