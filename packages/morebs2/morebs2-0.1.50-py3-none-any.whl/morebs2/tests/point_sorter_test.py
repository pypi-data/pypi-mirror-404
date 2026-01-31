from morebs2 import point_sorter
import unittest
import numpy as np

'''
python -m morebs2.tests.point_sorter_test  
'''

def sample_pointsort_vector_1():
    return np.array([[0.0,5.0,12.0],\
        [0.0, 7.1, 6.3],\
        [1.0,15.0,31.0],\
        [2.0,10.0,1000.0],\
        [3.1,6.6,1.6],\
        [3.1,6.6,7.1],\
        [3.2,10.5,1.1],\
        [4.0,1.0,11.0],\
        [5.0,5.0,5.0],\
        [5.0,5.0,5.0]])

def test_tie_sets_for_vector():

    v1 = np.array((3.4, 3.4, 5.0, 5.01, 6.32, 6.32, 6.32, 6.32, 10.003))
    ts = point_sorter.tie_sets_for_vector(v1)

    assert [0,1] in ts, "missing tie 1"
    assert [4,7] in ts, "missing tie 2"
    assert len(ts) == 2, "incorrect ties #1"

    v2 = np.array([5.5,5.5])
    ts = point_sorter.tie_sets_for_vector(v2)
    assert [0,1] in ts and len(ts) == 1, "incorrect ties #2"
    return

class TestPointSorterClass(unittest.TestCase):

    def test__PointSorter_sort_it(self):

        q = sample_pointsort_vector_1()
        np.random.shuffle(q)
        ps = point_sorter.PointSorter(q)

        ps.sort_it()
        '''
        print("------")
        print("PS")
        print(ps.newData)
        '''
        testPointSortVector = sample_pointsort_vector_1()
        assert np.all(np.equal(ps.newData,testPointSortVector))


    def test_sorted_vector_value_search(self):

        tv1 = np.array([1.0, 2.0, 3.3, 5.2, 6.7, 8.9, 9.2, 11.3, 14.2])
        tv2 = np.array([6.7])
        tv3 = np.array([0.2, 0.4, 3.1, 6.7, 9.1, 20.1])
        tv4 = np.array([0.2, 0.4, 3.1, 6.71, 9.1, 20.1])

        assert point_sorter.sorted_vector_value_search(tv1, 6.7)[1]
        assert point_sorter.sorted_vector_value_search(tv2, 6.7)[1]
        assert point_sorter.sorted_vector_value_search(tv3, 6.7)[1]
        assert not point_sorter.sorted_vector_value_search(tv4, 6.7)[1]

    def test_sorted_vector_value_range_search(self):
        q = sample_pointsort_vector_1()
        vec = q[:,0]
        vec = np.sort(list(vec) + [3.1])
        q = point_sorter.sorted_vector_value_range_search(vec, 3.1)
        assert q[0] == [4,6], "invalid range search #1"

        vec2 = np.array([6.6,6.6])
        q = point_sorter.sorted_vector_value_range_search(vec2, 6.6)
        assert q[0] == [0,1], "invalid range search #2"

        vec3 = np.array([0.2, 0.4, 0.4, 0.4, 3.1, 6.71, 9.1, 20.1])
        q = point_sorter.sorted_vector_value_range_search(vec3, 0.4)
        assert q[0] == [1,3]

        vec4 = np.array([0.2, 0.4, 3.1, 6.71, 9.1, 20.1])
        q = point_sorter.sorted_vector_value_range_search(vec4, 0.4)
        assert q[0] == [1,1]

    def test__PointSorter__vector_exists(self):

        q = sample_pointsort_vector_1()
        np.random.shuffle(q)
        ps = point_sorter.PointSorter(q)
        ps.sort_it()

        v = np.array([3.1,6.6,7.10])
        assert ps.vector_exists(v) != -1

        v2 = np.array([3.1,6.6,7.12])
        assert ps.vector_exists(v2) == -1

        v3 = np.array([5.0,5.0,5.0])
        assert ps.vector_exists(v3) != -1

    def test__PointSorter__insert_point(self):
        q = sample_pointsort_vector_1()
        np.random.shuffle(q)
        q2 = np.empty((0,q.shape[1]))
        ps = point_sorter.PointSorter(q2)

        for q_ in q:
            ps.insert_point(q_)

        q = sample_pointsort_vector_1()
        assert np.all(np.equal(ps.newData,q))

    def test__PointSorter__update_points_from_cache(self):
        q = sample_pointsort_vector_1()
        np.random.shuffle(q)
        q2 = np.empty((0,q.shape[1]))
        ps = point_sorter.PointSorter(q2)

        for q_ in q:
            ps.log_delta_cache(q_,1)

        ps.update_points_from_cache(np.array([5.0,5.0,5.0]))

        assert point_sorter.equal_iterables(ps.extremumData[-1][0],np.array([5.0,5.0,5.0]))
        assert point_sorter.equal_iterables(ps.extremumData[1][0],[   2.,   10., 1000.])

        # delete extremum 1 and recheck `extremumData`
        x = [   2.,   10., 1000.]
        ps.log_delta_cache(x,-1)

        ps.update_points_from_cache(np.array([5.0,5.0,5.0]))

        assert point_sorter.equal_iterables(ps.extremumData[-1][0],np.array([5.0,5.0,5.0]))
        assert point_sorter.equal_iterables(ps.extremumData[1][0],[ 1., 15., 31.])

if __name__ == "__main__":
    unittest.main()
