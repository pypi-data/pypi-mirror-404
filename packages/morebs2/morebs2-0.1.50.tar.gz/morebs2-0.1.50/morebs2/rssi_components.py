from .search_space_iterator import *
from .relevance_functions import *
from .numerical_generator import *

class RZoom:
    '''
    RZoom is a map-like class that uses a set `rf` of relevance functions to determine if a point satisfies.
    '''

    def __init__(self, rch):
        assert type(rch) is RChainHead, "invalid RChainHead"
        self.rch = rch
        self.activationRanges = [] # each element is a bound
        self.activationRange = None
        return

    def score(self,p):
        return self.rch.apply(p)

    def output(self,p):
        s = self.score(p)
        
        # do update on activation ranges
        if s:
            if type(self.activationRange) == type(None):
                self.activationRange = np.copy(p)
            else: # assume size 1
                if len(self.activationRange.shape) != 2:
                    self.activationRange = np.vstack((self.activationRange,p)).T
                else:
                    self.activationRange[:,1] = p
            
        else:
            if type(self.activationRange) == type(None): return

            # case: 0-size bounds
            if len(self.activationRange.shape) == 1:
                self.activationRange = np.vstack((self.activationRange,\
                                    self.activationRange)).T
            self.activationRanges.append(self.activationRange)
            self.activationRange = None
        
        return

class CenterResplat:
    '''
    used for resplatting mode `png`

    :param centerBounds: proper bounds vector
    :param rch: instance<RChainHead>
    :param noiseRange: n x 2 np.ndarray
    '''

    def __init__(self,centerBounds, rch, noiseRange):
        assert is_proper_bounds_vector(centerBounds), "invalid bounds"
        self.centerBounds = centerBounds
        self.rch = rch
        self.noiseRange = noiseRange

        #: cache of relevant points passed from class<ResplattingInstructor>.
        self.relevantPointsCache = []
        #: counter for index of relevant point in `self.relevantPointsCache` to the number of times the value was selected by class<ResplattingInstructor> for re-splatting purposes.
        self.rpIndexCounter = defaultdict(int) # index

    def output(self,p):
        if self.rch.apply(p):
            self.relevantPointsCache.append(p)

    def __next__(self):
        '''
        outputs a next value based on 
        '''

        if len(self.relevantPointsCache) == 0:
            return None

        # choose random relevant point
        rpi = random.randrange(len(self.relevantPointsCache))

        self.rpIndexCounter[rpi] += 1

        v = self.relevantPointsCache[rpi]

        # add noise
        n = one_random_noise(self.centerBounds,self.noiseRange)

        # round in bounds
        return vector_hop_in_bounds(v,n,self.centerBounds)

class ResplattingInstructor:
    '''
    Class provides resplatting instructions for ResplattingSearchSpaceIterator.
    If mode is "prg", then will output random point from .CenterResplat.
    '''

    def __init__(self,rzoom,centerResplat):
        self.rzoom = rzoom
        self.rzoomBoundsCache = [] # pop(0), push(-1)
        self.centerResplat = centerResplat

    def check_args(self):
        return type(self.rzoom) == type(None) or type(self.centerResplat) == type(None)

    def output(self,p):
        assert self.check_args()
        if type(self.centerResplat) != type(None):
            self.centerResplat.output(p)
        else:
            self.rzoom.output(p)

    '''
    if mode == relevance zoom:
    '''
    def __next__(self):
        assert self.check_args()
        if type(self.centerResplat) != type(None):
            return next(self.centerResplat)
        return self.next_activation_range()

    def next_activation_range(self):
        if len(self.rzoomBoundsCache) == 0: return None
        return self.rzoomBoundsCache.pop(0)
