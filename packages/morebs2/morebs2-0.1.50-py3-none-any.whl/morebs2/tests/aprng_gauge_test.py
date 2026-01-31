from morebs2 import aprng_gauge,search_space_iterator
import numpy as np
import unittest

"""
python -m morebs2.tests.aprng_gauge_test  
"""

def equal_BatchIncrStruct_output(bis,wanted):
    stat = True 
    coll = []
    while stat:
        p = next(bis)
        stat = not (type(p) == type(None))
        if stat: coll.append(p)
    coll = np.array(coll) 
    return np.equal(coll,wanted).all() 

class TestBatchIncrStructMethods(unittest.TestCase):

    def test__BatchIncrStruct_argseq_1(self):
        bis = aprng_gauge.BatchIncrStruct(3,True,True,2)
        ans = [[0, 0],\
        [0, 1],\
        [0, 2],\
        [1, 0],\
        [1, 1],\
        [1, 2],\
        [2, 0],\
        [2, 1],\
        [2, 2]]
        assert equal_BatchIncrStruct_output(bis,ans)

    def test__BatchIncrStruct_argseq_2(self):
        bis = aprng_gauge.BatchIncrStruct(3,True,False,2)
        ans = [[0, 1],\
        [0, 2],\
        [1, 0],\
        [1, 2],\
        [2, 0],\
        [2, 1]]
        assert equal_BatchIncrStruct_output(bis,ans)

    def test__BatchIncrStruct_argseq_3(self):
        bis = aprng_gauge.BatchIncrStruct(3,False,True,2)
        ans =[[0, 0],\
        [0, 1],\
        [0, 2],\
        [1, 1],\
        [1, 2],\
        [2, 2]]
        assert equal_BatchIncrStruct_output(bis,ans)

    def test__BatchIncrStruct_argseq_4(self):
        bis = aprng_gauge.BatchIncrStruct(3,False,False,2)
        ans = [[0, 1],\
        [0, 2],\
        [1, 2]]
        assert equal_BatchIncrStruct_output(bis,ans)

class TestAPRNGGaugeMethods(unittest.TestCase):

    def test__coverage_of_sequence(self):
        vf = [0.0,3.0,7.0]
        rv = [0.0,10.0]
        max_radius = 1.0
        cov = aprng_gauge.coverage_of_sequence(vf,rv,max_radius)
        assert cov == 0.5

        max_radius = 2.0
        cov = aprng_gauge.coverage_of_sequence(vf,rv,max_radius)
        assert cov == 0.9

        max_radius = 1.5
        cov = aprng_gauge.coverage_of_sequence(vf,rv,max_radius)
        assert cov == 0.75

    def test__normalized_uwpd(self):
        v = np.array([0,1,5,-10,12])
        rv = [-10,20]
        q0 = aprng_gauge.uwpd(v,accum_op = np.add)
        ans = sum([1, 5, 10, 12, 4, 11, 11, 15, 7, 22])
        assert q0 == ans

        q1 = aprng_gauge.max_float_uwpd(5,rv)
        nuwpd = aprng_gauge.normalized_float_uwpd(v,rv)
        assert np.round(ans / q1,5) == \
            nuwpd, "got {} wanted {}".format(nuwpd,ans/q1) 

    def test__to_noncontiguous_ranges(self):
        ranges = [[0,1],[0.7,1.5],[1.6,2.0],[1.65,2.3]]
        tnr = aprng_gauge.to_noncontiguous_ranges(ranges)
        assert tnr == [[0, 1.5], [1.6, 2.3]]

    def test__complement_of_noncontiguous_ranges(self): 
        rangez = [(0,20),(30,42),(45,65),(75,91)]
        rv1 = (0,100)
        q = aprng_gauge.complement_of_noncontiguous_ranges(rangez,rv1)

        rv2 = (-30,120)
        q2 = aprng_gauge.complement_of_noncontiguous_ranges(rangez,rv2)

        assert q == [(20, 30), (42, 45), (65, 75), (91, 100)]
        assert q2 == [(-30, 0), (20, 30), (42, 45), (65, 75), (91, 120)]

    def test__vector_to_noncontiguous_range_indices(self): 
        rangez = [(0,20),(30,42),(45,65),(75,91)]
        v = [1,2,3,25,44,41,70,112]
        ncri = aprng_gauge.vector_to_noncontiguous_range_indices(v,rangez)
        ncri_sol = np.array([ 0,  0,  0, -1, -1,  1, -1, -1])
        assert np.all(ncri == ncri_sol)

    def test__neighbors_of_ncrange(self): 
        rangez = [(0,20),(30,42),(45,65),(75,91)]
        rv1 = (0,100)
        q = aprng_gauge.complement_of_noncontiguous_ranges(rangez,rv1)

        rv2 = (-30,120)
        q2 = aprng_gauge.complement_of_noncontiguous_ranges(rangez,rv2)

        nxx = aprng_gauge.neighbors_of_ncrange(rangez,q2,0)
        nxx1 = aprng_gauge.neighbors_of_ncrange(rangez,q2,1)
        nxx2 = aprng_gauge.neighbors_of_ncrange(rangez,q2,2)

        assert nxx == [(-30, 0), (20, 30)]
        assert nxx1 == [(20, 30), (42, 45)]
        assert nxx2 == [(42, 45), (65, 75)]

        nxx3 = aprng_gauge.neighbors_of_ncrange(q2,rangez,0)
        nxx4 = aprng_gauge.neighbors_of_ncrange(q2,rangez,1)
        nxx5 = aprng_gauge.neighbors_of_ncrange(q2,rangez,2)
        nxx6 = aprng_gauge.neighbors_of_ncrange(q2,rangez,3)
        nxx7 = aprng_gauge.neighbors_of_ncrange(q2,rangez,4)

        assert nxx3 == [None, (0, 20)]
        assert nxx4 == [(0, 20), (30, 42)]
        assert nxx5 == [(30, 42), (45, 65)]
        assert nxx6 == [(45, 65), (75, 91)]
        assert nxx7 == [(75, 91), None]

    def test_APRNGGauge__measure_cycle(self):

        bounds = np.array([[0,5],\
                        [0,5],\
                        [0,5]])

        start_point = np.zeros((3,))
        column_order = [2,1,0] # [0,1,2]
        ssi_hop = 5
        cycle_on = False
        cycle_is = 0

        ssi = search_space_iterator.SearchSpaceIterator(bounds,start_point,column_order,\
            ssi_hop,cycle_on,cycle_is)
        def fq():
            return np.sum(next(ssi)) 

        ap = aprng_gauge.APRNGGauge(fq,[0,15.],0.5) 
        term_func = lambda l,l2: not (l == l2).all() if type(l2) != type(None) else True 
        mc = ap.measure_cycle(term_func=term_func)
        assert mc == [0.83333, 0.18622]
        return

if __name__ == '__main__':
    unittest.main()