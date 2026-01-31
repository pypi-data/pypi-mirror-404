from .rssi_components import *
# use for adding noise
from .numerical_generator import *
from copy import deepcopy
#: default range of relative randomness to add to a point in a relevant bound; used for mode `prg`
DEFAULT_RSSI__CR__NOISE_ADDER = np.array([[0.01,0.15]])

class ResplattingSearchSpaceIterator:
    """:class:`ResplattingSearchSpaceIterator` is a data-structure
    that relies on :class:`SearchSpaceIterator>. There are two modes for this class when it resplats on
    the original bounds:
    - "relevance zoom": requires an RChainHead to determine relevance of
    each point
    - "prg": pseudo-random generator of points in relevant bounds

    At timestamp 0, there is one relevant bound, the `bounds` parameter. 
    :class:`ResplattingSearchSpaceIterator` iterates through each bounds it considers
    relevant. When this class iterates through a bound and collects relevant points,
    a relevant sub-bound is one with a minumum relevant point and maximum relevant point
    such that the value preceding (if forward iteration) or succeeding (if backward iteration)
    the minumum relevant point is not relevant and the value succeeding (if forward iteration)
    or preceding (if backward iteration) the maximum relevant point is not relevant. 

    There is a special case that :class:`ResplattingSearchSpaceIterator` considers a sub-bound, when 
    it registers a relevant point in a bound, but the next point is not relevant, then the relevant sub-bound
    is one consisting of the relevant point and the midpoint between that and the next point.

    A generalization of the behavior of :class:`ResplattingSearchSpaceIterator` is that it narrows
    down the relevant space in an initial bound using the :class:`RChainHead` relevance function,
    and the points it generates can be exact (if "rezoom") or pseudo-random (if "prg").

    :class:`ResplattingSearchSpaceIterator` uses an :class:`RChainHead` that updates itself
    after every time it finishes iterating through a relevant bounds.The arguments it passes to
    the :class:`RChainHead` instance are: 
        
        [`self.bounds`, current bound, ssiHop] + list(`additionalUpdateArgs`)

    :param bounds: all generated points lie in this matrix
    :type bounds: np.ndarray, n x 2 matrix
    :param startPoint: n-point
    :type startPoint: np.ndarray
    :param columnOrder: order by which the columns of the reference value carry over values.
    :type columnOrder: iterable
    :param SSIHop: partition for each column of bounds
    :type SSIHop: int
    :param resplattingMode: determines how the data structure will generate new values after iterating through
                            the previous bounds and collecting relevant bounds.
    :type resplattingMode: ("relevance zoom"|"prg",:class:`RChainHead`)
    :param additionalUpdateArgs: additional arguments used to update :class:`RChainHead` when updating
        :class:`ResplattingInstructor` 
    :type additionalUpdateArgs: tuple
    """

    def __init__(self,bounds, startPoint, columnOrder = None, SSIHop = 7,\
        resplattingMode = ("relevance zoom",None), additionalUpdateArgs = (),verbose:bool=False):
        assert is_proper_bounds_vector(bounds), "bounds "
        assert is_vector(startPoint), "invalid start point"
        assert resplattingMode[0] in {"relevance zoom", "prg"}
        assert type(resplattingMode[1]) == RChainHead, "invalid argument for resplatting mode"

        self.bounds = bounds
        self.startPoint = startPoint
        self.referencePoint = np.copy(self.startPoint)
        self.columnOrder = columnOrder
        self.SSIHop = SSIHop
        self.rm = resplattingMode

        self.iteratedOnce = False # if SSI iterated over bounds once
        self.iterateIt = False
        self.terminated = False
        #: sequence of all sub-bounds in `self.bounds` that data structure has iterated over by :class:`SearchSpaceIterator``. 
        self.rangeHistory = [np.copy(self.bounds)]

        self.declare_new_ssi(np.copy(self.bounds), np.copy(self.startPoint))

        self.ri = None
        assert type(additionalUpdateArgs) == tuple, "invalid additionalUpdateArgs"
        self.aua = additionalUpdateArgs
        self.verbose = verbose 
        self.update_resplatting_instructor()
        return

    @staticmethod
    def iterate_one_bound(rssi):

        if rssi.terminated:
            yield None
            return

        if not rssi.iteratedOnce:
            while not rssi.iteratedOnce:
                yield next(rssi)
            yield rssi.ssi.close_cycle()
            rssi.iterateIt = False

        else:
            rssi.ssi.referencePoint = rssi.ssi.de_start()

            while not rssi.iterateIt:
                yield next(rssi)
            yield rssi.ssi.close_cycle()
            rssi.iterateIt = False

    @staticmethod
    def iterate_one_batch(rssi, batchSize):
        """
        outputs points corresponding to a relevant bound

        use only with `relevance zoom`
        """
        if rssi.terminated:
            yield None
            return

        if not rssi.iteratedOnce:
            while not rssi.iteratedOnce and batchSize > 0:
                qn = next(rssi)
                if not rssi.iterateIt: yield qn
                batchSize -= 1
            if rssi.iteratedOnce:
                yield rssi.ssi.close_cycle()
                rssi.ssi.referencePoint = rssi.ssi.de_start()

                batchSize -= 1
            rssi.iterateIt = False

        while not rssi.iterateIt and batchSize > 0:
            qn = next(rssi)
            if not rssi.iterateIt: yield qn
            batchSize -= 1

        # case: bound ends before batch size output
        if rssi.iterateIt and batchSize > 0:
            yield rssi.ssi.close_cycle()
            rssi.ssi.referencePoint = rssi.ssi.de_start()

            batchSize -= 1
            rssi.iterateIt = False
            ###print("\tremainder: ", batchSize)
            return ResplattingSearchSpaceIterator.iterate_one_batch(rssi,batchSize)

    def declare_new_ssi(self,bounds, startPoint):
        '''
        Declares either a :class:`SearchSpaceIterator` or :class:`SkewedSearchSpaceIterator`
        instance for the given bounds.

        :param bounds:
        :type bounds: 
        :param startPoint:
        :type startPoint:  
        '''

        # if no specified order, default is descending
        if type(self.columnOrder) == type(None):
            self.columnOrder =ResplattingSearchSpaceIterator.column_order(bounds.shape[0],"descending")

        if is_proper_bounds_vector(bounds):
            self.ssi = SearchSpaceIterator(bounds, startPoint, self.columnOrder, self.SSIHop,cycleOn = True)
        else: # make SkewedSearchSpaceIterator
            self.ssi = SkewedSearchSpaceIterator(bounds,self.bounds,startPoint,self.columnOrder,self.SSIHop,cycleOn = True)

    def update_resplatting_instructor(self,nbs = None):
        """
        Updates :class:`ResplattingInstructor` `self.ri`. If `self.ri` is None,
        then instantiates a new :class:`ResplattingInstructor` based on the mode `self.rm\\[0\\]`.

        :param nbs: new bounds vector
        :return nbs: np.ndarray
        """

        if type(self.ri) == type(None):
            if self.rm[0] == "relevance zoom":
                rz = RZoom(self.rm[1])
                q = (rz,None)
            else:
                cs = CenterResplat(np.copy(self.bounds), self.rm[1], DEFAULT_RSSI__CR__NOISE_ADDER)
                q = (None,cs)

            self.ri = ResplattingInstructor(q[0],q[1])
            return False

        if self.rm[0] == "relevance zoom":

            # draw from .cache
            if type(nbs) == type(None):
                nb = self.save_rzoom_bounds_info()

                if self.verbose: 
                    print("NEXT RANGE:")
                    print(nb)

                if type(nb) == type(None): return True
                sp = np.copy(nb[:,0])
            else:# use arg<nb>
                nb = nbs[0]
                sp = nbs[1]

            if self.check_duplicate_range(nb):
                return True

            self.declare_new_ssi(nb,sp)
            # log point into range history
            self.rangeHistory.append(nb)

            # update rch here
            s = [self.bounds, nb, self.SSIHop] + list(deepcopy(self.aua))
            self.rm[1].load_update_vars(s)
            self.rm[1].update_rch()
            self.ri.rzoom = RZoom(self.rm[1])

        # TODO: optional, add update func. for png here
        return False

    def update_vars_for_rch(self): 
        return [np.copy(self.bounds),self.ssi.de_bounds(),deepcopy(self.SSIHop)] + list(deepcopy(self.aua))

    def check_duplicate_range(self,d):
        '''
        checks if range `d` is already present in `self.rangeHistory`.

        :rtype: bool
        '''
        for d_ in self.rangeHistory:
            if equal_iterables(d_,d): return True
        return False

    def save_rzoom_bounds_info(self):
        '''
        stores activation ranges of rzoom pertaining to iteration of
        the most recent relevant bounds
        '''

        # case: current rzoom a.r. not saved
        if type(self.ri.rzoom.activationRange) != type(None):
            # case: make 0-bounds
            if len(self.ri.rzoom.activationRange.shape) == 1:
                 self.ri.rzoom.activationRange = np.vstack((self.ri.rzoom.activationRange,\
                    self.ri.rzoom.activationRange)).T
            self.ri.rzoom.activationRanges.append(self.ri.rzoom.activationRange)

        self.load_activation_ranges()
        # make the next rzoom
        nb = next(self.ri)
        # case: done
        if type(nb) == type(None): return nb

        # case: fix 0-bounds
        if equal_iterables(nb[:,0],nb[:,1]):
            nb = self.fix_zero_size_activation_range(nb)
        return nb

    def load_activation_ranges(self):
        '''
        used for rm[0] == "relevance rezoom"
        '''

        additions = []
        while len(self.ri.rzoom.activationRanges) > 0:
            # pop the activation range
            ar = self.ri.rzoom.activationRanges.pop(0)

            # case: 0-size bound, modify activation range
            if equal_iterables(ar[:,0],ar[:,1]):
                ar = self.fix_zero_size_activation_range(ar)

            if type(ar) != type(None):
                self.ri.rzoomBoundsCache.append(ar)

    def fix_zero_size_activation_range(self, ar):
        '''
        fixes the zero-size activation range `ar`; new activation range is ar[0], midpoint(ar[0],next(ar[0]))
        
        :param ar: zero-size activation range
        :type ar: np.ndarray, proper bounds
        :return: a range r with r\\[0\\] equal to ar\\[0\\] that is not a zero-sized range
        :rtype: np.ndarray, proper bounds
        '''

        assert equal_iterables(ar[:,0],ar[:,1]), "not zero-size"

        # terminating condition: bounds too small
        q = self.ssi.de_bounds()
        x = np.sum(point_difference_of_improper_bounds(q,self.bounds))
        if x <= 10 ** -3:
            return None

        # save ssi location
        q = self.ssi.de_value()
        #
        self.ssi.set_value(ar[:,0])

        e1 = next(self.ssi)
        self.ssi.rev__next__()
        e2 = self.ssi.rev__next__()
        e3 = np.array([e1,e2]).T

        rv = np.ones((e3.shape[0],)) / 2.0
        p = point_on_improper_bounds_by_ratio_vector(\
            self.bounds,e3,rv)

        e3[:,1] = p
        self.ssi.set_value(q)

        x = np.sum(point_difference_of_improper_bounds(e3,self.bounds))
        if x <= 10 ** -3:
            return None

        return e3

    @staticmethod
    def column_order(k,mode = "random"):
        '''
        Outputs an ordering for k columns based on `mode`, one of
        `random`, `ascending`, `descending`.
        '''
        
        assert mode in ["random","ascending","descending"]
        s = [i for i in range(k)]
        if mode == "random":
            random.shuffle(s)
        elif mode == "descending":
            s = s[::-1]
        return np.array(s)

    def __next__(self):
        return self.get_next()

    def get_next(self):
        if self.terminated: return None
        #
        q = self.pre_next()

        # case: prg terminates
        if type(q) == type(None):
            self.terminated = True
            return None

        # log point into ResplattingInstructor
        #$%$
        self.ri.output(q)

        # set a new ssi based on resplatting mode
        self.post_next()
        #if self.iterateIt: return None
        return q

    def pre_next(self):
        # case: RSSI switched to prg
        if self.iteratedOnce and self.rm[0] == "prg":
            return next(self.ri)
        return next(self.ssi)

    def post_next(self):
        if self.ssi.reached_end():
            self.iteratedOnce = True
            self.iterateIt = True
            self.terminated = self.update_resplatting_instructor()
        else:
            self.iterateIt = False

    def display_range_history(self):
        for (i,r) in enumerate(self.rangeHistory):
            print("{}:\t{}".format(i,r))

    def _summary(self):
        print("BOUND SUMMARY")
        print("parent bounds")
        print(self.bounds)
        print()
        print("start point")
        print(self.startPoint)
        print()
        print("reference point")
        print(self.referencePoint)
        print()

        #### do range history
        print("range history")
        self.display_range_history()
        #### do

def rssi__display_n_bounds(rssi, n):
    for i in range(n):
        print("iterating bound ",i)
        q = ResplattingSearchSpaceIterator.iterate_one_bound(rssi)
        for q_ in q:
            print(q_)
        # summary
        rssi._summary()
        print("\n--------------------------------------------------")
    return -1
