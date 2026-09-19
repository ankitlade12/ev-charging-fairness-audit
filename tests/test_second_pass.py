import unittest
from copy import deepcopy
from collections import Counter
import numpy as np
from scipy.sparse import csr_matrix
from scripts.audit_revision_order import ordered_input
from scripts.second_pass_diagnostics import lex_solver


def record():
    return dict(sessionID='s',connectionTime='2025-01-06T08:00:00Z',disconnectTime='2025-01-06T12:00:00Z',userInputs=[dict(modifiedAt='2025-01-06T08:01:00Z',kWhRequested=10),dict(modifiedAt='2025-01-06T08:05:00Z',kWhRequested=15)])

class RevisionOrderTests(unittest.TestCase):
    def test_latest_exact_update_wins_independent_of_input_order(self):
        x=record();a,_=ordered_input([x]);x['userInputs'].reverse();b,_=ordered_input([x])
        self.assertEqual(a,b);self.assertEqual(a['_items'][0]['userInputs'][0]['kWhRequested'],15)
    def test_exact_timestamp_conflict_quarantines_record(self):
        x=record();x['userInputs'][1]['modifiedAt']=x['userInputs'][0]['modifiedAt']
        a,b=ordered_input([x]);self.assertFalse(a['_items']);self.assertEqual(b['conflicting_exact_timestamp_record_quarantined'],1)
    def test_both_duplicate_ids_quarantined(self):
        x=record();a,b=ordered_input([x,deepcopy(x)]);self.assertFalse(a['_items']);self.assertEqual(b['all_duplicate_id_records_quarantined'],2)
    def test_later_bins_retained(self):
        x=record();x['userInputs'][1]['modifiedAt']='2025-01-06T08:16:00Z'
        a,_=ordered_input([x]);self.assertEqual(len(a['_items'][0]['userInputs']),2)
    def test_invalid_revision_does_not_revert_to_old_request(self):
        x=record();x['userInputs'][1]['kWhRequested']=float('nan')
        a,b=ordered_input([x]);self.assertFalse(a['_items']);self.assertEqual(b['invalid_revision_record_quarantined'],1)
    def test_lexicographic_pf_auxiliary_variable_not_treated_as_energy(self):
        # A one-EV, 96-slot LP with one PF utility variable. The optimum fixes utility
        # at 4; the earliest-energy secondary must deliver in the first four slots.
        stats=Counter();c=np.r_[np.zeros(96),-1.]
        A=np.zeros((2,97));A[0,:96]=1;A[1,:96]=-1;A[1,96]=1
        r=lex_solver('pf_mpc',stats)(c,A_ub=csr_matrix(A),b_ub=np.array([4.,0.]),bounds=[(0,1)]*96+[(None,None)],method='highs')
        self.assertTrue(r.success);self.assertAlmostEqual(r.x[-1],4,places=6)
        self.assertTrue(np.allclose(r.x[:4],1,atol=2e-7));self.assertLess(r.x[4:96].sum(),2e-7)
        self.assertEqual(stats['second_accepted'],1)

if __name__=='__main__':unittest.main()
