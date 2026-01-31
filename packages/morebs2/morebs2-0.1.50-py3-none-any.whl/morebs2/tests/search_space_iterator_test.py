from .search_space_iterator_test_cases import *
import unittest

'''
python -m morebs2.tests.search_space_iterator_test  
'''

# TODO: write tests on inverted bounds [1,0]
def test__SearchSpaceIterator__set_hop_pattern_fo():
    HopPattern.DEF_INCREMENT_RATIO = 0.5
    ssi = SearchSpaceIterator_case_1()
    ssi.set_hop_pattern_for_columns()

    for (i,x) in enumerate(ssi.hopPatterns):
        print("hop for ", i)
        print(x.hopDirection)
        print()

class TestSearchSpaceIteratorClass(unittest.TestCase):

    def test__SearchSpaceIterator__next__1(self):

        ssi = SearchSpaceIterator_case_1()

        """
        make sure cycle of correct length
        """
        c = 0
        while True:
            c += 1
            next(ssi)
            #print(next(ssi))
            if ssi.reached_end(): break
        assert c == 8, "c is wrong"

    """
    write data out to file
    `message_data/search_space/ssi_case_2.txt`
    """
    def test__SearchSpaceIterator__next__2(self):

        # case 2
        ssi2 = SearchSpaceIterator_case_2()
        ssi2.cycleOn = True

        # check correct endpoint
        ##print("endpoint: ", ssi2.endpoint)
        assert search_space_iterator.equal_iterables(ssi2.endpoint,np.array([0.8,0.8,0.8])), "invalid endpoint"

        # check correct number of elements in cycle
        # loop entirely
        c = 0
        while True:
            c += 1
            next(ssi2)
            #print(next(ssi2))
            if ssi2.reached_end(): break
        assert c == 125, "incorrect number of elements {}".format(c)

    def test__SearchSpaceIterator__next__3(self):

        ssi3 = SearchSpaceIterator_case_3()

        c = 0
        while c < 1000:
            c += 1
            next(ssi3)
            #print(next(ssi3))
            if ssi3.reached_end(): break
        assert c == 27, "c turns out to be more wrong than right"
        return

    '''
    '''
    def test__SearchSpaceIterator__next__4(self):
        ssi = SearchSpaceIterator_case_4()
        ssi.cycleIs = 1
        ssi.adjust_hop_pattern_heads()

        # print out hop pattern for each
        cycleLengths = []
        for hp in ssi.hopPatterns:
            s = search_space_iterator.cycle_hop_pattern(hp)
            cycleLengths.append(len(s))

        # all are length 7
        cycleLengths = np.array(cycleLengths)
        assert np.all(cycleLengths == cycleLengths[0])
        return


    def test__SearchSpaceIterator__next__9(self): 
        ssi = SearchSpaceIterator_case_9() 
        ans = {16: np.array([0.,0.,0.,0.,2.,2.]),\
        71: np.array([0.,0.,0.,2.,0.,1.]),\
        702: np.array([0.,0.,3.,2.,0.,2.])}

        i = 0 
        while not ssi.reached_end(): 
            q_ = next(ssi) 
            if i in ans: 
                q = ans[i] 
                assert matrix_methods.equal_iterables(q,q_)
            
            i += 1
        refpoint = np.array([1.,2.,3.,5.,4.,6.])
        assert matrix_methods.equal_iterables(ssi.referencePoint,refpoint)
        assert i == 2 * 3 * 4 * 5 * 6 * 7 

#-------------------------------------------------------------

    '''
    checks that the endpoint is correct for SSI case 6.
    '''
    def test__SearchSpaceIterator__CASE_6_endpoint(self):
        ssi = SearchSpaceIterator_case_6()
        sol = np.array([0.,9.,8.,3.,2.5])
        assert search_space_iterator.equal_iterables(ssi.endpoint,sol), "incorrect endpoint for case 6\ngot {}\nwant {}".format(ssi.endpoint,sol)

    # TODO: look into rev__next__
    ###
    def test__SearchSpaceIterator__rev__next__(self):
        ssi = SearchSpaceIterator_case_6()
        ssi.cycleOn = True
        ssi.cycleIs = 0

        q = [np.copy(ssi.referencePoint)]
        c = 0
        while not ssi.reached_end():
            ssi.rev__next__()
            q.append(np.copy(ssi.referencePoint))
            c += 1

            if c == 100:
                break
        assert c == 32, "[0] incorrect number of elements for search space {}".format(c)

        q = np.unique(q,axis = 0)
        assert q.shape[0] == 32 and q.shape[1] == 5, "[0] incorrect shape of q"

        # forward loop
        c = 1
        q = [np.copy(next(ssi))]
        while not ssi.reached_end():
            q.append(np.copy(next(ssi)))

            ##print("V ", next(ssi), "\tF ", ssi.reached_end())
            c += 1
            if c == 100:
                break

        assert c == 32, "[1] incorrect number of elements for search space"
        q = np.unique(q,axis = 0)
        assert q.shape[0] == 32 and q.shape[1] == 5, "[0] incorrect shape of q"

    # FAILS:
    def test__SearchSpaceIterator__rev__next__2(self):
        stat = True

        try:
            ssi = SearchSpaceIterator_case_7()
            stat = not stat
        except:
            pass

        assert stat, "invalid bounds for SSI 7"
        return


    def test__SkewedSearchSpaceIterator__case_1(self):
        sssi = SkewedSearchSpaceIterator_case_1()
        #return
        # check for correct number of elements
        c = 0
        while not sssi.reached_end():
            ##print("C ",c, " : ", next(sssi))
            next(sssi)
            c += 1
        assert c == 243, "incorrect number of elements in cycle {}".format(c)
        return

    def test__SkewedSearchSpaceIterator__case_1__set_point(self):

        sssi = SkewedSearchSpaceIterator_case_1()
        ps = []
        for i in range(10):
            q = next(sssi)
            ##print("Q: ",q)
            ps.append(q)

        sp = np.copy(ps[0])

        # case 1: set point at [3]
        sssi.set_value(sp)
        for i in range(3):
            q = next(sssi)
            assert search_space_iterator.equal_iterables(q,ps[1+i])

        # case 2:
        sssi.set_value(ps[4])
        for i in range(3):
            q = next(sssi)
            assert search_space_iterator.equal_iterables(q,ps[5+i])

    def test__SkewedSearchSpaceIterator__case_3(self):
        sssi = SkewedSearchSpaceIterator_case_3()

        # test for correct hop directions
        q = [0,1,1,0,0]
        for (i,hp) in enumerate(sssi.hopPatterns):
            if q[i]:
                assert hp.hopDirection[0] < 0, "[0] incorrect hop direction for {}".format(i)
            else:
                assert hp.hopDirection[0] > 0, "[1] incorrect hop direction for {}".format(i)

        # iterate for 243 times
        c = 0
        q2 = []
        while not sssi.reached_end():
            ##print(next(sssi))
            q3 = next(sssi)
            q2.append(q3)
            c += 1
        assert c == 243, "incorrect number of elements in cycle"

        q2 = np.array(q2)
        g = np.unique(q2,axis = 1).shape[0]
        assert g == 243, "got {} want {}".format(g,242)

        return

    def test__SearchSpaceIterator__case_1__set_point(self):
        ssi = SearchSpaceIterator_case_1()

        q = []
        for i in range(6):
            x = next(ssi)
            q.append(x)
        s = q[2]
        ssi.set_value(s)

        for i in range(3):
            q_ = next(ssi)
            assert search_space_iterator.equal_iterables(q_,q[3 + i])
        return -1

    def test__SkewedSearchSpaceIterator__case_2(self):
        sssi = SkewedSearchSpaceIterator_case_2()

        # iterate for 243 times
        c = 0
        ##q =
        q = []
        while not sssi.reached_end() and c < 1000:
            q.append(next(sssi))
            c += 1
        assert c == 243, "incorrect number of elements in cycle"
        q = np.array(q)
        assert np.unique(q,axis = 0).shape[0] == q.shape[0], "#1 incorrect number of elements in cycle"

"""
def test__SkewedSearchSpaceIterator__case_x():
    sssi = SkewedSearchSpaceIterator_case_1()

    print("SSSI ")
    print(sssi.iBounds)
    print("EP ")
    print(sssi.ref2)
    print()
    #return -1
    ##return -1

    ##return
    # check for correct number of elements
    c = 0
    ##while not sssi.reached_end():
    for i in range(245):
        print("C ",c, " : ", next(sssi), " end? ", sssi.reached_end())
        ##next(sssi)
        c += 1
    ##assert c == 243, "incorrect number of elements in cycle {}".format(c)

    print("REFBOUNDS")
    print(sssi.referenceBounds)
    print(sssi.ref2)
    print(sssi.endpoint)
    print(sssi.skew)
    return

    # check for correct end
    q = next(sssi)
    assert equal_iterables(q,sssi.referenceBounds[:,1])
    return
"""

################################### TODO: incomplete

# test used for the method right after
def test_x():

    h = HopPattern(0.75, 0.0, 1.0,DIR = 0.5)

    h.headIndex = 1.0
    h.head = 1.0

    print("HOP DIR")
    print(h.hopDirection)
    print()

    for i in range(10):
        print(i, " ", next(h), " | ", h.did_cycle())


def test__SearchSpaceIterator___head_is_correct___():
    # set up the SSI

    # case: head is 0
    ssi = SearchSpaceIterator_case_8(0)

    # iterate through
    c = 0
    #while c < 32:
    while not ssi.reached_end():
        print("{}: {}".format(c,next(ssi)))
        c += 1

    print("bounds: ", ssi.bounds)
    print("start: ", ssi.startPoint)
    print("last element: ", ssi.close_cycle())
    print("next: ", next(ssi))

    # case: head is 1
    print("-------")
    ssi = SearchSpaceIterator_case_8(1)

    c = 0
    while not ssi.reached_end():
        print("{}: {}".format(c,next(ssi)))
        c += 1
    print("bounds: ", ssi.bounds)
    print("start: ", ssi.startPoint)
    print("last element: ", ssi.close_cycle())
    print("next: ", next(ssi))


    return -1

if __name__ == "__main__":
    unittest.main()
    print()
