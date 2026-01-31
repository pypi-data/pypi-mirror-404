from .rssi_test_cases import *
import unittest
################################ start tests: relevance zoom, euclidean point distance on 5.0
#

'''
python -m morebs2.tests.rssi_test  
'''
class TestRSSIClass(unittest.TestCase):

    """
    >
    """
    def test__rssi__case1(self):
        print("\n\n\t*** testing case 1\n")
        r = sample_rssi_1(rchl = 1)
        rssi.rssi__display_n_bounds(r, 3)
        return

    """
    <
    """
    def test__rssi__case2(self):
        print("\n\n\t*** testing case 2\n")
        r = sample_rssi_1(rchl = 2)
        rssi.rssi__display_n_bounds(r, 2)
        return

    """
    >= and <=
    """
    def test__rssi__case3(self):
        print("\n\n\t*** testing case 3\n")
        r = sample_rssi_1(rchl = 3)
        rssi.rssi__display_n_bounds(r, 2)
        return

        ################################ end tests: relevance zoom, euclidean point distance on 5.0

        ################################ start tests: png, euclidean point distance on 5.0

    def test__rssi__case4(self):
        print("\n\n\t*** testing case 4\n")

        r = sample_rssi_1(rmMode = "prg")
        rssi.rssi__display_n_bounds(r,1)

        # check relevant points
        '''
        print("relevant points")
        for (i,v) in enumerate(rssi.ri.centerResplat.relevantPointsCache):
            print("{} : {}".format(i,v))
        '''
        assert len(r.ri.centerResplat.relevantPointsCache) == 32, "incorrect number of relevant pts."

        #print("\n\n\tNEZXTING 10\n")
        for i in range(10):
            #print(next(rssi))
            q = next(r)
            assert rssi.point_in_bounds(r.ri.centerResplat.centerBounds,q), "point w/ noise must stay in bounds"

        # display index counter
        print("RPI COUNTER")
        print(r.ri.centerResplat.rpIndexCounter)
        assert len(r.ri.centerResplat.rpIndexCounter) > 0, "center-resplat index counter cannot be empty"
        return

# testing for relevant points
################################ end tests: png, euclidean point distance on 5.0

if __name__ == "__main__":
    unittest.main()
    print()


# NEXT: verbose mode
