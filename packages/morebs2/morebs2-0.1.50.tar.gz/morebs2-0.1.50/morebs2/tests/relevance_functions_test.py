from morebs2 import relevance_functions
from morebs2 import search_space_iterator
import unittest
import numpy as np
import operator

'''
python -m morebs2.tests.relevance_functions_test  
'''

# modulo
"""

ispx,modulo

apply f(x) on v -> float q
apply modulo 9 on q -> float q2
q is in range (3,7)?
"""
def sample__RCHF__ISPoly__case_1():

    def qf2(f):
        return f % 9
    kwargs1 = ['nr', qf2]

    def cf1(x,x2):
        return x >= x2[0] and x <= x2[1]
    kwargs2 = ['nr', cf1, [3.0,6.0]]
    return relevance_functions.RCHF__ISPoly(5.0,[kwargs1,kwargs2])

"""
    examples:
    epd:
        - rf := reference (vector)
        - dm := euclidean_point_distance | vector modulo
        - cf := operator
        - dt := operand

    in bounds:
        [a] bool::(range each)
        [b] float::(ratio of columns in range)
        [c] bool([b])
"""
##----------------------------------------------------------
class TestRelevanceFunctions(unittest.TestCase):

    # normalized euclidean point distance, w/ reference?
    def test__rf__euclidean_point_distance(self):
        rf = np.array([8.0,2.3,3.1,4.5,7.1,8.8])
        dm = relevance_functions.euclidean_point_distance
        cf = operator.lt

        # distance threshold is float
        dt = 20.0
        q = relevance_functions.addon_singleton__bool__criteria_distance_from_reference(rf, dm, dt,cf)

        # test the points
        p1 = np.array([6.2,3.1,5.5,4.5,7.1,8.8])
        p2 = np.array([25.5,3.1,5.7,14.5,8.0,9.8])
        assert q(p1), "[0] incorrect case 1"
        assert not q(p2), "[0] incorrect case 2"

        # distance threshold is range
        cf = relevance_functions.lambda_floatin
        dt = (5.0,25.0)
        q = relevance_functions.addon_singleton__bool__criteria_distance_from_reference(rf, dm, dt,cf)
        assert not q(p1), "[1] incorrect case 1"
        assert q(p2), "[1] incorrect case 2"

    def test__RChainHead__euclidean_point_distance__(self):

        rf = np.array([8.0,2.3,3.1,4.5,7.1,8.8])
        dm = relevance_functions.euclidean_point_distance
        cf = operator.lt
        dt = 20.0
        kwargs = ['r', rf,dm,cf,dt]

        rc = relevance_functions.RChainHead()
        rc.add_node_at(kwargs)

        # args. for euclidean_point_distance

        p1 = np.array([6.2,3.1,5.5,4.5,7.1,8.8])
        p2 = np.array([25.5,3.1,5.7,14.5,8.0,9.8])
        assert rc.apply(p1), "[0] incorrect case 1"
        assert not rc.apply(p2), "[0] incorrect case 2"

    def test__RChainHead___in_bounds___(self):

        # case 1: bool::(range each)
        p1 = np.array([6.2,3.1,5.5,4.5,7.1,8.8])

            # subcase: dt is pair
        bounds0 = np.array([[3.1,9]])
        kwargs = ['nr', relevance_functions.lambda_pointinbounds, bounds0]
        rc = relevance_functions.RChainHead()
        rc.add_node_at(kwargs)
        assert rc.apply(p1) == True, "case 1.1: incorrect"

            # subcase: dt is bounds
        bounds = np.array([[5.0,7.0],\
                [3.2,4.1],\
                [5,6],\
                [4.5,4.7],\
                [6.5,7.5],\
                [8.5,9.2]])

        kwargs = ['nr', relevance_functions.lambda_pointinbounds, bounds]
        rc = relevance_functions.RChainHead()
        rc.add_node_at(kwargs)
        assert rc.apply(p1) == False, "case 1.2: incorrect"

        # case 2: float::(number of columns in range)
            # subcase: dt is pair
        kwargs = ['nr', relevance_functions.lambda_countpointsinbounds, bounds0]
        rc = relevance_functions.RChainHead()
        rc.add_node_at(kwargs)
        ##print("X ", rc.apply(p1))
        assert rc.apply(p1) == 6, "case 2.1: incorrect"

            # subcase: dt is pair
        bounds2 = np.array([[3.2,8.8]])
        kwargs = ['nr', relevance_functions.lambda_countpointsinbounds, bounds2]
        rc = relevance_functions.RChainHead()
        rc.add_node_at(kwargs)
        ##print("X ", rc.apply(p1))
        assert rc.apply(p1) == 5, "case 2.2: incorrect"

            # subcase: dt is bounds
        kwargs = ['nr', relevance_functions.lambda_countpointsinbounds,bounds]
        rc = relevance_functions.RChainHead()
        rc.add_node_at(kwargs)
        ##print("X ", rc.apply(p1))
        assert rc.apply(p1) == 5, "case 2.3: incorrect"

    # TODO: refactor into 2 branches
    """
    demonstrates how subvector selector is used
    by their input
    """
    def test__RChainHead___subvectorselector___(self):

        ## case 1: uses function `add_on_sample`
        p1 = np.array([6.2,3.1,5.5,4.5,7.1,8.8])

        def add_on_sample(v_):
            return v_ / 1.5 + 1 > np.mean(p1)

        q = relevance_functions.subvector_selector(add_on_sample,outputType =2)
        kwargs = ['nr', q]

        rc = relevance_functions.RChainHead()
        rc.add_node_at(kwargs)

        q = rc.apply(p1)
        assert relevance_functions.equal_iterables(q,np.array([[5.,8.8]])), "[0] invalid result"

    def test__sample__RCHF__ISPoly__case_1(self):
        q = sample__RCHF__ISPoly__case_1()

        p1 = np.array([3.0,4.0,0.0,11.1])
        p2 = np.array([0.0,14.0,2.0,3.1])

        # 486.1 % 9 = 0.1
        assert q(p1) == False, "incorrect ISPoly case 1.1"

        # 3.1
        assert q(p2) == True, "incorrect ISPoly case 1.1"

    def test__sample_rch_3_with_update(self):
            
        def new_sample_ssi(): 
            bounds = np.array([[-5.,15.],
                                [-10.,25.],
                                [16.,71.],
                                [30.,130.]])
            ssiHop = 5
            columnOrder = [0,1,2,3]
            return search_space_iterator.SearchSpaceIterator(bounds, np.copy(bounds[:,0]), columnOrder, ssiHop,True,0)

        s = new_sample_ssi()
        r = relevance_functions.sample_rch_3_with_update(9,7,14,[2,8])

        ts = []
        for i in range(10):
            v = next(s)
            t = r.apply(v)
            ts.append(t)

        answers = [True,True,True,True,True,True,True,False,True,False]
        assert ts == answers, "incorrect, first 10 samples"

        r.update_rch()

        ts = []
        for i in range(10):
            v = next(s)
            t = r.apply(v)
            ts.append(t) 

        answers2 = [False,False,False,False,False,False,False,False,False,False]
        assert ts == answers2, "incorrect, seconds 10 samples,\nwant {}\ngot {}".format(answers2,ts)



################################

if __name__ == '__main__':
    unittest.main()
