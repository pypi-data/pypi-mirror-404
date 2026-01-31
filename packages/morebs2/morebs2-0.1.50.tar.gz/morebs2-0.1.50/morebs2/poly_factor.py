from .poly_struct import *
from .numerical_extras import *

# TODO: negative exponents
def int_split(ex,ratio):
    '''
    splits an integer into two values;
    the magnitude of the first value is determined
    by the float `ratio`
    '''

    # case: 0
    if ex == 0: return [0,0]
    p1 = int(round(ex * ratio,0))
    return (p1, ex - p1)

def modify_candidate_exponent(p1,modDirection):
    '''
    :param modDirection: [exponent,delta]
    '''
    v = deepcopy(p1.v)
    index = -1
    for (i,v_) in enumerate(v):
        if round(v_[1],5) == round(modDirection[0],5):
            index = i
            break
    assert index != -1, "invalid exponent for modification"
    v[index,1] += modDirection[1]
    return 

def remainder_to_target(p1,p2,P,targetPIndex):
    '''
    '''
    q = P.v[targetPIndex,1]
    l = valid_existing_candidate_elements_for_exponent(p1,p2,q)
    c = multiple_pairs_to_CEPoly(p1,p2,l)
    return P.v[targetPIndex,0] - c.v[0,0]

def valid_existing_candidate_elements_for_exponent(p1,p2,targetExp):
    '''
    gets all pairs of elements (e1,e2) such that e1 in `p1`,e2 in `p2`
    and pow(e1 * e2) = `targetExp`. 

    :return: list<(index of p1 multiple,index of p2 multiple)>
    '''

    a = []
    # get all possible
    for (i,v1) in enumerate(p1.v):
        for (j,v2) in enumerate(p2.v):
            if round(v1[1] + v2[1] - targetExp,5) == 0.:
                a.append((i,j))
    return a

def multiple_pairs_to_CEPoly(p1,p2,iv):
    '''
    '''

    v = []
    for x in iv:
        pe1,pe2 = p1.v[x[0]],p2.v[x[1]]
        sx = (pe1[0] * pe2[0],pe1[1] + pe2[1])
        v.append(sx)
    return CEPoly.from_dict(merge_duplicates_cevector(v))

def possible_new_elements_of_factor_for_exponent(f,p,feb,peb,P,t):
    '''
    determines the possible exponents of a new element of factor `f`
    to produce a polynomial P' with 
                `power_sequence(P') subset_in power_sequence(P')`.

    Possible exponents for `f` that when multiplied with `p` takes a lower
    priority than 

    :param f: polynomial factor to add a new element to
    :param p: non-mutable factor p to solve for `fp=P`
    :param feb: exponential bounds for factor f
    :param peb: exponential bounds for factor p
    :param P: polynomial to be factored by `f`
    :param t: int|float, target exponent
    '''

    c1 = []
    fp = set([vp[1] for vp in f.v])
    sp = set([vp[1] for vp in P.v])

    for x in range(int(feb[0]), int(feb[1]) + 1):
        # case: x already in f
        if x in fp:
            continue

        # case:
        x2 = t - x

        # case: needed x2 falls out of the exp. bounds of p1
        if x2 > peb[1] or x2 < peb[0]:
            continue

        # determine if multiplying exponent x2 with any in p2 produces an
        # exponent not in P
        s = set([x + p.v[i,1] for i in range(len(p.v))])

        # case: produces exponent not in P, possibility has low priority
        if len(s - sp) != 0:
            c1.append(x)
            continue
        else:
            c1.insert(0,x)
    return c1

def select_median_in_sequence(s,m=0.5):
    assert m >= 0. and m <= 1., "invalid median ratio"
    l = int((len(s) - 1) * m)
    return s.pop(l)

def median_sort(s,m= 0.5):
    s_ = []
    while len(s) > 0:
        s_.append(select_median_in_sequence(s,m))
    return s_

# TODO: rational numbers
# TODO: make sure bounds for multiple is accurate
def decisive_guess_sequence_experimental(c,complementFactor,remainingInsertions):
    if remainingInsertions == 0:
        if c % complementFactor:
            return [], False
        return [int(c / complementFactor)], True

    x = int(c / complementFactor)
    return [i for i in range(1,x + 1)], True

def decisive_guess_sequence(c,complementFactor):
    x = int(c / complementFactor)
    d = -1 if x >= 0 else 1
    return [i for i in range(x,0,d)] 

# TODO: negative exponents
class PolyFactorEst:
    '''
    '''

    def __init__(self,p,verbose=False):
        assert type(p) == CEPoly, "invalid polynomial"
        self.p = p
        self.plabels = set()
        self.p1,self.p2 = None,None
        self.p1eb,self.p2eb = None,None

        self.initial_bounds_multiples = []
        self.ibm_cache = []

        self.cache = []
        self.tmpCache = []
        self.guessCount = 0
        self.elimCount = 0 

        self.pindex = None
        self.f1,self.f2 = None,None

        self.stat = True
        self.verbose = verbose
        return

    def guess(self,median=0.5):
        while self.stat: 
            self.guess_iteration()
            self.set_factor_guess() 

    def guess_iteration(self):
        while self.guess_insertion():
            continue
        return

    def guess_insertion(self):

        if not self.stat: return False

        if type(self.f1) != type(None):
            if self.verbose: print("solved")
            return False

        if len(self.cache) == 0:
            if self.verbose: print("not solved")
            return False

        # pop element from cache
        (self.p1,self.p2) = self.cache.pop(0)
        (a1,a2) = self.analyze_factor_pair()
        if self.verbose: print("analysis: {} {}".format(a1,a2))

        # case: invalid factor-pair guess
        if not a2:
            self.elimCount += 1
            return True

        # case: no more remaining non-null powers for P;
        #       check for .
        if a1 == -1:
            if str(self.p - (self.p1 * self.p2)) == '':
                self.f1 = deepcopy(self.p1)
                self.f2 = deepcopy(self.p2)
            return True

        x = self.guess_insertion_candidates(1,a1)
        if x == 0:
            self.guess_insertion_candidates(0,a1)
        if self.verbose:
            print("UDPATE")
            for t in self.tmpCache:
                print(str(t[0]))
                print(str(t[1]))
                print("-@-@-@-@-@")
            print("============")
        self.guessCount += len(self.tmpCache)
        self.cache.extend(self.tmpCache)
        self.tmpCache = []
        return True

    def set_exponential_bounds(self,p1eb,p2eb):
        '''
        used in initial hypothesis
        '''
        assert type(p1eb) is tuple and len(p1eb) == 2 and p1eb[0] <= p1eb[1], "polynomial 1 exponential bounds"
        assert type(p2eb) is tuple and len(p2eb) == 2 and p2eb[0] <= p2eb[1], "polynomial 2 exponential bounds"
        self.p1eb = p1eb
        self.p2eb = p2eb

    def initial_bounds_hypothesis(self,median=0.5):
        # case: P has length 1
        if len(self.p.v) < 2:
            #self.p.v[0]
            return

        # case: P has length >= 2
            # choose the multiples
        m = median_sort(all_multiple_pairs(self.p.v[0,0]),median)
        m2 = median_sort(all_multiple_pairs(self.p.v[-1,0]),median)

        self.ibm_cache = [None,[]]
        self.initial_bounds_multiples = [m,deepcopy(m2)]
        self.set_factor_guess()

        if self.p1 * self.p2 == self.p:
            self.f1,self.f2 = self.p1,self.p2
            self.stat = False

    def set_factor_guess(self):
        '''
        declares each 
        '''
        if len(self.initial_bounds_multiples[0]) == 0:
            self.stat = False
            return False

        # case: second multiple-pair candidate list exhausted 
        if len(self.ibm_cache[1]) == 0:
            self.ibm_cache[0] = self.initial_bounds_multiples[0].pop(0)
            self.ibm_cache[1] = deepcopy(self.initial_bounds_multiples[1])

        mdn2 = self.ibm_cache[1].pop(0)
        x1 = np.array([(deepcopy(self.ibm_cache[0][0]),self.p1eb[1]),(mdn2[0],self.p1eb[0])])
        x2 = np.array([(deepcopy(self.ibm_cache[0][1]),self.p2eb[1]),(mdn2[1],self.p2eb[0])])
        self.p1 = CEPoly(x1)
        self.p2 = CEPoly(x2)
        self.cache.append((deepcopy(self.p1),deepcopy(self.p2)))
        return True

    def guess_insertion_candidates(self,pid,pindex):
        ex = self.p.v[pindex,1]
        (exp1,coeff) = self.new_max_exponent_w_complement_for_factor(pid,ex)
        
        if coeff == None:
            return 0

        # guess the possible coefficients
        d = decisive_guess_sequence(deepcopy(self.p.v[pindex,0]),coeff)
        
        # add candidates to tmp cache
        q = [deepcopy(self.p1),deepcopy(self.p2)]
        for x in d:
            # make the CEPoly
            
            px = CEPoly.from_dict({exp1: x})
            
            # add the CEPoly
            qx = deepcopy(q)
            qx[(pid + 1) % 2] = qx[(pid + 1) % 2] + px
            self.tmpCache.append(qx)
        return len(d)
    
    def new_max_exponent_w_complement_for_factor(self,pid,te):
        '''
        :param pid:
        :param te:
        :return: (exponent for factor `pid`, coefficient of complement)
        '''
        new_elements = possible_new_elements_of_factor_for_exponent(self.p1,self.p2,self.p1eb,self.p2eb,self.p,te)\
                if pid else possible_new_elements_of_factor_for_exponent(self.p2,self.p1,self.p2eb,self.p1eb,self.p,te)

        # iterate through and get the element with the 
        for n in new_elements:
            n2 = te - n
            c = self.p2.c_of_p(n2) if pid else self.p1.c_of_p(n2)
            if c != None:
                return (n,c)
        return (None,None)

    def analyze_factor_pair(self):
        '''
        perform analysis of p1 and p2. 

                - First output:
        Determine the first element from the max in `P` that requires
        insertions.

                - Second output: 
        If `p1 * p2` produces a polynomial with exponents that parent 
        polynomial `P` does not own, and there does not exist possible
        new insertions into either `p1` and `p2` that can cancel out 
        the excess exponents, output `False`. Otherwise, `True`. 
        '''
        ###
        #print("analyzing")
        #print("P1: {}",str(self.p1))
        #print("P2: {}",str(self.p2))
        #print("----------------------")
        ###

        if not self.excess_element_analysis():
            return None,False

        if not self.unequal_element_analysis():
            return None,False

        px = self.p1 * self.p2
        for (i,q) in enumerate(self.p.v):
            c2 = px.c_of_p(q[1])
            if c2 == None: c2 = 0.

            if round(q[0] - c2,5) != 0.:
                return (i,True)
        return -1,True

    def excess_element_analysis(self):
        es = (self.p1 * self.p2).exponential_subtract(self.p)
        for s in es:
            # possible elements 
            q1 = len(possible_new_elements_of_factor_for_exponent(self.p1,self.p2,self.p1eb,self.p2eb,self.p,s))
            q2 = len(possible_new_elements_of_factor_for_exponent(self.p2,self.p1,self.p2eb,self.p1eb,self.p,s))
            if q1 + q2 == 0: 
                return False
        return True

    def unequal_element_analysis(self):
        p3 = self.p1 * self.p2
        exp = []
        for v_ in p3.v:
            c = self.p.c_of_p(v_[1])
            if c - v_[0] != 0.:
                exp.append(v_[1])

        for s in exp:
            q1 = len(possible_new_elements_of_factor_for_exponent(self.p1,self.p2,self.p1eb,self.p2eb,self.p,s))
            q2 = len(possible_new_elements_of_factor_for_exponent(self.p2,self.p1,self.p2eb,self.p1eb,self.p,s))
            if q1 + q2 == 0:
                return False
        return True

    def check_valid_guess(self):
        return -1

    def poly_type(self):
        self.plabels = set()
        for x in self.p.v:
            # no more searching needed.
            if self.plabels == {complex,"q"}: break

            if type(x) == complex:
                self.plabels |= {complex}
            if int(x) != x:
                self.plabels |= {"q"}
        return