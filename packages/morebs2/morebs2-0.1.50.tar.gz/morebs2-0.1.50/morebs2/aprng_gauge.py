from .search_space_iterator import *
from itertools import combinations 

def range_op(rangez,default_value=0.,f_inner=np.subtract,f_outer=np.add):
    rangez_ = to_noncontiguous_ranges(rangez)
    l = len(rangez_)
    s = default_value
    for i in range(0,l):
        f_out = f_inner(rangez_[i][1],rangez_[i][0])
        s = f_outer(s,f_out)
    return s

"""
float accumulator operation over vector `v`
"""
def vec_op(v,interop,default_value=0.):
    s = default_value
    for v_ in v: 
        s = interop(s,v_)
    return s


############### a lightweight standard n-dimensional index incrementor
############### built on top of <SearchSpaceIterator>. 
##################################################################

def not_permutation_condition(v):
    stat = True
    l = len(v) - 1
    for i in range(l):
        stat = v[i] <= v[i+1]
        if not stat: break 
    return stat 

def is_reflective_condition(v):
    return len(v) == len(np.unique(v))

"""
Generates numbers in an n-dimensional square
structure according to variables such as 
`is_perm`, `is_reflective`. The variable 
`subset_size` indicates the dimension of the 
output from `__next__`. 

The value `length` is the length of the vector
that the output of this class is supposed to 
accomodate. 
"""
class BatchIncrStruct:

    def __init__(self,length:int,is_perm=False,\
        is_reflective=False,subset_size=2):
        """
        length := int or float, specifies the max 
                for each bound
        subset_size := int, otherwise known as the n in n-dim.
        """

        assert type(length) == type(subset_size)
        assert type(length) == int
            
        assert type(is_reflective) == type(is_perm)
        assert type(is_reflective) == bool

        self.l = length
        self.is_perm = is_perm
        self.is_ref = is_reflective
        self.subset_size = subset_size
        self.at_i = np.zeros((subset_size,))
        self.preprocess()
        return

    def preprocess(self):
        bounds = np.zeros((self.subset_size,2))
        bounds[:,1] = self.l

        column_order = [i for i in range(self.subset_size)][::-1]
        ssi_hop = self.l
        cycle_on = False
        cycle_is = 0
        self.ssi = SearchSpaceIterator(bounds,self.at_i,\
            column_order,ssi_hop,cycle_on,cycle_is)

    """
    end value is `None` instance. 
    """
    def __next__(self):
        stat = False
        while not stat: 
            q,stat = self.next_() 
        return q 

    def next_(self): 
        if self.ssi.reached_end():
            return None,True 

        v = next(self.ssi)
        v,stat = self.pass_next(v) 
        if type(v) != type(None): 
            v = np.asarray(v,dtype=int)

        return v,stat 

    def pass_next(self,v):

        stat = True if type(v) != type(None) else False
        if not stat: return v,stat 

        if not is_reflective_condition(v) and not self.is_ref:
            stat = False

        if not not_permutation_condition(v) and not self.is_perm:
            stat = False

        return v,stat

#################### methods for calculating coverage of sequence
###################################################

"""
maps a sequence of ranges to one, with 
noncontiguous ranges and has the greatest
similarity to original `rangez`. 

"""
def to_noncontiguous_ranges(rangez,is_sorted=False):
    if not is_sorted:
        rangez = sorted(rangez,key=lambda x: x[0])
    
    i = 0
    while i < len(rangez) - 1:

        r1 = rangez[i]
        r2 = rangez[i+1]
        # check if intersection
        stat = r1[1] >= r2[0] and r1[1] <= r2[1]
        # case: intersection
        if stat:
            r3 = [r1[0],r2[1]]
            rangez.pop(i)
            rangez.pop(i)
            rangez.insert(i,r3)
        else: 
            i += 1
    return rangez

"""
extension of the method<matrix_methods.complement_of_range_in_range> 
"""
def complement_of_noncontiguous_ranges(rangez,rv): 
    assert is_valid_range(rv,False,True) 
    
    q = rv[0]
    res = []
    for r in rangez:
        if r[0] > q:
            rx = (q,r[0]) 
            res.append(rx)
        q = r[1] 
    if q < rv[1]:
        rx = (q,rv[1]) 
        res.append(rx) 

    return res 

"""
NOTE: 
assumes `ncrange` and `ncrange_comp` are of proper form as
sequences of non-contiguous ranges. 

Outputs the complementary neighbors of the i'th 
subrange in `ncrange`, alongside its complement 
`ncrange_comp`. 
"""
def neighbors_of_ncrange(ncrange,ncrange_comp,i):
    j = i
    x = 0
    ref = ncrange[i] 
    stat = True 
    cache = [None,None] 

    greater_left_stat = ref[0] < ncrange_comp[0][0]
    greater_right_stat = ref[1] > ncrange_comp[-1][1] 
    while stat:
        jx = list(set([x,x*-1])) 

        ##?
        #active = set() 
        for jx_ in jx:  
            j2 = j + jx_ 
            if not (0 <= j2 < len(ncrange_comp)): 
                continue
            ##?
            #active |= {j2} 
            
            ref2 = ncrange_comp[j2]
            # case: left  
            if ref[0] == ref2[1]: 
                cache[0] = ref2
                continue

            # case: right 
            if ref[1] == ref2[0]: 
                cache[1] = ref2 
                continue

        ##?
        #if len(active) == 0: break 
        x += 1 

        # no left
        if greater_left_stat: 
            if type(cache[1]) != type(None): return cache 

        if greater_right_stat: 
            if type(cache[0]) != type(None): return cache 
     
        done = type(cache[0]) != type(None) and type(cache[1]) != type(None)
        stat = not done 

    return cache

def qualifying_ranges_for_coverage_expansion(ncrange,ncrange_comp,changean,\
    output_type="index"):
    assert output_type in {"index","literal"} 

    # get qualifying ranges 
    qrs = []
    for (i,r) in enumerate(ncrange):
        neighbors = neighbors_of_ncrange(ncrange,ncrange_comp,i)
        if type(neighbors[0]) != type(None):
            stat1 = abs(changean) <= neighbors[0][1] - neighbors[0][0] 
        else: 
            stat1 = False

        if type(neighbors[1]) != type(None): 
            stat2 = abs(changean) <= neighbors[1][1] - neighbors[1][0] 
        else: 
            stat2 = False

        if stat1 or stat2: 
            qrs.append(i) 

    if output_type == "index": 
        return qrs 
    return [ncrange[q] for q in qrs]

def qualifying_ranges_for_coverage_shrinkage(ncrange,changean,output_type="index"):
    assert output_type in {"index","literal"} 

    qrs = []
    for (i,r) in enumerate(ncrange):
        if r[1] - r[0] >= abs(changean): 
            qrs.append(i) 
    if output_type == "index":
        return qrs 
    return [ncrange[q] for q in qrs] 

"""
maps every element v_ in vector `v` to the index of the 
range in `ncr`, an ordered sequence of non-contiguous ranges, 
that contains v_. 
"""
def vector_to_noncontiguous_range_indices(v,ncr):
    def index_of(v_):
        for (i,ncr_) in enumerate(ncr):
            if ncr_[0] <= v_ <= ncr_[1]:
                return i
        return -1 
    
    return np.array([index_of(v_) for v_ in v],dtype=int) 

def floatseq_to_rangeseq(vf,rv,max_radius:float):
    assert len(rv) == 2 and rv[0] <= rv[1]
    assert max_radius > 0
    r = []
    for f in vf:
        min_f = max(rv[0],f-max_radius)
        max_f = min(rv[1],f+max_radius)
        r.append([min_f,max_f])
    return np.array(r) 

"""
measure does not take into account improper bounds (see 
the section of library on functions `*improper_bounds*`)
"""
def coverage_of_sequence(vf,rv,max_radius:float):
    rs = floatseq_to_rangeseq(vf,rv,max_radius)
    q = range_op(rs,default_value=0.,f_inner=np.subtract,f_outer=np.add)
    qmax = rv[1] - rv[0]
    return np.round(q/qmax,5)

############ methods for calculating unidirectional point distance
#######################################################

def normalized_float_uwpd(v,rv):
    l = len(v)
    d = uwpd(v,accum_op=lambda x1,x2: x1 + x2)
    dmax = max_float_uwpd(l,rv) 
    return np.round(d/dmax,5)

def uwpd(v,pairwise_op=lambda x1,x2: np.abs(x2 - x1),accum_op=None):
    assert type(v) == np.ndarray
    assert v.ndim == 1

    # using the 
    ##bis = BatchIncrStruct(len(v),False,False,2)
    bis = combinations([i for i in range(len(v))],2) 
    stat = True 
    stat2 = type(accum_op) == type(None)
    result = [] if stat2 else 0.0
    while stat:
        try: 
            index = next(bis)
        except: 
            stat = not stat
            continue 

        stat = not (type(index) == type(None))

        if not stat: 
            continue 

        op_val = pairwise_op(v[index[0]],v[index[1]])

        if stat2:
            result.append(op_val)
            continue
        result = accum_op(result,op_val) 
    return result

def max_float_uwpd(l,fr):
    assert len(fr) == 2 and fr[0] <= fr[1]
    s = 0
    for i in range(0,l): s += i
    return (fr[1] - fr[0]) * s  

###################################################

class APRNGGauge: 

    """
    aprng := Abstract Pseudo random generator function; values are called by 
             `aprng()`.
    frange := float range
    """
    def __init__(self,aprng,frange,pradius:float):
        assert len(frange) == 2
        assert frange[0] <= frange[1] 

        self.aprng = aprng
        self.frange = frange
        self.frange_default = frange 
        self.pradius = pradius
        # n * 2 array; 
        ## two columns
        ## [0]: cycle coverage
        ## [1]: unidirectional weighted point distance measure
        self.measurements = []
        self.cycle = None
        return 

    def assign_cycle(self,cycle):
        self.cycle = cycle

    def measure_cycle(self,max_size=100000,\
        term_func=lambda l,l2: type(l) == type(None),\
        auto_frange:bool=False):

        if type(self.cycle) == type(None):
            self.cycle = self.cycle_one(max_size,term_func)
        assert self.cycle.ndim == 1

        # get the coverage
        if auto_frange:
            m1,m2 = min(self.cycle),max(self.cycle)
            self.frange = [m1,m2] 

        cov = coverage_of_sequence(self.cycle,self.frange,self.pradius)

        # get the normed uwpd
        nuwpd = normalized_float_uwpd(self.cycle,self.frange)
        self.measurements.append([cov,nuwpd])
        return [cov,nuwpd]

    def cycle_one(self,max_size:int,term_func):
        start = self.aprng()
        c = [start]
        stat = True
        l,prev = None,None 

        while len(c) < max_size and stat:
            prev = l
            l = self.aprng()
            stat = term_func(l,prev)  

            # if terminate, 
            if stat: 
                c.append(l) 
        return np.array(c)

###################################################################################