from morebs2 import numerical_generator
import numpy as np
from collections import OrderedDict

import unittest

'''
python -m morebs2.tests.numerical_generator_test  
'''
class TestNumericalGeneratorClass(unittest.TestCase):

    def test_CycleMap__random_map(self):
        vr = numerical_generator.CycleMap.random_cycle_map(5)
        ##print("VR")
        ##print(vr)

        f = numerical_generator.CycleMap.is_valid_map(vr)
        ##print("F: ", f)
        assert f, "random cycle map is not cycle"

        q = OrderedDict()
        x = [(3,1),(1,3),(2,4),(4,2)]
        for k,v in x:
            q[k] = v

        f2 = numerical_generator.CycleMap.is_valid_map(q)
        ##print("F2: ", f2)
        assert not f2, "non-cyclic map"
        return

    def test__generate_possible_binary_sequences(self):
        g = numerical_generator.generate_possible_binary_sequences(5, [])
        g = list(g)
        assert len(g) == 2 ** 5, "incorrect generation"

        # uncomment for viewing
        '''
        for g_ in g:
            print(g_)
        '''

    def test__random_npoint_from_point_in_bounds(self):

        bounds = np.array([[-100,100.0],\
                        [-100,100.0],\
                        [-100,100.0],\
                        [-100,100.0],\
                        [-100,100.0],\
                        [-100,100.0]])
        r = 200.0

        # case point on >= 1 of the bound extremes
        p1 = np.array([-100,100,-99,80,95.0,-100])
        for i in range(100):
            p2 = numerical_generator.random_npoint_from_point_in_bounds(bounds,p1,r)
            assert type(p2) != type(None)
        return

    def test__random_npoint_from_point(self):
        r = 200.0

        # case point on >= 1 of the bound extremes
        p1 = np.array([-100,100,-99,80,95.0,-100])
        for i in range(100):
            p2 = numerical_generator.random_npoint_from_point(p1,r)
            assert type(p2) != type(None)
        return

    def test__CycleMap__next(self): 
        cm = numerical_generator.CycleMap(5)
        d = OrderedDict({10:13,13:74,74:21,21:16,16:10})
        cm.set_map(d)
        q = set() 

        for i in range(10): 
            q_ = next(cm) 
            q |= {q_}
        assert len(q) == 5 

        cm = numerical_generator.CycleMap(7)
        f = numerical_generator.CycleMap.random_cycle_map(7)
        cm.set_map(f) 
        q = set()
        for i in range(10): 
            q_ = next(cm) 
            q |= {q_}
        assert len(q) == 7

    def test__prg_seqsort_ties(self): 
        prg0 = numerical_generator.prg__constant(5)
        prg4 = numerical_generator.prg__n_ary_alternator(s0=3,s1=25,start=1) 
        R2 = ["3","52432","cat","DGO","bingo","ROGUE", "rauchu", "NOBODIES","12,55","32","43,10,13","12"] 
        Q = [(40,r) for r in R2] 
        vf = lambda x: x[1] 
        rq = numerical_generator.prg_seqsort_ties(Q,prg4,vf) 

        assert rq == [(40, '12'), (40, '12,55'), (40, '3'), \
            (40, '32'), (40, '43,10,13'), (40, '52432'), \
            (40, 'DGO'), (40, 'NOBODIES'), (40, 'ROGUE'), \
            (40, 'bingo'), (40, 'cat'), (40, 'rauchu')]

        Q2 = [(prg4(),r) for r in R2] 
        Q2.extend([(prg4(),r) for r in R2]) 
        Q2.extend([(prg4(),r) for r in R2]) 

        vf2 = lambda x: x[0] 
        rq2 = numerical_generator.prg_seqsort_ties(Q2,prg4,vf2) 
        rq3 = numerical_generator.prg_seqsort_ties(Q2,prg0,vf2) 

        assert rq2 == [(3, '32'), (3, 'NOBODIES'), \
            (4, '43,10,13'), (4, '12,55'), (5, '12'), \
            (5, '32'), (6, '3'), (6, '43,10,13'), \
            (7, '52432'), (7, '12'), (8, 'cat'), \
            (9, 'DGO'), (10, 'bingo'), (11, 'ROGUE'), \
            (12, 'rauchu'), (13, 'NOBODIES'), (14, '12,55'), \
            (15, '32'), (16, '3'), (16, '43,10,13'), \
            (17, '52432'), (17, '12'), (18, 'cat'), (18, '3'), \
            (19, 'DGO'), (19, '52432'), (20, 'bingo'), (20, 'cat'), \
            (21, 'ROGUE'), (21, 'DGO'), (22, 'rauchu'), \
            (22, 'bingo'), (23, 'NOBODIES'), (23, 'ROGUE'), \
            (24, '12,55'), (24, 'rauchu')]

        assert rq3 == [(3, 'NOBODIES'), (3, '32'), (4, '12,55'), \
            (4, '43,10,13'), (5, '32'), (5, '12'), (6, '43,10,13'), \
            (6, '3'), (7, '12'), (7, '52432'), (8, 'cat'), (9, 'DGO'), \
            (10, 'bingo'), (11, 'ROGUE'), (12, 'rauchu'), \
            (13, 'NOBODIES'), (14, '12,55'), (15, '32'), \
            (16, '43,10,13'), (16, '3'), (17, '12'), (17, '52432'), \
            (18, '3'), (18, 'cat'), (19, '52432'), (19, 'DGO'), \
            (20, 'cat'), (20, 'bingo'), (21, 'DGO'), (21, 'ROGUE'), \
            (22, 'bingo'), (22, 'rauchu'), (23, 'ROGUE'), (23, 'NOBODIES'), \
            (24, 'rauchu'), (24, '12,55')]

    def test__prg_partition_for_sz(self): 
        import random 
        random.seed(100)

        lc = numerical_generator.LCG(32,3901)
        def prg1_(): 
            def f(): 
                return next(lc) 
            return f 

        prg1 = prg1_() 
        S = 100
        num_sets = 100 
        p1 = numerical_generator.prg_partition_for_sz(S,num_sets,prg1,0.0)
        assert p1 == [1] * 100 

        num_sets = 50 
        p2 = numerical_generator.prg_partition_for_sz(S,num_sets,prg1,0.0)
        assert p2 == [2] * 50

        prg1 = prg1_() 
        num_sets = 50 
        p3 = numerical_generator.prg_partition_for_sz(S,num_sets,prg1,0.5)
        assert p3 == [30, 18, 4, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, \
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, \
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, \
            1, 1, 1],"got {}".format(p3)
        assert sum(p3) == 100 


        num_sets = 50 
        p4 = numerical_generator.prg_partition_for_sz(S,num_sets,prg1,0.1)
        assert p4 == [31, 3, 8, 12, 1, 1, 1, 1, 1, 1, 1, 1, 1, \
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, \
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, \
            1, 1, 1],"got {}".format(p4) 
        assert sum(p4) == 100 

        num_sets = 15 
        p5 = numerical_generator.prg_partition_for_sz(S,num_sets,prg1,0.1)
        assert p5 == [56, 27, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], \
            "got {}".format(p5) 
        assert sum(p5) == 100 

        num_sets = 4
        p6 = numerical_generator.prg_partition_for_sz(S,num_sets,prg1,0.1)
        assert p6 == [86, 2, 9, 3], "got {}".format(p6) 
        assert sum(p6) == 100 

        prng = numerical_generator.prg__LCG(-4,5,2,29)
        S = 100
        num_sets = 20
        prt = numerical_generator.prg_partition_for_sz(S,num_sets,prng,0.0)
        assert prt == [5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 26]
        assert sum(prt) == 100 

    def test__prg_partition_for_float(self):
        F = 50. 
        df = 60
        prg = numerical_generator.prg__LCG(144,544,-32,4012) 
        var = 0.25 
        P = numerical_generator.prg_partition_for_float(F,df,prg,var,n=1000,rounding_depth=5)
        P_sol = np.array([0.2, 0.4, 1. , 0.5, 0.7, \
            0.2, 0.6, 0.1, 0.1, 1.2, 0.6, 0.3, 0.5,\
            1.7, 2.2, 0.1, 1.8, 0.1, 0.8, 0.2, 0.7, \
            1.5, 0.3, 0.4, 0.4, 1.5, 0.1, 0.1, 0.7, \
            1.6, 2.1, 1.5, 0.3, 0.5, 1.4, 1.5, 0.8, \
            2.7, 2.2, 0.2, 0.3, 1.8, 0.8, 0.2, 0.6, \
            0.7, 0.4, 0.7, 1.1, 0.6, 0.6, 0.6, 1.8, \
            1.5, 0.6, 0.5, 1.2, 1.3, 0.5, 0.4])

        assert np.sum(P) == F
        assert np.all(P == P_sol) 

        df2 = 20
        P2 = numerical_generator.prg_partition_for_float(F,df2,prg,var,n=1000,rounding_depth=5)
        assert np.sum(P2) == F

        df3 = 600 
        P3 = numerical_generator.prg_partition_for_float(F,df3,prg,var,n=1000,rounding_depth=5)
        assert np.sum(P3) == F


if __name__ == '__main__':
    unittest.main()
