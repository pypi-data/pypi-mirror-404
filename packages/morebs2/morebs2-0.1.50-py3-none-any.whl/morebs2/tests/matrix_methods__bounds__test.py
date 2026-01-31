'''
this file tests the subset of
methods found in `matrix methods`
that are for bounds-related calculations
'''
from morebs2 import matrix_methods
import unittest
import numpy as np

'''
python -m morebs2.tests.matrix_methods__bounds__test  
'''
class TestNumericalGeneratorClass(unittest.TestCase):

    def test__point_in_improper_bounds(self):

        pb = np.array([[0.4,12],[-30,40],[70,112],[10,14]])
        b = np.array([[10,2],[9,-28], [93,72],[13.5,11.0]])
        q = matrix_methods.split_improper_bound(pb,b)
        p1 = np.array([3,-25,77,11.7]) # not
        p2 = np.array([11,39,102,10.1])

        x = matrix_methods.point_in_improper_bounds(pb,b,p1)
        assert not matrix_methods.point_in_improper_bounds(pb,b,p1), "incorrect case 1"
        assert matrix_methods.point_in_improper_bounds(pb,b,p2), "incorrect case 2"
        return

    def test__point_on_improper_bounds_by_ratio_vector(self):

        pb = np.array([[0.4,12],[-30,40],[70,112],[10,14]])
        b = np.array([[10,2],[9,-28], [93,72],[13.5,11.0]])

        # case 1:
        v = np.array([0.5,0.5,0.5,0.5])
        q = matrix_methods.point_on_improper_bounds_by_ratio_vector(pb,b,v)
        assert matrix_methods.point_in_improper_bounds(pb,b,q), "incorrect case 1.1"
        assert matrix_methods.equal_iterables(q,np.array([11.8,25.5,103.5,10.25])), "incorrect case 1.2"

        # case 2:
        v = np.array([0.9,0.9,0.8,0.1])
        q = matrix_methods.point_on_improper_bounds_by_ratio_vector(pb,b,v)
        assert matrix_methods.point_in_improper_bounds(pb,b,q), "incorrect case 2.1"
        assert matrix_methods.equal_iterables(q,np.array([1.64,38.7,109.8,13.65])), "incorrect case 2.2"
        return

    def test__vector_ratio_improper(self):

        pb = np.array([[0.4,12],[-30,40],[70,112],[10,14]])
        b = np.array([[10,2],[9,-28], [93,72],[13.5,11.0]])

        p1 = np.array([11.8,25.5,103.5,10.25])
        p2 = np.array([1.64,38.7,109.8,13.65])

        vr1 = matrix_methods.vector_ratio_improper(pb,b,p1)
        assert matrix_methods.equal_iterables(vr1,np.array([0.5,0.5,0.5,0.5])), "incorrect case 1.1"

        vr2 = matrix_methods.vector_ratio_improper(pb,b,p2)
        assert matrix_methods.equal_iterables(vr2,np.array([0.9,0.9,0.8,0.1])), "incorrect case 1.2"


    def test__point_difference_of_improper_bounds(self):

        pb = np.array([[0,1.00],\
                        [0,1.00],\
                        [0,1.00],\
                        [0,1.00]])

        # one index is improper
        bp1 = np.array([[0.5,0.75],\
                        [0.25,0.50],\
                        [0.9,0.1],\
                        [0,0.27]])

        # two indices are improper
        bp2 = np.array([[0.5,0.75],\
                        [0.5,0.15],\
                        [0.9,0.1],\
                        [0,0.27]])

        # all indices are improper
        bp3 = np.array([[0.5,0.17],\
                        [0.5,0.15],\
                        [0.9,0.1],\
                        [0.72,0.3]])

        q = matrix_methods.point_difference_of_improper_bounds(bp1,pb)
        s1 = np.array([0.25,0.25,0.2,0.27])
        assert matrix_methods.equal_iterables(q,s1)

        q = matrix_methods.point_difference_of_improper_bounds(bp2,pb)
        s2 = np.array([0.25,0.65,0.2,0.27])
        assert matrix_methods.equal_iterables(q,s2)

        q = matrix_methods.point_difference_of_improper_bounds(bp3,pb)
        s3 = np.array([0.67,0.65,0.2,0.58])
        assert matrix_methods.equal_iterables(q,s3)
        return

    def test__point_on_improper_bounds_by_ratio_vector(self):

        pb = np.array([[0,1.00],\
                        [0,1.00],\
                        [0,1.00],\
                        [0,1.00]])

        # one index is improper
        bp1 = np.array([[0.5,0.75],\
                        [0.25,0.50],\
                        [0.9,0.1],\
                        [0,0.27]])

        # half
        rv = np.array([0.5,0.5,0.5,0.5])
        p1 = matrix_methods.point_on_improper_bounds_by_ratio_vector(pb,bp1,rv)
        assert matrix_methods.equal_iterables(p1,[0.625,0.375,0.,0.135])

        # max dominant
        rv = np.array([0.9,0.9,0.9,0.9])
        p1 = matrix_methods.point_on_improper_bounds_by_ratio_vector(pb,bp1,rv)
        assert matrix_methods.equal_iterables(p1,[0.725,0.475,0.08,0.243])

        # min dominant
        rv = np.array([0.1,0.1,0.1,0.1])
        p1 = matrix_methods.point_on_improper_bounds_by_ratio_vector(pb,bp1,rv)
        assert matrix_methods.equal_iterables(p1,[0.525,0.275,0.92,0.027])

    def test__submatrix__2d(self): 

        x = np.arange(1,21)
        x = x.reshape((4,5))
        q0 = matrix_methods.submatrix__2d(x,(1,2),"L+U")
        assert np.all(q0 == np.array(\
        [[ 6,  7,  8],\
        [11, 12, 13],\
        [16, 17, 18]]))

        q1 = matrix_methods.submatrix__2d(x,(1,2),"L+L")
        assert np.all(q1 == np.array([\
        [ 8,  9, 10],\
        [13, 14, 15],\
        [18, 19, 20]]))

        q2 = matrix_methods.submatrix__2d(x,(1,2),"R+L")
        assert np.all(q2 == np.array([\
        [ 3,  4,  5],\
        [ 8,  9, 10]])) 

        q3 = matrix_methods.submatrix__2d(x,(1,2),"R+U")
        assert np.all(q3 == np.array([\
        [1, 2, 3],\
        [6, 7, 8]])) 

    def test__index_range_of_subvec__case1(self):

        v = [0,10,13,14,17,19,20,21,21,21,0,20,21,10,14,17] 
        sv = [17,19,20,21] 
        ir1 = matrix_methods.index_range_of_subvec(v,sv,is_contiguous=True)
        assert v[ir1[0]:ir1[1]] == sv 

        sv1 = [0,10,17,21]
        ir1 = matrix_methods.index_range_of_subvec(v,sv1,is_contiguous=False)
        assert ir1 == (0,7)

        sv2 = [10,14,19,14,17] 
        ir2 = matrix_methods.index_range_of_subvec(v,sv2,is_contiguous=False)
        assert ir2 == (1,15)

        sv3 = [10,14,19,14,17100]  
        ir3 = matrix_methods.index_range_of_subvec(v,sv3,is_contiguous=False)
        assert type(ir3) == type(None)


if __name__ == '__main__':
    unittest.main()
