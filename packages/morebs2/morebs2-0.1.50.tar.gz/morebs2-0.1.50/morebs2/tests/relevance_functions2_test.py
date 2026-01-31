from morebs2 import rssi,relevance_functions
#from relevance_functions import * 

import unittest
import numpy as np

'''
python -m morebs2.tests.relevance_functions2_test  
'''
class TestRelevanceFunctions(unittest.TestCase):

    def test__sample_rch_1_with_update(self):
        b = np.array([[0,1.0],[0,1.0],[0,1.0]])
        pb = np.copy(b)
        h = 9
        cv = 0.4
        rch = relevance_functions.sample_rch_1_with_update(b,pb,h,cv)

        # do one
        p = np.array([0.5,0.5,0.5])
        q = rch.apply(p)
        assert not q, "failed case 1"

        # update args
        pb2 = np.array([[0,0.6],[0,0.6],[0,0.6]])
        pb2 = np.array([[0,0.5],[0,0.5],[0,0.5]])

        updateArgs = [b,pb2,h,cv]
        rch.load_update_vars(updateArgs)
        rch.update_rch()

        p2 = np.array([0.3,0.3,0.3])
        p2 = np.array([0.25,0.25,0.25])

        q = rch.apply(p2)
        assert not q, "failed case 2"


    def sample_rssi_1_with_update(self):
        """
        an RSSI instance with an updating RCH. RSSI runs in mode::(relevance zoom)
        """
        b = np.array([[0,1.0],[0,1.0],[0,1.0]])
        pb = np.copy(b)
        h = 9
        cv = 0.4

        rch = relevance_functions.sample_rch_1_with_update(b,pb,h,cv)
        ##
        r = ResplattingSearchSpaceIterator(b, np.copy(b[:,0]), None, h,\
            resplattingMode = ("relevance zoom",rch), additionalUpdateArgs = (cv,))
        return r


if __name__ == '__main__':
    unittest.main()
