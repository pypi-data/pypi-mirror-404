from .graph_basics_test_cases import *
from morebs2 import graph_basics 
import unittest


def nx_mapcheck_with_functions(D,nx_map,is_np:bool): 
    """
    nx map is either neighbor-child or neighbor-parent 
    map 
    """

    nf = graph_basics.doubly_connected
    f = graph_basics.parents_of if is_np else graph_basics.children_of

    for k,v in nx_map.items(): 
        assert v[0] == len(nf(D,k))
        assert v[1] == len(f(D,k))
    return 

'''
python -m morebs2.tests.graph_basics_test  
'''
class TestGraphBasicsMethods(unittest.TestCase):

    def test__GraphBasics__connections_measures_case1(self):
        D = graph_case_1()
        C = graph_basics.connected_to(D,0)
        assert C == set([1,2,3])
        P = graph_basics.parents_of(D,0)
        assert P == set([2,3])
        C2 = graph_basics.children_of(D,0)
        assert C2 == set([])
        D2 = graph_basics.doubly_connected(D,0)
        assert D2 == set([1])
        return

    def test__GraphBasics__connections_measures_case2(self):
        D = graph_case_8() 
        C = graph_basics.connected_to(D,7)
        assert C == set([0,3,8]) 
        P = graph_basics.parents_of(D,7) 
        assert P == set() 
        C2 = graph_basics.children_of(D,7) 
        assert C2 == set([0]) 
        D2 = graph_basics.doubly_connected(D,7)
        assert D2 == set([3,8])

    def test__GraphBasics__connections_measures_case3(self):
        D = graph_case_9() 
        prt = graph_basics.directed_edge_partition(D,1,D[1]) 
        assert prt == [set([0]),set([5,6])]

        D = graph_case_4()
        P = graph_basics.directed_edge_partition(D,0,[1,2])
        assert P == [set(), {1, 2}]

    def test__GraphBasics__connections_measures_case4(self):
        D = graph_case_9() 
        assert graph_basics.edge_count(D) == 11 

        D = graph_case_2() 
        assert graph_basics.edge_count(D) == 4 

        D = graph_case_3() 
        assert graph_basics.edge_count(D) == 8 

        D = graph_case_1() 
        assert graph_basics.edge_count(D) == 5 

    def test__GraphBasics__connections_measures_case5(self):

        D = graph_case_10()
        assert not graph_basics.is_directed_graph(D)

        D = graph_case_4()
        assert graph_basics.is_directed_graph(D)

        D = graph_case_2()
        assert graph_basics.is_directed_graph(D)

        D = graph_case_3()
        assert not graph_basics.is_directed_graph(D)

    def test__GraphBasics__connections_measures_case6(self):
        D = graph_case_12() 

        nc = graph_basics.nc_degree_map(D)
        npx = graph_basics.np_degree_map(D) 
        nx_mapcheck_with_functions(D,nc,False)
        nx_mapcheck_with_functions(D,npx,True) 

    def test__GraphBasics__connections_measures_case7(self):
        D = graph_case_1() 

        nc = graph_basics.nc_degree_map(D)
        npx = graph_basics.np_degree_map(D) 
        nx_mapcheck_with_functions(D,nc,False)
        nx_mapcheck_with_functions(D,npx,True) 

        assert nc == defaultdict(list, \
            {0: [1, 0], 1: [1, 1], 2: [0, 1], 3: [0, 1]})
        assert npx == defaultdict(list, \
            {0: [1, 2], 1: [1, 0], 2: [0, 1], 3: [0, 0]})

    def test__GraphBasics__connections_measures_case8(self):
        D = graph_case_2() 

        nc = graph_basics.nc_degree_map(D)
        npx = graph_basics.np_degree_map(D) 
        nx_mapcheck_with_functions(D,nc,False)
        nx_mapcheck_with_functions(D,npx,True) 

        assert nc == defaultdict(list, \
            {0: [0, 0], 1: [0, 1], 2: [0, 1], 3: [0, 1], 4: [0, 1]})
        assert npx == defaultdict(list, \
            {0: [0, 4], 1: [0, 0], 2: [0, 0], 3: [0, 0], 4: [0, 0]})



class TestGraphComponentDecompositionClass(unittest.TestCase):

    def test__GraphComponentDecomposition__init_decomp(self):
        D = graph_case_2() 
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.init_decomp(0) 
        assert gd.components == [[{0}]]

        D = graph_case_3()
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.is_directed = True 
        gd.init_decomp(0) 
        assert gd.components == [[{0,1,2,3,4}]]
        assert gd.key_cache == {0}
        assert gd.key_queue == [1, 2, 3, 4]
        gd.next_key()
        assert gd.key_queue == [2, 3, 4]
        assert gd.components == [[{0,1,2,3,4}]]

    def test__GraphComponentDecomposition__next_key_case1(self):
        D = graph_case_4()
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.next_key()
        assert gd.components == [[{0}, {1}], [{0}, {2}]]
        gd.next_key()
        assert gd.components == [[{0}, {2}], [{0}, {1}, {3}], [{0}, {1}, {4}]]
        while not gd.finstat:
            gd.next_key()
        assert gd.components == \
            [[{0}, {1}, {4}], [{0}, {2}, {5}], [{0}, {2}, {6}], [{0}, {1}, {3, 7}]]

    def test__GraphComponentDecomposition__next_key_case2(self):
        D = graph_case_5()

        P = graph_basics.directed_edge_partition(D,0,[1,2])
        assert P == [set(), {1, 2}]

        gd = graph_basics.GraphComponentDecomposition(D)
        gd.next_key()
        assert gd.components == [[{0}, {1}], [{0}, {2}]]
        gd.next_key()
        assert gd.components == [[{0}, {2}], [{0}, {1}, {3}], [{0}, {1}, {4}]]

    def test__GraphComponentDecomposition__next_key_case3(self):
        D = graph_case_6()
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.is_directed = True 
        while not gd.finstat:
            gd.next_key()

        assert gd.components == [[{0, 1, 2, 3, 4, 5, 6}]]

    def test__GraphComponentDecomposition__next_key_case4(self):
        D = graph_case_7()
        gd = graph_basics.GraphComponentDecomposition(D)
        while not gd.finstat:
            gd.next_key()

        assert graph_basics.edge_count(gd.d_) == 0 
        assert gd.components == \
            [[{0}, {1}, {4}], [{0}, {2}, {5}], \
            [{0}, {2}, {6}], \
            [{0}, {1}, {8, 9, 3, 7}, {10}]]
        assert gd.cyclic_keys == defaultdict(set,{7: {0}})
        assert gd.cyclic_component_indices() == [3]

        drm = defaultdict(int, {0: 0, 1: 2, 4: 2, \
            2: 2, 5: 2, 6: 2, 8: 2, 9: 2, 3: 2, 7: 2, 10: 3})
        assert gd.depth_rank_map() == drm 
        return

    def test__GraphComponentDecomposition__next_key_case5(self):
        D = graph_case_8()
        gd = graph_basics.GraphComponentDecomposition(D)
        while not gd.finstat:
            gd.next_key()

        assert graph_basics.edge_count(gd.d_) == 0 

        assert gd.components == \
            [[{0}, {1}, {4}], [{0}, {2}, {5}], \
            [{0}, {2}, {6}], \
            [{0}, {1}, {3, 7, 8, 9, 10}]]


        gd = graph_basics.GraphComponentDecomposition(D) 
        gd.init_decomp(9) 
        while not gd.finstat:
            gd.next_key()

        assert gd.components == [[{3, 7, 8, 9, 10}, {0}, {1}, {4}], \
            [{3, 7, 8, 9, 10}, {0}, {2}, {5}], \
            [{3, 7, 8, 9, 10}, {0}, {2}, {6}]]

        return 

    def test__GraphComponentDecomposition__next_key_case6(self):

        D = graph_case_9()
        gd = graph_basics.GraphComponentDecomposition(D)
        while not gd.finstat:
            gd.next_key()
        assert gd.cyclic_keys == defaultdict(set, {5: {0}})
        assert gd.components == [[{0, 1, 2, 3, 4}, {5}], [{0, 1, 2, 3, 4}, {6}]]

    def test__GraphComponentDecomposition__next_key_case7(self):
        D = graph_case_10()
        gd = graph_basics.GraphComponentDecomposition(D)

        while not gd.finstat: 
            gd.next_key()

        assert gd.components == [{0, 1, 2, 3, 4}, {7, 8, 9}, {10, 111}]

    def test__GraphComponentDecomposition__next_key_case8(self):
        D = graph_case_11() 
        gd = graph_basics.GraphComponentDecomposition(D) 
        gd.decompose()
        assert gd.components == [[{0, 1, 2, 3, 4}, {5}], \
            [{0, 1, 2, 3, 4}, {6}], [{7}, {12}, {41}], [{7}, {20}, {64}], \
            [{7}, {20}, {15}], [{7}, {12}, {38}, {11}, {31}]], "got {}".format(gd.components)

    def test__GraphComponentDecomposition__next_key_case9(self):

        D = graph_case_2()
        gd = graph_basics.GraphComponentDecomposition(D) 
        gd.decompose() 

        dr = gd.depth_rank_map() 
        assert dr == defaultdict(int, \
            {0: 4, 1: 0, 2: 0, 3: 0, 4: 0})

        assert gd.components == \
            [[{0}], [{1}, {0}], [{2}, {0}], [{3}, {0}], [{4}, {0}]]

    def test__GraphComponentDecomposition__next_key_case10(self):

        D = graph_case_3()
        gd = graph_basics.GraphComponentDecomposition(D) 
        gd.decompose() 

        ci = gd.cyclic_component_indices()
        dr = gd.depth_rank_map() 

        assert gd.components == [{0, 1, 2, 3, 4}]
        assert type(dr) == type(None) 

    def test__GraphComponentDecomposition__next_key_case11(self):
        D = graph_case_13() 
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.decompose()
        assert gd.components == [[{0, 7}, {9, 6}, {8}, {10}]]
        assert gd.cyclic_keys == defaultdict(set, {8: {0}})

    def test__GraphComponentDecomposition__dcomponent_cyclic_indices(self): 

        D = graph_case_14() 
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.decompose()
        assert gd.dcomponent_cyclic_indices(0) == [(0, 2), (3, 5)]
        q = gd.depth_rank_map__component(0)
        assert q == defaultdict(int, {0: 0, 7: 0, \
            9: 0, 6: 0, 8: 0, 10: 1, 12: 1, \
            11: 2, 13: 2})

        D[13].clear() 
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.decompose()
        assert gd.dcomponent_cyclic_indices(0) == [(0, 2)]
        q = gd.depth_rank_map__component(0)
        assert q == defaultdict(int, {0: 0, \
            7: 0, 9: 0, 6: 0, 8: 0, \
            10: 1, 12: 1, 11: 2, 13: 3})

    def test__GraphComponentDecomposition__depth_rank_map__component(self): 
        D = graph_case_2() 
        gd = graph_basics.GraphComponentDecomposition(D)
        gd.decompose()
        q = gd.depth_rank_map__component(0)
        assert q == defaultdict(int,{0:0})
        q2 = gd.depth_rank_map__component(1)
        assert q2 == defaultdict(int, {1: 0, 0: 1})
        return 


if __name__ == '__main__':
    unittest.main()
