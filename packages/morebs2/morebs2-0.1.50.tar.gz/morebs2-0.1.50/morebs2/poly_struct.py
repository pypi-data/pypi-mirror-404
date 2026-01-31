from .poly_interpolation import *
from .numerical_extras import fractional_add,fractional_mul,reduce_fraction
from copy import deepcopy
import random

def merge_duplicates_cevector(v):
    """merges elements of a (coefficient,exponent) vector
    so that there are no duplicate exponents
    """
    d = {}
    for v_ in v:
        x = v_[0]
        if v_[1] in d:
            x += d[v_[1]]
            if x == 0:
                del d[v_[1]]
            else:
                d[v_[1]] = x
        else:
            d[v_[1]] = x
    return d

def merge_duplicates_ceqvector(v):
    d = {}
    for v_ in v:
        x1 = deepcopy(v_) 
        if v_[2] in d:
            x1 = (deepcopy(d[v_[2]]), deepcopy(v_[:2]))
            x1 = fractional_add(x1[0],x1[1])
            if x1[0] == 0:
                del d[v_[2]]
                continue
        d[v_[2]] = x1  
    return d

class CEQPoly:

    def __init__(self,v):
        if len(v) > 0:
            assert v.shape[1] == 3, "invalid"
        assert len(np.unique(v[:,2])) == len(v), "duplicate exponent in c-e format"
        indexOrder = np.argsort(v[:,2])[::-1]
        v = v[indexOrder]
        self.v = []
        for v_ in v:
            if v_[0] == 0: continue
            self.v.append(v_)
        self.v = np.array(self.v)
    
    def __str__(self):
        s = ""
        for y_ in self.v:
            s += " +" if y_[0] >= 0 else " -"
            c = "(" + str(abs(y_[0])) + "/" + str(y_[1]) + ")"
            s += " {}x^{}".format(c,y_[2])
        if len(s) == 0:
            return s
        return s[2:]

    def apply(self,x):
        s = 0.0
        for v_ in self.v:
            s += (v_[0] /v_[1] * x ** v_[1])
        return s

    def __add__(self,s):
        v1 = deepcopy(self.v)
        v2 = deepcopy(s.v)

        # case: one of the additives is 0.
        if len(v1) == 0:
            return deepcopy(s)
        if len(v2) == 0:
            return deepcopy(self)
        v2 = list(v2)
        v3 = []

        for v in v1:
            index = -1
            for (i,vx) in enumerate(v2):
                if round(v[2],5) == round(vx[2],5):
                    index = i
                    break

            if index == -1:
                v3.append(v)
            else:
                s1,s2 = fractional_add((v[0],v[1]),(v2[0],v2[1]))
                v3.append((s1,s2,v[2]))
                v2.pop(index) 

        # add the remainder of v2
        for v in v2:
            v3.append(v)
        return CEQPoly(np.array(v3))

    def __mul__(self,s):
        if type(s) in {int,float,complex,tuple}:
            return self.mul_s(s)

        ecv = []
        for v_ in self.v:
            for s_ in s.v:
                m = fractional_mul((v_[0],v_[1]),(s_[0],s_[1]))
                ecv.append((m[0],m[1],v_[2] + s_[2]))
        d = merge_duplicates_ceqvector(ecv)
        return CEQPoly.from_dict(d)

    # TODO: caution with imaginary numbers.
    def mul_s(self,s):
        v2 = []

        for v_ in self.v:
            if type(s) == tuple:
                m = fractional_mul((v_[0],v_[1]),(s[0],s[1]))
            else:
                m = reduce_fraction((v_[0] * s,v_[1]))
            v2.append((m[0],m[1],v_[2]))
        return CEQPoly(np.array(v2))

    @staticmethod
    def from_dict(d):
        '''
        dictionary is in e-c format.
        '''
        x = np.array([(v[0],v[1],k) for k,v in d.items()])
        return CEQPoly(x)

class CEPoly:
    """polynomial represented in coefficient-exponent form. 
    
    :param v: vector of values, length l -1 is power, index 0 is greatest power
    """
    
    def __init__(self,v):
        if len(v) > 0:
            assert v.shape[1] == 2, "invalid"
        assert len(np.unique(v[:,1])) == len(v), "duplicate exponent in c-e format"
        indexOrder = np.argsort(v[:,1])[::-1]
        v = v[indexOrder]
        self.v = []
        for v_ in v:
            if v_[0] == 0: continue
            self.v.append(v_)
        self.v = np.array(self.v) 

    def __str__(self):
        s = ""
        for y_ in self.v:
            s += " +" if y_[0] >= 0 else " "
            c = str(y_[0]) if type(y_[0]) != complex else "(" + str(y_[0]) + ")"
            s += " {}x^{}".format(c,y_[1])
        if len(s) == 0:
            return s
        return s[2:]

    def apply(self,x):
        s = 0.0
        for v_ in self.v:
            s += (v_[0] * x ** v_[1])
        return s

    def __sub__(self,s):
        return self + (s * -1)

    def __add__(self,s):
        v1 = deepcopy(self.v)
        v2 = deepcopy(s.v)

        # case: one of the additives is 0.
        if len(v1) == 0:
            return deepcopy(s)
        if len(v2) == 0:
            return deepcopy(self)
        v2 = list(v2)
        v3 = []

        for v in v1:
            index = -1
            for (i,vx) in enumerate(v2):
                if round(v[1],5) == round(vx[1],5):
                    index = i
                    break

            if index == -1:
                v3.append(v)
            else:
                v3.append((v[0] + v2[i][0],v[1]))
                v2.pop(index) 

        # add the remainder of v2
        for v in v2:
            v3.append(v)
        return CEPoly(np.array(v3))

    '''
    singleton multiplication
    '''
    def __mul__(self,s):
        if type(s) in {int,float,complex}:
            return self.mul_s(s)

        ecv = []
        for v_ in self.v:
            for s_ in s.v:
                ecv.append((v_[0] * s_[0],v_[1] + s_[1]))
        d = merge_duplicates_cevector(ecv)
        return CEPoly.from_dict(d)

    
    def __eq__(self,s):
        return str(self - s) == "" 
    
    def mul_s(self,s):
        v2 = deepcopy(self.v)
        v2 = np.array([(v_[0] * s,v_[1]) for v_ in v2])
        return CEPoly(v2)

    @staticmethod
    def from_dict(d):
        '''
        dictionary is in e-c format.
        '''
        x = np.array([(v,k) for k,v in d.items()])
        return CEPoly(x)

    def to_dict(self):
        x = {}
        for v_ in self.v:
            x[v_[1]] = v_[0]
        return x

    def c_of_p(self,p):
        '''
        coefficient of power
        '''
        for v_ in self.v:
            if round(v_[1] - p,5) == 0.:
                return v_[0]
        return None

    def exp_bounds(self):
        '''
        exponent bounds
        '''
        return (self.v[0,1],self.v[-1,1])

    def min_right_exp(self,distance = 1):
        '''
        '''
        l = len(self.v) - 1

        # case: polynomial length is 1.
        if l == 0: return None

        prev = deepcopy(self.v[0])
        for i in range(1,l):
            if prev[1] - self.v[i,1] > distance:
                return prev[1]
            prev = deepcopy(self.v[i])
        return None

    def max_left_exp(self,distance = 1):
        '''
        '''
        l = len(self.v) - 1

        # case: polynomial length is 1.
        if l == 0: return None

        prev = deepcopy(self.v[l])
        for i in range(l - 1,-1,-1):
            if prev[1] + distance < self.v[i,1]:
                return prev[1]
            prev = deepcopy(self.v[i])        
        return None

    def exponential_subtract(self,p2):
        return set(self.v[:,1]) - set(p2.v[:,1])

class SPoly:
    """polynomial operator over 1 float variable;
    data structure uses vector-index notation.

    :param v: vector of values, length l -1 is power, index 0 is greatest power
    """

    def __init__(self,v):
        assert is_vector(v), "invalid vector"

        i = 0
        for (j,v_) in enumerate(v):
            if v_ != 0:
                break
            i = j + 1

        self.v = v[i:]

    def __str__(self):
        y = self.ce_notation()
        s = ""
        for y_ in y:
            s += " +" if y_[0] >= 0 else " "
            s += " {}x^{}".format(y_[0],y_[1])
        if len(s) == 0:
            return s
        return s[2:]

    def apply(self,x):
        s = 0.0
        l = len(self.v) - 1
        for v_ in self.v:
            s += (v_ * x ** l)
            l -= 1
        return s

    def __add__(self,s):
        v1 = deepcopy(self.v)
        v2 = deepcopy(s.v)

        # make the two vectors equal in length by adding 0's at
        # the beginning of the shorter one 
        l = len(v1) - len(v2)
        
        # case: add to v1
        if l < 0:
            v3 = np.zeros(-1 * l)
            v1 = np.hstack((v3,v1))
        else:
            v3 = np.zeros(l)
            v2 = np.hstack((v3,v2))
        return SPoly(v1 + v2)

    def __sub__(self,s):
        return self + (s * -1)

    def __mul__(self,s):
        if type(s) in [int,float,complex]:
            return SPoly(s * self.v) 

        l2 = len(self.v) -1 + len(s.v)
        v = np.zeros(l2)
        v2 = np.zeros(l2)

        le1 = len(self.v) - 1
        le2 = len(s.v) - 1

        for (i,x) in enumerate(self.v):
            v3 = deepcopy(v2)
            e1 = le1 - i
            for (j,x2) in enumerate(s.v):
                x3 = x * x2
                e2 = le2 - j
                e3 = e1 + e2
                v3[l2 - e3 - 1] = x3
            v = v + v3
        return SPoly(v) 

    def vector_index_notation(self):
        return deepcopy(self.v)

    def ce_notation(self):
        '''
        coefficient-exponent notation
        '''
        p = []
        l = len(self.v) - 1 

        for (i,v_) in enumerate(self.v):
            if v_ == 0.:
                continue
            p.append((v_,l - i))
        return np.array(p)

    @staticmethod
    def from_ce_notation(v):
        # get the max exponent
        q = max([v_[1] for v_ in v])
        q2 = np.zeros(q + 1)

        for v_ in v:
            q2[q - v_[1] - 1] = v_[0]
        return SPoly(q2)

class ISPoly:
    """
    inversion of SPoly
    """

    def __init__(self,x):
        """
        v := vector of values, length l -1 is power, index 0 is greatest power
        """
        assert type(x) == float, "invalid x"
        self.x = x

    def apply(self,v):
        q = SPoly(v)
        return q.apply(self.x)

class RandomPolyGenerator:
    """generates a random polynomial, an expression represented
    by :class:`SPoly` that has coefficients in the range
    `coefficientRange` with a NON-ZERO 

                `cx^maxExp; c is a coefficient.`
                
    The rest of the values have a probability of `nullPr`
    for being zero.

    :param rsf: seed object, should have the two functions 
                (`randrange(min int,max int)` => int) and (`random()` => x in [0,1])
    :type rsf: seed-like object
    :param coefficientRange:
    :type coefficientRange:
    :param maxExp:
    :type maxExp:
    :param nullPr:
    :type nullPr:
    """

    def __init__(self,rsf,coefficientRange,maxExp,nullPr):
        assert type(coefficientRange[0]) == int and type(coefficientRange[1]) == int, "invalid coefficient range,cond.1"
        assert coefficientRange[1] >= coefficientRange[0], "invalid coefficient range,cond.2"
        assert coefficientRange[1] != coefficientRange[0],"invalid coefficient range,cond.3"
        assert type(nullPr) == float and nullPr >= 0. and nullPr <= 1., "invalid null probability"

        self.rsf = rsf
        self.coefficientRange = coefficientRange
        self.maxExp = maxExp
        self.nullPr = nullPr

    def output(self):
        # non-zero coefficient for the first 
        p = np.zeros(self.maxExp + 1)
        x = 0

        while x == 0:
            x = self.rsf.randrange(self.coefficientRange[0],self.coefficientRange[1])
            p[0] = x
        
        l = len(p)

        # for the remainder, random chance of non-zero value
        for j in range(1,l):
            if self.rsf.random() > self.nullPr:
                x = 0
                while x == 0:
                    x = self.rsf.randrange(self.coefficientRange[0],self.coefficientRange[1])
                    p[j] = x
        return SPoly(p)
        