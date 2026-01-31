from .ball_comp_components_test_cases import *
import unittest

"""
python -m morebs2.tests.ball_comp_components_test  
"""
class TestBallCompComponents(unittest.TestCase):

    def test__intersection_ratio(self):

        b1,b2 = sample_ball_pair_1()
        ir1,ir2 = ball_comp_components.intersection_ratio(b1,b2)
        assert ir1 == 0.2 and ir2 == 0.25

        # case 2
        b1,b2 = sample_ball_pair_2()
        ir1,ir2 = ball_comp_components.intersection_ratio(b1,b2)
        assert ir1 == 0.0 and ir2 == 1.0

        b1,b2 = sample_ball_pair_3()
        ir1,ir2 = ball_comp_components.intersection_ratio(b1,b2)
        assert ir1 == 0.3 and ir2 == 0.75
        return

    def test__volume_2intersection_estimate(self):
        # case 1
        b1,b2 = sample_ball_pair_1()
        v = ball_comp_components.volume_2intersection_estimate(b1,b2)
        """
        print("ball volumes")
        print(ball_area(b1.radius,4))
        print(ball_area(b2.radius,4))
        print()
        print(intersection_ratio(b1,b2))
        """
        r1,r2 = ball_comp_components.intersection_ratio(b1,b2)
        q = ball_comp_components.ball_area(b2.radius,4) * r2
        assert v <= q

        # case 2
        b1,b2 = sample_ball_pair_2()
        v = ball_comp_components.volume_2intersection_estimate(b1,b2)
        assert v == ball_comp_components.ball_area(b2.radius,4), "incorrect estimation of volume of intersection"

        # case 3
        b1,b2 = sample_ball_pair_3()
        v = ball_comp_components.volume_2intersection_estimate(b1,b2)
        r1,r2 = ball_comp_components.intersection_ratio(b1,b2)
        q = ball_comp_components.ball_area(b2.radius,4) * r2
        assert v < q, "case 4: incorrect estimation"

        # case 4
        b1,b2 = sample_ball_pair_4()
        v = ball_comp_components.volume_2intersection_estimate(b1,b2)
        assert v == 0.0, "case 4: balls do not intersect"

    def test__Ball____add__(self):
        # case 1
        b1,b2 = sample_ball_pair_1()

        c1 = np.array((10.0,10.0,10.0,10.0))
        q1 = np.empty((6,4))
        for i in range(6):
            p = c1 + i * np.array([0.1,-0.3,-0.2,0.1])
            b1.add_element(p)

        c2 = np.array((17.0,10.0,10.0,10.0))
        q2 = np.empty((6,5))
        for i in range(6):
            p = c2 + i * np.array([0.05,-0.03,-0.2,0.01])
            b2.add_element(p)

        b3 = b1 + b2
        for x in b1.data.newData:
            assert ball_comp_components.euclidean_point_distance(b3.center,x) <= b3.radius, "all points of b1 must be in new ball"
        for x in b2.data.newData:
            assert ball_comp_components.euclidean_point_distance(b3.center,x) <= b3.radius, "all points of b2 must be in new ball"
        assert b3.data.newData.shape == (16,4), "invalid new shape"

        # case 2
        b1,b2 = sample_ball_pair_2()
        b3 = b1 + b2
        assert b3 == b1

if __name__ == '__main__':
    unittest.main()