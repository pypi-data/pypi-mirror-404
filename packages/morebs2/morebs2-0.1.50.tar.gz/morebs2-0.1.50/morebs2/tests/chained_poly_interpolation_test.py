from morebs2 import chained_poly_interpolation
import numpy as np
import unittest

'''
python -m morebs2.tests.chained_poly_interpolation_test  
'''
class TestChainedLagrangePolySolverClass(unittest.TestCase):

    """
    1 y
    2 n
    """
    def LagrangePolySolver___duplicates_exist(self):
        # duplicates work 1
        x1 = [1.0,4.2]
        x2 = [5.0,4.2]
        x3 = [5.0,4.2]
        #ps = np.array([x1,x2])
        ps = np.array([x1,x2,x3])
        lps = chained_poly_interpolation.LagrangePolySolver(ps)
        ps2 = lps.form_point_sequence()

        # duplicates work 2
        x1 = [1.0,4.2]
        x2 = [5.0,4.2]
        x3 = [5.0,4.3]
        ps = np.array([x1,x2,x3])
        lps = chained_poly_interpolation.LagrangePolySolver(ps)
        ps2 = lps.form_point_sequence()

        ##
        """
        print("TESTING")
        for p in ps2:
            print(p)

        print("CASE 3")
        r = lps.output_by_lagrange_basis(1.0)
        print(r)
        """

    def test__ChainedLagrangePolySolver__init___failed(self):

        # a 4-d case 1
        x1 = [1.0,4.2,7.3,1.0]
        x2 = [5.0,4.2,7.3,2.0]
        x3 = [7.0,4.2,7.3,3.0]
        xs = np.array([x1,x2,x3])
        try:
            clps = chained_poly_interpolation.ChainedLagrangePolySolver(xs)
            assert False, "failioncos"
        except:
            #print("failed point-set 1.1")
            pass

        # a 4-d case 2
        x1 = [1.0,4.2,7.3,1.0]
        x2 = [5.0,4.5,7.2,2.0]
        x3 = [7.0,3.0,7.1,3.0]
        x4 = [1.0,5.0,7.0,1.0]
        x5 = [5.0,4.2,7.05,2.0]
        x6 = [7.0,4.2,6.8,3.0]
        xs = np.array([x1,x2,x3,x4,x5,x6])

        clps = chained_poly_interpolation.ChainedLagrangePolySolver(xs)#.form_point_sequence(hopIncrement = hopIncrement,capture = False)
        clps.set_axis_order_of_interpolation(np.array([3,1,0,2]))
        assert not clps.check_valid_ordering(), "invalid case 2"
        return

    def test__ChainedLagrangePolySolver__at_x1(self):

        # a 4-d case 2
        x1 = [1.0,4.2,7.3,1.0]
        x2 = [15.0,4.5,7.2,5.0]
        x3 = [7.5,1.0,1.1,3.0]
        x4 = [3.0,2.3,2.7,4.0]
        x5 = [2.0,0.29,3.05,12.0]
        x6 = [10.0,3.2,4.8,3.3]
        xs = np.array([x1,x2,x3,x4,x5,x6])

        clps = chained_poly_interpolation.ChainedLagrangePolySolver(xs)
        clps.set_axis_order_of_interpolation(np.array([0,1,2,3]))
        clps.formulate()

        q = clps.points[:,0]
        for (i,q_) in enumerate(q):
            p = clps.at_x1(q_)
            """
            print("point")
            print(p)
            print("actual")
            print(clps.points[i])
            """
            assert chained_poly_interpolation.equal_iterables(p,clps.points[i])
        return

if __name__ == '__main__':
    unittest.main()
