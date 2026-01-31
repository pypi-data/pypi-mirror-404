'''
(a(X_n) + c) modulo m
'''
import random
from math import ceil
from .matrix_methods import *
from .variance_works import *
from .measures import zero_div 
from collections import OrderedDict

def modulo_in_range(i,r): 
    assert r[0] < r[1], "invalid range {}".format(r) 
    return i % (r[1] - r[0]) + r[0] 

class LCG:
    '''
    linear congruential generator
    '''
    
    def __init__(self, startingInteger, modulo):
        assert type(modulo) is int and modulo > 128, "invalid modulo"
        assert type(startingInteger) is int and startingInteger < modulo, "invalid starting integer"

        self.startingInteger = startingInteger
        self.vInt = startingInteger
        self.modulo = modulo
        self.fetch_arguments()

    # TODO: mod here?
    def fetch_arguments(self):
        self.multiplier = self.fetch_random_integer_in_range((0, self.modulo))
        self.increment = self.fetch_random_integer_in_range((0, self.modulo))

    def fetch_random_integer_in_range(self, ranje):
        assert type(ranje[0]) is int and type(ranje[1]) == type(ranje[0]), "invalid range"
        assert ranje[0] < ranje[1], "invalid range [1]"

        q = random.random()
        c = ceil(ranje[0] + q * (ranje[1] - ranje[0]))
        return int(c)

    def calculate(self, v):
        assert type(v) in {int,float,np.int32,np.int64,\
            np.float32,np.float64}, "invalid value v,type {}".format(type(v))
        return (self.multiplier * v + self.increment) % self.modulo

    def __next__(self):
        q = self.vInt
        self.vInt = self.calculate(q)
        return q


def prg__LCG(start,multiplier,increment,modulo):

    lcg = LCG(1,np.iinfo(np.int32).max) 
    lcg.startingInteger = start 
    lcg.vInt = start 
    lcg.modulo = modulo
    lcg.multiplier = multiplier
    lcg.increment = increment 
    return lcg.__next__ 

#############------------------------------------------------------------

# NOTE: __next__ not working. 
class CycleMap:

    '''
    '''
    def __init__(self, cRange:'int'):
        assert type(cRange) is int, "invalid type for cycle range"
        self.cRange = cRange
        self.mahp = OrderedDict()
        self.c = None 
        self.head = None
        return

    def set_map(self, m):
        assert type(m) is OrderedDict, "invalid type for map"
        assert CycleMap.is_valid_map(m), "invalid cycle map"
        assert len(m) == self.cRange, "invalid length for map"
        self.mahp = m

    @staticmethod
    def random_cycle_map(vortexRange):
        ks = np.arange(vortexRange)
        np.random.shuffle(ks)

        # select the head
        h = ks[0]
        h_ = h
        l = OrderedDict()
        rem = np.arange(vortexRange)
        for i in range(vortexRange - 1):
            possible = [r for r in rem if r != h]

            # choose random
            lp = len(possible)
            ri = random.randrange(lp)
            l[h] = possible[ri]

            rem = np.array(possible)
            h = l[h]

        l[h] = h_

        return l

    @staticmethod
    def is_valid_map(m):
        if len(m) == 0: 
            return False 

        # fetch the first element in the map
        q = list(m.keys())[0]

        # check for cycle
        x = [q]
        l = len(m)
        c = 0
        while c < l:
            r = m[x[-1]]
            x.append(r)
            c += 1

        # check that last element is first key
        if not (x[-1] == x[0]): return False
        # check that number of unique elements is l
        if len(set(x)) != l: return False
        return True

    def head_(self):
        for k,v in self.mahp.items():
            self.head = k
            self.c = k
            break

    def __next__(self):
        if type(self.c) == type(None): self.head_()
        q = self.mahp[self.c]
        self.c = q
        return q

    def v(self,k):
        return self.mahp[k]

    #### TODO: make generators for non-cycles
    
#------------------------------------------------------------------
#### binary sequence generators

def generate_possible_binary_sequences(vecOrder, thisNumber, elements = [0,1]):

    if len(thisNumber) == vecOrder:
        yield thisNumber
        return

    q1, q2 = np.copy(thisNumber), np.copy(thisNumber)
    q1, q2 = np.hstack((q1,[elements[0]])), np.hstack((q1,[elements[1]]))
    yield from generate_possible_binary_sequences(vecOrder, q1,elements)
    yield from generate_possible_binary_sequences(vecOrder, q2,elements)

def generate_random_binary_sequence(vecOrder):
    assert type(vecOrder) is int, "invalid vec. order"
    return np.random.randint(0, 2, (vecOrder,))

def prg__constant(x=0): 

    def f(): 
        return x
    return f 

class ModuloAlternator: 

    def __init__(self,s0,s1,s=None): 
        assert s1 > s0 
        assert type(s1) == type(s0)
        assert type(s1) == int 

        self.s0 = s0 
        self.s1 = s1 
        if s == None: 
            self.s = self.s0 
        else: 
            self.s = (s % self.s1) + self.s0 

    def __next__(self): 
        q = self.s
        self.s += 1
        if self.s >= self.s1: 
            self.s = (self.s % self.s1) + self.s0 
        return q 


def prg__n_ary_alternator(s0=0,s1=2,start=0): 
    ma = ModuloAlternator(s0,s1,start) 
    return ma.__next__ 

####---------------------------------------------------------------------
#### uniform dist. numerical generators

"""
"""
def generate_uniform_sequence_in_bounds(vecOrder, bounds,rnd_struct=rng):
    assert is_2dmatrix(bounds), "invalid bounds {}".format(bounds)
    assert vecOrder == len(bounds) or len(bounds) == 1, "invalid bounds"

    if len(bounds) == 1:
        return rnd_struct.uniform(bounds[0,0], bounds[0,1], (vecOrder,))
    else:
        q = np.zeros((vecOrder,))
        for i in range(vecOrder):
            q[i] = rnd_struct.uniform(bounds[i,0], bounds[i,1])#, (vecOrder,))
        return q

def random_bounds_edge(bounds):
    assert is_bounds_vector(bounds), "invalid bounds"
    bs = generate_random_binary_sequence(bounds.shape[0])
    r = [i for i in range(bounds.shape[0])]
    return bounds[r,bs]

################################# TODO: noise methods need to be checked.


def k_random_points_in_bounds(minVec,maxVec,k):
    '''
    A method that generates `k` points in bounds [`minVec`,`maxVec`] by random.random().

    :param minVec: n-dimensional vector with each dimension the minumum value
    :type minVec: np.ndarray
    :param maxVec: n-dimensional vector with each dimension the maximal value
    :type maxVec: np.ndarray
    :param k: number of points to generate
    :type k: int, > 0
    '''
    assert np.all(maxVec - minVec >= 0.0), "invalid arguments min.,max. vec"

    d = maxVec - minVec
    for i in range(k):
        x = random.random()
        yield minVec + (d * x)

###------------------------

def one_random_noise(bounds,noiseRange):
    """
    :param bounds: bounds matrix
    :type bounds: np.ndarray, n x 2 matrix
    :param noiseRange: 2dmatrix, len is 1 or bounds.shape[0]
    """
    assert is_proper_bounds_vector(bounds), "invalid bounds"

    # set max distance for each dim.
    q = bounds[:,1] - bounds[:,0]
    us = generate_uniform_sequence_in_bounds(bounds.shape[0], noiseRange)
    q = q * us
    return q

def random_npoint_from_point(p1,l,roundDepth=5):
    p2 = np.copy(p1)
    r = np.arange(p1.shape[0])
    np.random.shuffle(r)
    r,x = r[:-1],r[-1]
    d = 0.0

    def delta_extreme():
        return math.sqrt(l ** 2 - d)

    def random_delta(j,randomize = True):
        delta = delta_extreme()
        delta = delta if random.random() > 0.5 else -delta

        if randomize:
            delta = random.uniform(0.0,delta)
        return delta

    for r_ in r:
        rd = random_delta(r_)
        p2[r_] = p2[r_] + rd
        d += (rd **2)
    p2[x] = p2[x] + random_delta(x,False)
    return np.round(p2,5)

def random_npoint_from_point_in_bounds_(b,p1,l,roundDepth = 5):
    """
    calculates a random n-dimensional point p2 in bounds `b` of distance `l`
    from `p1`.
    """

    p2 = np.copy(p1)
    r = np.arange(p1.shape[0])
    np.random.shuffle(r)
    r,x = r[:-1],r[-1]
    d = 0.0

    def delta_extreme():
        return math.sqrt(l ** 2 - d)

    def possible_extreme(j):
        return [b[j,0] - p1[j],b[j,1] - p1[j]]

    def random_delta(j,randomize = True):
        delta = delta_extreme()
        delta = delta if random.random() > 0.5 else -delta

        if randomize:
            delta = random.uniform(0.0,delta)

        pe = possible_extreme(j)
        pe = pe[1] if delta > 0 else pe[0]
        sols = [pe,delta]
        k = np.argmin(np.abs(sols))
        return sols[k]

    for r_ in r:
        rd = random_delta(r_)
        p2[r_] = p2[r_] + rd
        d += (rd **2)
    p2[x] = p2[x] + random_delta(x,False)
    return np.round(p2,5)

def random_npoint_from_point_in_bounds(b,p1,l,attempts = 15):
    t = False

    while not t and attempts > 0:
        p2 = random_npoint_from_point_in_bounds_(b,p1,l)
        #print("DISTANCE ", euclidean_point_distance(p1,p2))
        t = abs(euclidean_point_distance(p1,p2) - l) < 10 ** -5
        attempts -= 1
    return p2 if t else None

def add_noise_to_points_restricted_bounds(minVec,maxVec, points, noiseRange = np.array([[0.25,0.65]]), boundsRestriction = False):
    '''
    adds noise to points in restricted bounds by noise range,
    set to (0.25,0.65) by default.

    each output in yield is a point that may not lie within the bounds set by minVec
    and maxVec
    '''

    b = np.array([minVec,maxVec]).T
    for p in points:
        yield p + one_random_noise(b,noiseRange)

def random_noise_sequence(s,b,noiseRange):
    rn = []
    for i in range(s):
        n = one_random_noise(b,noiseRange)
        rn.append(n)
    return np.array(rn)

# TODO:
def generate_gaussian_sequence_in_bounds(mean, var):
    rng.normal()
    return -1

def default_std_Python_prng(integer_seed=None,output_range=[-10**6,10**6],rounding_depth=0): 
    if type(integer_seed) == int:
        random.seed(integer_seed)

    assert output_range[0] <= output_range[1]
    assert rounding_depth >= 0 and type(rounding_depth) == int 

    def fx():
        v = random.uniform(output_range[0],output_range[1]) 
        v = round(v,rounding_depth) 

        if rounding_depth == 0: 
            return int(v) 
        return v  
    return fx

#-------------------------- sequence sorters using prgs

def prg_seqsort(l,prg): 
    """
    sorts a sequence using a pseudo-random number generator 

    :param l: sequence of elements; all elements of same type. 
    :type l: list 
    :param prg: pseudo-random number generator used to choose indices. 
    :type prg: function, no parameters. 
    """
    l_ = [] 
    while len(l) > 0: 
        i = int(prg()) % len(l) 
        l_.append(l.pop(i))
    return l_ 

# TODO: unit-test this more 
def prg_seqsort_ties(l,prg,vf): 
    """
    sorts a sequence l

    :param l: sequence of elements; all elements of same type. 
    :type l: list 
    :param prg: pseudo-random number generator used to choose indices. 
    :type prg: function, no parameters. 
    :param vf: value-access function for element of l
    :type vf: function, one parameter is instance of element type for `l`. 
    """

    # sort l by vf first 
    q = sorted(l,key=vf)
    Q = [] 
    while len(q) > 0: 
        x = q.pop(0) 
        y = vf(x) 
        q2 = [x]

        # collect all ties with x
        j = -1 
        for (i,q_) in enumerate(q): 
            y2 = vf(q_) 
            if y == y2: 
                j = i 
            else: 
                break 
        j += 1 
        q2.extend(q[:j])
        while j > 0: 
            q.pop(0) 
            j -= 1 
        # permute q2 by prg 
        q2 = prg_seqsort(q2,prg)
        Q.extend(q2) 
    return Q 

#----------------------------------- partitioning of integers into sets using PRNGs 

def prg_partition_for_sz(S,num_sets,prg,variance):  
    """
    outputs a partition P (list) with positive integers 
    of length `num_sets` that sums to S. Uses the argument 
    `prg` that acts as a pseudo-random number generator 
    to output values with respect to `variance`. 

    NOTE: output may appear wrong according to `variance`. 
          The partitioning scheme assigns 1 to every set  
          in the beginning. Then it iterates through the 
          sets, P, and draws a number using the `prg` that is 
          at most the remaining number left, S - sum(P). This 
          drawing is what the `variance` measure relates to. 
          The range of possible numbers decreases the further 
          down the iteration. 
    """
    
    assert variance >= 0.0 and variance <= 1.0 
    assert S >= num_sets 

    P = [1 for _ in range(num_sets)] 
    S -= sum(P)

    i = 0 
    stat = S > 0 and i < num_sets 
    while stat:
        if i + 1 == num_sets: 
            P[-1] += S 
            break
        if S < 0: break  

        x = ceil(S / num_sets) 
        rem = ceil((S - x) * variance)

        rng = [x - rem, x + rem]

        if rng[0] == rng[1]: 
            P[i] += rng[0] 
            S -= rng[0] 
        else: 
            q = modulo_in_range(prg(),rng)
            q = modulo_in_range(prg(),[1,S+1]) 
            P[i] += q
            S -= q
        i += 1 

    return P 

def prg_partition_for_sz__n_rounds(l,num_sets,px,var,n): 

    if num_sets == 1:
        return [l] 

    q = prg_partition_for_sz(l,num_sets,px,var)

    def mod_q(q_):
        # choose a random index 
        ix = [i for i in range(len(q_))] 

        qi = None
        while len(ix) > 0:
            qi_ = px() % len(ix)
            qi_ = ix.pop(qi_) 

            if q_[qi_] <= 1: 
                continue
            qi = qi_ 
            break  
        
        if type(qi) == type(None):
            return False 

            # determine a 
        ix = [i for i in range(len(q_)) if i != qi] 
        dx = modulo_in_range(px(),[1,q_[qi]]) 

        while dx > 0:
            ix2 = px() % len(ix) 
            ix2 = ix[ix2]
            dx2 = modulo_in_range(px(),[1,dx+1])
            q_[ix2] += dx2 
            q_[qi] -= dx2 
            dx -= dx2
        return q_ 

    for _ in range(n-1):
        q_ = mod_q(q)

        # case: sequence was not modified 
        if type(q_) == bool:
            continue  
        q = prg_seqsort(q_,px)
    return q 


def prg_choose_n(Q,n,prg,is_unique_picker:bool=False):
    l = len(Q)
    assert l > 0 

    if is_unique_picker: 
        assert l >= n 

    q = []
    while n > 0:  
        i = prg() % l
        q.append(Q[i])

        if is_unique_picker:
            Q.pop(i)
            l -= 1 
        n -= 1
    return q 

def prg_partition_for_float(F,df,px,var,n=1000,rounding_depth=5):

    # scale the dividor integer px` from px so that 
    # px` is less than F 
    scale = 0 
    stat = True
    while stat: 
        df_ = df / (10. ** scale) 
        if F >= df_: 
            stat = False 
            continue 
        scale += 1

    F_ = F * (10. ** scale) 
    q = prg_partition_for_sz__n_rounds(F_,df,px,var,n)
    q2 = [round(q_ / (10. ** scale),rounding_depth) for q_ in q]
    return np.array(q2)

#---------------------------------------- conversions using PRNGs: outputting decimals, generating new PRNGs, etc. 

def prg_decimal(prg,output_range): 
    r0,r1 = abs(prg()),abs(prg())
    rx = sorted([r0,r1]) 
    rx = zero_div(rx[0],rx[1],0.5) 
    return modulo_in_range(rx,output_range)

def prg_to_prg__LCG_sequence(prg,n,moduli_scale=3): 
    l = [] 
    for i in range(n): 
        l_ = [] 
        for j in range(4): 
            m = int(prg()) % 2 
            if m == 0: m = -1 
            l_.append(prg() * moduli_scale) 

        l_[3] = l_[3] * 3 
        l.append(prg__LCG(l_[0],l_[1],l_[2],l_[3]))
    return l 

    #------------------------------ copied from project<seqbuild> 

def prg__single_to_nvec(prg,n):

    def f():
        q = np.zeros((n,))
        for i in range(n): 
            q[i] = prg()
        return q 
    return f 

def prg__single_to_int(prg):

    def f(): 
        return int(round(prg())) 

    return f  