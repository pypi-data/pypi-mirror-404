from collections import defaultdict
import random
from copy import  deepcopy
import operator
from .line import *
from .relevance_functions_extended import *

# NOTE: when devising euclidean_point_distance measures
'''
reference count
vector -> ed vector -> (ed in bounds):float -> bool(float)

reference existence
vector -> ed vector -> (ed in bounds):bool
'''
lambda_floatin = lambda x,b: x >= min(b) and x <= max(b)

lambda_pointinbounds = lambda p,b: point_in_bounds_(b,p)

def lambda_countpointsinbounds(p,b):
    if b.shape[0] == 1:
        mask = np.logical_and(p >= b[0,0],p <= b[0,1])
    else:
        mask = np.logical_and(p >= b[:,0],p <= b[:,1])
    q = len(np.where(mask == True)[0])
    return q

def lambda_ratiopointsinbounds(p,b):
    x = lambda_countpointsinbounds(p,b)
    return zero_div(x,len(p),np.inf)

def random_select_k_unique_from_sequence(s, k):
    s = list(s)
    assert len(s) >= k
    random.shuffle(s)
    return s[:k]


################################### TODO: delete these functions after refactor

# TODO:
def relevance_zoom_func_1(referencePoint,boundsDistance,activationThreshold):
    # TODO: check for 0-case
    assert boundsDistance >= 0.0, "invalid bounds distance {}".format(boundsDistance)
    assert activationThreshold >= 0.0 and activationThreshold <= 1.0, ""
    return lambda p: euclidean_point_distance(p, referencePoint) <= activationThreshold * boundsDistance

def relevance_zoom_func_2(referencePoint, modulo, activationThreshold):
    rp = np.array(referencePoint, dtype = "int")
    lim = referencePoint.shape[0]
    def p(x):
        q = (rp - np.array(x,dtype="int")) % 2
        return lambda p: True if len(q == 1.0) >= lim else False
    return p


## TODO: delete?
def relevance_func_2(modulo, moduloPercentileRange):
    '''
    a sample relevance function to help demonstrate the work of CenterResplat.

    :return: function(vector) -> True if all values in (point % modulo) fall within moduloPercentileRange
    :rtype: function<vector>
    '''
    assert modulo >= 0.0, "invalid modulo"
    assert is_valid_point(moduloPercentileRange)
    assert min(moduloPercentileRange) >= 0.0 and max(moduloPercentileRange) <= 1.0
    assert moduloPercentileRange[0] <= moduloPercentileRange[1]

    minumum,maximum = moduloPercentileRange[0] * modulo,moduloPercentileRange[1] * modulo

    def f(p):
        p_ = p % modulo
        return np.all(p_ >= minumum) and np.all(p_ <= maximum)

    return f

def vector_modulo_function_with_addon(modulo, addOn):
    """
    boolean function, addon determines
    """
    def x(v):
        q = np.array(v,dtype="int")
        v_ = q % modulo
        return addOn(v_)
    return x

##### add-on functions : vector -> bool

"""
"""
def vf_vector_reference(vr, pw):
    def x(v):
        return pw(vr,v)
    return x

def subvector_iselector(indices):
    def a(v):
        return v[indices]
    return a


def m(v,addOn,iov,outputType):
    """
    m is index|value selector function for arg. to func<addOn>
    """
    assert iov in [0,1,2]

    x = []
    for t in enumerate(v):
        qi = t[iov] if iov != 2 else t
        print("QI: ",qi)
        if addOn(qi):
            if outputType == 1: q = t[1]
            else: q = t
            x.append(q)
    return np.array(x)

def subvector_selector(addOn, inputType =1, outputType = 1):
    """
    outputs elements by addOn

    :param addOn: function that outputs either singleton or pair
    :type addOn: function
    """
    assert inputType in [0,1,2], "invalid input"
    assert outputType in [1,2], "invalid output"

    def m_(v):
        return m(v,addOn,inputType,outputType)

    return m_

## $
def addon_singleton__bool__criteria_range_each(rangeReq):
    '''
    :param rangeReq: proper bounds vector
    :type rangeReq: proper bounds vector
    :return:
    :rtype: function<vector>->bool
    '''

    assert is_proper_bounds_vector(rangeReq), "invalid ranges"
    # rangeReq := length 1 or vr.shape[0]
    if rangeReq.shape == (1,2):
        q = rangeReq[0]
        p = lambda v: np.all(v >= q[0]) and np.all(v <= q[1])
    else:
        p = lambda v: point_in_bounds(rangeReq,v)
    return p

def addon_singleton__bool__criteria_distance_from_reference(rf, dm, dt,cf):
    """
    :param rf: reference value
    :type rf: ?
    :param dm: distance measure between (rf,v)
    :type dm: func<v1::vector,v2::vector>->float
    :param dt: distance threshold
    :type dt: float
    :param cf: comparator function on (dist,dt)
    :type cf: function<?>->?
    :return: function on `cf`
    :type: function<cf>->?
    """
    return lambda v: cf(dm(rf,v),dt)

class RCInst:
    """
    class that acts as a node-like structure and a function, node is designed to be used w/ the capabilities:
    
    (1) referential data (from outside of chain)
    
    (2) (standard operator,operand)

    This class is a function on a vector `v` that works by one of the four paths:
    
    (1) deciding path with reference : `cf(dm(rf,v),dt)`.
    
    (2) deciding path w/o reference: `cf(v,dt)`.
    
    (3) non-deciding path w/ reference: `cf(dm(rf,v))`.
    
    (4) non-deciding path w/o reference: `cf(v)`.

    Deciding paths require a none-null threshold value `dt`.

    In addition to these capabilities, :class:`RCInst` can update its variables.  

    :attribute rf: reference value, as argument to dm(v,rf)
    :attribute dm: function f(rf,v)
    :attribute cf: function f(v,*dt), examples include  operator.lt, operator.le, lambda_floatin, np.cross
    :attribute dt: value, use in the case of decision
    """

    def __init__(self):
        self.rf = None
        self.dm = None
        self.cf = None
        self.dt = None
        #: key is one of `rf`, `dt`; value is update function for that variable
        self.updateFunc = {}
        #: list of values used in accordance with update function in `self.updateFunc` by indices specified in `self.updatePath`
        self.updateInfo = None
        #: key is one of `rf`, `dt`; value is list of indices corresponding to values in `self.updateInfo`
        self.updatePath = {}

    def __str__(self):
        s = "* RCInst contents\n\t"
        s += str(self.rf) + "\n\t"
        s += str(self.dm) + "\n\t"
        s += str(self.cf) + "\n\t"
        s += str(self.dt) + "\n\t"
        return s

    def inst_update_var(self):
        ''' updates each key `k` in `updatePath` by the following:
        for `k`, retrieve all relevant variables `q` from `updateInfo`
        by the indices specified by `updatePath`[k] and then 
        then uses the update function `updateFunc`[k] on `q` to 
        produce the updated value for variable `k`. 
        '''

        for k,v in self.updatePath.items():

            # fetch function args
            q = []
            for v_ in v:
                q.append(self.updateInfo[v_])

            f = self.updateFunc[k]
            x = f(*tuple(q))
            self.update_var(k,x)

    def load_update_info(self,updateInfo):
        self.updateInfo = updateInfo

    def update_var(self,k,v):
        '''
        updates one of the class attributes `rf`, `dm`, `cf`,or `dt`
        with value `v`.

        :param k: attribute name
        :type k: str
        :param v: new update value
        :type v: ?
        '''

        if k == "rf":
            self.rf = v
        elif k == "dm":
            self.dm = v
        elif k == "cf":
            self.cf = v
        elif k == "dt":
            self.dt = v
        else:
            raise ValueError("invalid key _{}_".format(k))

    def mod_cf(self,dcf):
        self.cf = dcf(self.cf)
        return

    def set_reference_data(self,rf,dm):
        
        self.load_var_ref(rf)
        self.load_var_dm(dm)
        return

    ############# some functions

    def branch_at(self,n,i):
        return -1

    def load_var_ref(self,rf):
        self.rf = rf

    def load_var_cf(self,cf):
        self.cf = cf

    def load_var_dt(self,dt):
        '''
        loads a new deciding threshold value `dt`; used as `cf(v,dt)`
        '''

        self.dt = dt

    def path_type(self):
        if type(self.rf) != type(None):
            return "ref"
        return "dir"

    # TODO: class does not know.
    def output_type():
        return -1

    def load_var_dm(self,dm):
        """
        :param dm: function on (rf,v)
        """
        self.dm = dm

    def load_path(self):
        '''
        instantiates the main function `self.f` by one of the four specifications
        in the description for this class
        '''
        
        # deciding path
        if type(self.dt) != type(None):
            # for output type bool|float
            if self.path_type() == "ref":
                # calculates distance from .reference
                self.f = lambda v: self.cf(self.dm(self.rf,v),self.dt)
            else:
                self.f = lambda v: self.cf(v, self.dt)
        # non-deciding path
        else:
            if self.path_type() == "ref":
                # calculates distance from .reference
                self.f = lambda v: self.cf(self.dm(self.rf,v))
            else:
                self.f = lambda v: self.cf(v)
        return deepcopy(self.f)

class RChainHead:
    """
    :class:`RChainHead` is a sequence of functions with each element a node-like structure,represented by `RCInst`,
    that acts as a 'super' function. 
    
    Each node of this class is modifiable by update.
    ------------------------------------------------

    To make an :class:`RCInst` at index `i` of the :class:`RChainHead` instance updatable at a variable `v`,
    set its update function in the :class:`RCInst` dictionary class variable `updateFunc` for `v`, set the 
    variable path index vector `updatePath` for the same variable.

    Then update the `updatePath` variable of the :class:`RChainHead` instance with
    key `i` (denoting the node index of the :class:`RCInst` instance) with a vector of
    indices corresponding to the `variablesList` parameter in the 
    :class:`RChainHead`.load_update_vars function.

    Example:
                ```
                rch.s[0].updateFunc = {'rf': update_dt_function}
                rch.s[0].updatePath = {'rf':[0]}
                rch.updatePath = {0: [0]}

                rch.load_update_vars([one,two,three,four])
                ```
        * :class:`RChainHead` instance loads list of variables, and the variable
          `one` is loaded into the :class:`RCInst` at index 0, and `one` is used to
          update the reference value `rf` of the :class:`RCInst` instance. 


    :attribute s: the chain of class<RCInst> instances.
    :type s: list(`RCInst`)
    :attribute vpath: the sequence of transformation values that a value `v` goes through at each node in `s`. 
    :type vpath: list(values) 
    :param updatePath: a dictionary of the key-value form `node index -> sequence of indices in arg<varList>`.
    :type updatePath: dict
    :param verbose: for print-display at each class<RCInst> transformation.
    :type verbose: bool
    """
    
    def __init__(self,verbose = False):
        self.s = []
        self.vpath = []
        self.updatePath = {}
        self.verbose = verbose

    def update_rch(self):
        '''
        Updates variables of each node class<RCInst>.

        - example:
        class<ResplattingSearchSpaceIterator> calls this method on its class<RChainHead> instance
        after iterating through one pertinent bound. 
        '''

        for s_ in self.s:
            s_.inst_update_var()

    def load_update_path(self,up):
        '''
        loads a `self.updatePath`

        :param updatePath: update information (see )
        '''

        self.updatePath = up
        return

    def load_update_vars(self,varList):
        '''
        :param varList: tuple of update-variables
        '''

        for k,v in self.updatePath.items():
            vl = []
            for (i,v2) in enumerate(varList):
                if i in set(v):
                    vl.append(v2)
            self.s[k].load_update_info(vl)

    def link_rch(self,rch,linkerFunc, prev = False):
        if prev:
            return linkerFunc(self,rch)
        return linkerFunc(self,rch)

    def vpath_subset(self,si):
        return [x for (i2,x) in enumerate(self.vpath) if i2 in si]

    def load_cf_(self, rci,cfq):
        '''
        '''

        if type(cfq) == type(()):
            xs = tuple(self.vpath_subset(cfq[1]))
            cf = cfq[0](*xs)

            # below method
            rci.load_var_cf(cf)
        else:
            rci.load_var_cf(cfq)

    def make_node(self,kwargz):
        '''
        instantiates an `RCInst` node using the argument
        sequence `kwargz`.
        Note: selectorIndices refer to values in `vpath`.

        :param kwargz: If index 0 is `r` (node uses reference values), then
                format is (`r`,rf,dm|(dm,selector indices),cf|(cf,selectorIndices),?dt?).
                If index 0 is `nr` (node does use reference values), then
                format is (`nr`,cf|(cf,selectorIndices),?dt?).
                
                Please see the description for `RCInst` for details on these values.
        :type kwargz: iterable
        '''

        assert kwargz[0] in ["r","r+","nr"]

        rci = RCInst()
        if kwargz[0] == "r":
            assert len(kwargz) in [4,5], "invalid length for kwargs"
            rci.set_reference_data(kwargz[1],kwargz[2])
            self.load_cf_(rci,kwargz[3])
            try: rci.load_var_dt(kwargz[4])
            except: pass

        elif kwargz[0] == "nr":
            assert len(kwargz) in [2,3], "invalid length for kwargs"
            self.load_cf_(rci,kwargz[1])
            try: rci.load_var_dt(kwargz[2])
            except: pass

        elif kwargz[0] == "r+":
            return -1

        rci.load_path()
        return rci

    def add_node_at(self, kwargz, index = -1):
        '''

        '''

        assert index >= -1, "invalid index"
        n = self.make_node(kwargz)
        if index == -1:
            self.s.append(n)
        else:
            self.s.insert(index,n)
        return -1

    def apply(self,v):
        '''
        main function of RChainHead; applies the composite function (full function path) onto v
        
        :param v: argument into chain function
        :type v: ?
        '''

        i = 0
        v_ = np.copy(v)
        self.vpath = [v_]
        
        if self.verbose:
            print("-- applying function on {}".format(v))

        while i < len(self.s):
            q = self.s[i]
            v_ = q.f(v_)
            if self.verbose:
                print("\t-- new value: {}".format(v_))

            self.vpath.append(v_)
            i += 1
        return v_

    def cross_check(self):
        return -1

    def merge(self):
        return -1

    def __next__(self):
        return -1

####----------------------------------------------------------

###### START: helper functions for next section

def boolies(v_):
    '''
    :return: is boolean vector all true?
    :rtype: bool
    '''

    return v_ == True

def column_selector(columns, flatten = False):

    def p(v):
        q = v[:,columns]
        if flatten: return q.flatten()
        return q
    return p

def vector_index_selector(indices):
    def p(v):
        return v[indices.astype('int')]
    return p

def vector_index_inverse_selector(v):
    def p(indices):
        return v[indices.astype('int')]
    return p


###### END: helper functions for next section

###### START: functions used for relevance zoom

'''
'''
def RCHF__point_in_bounds(b):
    kwargs = ['nr', lambda_pointinbounds, b]
    # f : v -> v::bool
    rc = RChainHead()
    rc.add_node_at(kwargs)
    return rc.apply

def hops_to_default_noise_range(h):
    return np.array([[(h ** -1) / 2.7, (h ** -1) / 2.3]])

#################################### start : ostracio && deletira

def hops_to_coverage_points__standard(k,h):
    """

    arguments:
    - k :=
    - h := hop value of SSI

    return:
    - matrix, dim (m,k), m the required number of points
    """

    z = np.zeros((k,))
    o = np.ones((k,))

    #
    partition = n_partition_for_bound(np.array([z,o]).T,h)

    # case: odd
    if h % 2:
        x = [i for i in range(h + 1) if i % 2]
    # case: even
    else:
        x = [i for i in range(h + 1) if not i % 2]
    return partition[x]

# TODO: test this.
def hops_to_coverage_points_in_bounds(parentBounds,bounds,h):

    k = bounds.shape[0]
    cp = hops_to_coverage_points__standard(k,h)

    if is_proper_bounds_vector(bounds):
        s = [point_on_bounds_by_ratio_vector(bounds,c) for c in cp]
    else:
        s = [point_on_improper_bounds_by_ratio_vector(\
            parentBounds,bounds,c) for c in cp]
    return np.array(s)

def coverage_ratio_to_distance(boundsEDistance, h,cr):
    '''
    given a coverage ratio `cr`, calculates its corresponding distance to the
    euclidean distance of a bounds `boundsEDistance`. 
    
    :param boundsEDistance: euclidean distance pertaining to a bounds
    :type boundsEDistance: float
    :param h: hop
    :type h: int|float
    :param cr: 0 <= x <= 1
    :type cr: float
    '''

    assert h >= 1.0, "invalid h"
    assert cr >= 0.0 and cr <= 1.0, "invalid cr"

    total = boundsEDistance / h
    return total * cr

#################################### end : ostracio && deletira


'''
'''
def RCHF__point_in_bounds_subvector_selector(b):
    def qf(xi):
        return operator.le(xi[1],b[xi[0],1]) and operator.ge(xi[1],b[xi[0],0])

    q2 = subvector_selector(qf,inputType = 2,outputType = 1)
    kwargs = ['nr', q2]
    rc = RChainHead()
    rc.add_node_at(kwargs)
    return rc.apply

from .poly_struct import *

def RCHF__ISPoly(x:'float',largs):
    """constructs a :class:`RChainHead` function that has as its first function
    a polynomial function represented by :class:`ISPoly` over float `x`. The
    remaining nodes of the :class:`RChainHead` instance are constructed by the
    sequence of arguments `largs` to produce a :class:`RChainHead` with 1+ nodes.
    
    :param x: value that single-variable polynomial applies over
    :type x: float
    :param largs: sequence of `kwargs` used by `RChainHead.make_node`
    """

    rc = RChainHead()

    isp = ISPoly(x)

    def qf(v):
        return isp.apply(v)

    kwargs = ['nr',qf]
    rc.add_node_at(kwargs)

    for a in largs:
        rc.add_node_at(a)
    return rc.apply

def RCHF___in_bounds(bounds0):
    '''
    non-referential class<RChainHead> instance that outputs the func for in bounds
    '''

    kwargs = ['nr', lambda_pointinbounds, bounds0]
    # f : v -> v::bool
    rc = RChainHead()
    rc.add_node_at(kwargs)

    # f : filter out True | False
    subvectorSelector = boolies
    ss = subvector_selector(subvectorSelector,2)
    kwargs = ['nr',ss]
    rc.add_node_at(kwargs)

    # f : get indices
    ss = column_selector([0],True)
    kwargs = ['nr',ss]
    rc.add_node_at(kwargs)

    # f : apply indices on reference
    kwargs = ['nr',(vector_index_inverse_selector,[0])]
    rc.add_node_at(kwargs)

    return rc.apply

def ffilter(v,f):
    '''
    filters out elements of vector `v` by boolean function `f` into
    two lists `TRUE` and `FALSE`.
    '''
    t,l = [],[]
    for v_ in v:
        if f(v_): t.append(v_)
        else: l.append(v_)

    return t,l

def rpmem_func(rf,rOp):
    '''
    using reference rf,
    odd_multiply
    even

    [0] multiplier of even indices
    [1] multiplier of odd indices

    recent memory
    * + - => -
    * - - => -
    * - + => +
    * + + => +

    past memory
    * + - => +
    * - - => -
    * - + => -
    * + + => +
    '''

    rfo0,rfo1 = ffilter(rf,lambda i: i % 2)
    r1 = np.product(rfo1) if rOp else np.product(rfo0)

    def p(v):
        v0,v1 = ffilter(v,lambda i: i % 2)
        r2 = np.product(v1) if rOp else np.product(v0)
        return int(r2) % 2

    # try swapping them

    return p


def is_valid_pm(pm):
    """
    is permutation map valid?
    """
    assert pm.shape[1] == 2, "invalid pm shape"
    tf1 = len(np.unique(pm[:,0])) == pm.shape[0]
    tf2 = len(np.unique(pm[:,1])) == pm.shape[0]
    return tf1 and tf2

def is_proper_pm(pm):
    """
    is permutation map proper?

    "proper" := valid and all valids in range [0,n-1]
    """
    s = is_valid_pm(pm)
    if not s: return s
    s1 = min(pm[:,0]) == 0 and max(pm[:,0])  == pm.shape[0]
    s2 = min(pm[:,1]) == 0 and max(pm[:,1])  == pm.shape[0]
    return s1 and s2

# a version of rp mem that uses a permutation map
# TODO
def rpmem_func__pm(rfs,pm):
    """
    the original func<rpmem_func> operates on the binary choice
    """
    assert is_proper_pm(pm), "[0] invalid permutation map"
    assert pm.shape[0] == len(rfs) + 1,"[1] invalid permutation map"
    return -1

def is_valid_subset_sequence(s,n):
    q = []
    for s_ in s:
        q.extend(list(s))

    tf0 = len(q)
    q = np.unique(q)
    tf1 = len(q)
    if tf0 != tf1: return False

    m0,m1 = min(q),max(q)
    return m0 == 0 and m1 == n - 1

###### END: functions used for relevance zoom


###### a sample RCH w/ update functionality

def sample_rch_1_with_update(parentBounds, bounds, h, coverageRatio):
    '''
vector -> e.d. vector -> (ed in bounds):bool
    '''
    def dm(rp,v):
        #print("LENGO: ",len(rp))
        return np.array([euclidean_point_distance(v,rp_) for rp_ in rp])

    def cf(ds,dt_):
        return np.any(ds <= dt_)

    def update_dt_function(parentBounds,bounds,h,coverageRatio):
        return (euclidean_point_distance_of_bounds(parentBounds,bounds) / h)\
                    * coverageRatio

    rch = RChainHead()
    # add the node
    rf = hops_to_coverage_points_in_bounds(parentBounds,bounds,h)
    dm = dm
    cf = cf
    ed = euclidean_point_distance_of_bounds(parentBounds,bounds)

    # WRONG
    dt = coverage_ratio_to_distance(ed,float(h),coverageRatio)

    kwargs = ['r',rf,dm,cf,dt]
    rch.add_node_at(kwargs)

    # add update functionality
    rch.s[0].updateFunc = {'rf': hops_to_coverage_points_in_bounds,\
            'dt': update_dt_function}
    rch.s[0].updatePath = {'rf': [0,1,2],'dt':[0,1,2,3]}
    rch.updatePath = {0: [0,1,2,3]}
    return rch

def sample_rch_2_with_update(parentBounds, bounds):
    """
    one node; updates `dt` every batch with new `bounds` parameter.

    For each point, outputs true if it is in 0-20 percentile or 80-100 percentile
    of area in `bounds`. 
    """

    def activation_range(parentBounds,bounds):
        v = np.ones((parentBounds.shape[0],)) * 0.2
        b1s = np.copy(bounds[:,0])
        b1e = point_on_improper_bounds_by_ratio_vector(parentBounds,bounds,v)

        v = np.ones((parentBounds.shape[0],)) * 0.8
        b2s = point_on_improper_bounds_by_ratio_vector(parentBounds,bounds,v)
        b2e = np.copy(bounds[:,1])

        B1 = np.vstack((b1s,b1e)).T
        B2 = np.vstack((b2s,b2e)).T
        return B1,B2

    def update_dt_function(parentBounds,bounds):
        b1,b2 = activation_range(parentBounds,bounds)
        return (np.copy(parentBounds),b1,b2)

    """
    r := parentBounds,b1,b2
    """
    def cf(p,r):
        if point_in_improper_bounds(r[0],r[1],p):
            return True
        if point_in_improper_bounds(r[0],r[2],p):
            return True
        return False

    rch = RChainHead()
    dt = update_dt_function(parentBounds,bounds)
    kwargs = ['nr',cf,dt]
    rch.add_node_at(kwargs)

    # add update functionality
    rch.s[0].updateFunc = {'dt': update_dt_function}
    rch.s[0].updatePath = {'dt':[0,1]}
    rch.updatePath = {0: [0,1]}

    return rch

def sample_rch_3_with_update(modulo,updateAdder,updateModulo,targetValueRange):
    '''
    class<RChainHead> instance has one node that updates reference values and deciding threshold
    using function<vector_summation_modulo>. 

    use simple bounds and selector indices.

    NOTE: class<RChainHead> is not compatible with class<ResplattingSearchSpaceIterator> and is used
    to test accuracy and capability of class<RChainHead>.  
    '''

    assert targetValueRange[0] <= targetValueRange[1], "invalid targetValueRange"
    
    
    def cf(x,t):
        return x >= t[0] and x <= t[1]
    
    """
    def cf(x): 
        return x
    """
    rch = RChainHead(False)

    # declare the node
    kwargs = ['r',modulo,vector_summation_modulo,cf,targetValueRange]
    #kwargs = ['r',modulo,vector_summation_modulo,cf]

    rch.add_node_at(kwargs)

    # add the update function for argument `modulo`; 
    # update function does not require additional variable
    update_dt_function = update_modulo_function(updateAdder,updateModulo)
    rch.s[0].updateFunc = {'rf': update_dt_function}
    rch.s[0].updatePath = {'rf':[0]}
    rch.updatePath = {0: [0]}
    rch.load_update_vars([modulo]) 

    return rch

def sample_rch_constant_mapper(c):
    '''
    one node; maps any vector to <c> vector. 
    '''

    def l(v):
        x = np.ones((len(v),))
        return x * c

    kwargs = ['nr',l]
    rc = RChainHead()
    rc.add_node_at(kwargs)
    return rc

def sample_rch_blind_accept():
    '''
    one node; deciding + non-referential, outputs true for all vectors.
    '''

    def accept(v,i):
        return type(v) == type(i)

    rc = RChainHead()
    idv = np.ones(10)
    kwargz = ["nr",accept,idv]
    rc.add_node_at(kwargz)
    return rc

def idv(v):
    return v

def sample_rch_hop_counts_scheme_type_1(parentBound,bound,hop,cf=idv):
    '''
    one node; requires a parent bound,bound,and hop as update values
    for argument `p` (vector point).
    '''

    def f(r,v):
        return bounded_point_to_hop_counts(r[0],r[1],v,r[2])
    
    def idrf(x1,x2,x3):
        return (x1,x2,x3)

    rch = RChainHead()
    kwargs = ['r',(parentBound,bound,hop),f,cf]
    rch.add_node_at(kwargs)

    rch.s[0].updateFunc = {'rf': idrf} 
    rch.s[0].updatePath = {'rf': [0,1,2]}
    rch.updatePath = {0: [0,1,2]}
    return rch

def index_map_summation_scheme_type_1(m2,m):
    '''
    calculates a vector of indices for v based on a summation scheme.
    '''
    assert m > m2, "modulo has to be greater than v"

    def indexia(v):
        vx_ = []
        c = 1
        l = len(v) + 1
        s = np.sum(v)
        s = int(s * 10 ** decimal_places_of_float(s))
        while c < l:
            s2 = (s * c) % m
            if s2 >= l - 1: break
            vx_.append(s2)
            c += 1
        return np.array(vx_)
    return indexia

def subvector_selector_summation_scheme_type_1(m2,m):
    qf = index_map_summation_scheme_type_1(m2,m)

    def f(v):
        iv = qf(deepcopy(v))
        return np.array([v[i] for i in iv])
    return f


def sample_rch_hop_counts_scheme_type_2(parentBound,bound,hop,m2,cf=idv):
    '''
    one node; requires a parent bound,bound,and hop as update values
    for argument `p` (vector point).
    '''

    qf = subvector_selector_summation_scheme_type_1(bound.shape[0],m2)
    
    def f(r,v):
        #return qf(bounded_point_to_hop_counts(r[0],r[1],v,r[2]))
        return qf(v) 
    
    def idrf(x1,x2,x3):
        return (x1,x2,x3)

    rch = RChainHead()
    kwargs = ['r',(parentBound,bound,hop),f,cf]
    rch.add_node_at(kwargs)

    rch.s[0].updateFunc = {'rf': idrf} 
    rch.s[0].updatePath = {'rf': [0,1,2]}
    rch.updatePath = {0: [0,1,2]}
    return rch


def binary_labelling_scheme_1(v,m = 7,m2 = 4):
    '''
    outputs a vector v' of equal length to v.

    '''
    if len(v) == 0: return np.array([])
    f = decimal_order_of_vector(v) 
    v = [int(v_ * 10 ** f) for v_ in v]
    return np.array([1. if v_ % m >= m2 else 0. for v_ in v])

def sample_rch_binary_labelling_scheme_1():
    '''
    uses default parameters `m` and `m2` of method<binary_labelling_scheme_1>
    '''
    rch = RChainHead()
    kwargs = ['nr',binary_labelling_scheme_1]
    rch.add_node_at(kwargs)
    return rch