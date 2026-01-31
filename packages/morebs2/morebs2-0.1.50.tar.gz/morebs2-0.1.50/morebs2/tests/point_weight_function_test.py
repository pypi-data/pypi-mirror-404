from morebs2 import point_weight_function
import unittest
import numpy as np

'''
python -m morebs2.tests.point_weight_function_test  
'''
class TestPointWeightFunction(unittest.TestCase):

    '''
    '''
    def test__angle_between_two_points_clockwise(self):

        p = (55.0,65.0)

        # deg 0
        p1 = (56.0,65.0)
        # deg 90
        p2 = (55.0, 66.0)
        # deg 180
        p3 = (54.0, 65.0)
        # deg 270
        p4 = (55.0,64.0)

        assert point_weight_function.angle_between_two_points_clockwise(p,p1) == 0.0, "wrong angle for 0.0"
        assert point_weight_function.angle_between_two_points_clockwise(p,p2) == 90.0, "wrong angle for 00.0"
        assert point_weight_function.angle_between_two_points_clockwise(p,p3) == 180.0, "wrong angle for 180.0"
        assert point_weight_function.angle_between_two_points_clockwise(p,p4) == 270.0, "wrong angle for 270.0"

    '''
    uniform weights
    '''
    def test__similarity_measure__type43___uw_(self):

        bounds = np.array([[-70.0,60],[60,-70.0], [0.0,60], [-30.0,25]])
        weights = np.asarray(np.ones(4),dtype='float')

        # at opposing ends
        v1 = np.copy(bounds[:,0])
        v2 = np.copy(bounds[:,1])
        sm = point_weight_function.similarity_measure__type43(v1,v2, bounds, weights)
        assert sm == 1.0, "invalid 1"

        # test for commutativity
        sm = point_weight_function.similarity_measure__type43(v2,v1, bounds, weights)
        assert sm == 1.0, "invalid 2"

        # at same point: center
        v3 = np.copy(v1)
        v1 = v1 + (v2 - v1) / 2
        v2 = np.copy(v1)
        sm = point_weight_function.similarity_measure__type43(v1,v2,bounds,weights)
        assert sm == 0.0, "invalid 3"

        # at same point: end
        v1 = np.copy(v3)
        v2 = np.copy(v3)
        sm = point_weight_function.similarity_measure__type43(v1,v2,bounds,weights)
        assert sm == 0.0, "invalid 4"

        # at opposing ends +/- 1/2
        v1 = np.copy(bounds[:,0])
        v2 = np.copy(bounds[:,1])
        diff = bounds[:,1] - bounds[:,0]
        v1 += (diff / 4.0)
        v2 -= (diff / 4.0)
        sm = point_weight_function.similarity_measure__type43(v1,v2,bounds,weights)
        assert sm == 0.5, "invalid 5"

    # TODO: more testing needed.
    def test__similarity_measure__type43___nuw_(self):

        #
        bounds = np.array([[-70.0,60],[60,-70.0], [0.0,60], [-30.0,25]])
        weights = np.array([0.5,0.4,0.0, 0.25])

        # at opposing ends
        v1 = np.copy(bounds[:,0])
        v2 = np.copy(bounds[:,1])

        sm = point_weight_function.similarity_measure__type43(v1,v2,bounds,weights)
        weights = np.asarray(np.ones(4),dtype='float')
        sm1 = point_weight_function.similarity_measure__type43(v1,v2,bounds,weights)
        assert sm < sm1, "wrong relation for measure"

    def test__similarity_measure__type44___uw_(self):

        bounds = np.array([[-70.0,60],[60,-70.0], [0.0,60], [-30.0,25]])
        weights = np.asarray(np.ones(8),dtype='float')
        weights = weights.reshape((4,2))
        weights[:,1] = weights[:,1] * -1
        ##print("WEIGHTS ", weights)

        # case : `basically` at left endpoint
        v1 = np.array([-70.0,60,0.5, -30.0])
        v2 = np.copy(bounds[:,1])
        sm = point_weight_function.similarity_measure__type44(v1,v2,bounds,weights)
        ##print("SM ",sm)

        # case: `basically` at right endpoint
        v1 = np.copy(bounds[:,0])
        v2 = np.array([60.0,-69.5,60.0,25.0])
        sm1 = point_weight_function.similarity_measure__type44(v1,v2,bounds,weights)
        ##print("SM ",sm1)
        assert sm1 < sm, "[0] invalid sim. measure"

        sm1_ = point_weight_function.similarity_measure__type43(v1,v2,bounds,weights[:,0])
        assert sm1_ == sm1, "[1] invalid sim. measure"

        ###assert abs(sm1 - 1.0) == abs(sm - 1.0), "[2] incorrect relation"

        # case: v2 is at 1/2 + 1/4
        diff = bounds[:,1] - bounds[:,0]
        v1 = np.copy(bounds[:,0])
        v2 = np.copy(bounds[:,1]) - (diff * 3/8.0)
        sm2 = point_weight_function.similarity_measure__type44(v1,v2,bounds,weights)
        ##print("SM ",sm2)

        # case: v2 is at 1/2
        v2 = np.copy(bounds[:,1]) - (0.5 * diff)
        sm3 = point_weight_function.similarity_measure__type44(v1,v2,bounds,weights)
        ##print("SM ",sm3)
        assert sm2 > sm3, "[2] slant to right"

        # case: switch v1 and v2
        v1_ = np.copy(bounds[:,1])
        v2_ = np.copy(bounds[:,0]) + (0.5 * diff)
        sm3_ = point_weight_function.similarity_measure__type44(v1_,v2_,bounds,weights)
        ##print("@SM ", sm3_)
        sm3__ = point_weight_function.similarity_measure__type44(v2_,v1_,bounds,weights)
        ##print("@SM ",sm3_)
        assert sm3_ == sm3__, "[3] measure must be commutative"

        # case: v2 is at 3/8
        v2 = np.copy(bounds[:,0]) + (3.0/8.0 * diff)
        sm4 = point_weight_function.similarity_measure__type44(v1,v2,bounds,weights)
        ##print("SM ",sm4)
        assert sm3 < sm4

        # case: v2 is at 2^(-17)
        v2 = np.copy(bounds[:,0]) + (1.0/131072.0 * diff)
        sm5 = point_weight_function.similarity_measure__type44(v1,v2,bounds,weights)
        assert sm5 == 0.5, "incorrect sim. measure"

        v1 = np.copy(bounds[:,1])
        v2 = np.copy(bounds[:,1]) - (1.0/131072.0 * diff)
        sm6 = point_weight_function.similarity_measure__type44(v1,v2,bounds,weights)
        assert sm6 == 1.0 + (1.0 - sm5), ""

    def test___equal_matrices(self):
        m = np.arange(16).reshape((4,4))
        n = np.arange(16).reshape((4,4))
        assert point_weight_function.equal_iterables(m,n), "basic equality test failed"

########################### start: some tests on `matrix_methods`

    def test_intersection_of_bounds___1(self):

        # case 1: 1/2 of b2 in b1, b2 on right
        b1 = np.array([[0,40],[-20,59],[-299,-174],[60,112],[-20,65]])

            # make b2 by taking half
        b2 = []
        for i in range(b1.shape[0]):
            diff = (b1[i,1] - b1[i,0]) / 2
            s = b1[i,0] + diff
            e = s + diff
            b2.append([s,e])

        b2 = np.array(b2)
        intersection = point_weight_function.intersection_of_bounds(b1,b2)
        trueIntersection = [[  20.,    40. ],\
                            [  19.5,   59. ],\
                            [-236.5, -174. ],\
                            [  86.,   112. ],\
                            [  22.5,   65. ]]

        assert point_weight_function.equal_iterables(intersection,trueIntersection), "bounds intersection incorrect"

        # case 2: end bound of 1 is startbound of second
        b31 = b1[:,1] + 20.0
        b30 = np.copy(b1[:,1])
        b3 = np.vstack((b30,b31)).T

        intersection = point_weight_function.intersection_of_bounds(b1,b3)
        assert type(intersection) == type(None), "[3] invalid intersection"

        # case 3: no intersection at all
        b40 = np.copy(b3[:,1])
        b41 = b40 + 50.0
        b4 = np.vstack((b40,b41)).T

        intersection = point_weight_function.intersection_of_bounds(b1, b4)
        assert type(intersection) == type(None), "[4] invalid intersection {}".format(intersection)

    def test_intersection_of_bounds___2(self):
        # case 1: b2 in b1, and b1 bounds are not sorted
        b1 = np.array([[40,0],[-20,59],[-174,-299],[60,112],[-20,65]])
        b2 = np.array([[0,10], [10,-10],[-299,-250],[90,110],[10,-15]])
        intersection = point_weight_function.intersection_of_bounds(b1,b2)

        trueIntersection = [[   0.,   10.],\
                            [ -10.,   10.],\
                            [-299., -250.],\
                            [  90.,  110.],\
                            [ -15.,   10.]]
        assert point_weight_function.equal_iterables(intersection,trueIntersection)

    def test_euclidean_point_distance(self):
        p1 = np.array([4,15,20,7])
        p2 = np.array([14,20,21,12])
        q = point_weight_function.euclidean_point_distance(p1,p2)
        assert abs(q - 12.288) < 10 ** -3

if __name__ == '__main__':
    unittest.main()
