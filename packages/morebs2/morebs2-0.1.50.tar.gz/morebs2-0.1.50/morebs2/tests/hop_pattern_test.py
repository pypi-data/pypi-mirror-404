from morebs2 import hop_pattern
import unittest

# TODO: check reversing bounds [1,0] <-> [0,1]
'''
python -m morebs2.tests.hop_pattern_test  
'''
class TestHopPatternClass(unittest.TestCase):

    def test__HopPattern__calculate_hop_directions(self):

        # tests hop_one method by calling it
        # for a cycle

        # case 0:
        q = hop_pattern.HopPattern(23.0,23.0,97.0)
        q.calculate_hop_directions()
        assert q.hopDirection.shape == (2,)
        assert abs(q.hopDirection[0] - (97 - 23.00) / 5) <= 10 ** -5
        ##return -1

        # case 1:
        q = hop_pattern.HopPattern(97.0,23.0,97.0)
        q.calculate_hop_directions()
        assert abs(q.hopDirection[0] + (97 - 23.00) / 5) <= 10 ** -5, "incorrect hop directions {}".format(q.hopDirection)
        assert q.hopDirection[0] < 0.0, "incorrect hop direction"

        # case 2:
        q = hop_pattern.HopPattern(50.0,23.0,97.0)
        q.calculate_hop_directions()
        assert abs(q.hopDirection[0] - (97 - 23.00) / 5) <= 10 ** -5


    def test__HopPattern__hop_one(self):

        q = hop_pattern.HopPattern(50.0,23.0,97.0, DIR = 0.2)
        q.calculate_hop_directions()

        assert not q.did_cycle(), "invalid cycle register"

        c = 0
        for i in range(30):
            next(q)
            c += 1

            if (c - 1) % 5 == 0 and c > 1:
                assert q.did_cycle()
            else:
                assert not q.did_cycle()
        return

    def test__HopPattern__hop_one_2(self):
        hop_pattern.HopPattern.DEF_INCREMENT_RATIO = 0.2
        q = hop_pattern.HopPattern(23.0,23.0,97.0)
        q.calculate_hop_directions()

        c = 0
        while not q.did_cycle():
            q2 = next(q)
            c += 1
        assert c == 6, "cycle is incorrect length"

    """
    Runs HopPattern on the following range:
    [0,1]
    """
    def test__HopPattern__hop_one_4(self):
        q = hop_pattern.HopPattern(1.0,0.0,1.0, DIR = 0.5)
        q.calculate_hop_directions()
        c = 0
        x = [1.0, 0.5]

        for i in range(10):
            assert next(q) == x[c % 2], "incorrect "
            c += 1
        return

    def test__HopPattern__hop_one_5(self):
        q = hop_pattern.HopPattern(0.0,0.0,1.0, DIR = round(1/3,10))
        q.calculate_hop_directions()
        next(q)
        c = 1
        for i in range(10):
            #print(next(q))
            next(q)
            c += 1

            if c % 3 == 0:
                assert q.did_cycle()
            else:
                assert not q.did_cycle()

            c += 1

    ### HERE: do some tests on non-endpoint startpoint,
    ###       transfer those tests over to
    def test__HopPattern__hop_one_6(self):
        q = hop_pattern.HopPattern(50.0, 23.0, 97.0, DIR = round(1/3,10))
        q.calculate_hop_directions()

        c = 0
        next(q)
        while c < 100:
            next(q)
            c += 1
            if c % 3 == 0: assert q.did_cycle(), "q is supposed to cycle."
        return

    """
    """
    def test__HopPattern__modulo_hop(self):

        assert hop_pattern.HopPattern.modulo_hop(0.0, 0.0, [0.0,1.0], 0) == 0.0
        assert hop_pattern.HopPattern.modulo_hop(0.0, 0.0, [0.0,1.0], 1) == 1.0

        assert hop_pattern.HopPattern.modulo_hop(0.0, -0.5, [0.0,1.0], 0) == 0.5

        assert hop_pattern.HopPattern.modulo_hop(0.5, 0.5, [0.0,1.0], 1) == 1.0
        assert hop_pattern.HopPattern.modulo_hop(0.5, 0.5, [0.0,1.0], 0) == 0.0

    # TODO: add more cases
    def test__HopPattern__cycle_check(self):

        # case 1
        q = hop_pattern.HopPattern(1.0,0.0,1.0, DIR = 0.5)
        q.calculate_hop_directions()

        q2 = next(q)
        assert q2 == 1.0 and not q.cycle_check()

        q2 = next(q)
        assert q2 == 0.5 and not q.cycle_check()

        q2 = next(q)
        assert q2 == 1.0 and q.cycle_check()

        # case 2
        q = hop_pattern.HopPattern(0.0,0.0,1.0, DIR = 0.5)
        q.calculate_hop_directions()

        q2 = next(q)
        assert q2 == 0.0 and not q.cycle_check()

        q2 = next(q)
        assert q2 == 0.5 and not q.cycle_check()

        q2 = next(q)
        assert q2 == 0.0 and q.cycle_check()

    def test__HopPattern__rev__next__(self):
        # case 1
        q = hop_pattern.HopPattern(0.0,0.0,1.0, DIR = 0.5)
        x = [0.5, 1.0]
        next(q)

        for i in range(10):
            q2 = q.rev__next__()
            i = i % 2
            assert q2 == x[i]

        # case 2
        q = hop_pattern.HopPattern(1.0,0.0,1.0, DIR = 0.5)
        q.calculate_hop_directions()
        x = [0.5, 0.0]
        next(q)
        for i in range(10):
            q2 = q.rev__next__()
            i = i % 2
            assert q2 == x[i]

        # case 3
        q = hop_pattern.HopPattern(1.0,0.0,1.0, DIR = round(1/3,10))
        q.calculate_hop_directions()
        x = [1.0, round(1/3,5), round(1/3,5) * 2]
        for i in range(10):
            q2 = q.rev__next__()
            i = i % 3
            assert q2 - x[i] < 10 ** -5, "wrong"
        return

def test__HopPattern__rev__next__2():
    q = HopPattern(0.5,0.0,1.0,DIR = round(1/3,10))
    # get hop info
    q.rev__next__()
    q.rev__next__()
    assert not q.did_cycle()
    q.rev__next__()
    q.rev__next__()
    assert q.did_cycle()

def test__HopPattern__rev__next__3():
    q = HopPattern(0.5,1.0,0.0,DIR = round(1/3,10))
    # get hop info
    for i in range(10):
        print("Q ", q.rev__next__())

    return -1

    q.rev__next__()
    q.rev__next__()
    assert not q.did_cycle()
    q.rev__next__()
    q.rev__next__()
    assert q.did_cycle()

if __name__ == '__main__':
    unittest.main()
