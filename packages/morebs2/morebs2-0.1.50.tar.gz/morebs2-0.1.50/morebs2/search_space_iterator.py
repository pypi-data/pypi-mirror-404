from .hop_pattern import *
from .measures import *
from copy import deepcopy


class SearchSpaceIterator:
    """
    iterator operates in a sequential/linear manner over an n-dimensional
    space with an m partition on each space. For a bounds with `n by m` specifications,
    outputs `n x m - 1` unique points in a forward (start is minumum bound point) or 
    backwards order (start is maximum bound point) 

    :param bounds: target bounds
    :type bounds: proper bounds, `m x 2`
    :param startPoint: initial point
    :type startPoint: vector, m-sized
    :param columnOrder: vector<column indices>, first is left head
    :type columnOrder: vector<int>
    :param SSIHop: hop over total distance ratio for each increment
    :type SSIHop: int
    :param cycleOn: keep going after cycle?
    :type cycleOn: bool
    :param cycleIs: cycle is maximum of bounds?
    :type cycleIs: bool
    """

    def __init__(self,bounds, startPoint, columnOrder, SSIHop = 7,cycleOn = False, cycleIs = 0):
        assert is_proper_bounds_vector(bounds), "invalid bounds"
        assert is_vector(startPoint), "invalid start point"
        assert cycleIs in [0,1], "cycle-is is wrong"

        # TODO: check column order
        self.bounds = bounds
        self.startPoint = startPoint
        self.referencePoint = np.copy(self.startPoint)
        self.cycleIs = cycleIs# 0 for left end, 1 for right end

        self.startPointContext = self.analyze_startpoint_in_bounds()
        self.columnOrder = columnOrder # alternative: could do column weights
        self.columnOrderPtr = 0  # TODO: delete, unused.
        self.hopPatterns = []

        # use the below variable if the cycle is on.
        self.cycleOn = cycleOn
        self.ssiHop = SSIHop

        self.set_hop_pattern_for_columns(self.ssiHop)

        # adjust hop pattern heads based on `cycleIs`
        self.cycleIs = cycleIs# 0 for left end, 1 for right end
        self.adjust_hop_pattern_heads()

        self.calculate_endpoint()
        self.cache = np.copy(self.startPoint)
        self.initialized = False
        return

    def de_value(self):
        return np.copy(self.referencePoint)

    def de_bounds(self):
        return np.copy(self.bounds)

    def de_start(self):
        return np.copy(self.startPoint)

    def de_end(self):
        return np.copy(self.endpoint)

    def proper_endpoint(self):
        q = []
        for (i,hp) in enumerate(self.hopPatterns):
            # calculate head
            h_ = hp.head_()
            if abs(h_ - hp.bounds[0]) < 10 ** -4:
                q.append(hp.bounds[1])
            elif abs(h_ - hp.bounds[1]) < 10 ** -4:
                q.append(hp.bounds[0])
            else:
                # make endpoint startPoint - (hopDir * 10 ** -4)
                x = 1.0 if hp.hopDirection[0] > 0 else -1.1
                q_ = self.startPoint[i] + (x * 5 * 10 ** 1)
                q.append(q_)
        return np.array(q)

    def close_cycle(self):
        """
        outputs the element after the last, and sets !terminate
        """
        pe = self.proper_endpoint()

        # turn off
        self.referencePoint = np.copy(self.endpoint)
        self.cycleOn = False

        return pe

    def adjust_hop_pattern_heads(self):
        '''
        adjusts the heads of hop pattern instances to match
        `cycleIs`
        '''

        for (i,hp) in enumerate(self.hopPatterns):
            if hp.value == self.bounds[i,0] or hp.value == self.bounds[i,1]:
                hp.head = self.bounds[i,self.cycleIs]
                hp.headIndex = self.cycleIs
            else:
                pass
        return

    def analyze_startpoint_in_bounds(self):
        """
        determines ratio of each element in startpoint with respect to
        their column size and hop partition.

        :return: vector of floats v in [0,1]
        """

        # TODO: assert start point in bounds
        v = np.asarray(self.bounds[:,1] - self.bounds[:,0], dtype=float)
        q = np.asarray(self.startPoint - self.bounds[:,0], dtype = float)
        try:
            return q / v
        except:
            return np.zeros((v.shape[0],))

    def calculate_endpoint(self):
        '''
        method called before iteration to obtain iterating endpoint
        '''

        # decrement each one
        self.endpoint = np.empty((len(self.columnOrder),))
        for (i,x) in enumerate(self.hopPatterns):
            q = deepcopy(x)
            q.rev__next__()
            self.endpoint[i] = q.rev__next__()

            # round the value to head
            q = 1

            otherV = self.bounds[i,q]
            if abs(self.endpoint[i] - otherV) < 10 ** -4.7:
                self.endpoint[i] = self.bounds[i,(q + 1) % 2]

        return np.round(self.endpoint,5)

    def set_hop_pattern_for_columns(self, dividor):
        '''
        declares n :class:`HopPattern` instances each with partition `dividor`. 

        :param dividor: partition value for each :class:`HopPattern` instance. 
        :type dividor: int
        '''
        stat = is_vector(dividor) 
        qdiv = None
        if not stat:
            assert type(dividor) in {int,np.int32,float,np.float64}
            qdiv = np.ones((self.bounds.shape[0],)) * dividor 
        else: 
            assert len(dividor) == self.bounds.shape[0]
            qdiv = dividor
        
        for (i,c) in enumerate(self.startPoint):
            diver = float(qdiv[i])
            hp = HopPattern(c, self.bounds[i,0], self.bounds[i,1], DIR = round(diver ** -1, 10))
            self.hopPatterns.append(hp)

    ###------------------------------------------------------------

    def finished(self):
        '''
        determines if iterator is finished
        
        :rtype: bool
        '''

        return not self.cycleOn and self.reached_end()

    def __next__(self):
        q = self.reached_end()
        if not self.cycleOn and q:
            #print("done with iteration")
            return np.copy(self.referencePoint)

        # check if reached end
        self.cache = np.copy(self.referencePoint)
        if q:
            self.referencePoint = np.copy(self.bounds[:,self.cycleIs])
            copi = np.copy(self.referencePoint)
        else:
            # initialize here
            copi = self.inc1()
            self.referencePoint = copi
        return np.copy(copi)

    def rev__next__(self):
        self.referencePoint = np.copy(self.rinc1())
        return np.copy(self.referencePoint)

    def rinc1(self):

        # inishiaadoe
        q = self.initiado()

        if type(q) != type(None):
            return q

        self.cache = np.empty((self.startPoint.shape[0],))

        # increment the first hop pattern
        index = len(self.columnOrder) - 1

        x = self.hopPatterns[self.columnOrder[index]].rev__next__()
        self.cache[self.columnOrder[index]] = x

        # carry-over
        index = self.carry_over(index, "finite", True)

        # for remaining indices, add value
        for i in range(index):
            self.cache[self.columnOrder[i]] = self.hopPatterns[self.columnOrder[i]].value_at()
        return np.round(self.cache, 5)

    def initiado(self):

        if not self.initialized:
            self.initialized = not self.initialized
            for i in range(len(self.hopPatterns)):
                next(self.hopPatterns[i])
            return np.copy(self.referencePoint)
        return None

    def inc1(self):
        q = self.initiado()
        if type(q) != type(None):
            return q

        # TODO: make this reference point instead
        self.cache = np.empty((self.startPoint.shape[0],))

        # increment the first hop pattern
        index = 0
        x = next(self.hopPatterns[self.columnOrder[index]])
        self.cache[self.columnOrder[index]] = x

        # carry-over
        index = self.carry_over(index, "finite")
        diff = len(self.columnOrder) - index # TODO: error here???
        for i in range(diff):
            columnOrderIndex = index + i
            columnIndex = self.columnOrder[columnOrderIndex]
            self.cache[columnIndex] = self.hopPatterns[columnIndex].value_at()
        return np.round(self.cache, 5)

    # TODO: run tests on `carryOverType`

    # TODO: rev is actually inverse
    def carry_over(self, lastIndex, carryOverType = "finite", rev = False):
        """
        method used to carry over column values to affect the next column in the
        ordering `self.columnOrder`.

        :param lastIndex: index that corresponds to column in `self.columnOrdering` where
                        the most recent delta to `self.referencePoint` occurred.
        :type lastIndex: int
        :param carryOverType: specifies if carry-over operation can cycle back to the first element in column ordering.
        :type carryOverType: str, `infinite` or `finite`.
        :param rev: carry-over in column-ordering is in decreasing order? 
        :type rev: bool
        """

        assert carryOverType in ["infinite", "finite"], "carry-over type"

        ## TODO: below two ## are for inverse mode
        if not rev:
            lf = lambda li: True if li >= len(self.columnOrder) else False
            increment = 1
        else:
            lf = lambda li: True if li < 0 else False
            increment = -1

        # check for column carry-over
        while True:
            if carryOverType == "finite" and lf(lastIndex):
                break

            modIndex = lastIndex % len(self.columnOrder)

            # check index
            if self.hopPatterns[self.columnOrder[modIndex]].did_cycle():
                modIndex2 = (modIndex + increment) % len(self.columnOrder)

                if rev:
                    x = self.hopPatterns[self.columnOrder[modIndex2]].rev__next__()
                else:
                    x = next(self.hopPatterns[self.columnOrder[modIndex2]])
                self.cache[self.columnOrder[modIndex2]] = x
            else:
                break
            lastIndex += increment

        return lastIndex

    def reached_end(self):
        '''
        determines if reference point has reached endpoint
        '''
        return equal_iterables(self.referencePoint,self.endpoint,2)

    def set_value(self,v):
        v = self.round_correct_point_in_bounds(v)
        # case: point not in bounds
        if type(v) == type(None):
            return

        self.referencePoint = v
        for (i,hp) in enumerate(self.hopPatterns):
            hp.set_value(self.referencePoint[i])

    def round_correct_point_in_bounds(self,p,roundDepth = 4):
        assert is_vector(p), "invalid vector"
        p_ = np.copy(p)
        for i in range(p_.shape[0]):
            if not (p_[i] <= self.bounds[i,1] and p_[i] >= self.bounds[i,0]):
                if abs(p_[i] - self.bounds[i,1] <= 10 ** -4):
                    p_[i] = self.bounds[i,1]
                elif abs(p_[i] - self.bounds[i,0] <= 10 ** -4):
                    p_[i] = self.bounds[i,0]
                else:
                    return None
        return p_

"""
used for improper bounds
"""
class SkewedSearchSpaceIterator(SearchSpaceIterator):
    """
    :class:`SearchSpaceIterator`-like class used to iterate over improper bounds.

    :param bounds: target bounds
    :type bounds: improper bounds, `m x 2`
    :param parentBounds: reference bounds for `self.bounds`
    :type parentBounds: proper bounds, `m x 2`
    :param startPoint: initial point
    :type startPoint: vector, m-sized
    :param columnOrder: vector<column indices>, first is left head
    :type columnOrder: vector<int>
    :param SSIHop: hop over total distance ratio for each increment
    :type SSIHop: int
    :param cycleOn: keep going after cycle?
    :type cycleOn: bool
    :param cycleIs: cycle is maximum of bounds?
    :type cycleIs: bool
    """


    def __init__(self, bounds, parentBounds,startPoint,columnOrder = None,SSIHop = 7,cycleOn = False,cycleIs = 0):
        assert not is_proper_bounds_vector(bounds), "[1] invalid bounds"
        assert is_proper_bounds_vector(parentBounds), "[2] invalid bounds"
        assert point_in_bounds(parentBounds,bounds[:,0]), "[0] invalid bound {} for {}".format(bounds[:,0],parentBounds)
        assert point_in_bounds(parentBounds,bounds[:,1]), "[1] invalid bound {} for {}".format(bounds[:,1],parentBounds)

        if type(columnOrder) == type(None):
            columnOrder = np.arange(bounds.shape[0])[::-1]

        self.referenceBounds = bounds
        self.parentBounds = parentBounds
        self.skew = self.referenceBounds[:,0] - self.parentBounds[:,0]

        # caution: no error-check
        self.sp2 = np.copy(self.referenceBounds[:,0]) if type(startPoint)\
            == type(None) else startPoint
        self.ref2 = np.copy(self.referenceBounds[:,0])

        pd = point_difference_of_improper_bounds(self.referenceBounds, self.parentBounds)
        self.iBounds = np.vstack((self.parentBounds[:,0],self.parentBounds[:,0] + pd)).T
        self.set_skew()
        sp = np.array([self.iBounds[i,self.skewEdgeIndices[i]] for i in range(self.iBounds.shape[0])])

        # declare SSI
        super().__init__(self.iBounds, np.copy(sp), columnOrder, SSIHop,cycleOn, cycleIs)

        # sort reference bounds
        self.e2 = vector_hop_in_bounds(self.endpoint,self.skew,self.parentBounds)
        return

    # TODO: test this
    @staticmethod
    def k_random_points_in_bounds(parentBounds,bounds,k):
        start = parentBounds[:,0]

        s = split_improper_bound(parentBounds,bounds,checkPoints = True)
        d2,d1 = s[1][:,1] - s[0][:,1], s[1][:,0] - s[0][:,0]
        dx = d1 + d2
        sssi = SkewedSearchSpaceIterator(bounds, parentBounds,start,None,3)

        for i in range(k):
            q = random.random() * dx
            r = start + q
            yield sssi.round_value(r)

    def de_value(self):
        return np.copy(self.referencePoint)

    def de_start(self):
        return np.copy(self.sp2)

    def de_bounds(self):
        return np.copy(self.referenceBounds)

    def de_end(self):
        return np.copy(self.e2)

    def set_skew(self):
        """
        sets skew value and its index template;
        Skew value used to calibrate value from .`self.ssi`.
        """

        skew = []
        si = []
        for i in range(self.referenceBounds.shape[0]):
            # forward traversal
            if abs(self.sp2[i] - self.referenceBounds[i,0]) <= 10 ** -5:
                skew.append(self.referenceBounds[i,0] - self.iBounds[i,0])
                si.append(0)
            # backwards traversal
            elif abs(self.sp2[i] - self.referenceBounds[i,1]) <= 10 ** -5:
                skew.append(self.referenceBounds[i,1] - self.iBounds[i,1])
                si.append(1)
            else:
                raise ValueError("cannot initialize start point at non-vertex of space")

        self.skew = np.array(skew)
        self.skewEdgeIndices = np.array(si)

    def round_value(self,v):
        return vector_hop_in_bounds(v,self.skew,self.parentBounds)

    def inverse_round_value(self,v):
        """
        inverse round value in `referenceBounds` to value in `iBounds`
        """

        return vector_hop_in_bounds(v,-self.skew,self.parentBounds)

    def __next__(self):

        if not self.cycleOn and self.reached_end():
            #print("done with iteration")
            return np.copy(self.ref2)

        q = SearchSpaceIterator.__next__(self)
        self.ref2 = self.round_value(q)
        return np.copy(self.ref2)

    def rev__next__(self):
        SearchSpaceIterator.rev__next__(self)
        self.ref2 = self.round_value(self.referencePoint)
        return np.copy(self.ref2)

    def reached_end(self):
        q = equal_iterables(self.ref2,self.e2, 4)
        return q

    def set_value(self,v):
        """
        sets value v as reference point

        :param v: vector, value in `self.referenceBounds`
        """

        assert is_vector(v), "invalid vector"
        self.ref2 = v
        q = self.inverse_round_value(v)
        SearchSpaceIterator.set_value(self,q)
        return

    def de_value(self):
        return np.copy(self.ref2)
