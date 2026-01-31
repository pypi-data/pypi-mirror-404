
'''
2 and 2 fit: various fit-formulae between two points
            in a 2-d space. 
'''
from .distributions import *
from .line import *
from .matrix_methods import is_2dmatrix
from copy import deepcopy

class Fit22:

    def __init__(self,ps,direction=[0,1]):
        assert ps.shape == (2,2)
        assert len(direction) == 2 and set(direction) == {0,1}, "invalid direction"
        self.ps = ps
        self.direction = direction
        assert self.ps[self.direction[1],1] > self.ps[self.direction[0],1], "invalid y's"
        self.f = None

class LogFit22(Fit22):
    '''
    structure fits a 
    '''

    def __init__(self,ps,direction=[0,1]):
        super().__init__(ps,direction)
        self.f = self.fit() 
        self.g = self.yfit()

    def fit(self):

        def f(x):
            # ratio of x on x-span
            r1 = abs(x - self.ps[self.direction[0],0]) / abs(self.ps[1,0] - self.ps[0,0])
            real = log(r1 * 9. + 1.) / log(10.)
            return self.ps[self.direction[0],1] + real * abs(self.ps[0,1] - self.ps[1,1])    
        return f

    def yfit(self):

        def g(y):
            p = log(10) * (y - self.ps[self.direction[0],1]) / (abs(self.ps[self.direction[1],1] - self.ps[self.direction[0],1]))
            ep = (e ** p - 1) / 9
            r = ep * abs(self.ps[1,0] - self.ps[0,0])
            x1 = np.round(self.ps[self.direction[0],0] - r,5)
            x2 = np.round(self.ps[self.direction[0],0] + r,5)

            if x1 >= min(self.ps[:,0]) and x1 <= max(self.ps[:,0]):
                return x1

            if x2 >= min(self.ps[:,0]) and x2 <= max(self.ps[:,0]):
                return x2
            raise ValueError("invalid y-input") 

        return g

# case 1
'''
lf22 = LogFit22(np.array([[30.,12.],[60.,80.]]))
function_to_2dplot(generate_2d_data_from_function,\
    lf22.f,[30.,60.],0.1,())
'''

# case 2
'''
lf22 = LogFit22(np.array([[0.,0.],[1.,1.]]))
function_to_2dplot(generate_2d_data_from_function,\
    lf22.f,[0.,1.],0.1,())
'''

# case 3
'''
lf22 = LogFit22(np.array([[60.,12.],[30.,80.]]))
function_to_2dplot(generate_2d_data_from_function,\
    lf22.f,[30.,60.],0.1,())
'''

# case 4
"""
lf22 = LogFit22(np.array([[60.,80.],[30.,12.]]),direction=[1,0])
function_to_2dplot(generate_2d_data_from_function,\
    lf22.f,[30.,60.],0.1,())
"""

class Exp2Fit22(Fit22):
    '''
    structure fits a 
    '''

    def __init__(self,ps,direction=[0,1]):
        super().__init__(ps,direction)
        self.f = self.fit() 
        self.g = self.yfit() 

    def fit(self):

        def f(x):
            # ratio of x on x-span
            r1 = abs(x - self.ps[self.direction[0],0]) / abs(self.ps[1,0] - self.ps[0,0])
            real = r1 ** 2
            return self.ps[self.direction[0],1] + real * abs(self.ps[0,1] - self.ps[1,1])    
        return f

    def yfit(self):

        def g(y):
            m1 = (y - self.ps[self.direction[0],1]) / abs(self.ps[self.direction[0],1] - self.ps[self.direction[1],1])
            m2 = (self.ps[self.direction[0],0] - self.ps[self.direction[1],0]) ** 2
            m = sqrt(m1 * m2)

            x1 = round(self.ps[self.direction[0],0]  + m,5)
            x2 = round(self.ps[self.direction[0],0] - m ,5)

            if x1 >= min(self.ps[:,0]) and x1 <= max(self.ps[:,0]):
                return x1

            if x2 >= min(self.ps[:,0]) and x2 <= max(self.ps[:,0]):
                return x2
            raise ValueError("invalid y-input") 
            
        return g

# case 1
'''
lf22 = Exp2Fit22(np.array([[60.,80.],[30.,12.]]),direction=[1,0])
function_to_2dplot(generate_2d_data_from_function,\
    lf22.f,[30.,60.],0.1,())
'''
#########

class DCurve:

    def __init__(self,fitstruct,activationDirection):
        self.fs = fitstruct
        self.ad = activationDirection

    def x_given_y(self,y):

        if type(self.fs) == Line:
            return self.fs.x_given_y(y)
        return round(self.fs.g(y),5)

    def y_given_x(self,x):
        if type(self.fs) == Line:
            #try:
            return self.fs.y_given_x(round(x,5))
            #except:
            #    return None
        return round(self.fs.f(x),5)

    def __str__(self):
        l = None
        if type(self.fs) == Line: l = "line"
        elif type(self.fs) == LogFit22: l = "logfit22"
        else: l = "exp2fit22"
        p = self.get_point()

        s = "* struct: {} \n".format(l)
        s2 = "* points\n-- {}\n-- {}\n".format(p[0],p[1])
        s3 = "* direction: {}\n".format(self.ad)
        return s + s2 + s3 + "---"

    def get_point(self):
        if type(self.fs) == Line: 
            return deepcopy(self.fs.endpoints)
        return deepcopy(self.fs.ps)

    def point_range(self):
        '''
        [[x-min,x-max],[y-min,y-max]]
        '''
        p = deepcopy(self.fs.endpoints) if type(self.fs) == Line\
            else deepcopy(self.fs.ps)

        x = np.sort(p[:,0])
        y = np.sort(p[:,1])
        return np.array([x,y])

    def in_point_range(self,p):
        pr = self.point_range()
        # case: in y-range?
        if self.ad in {'l','r'}:
            return p[1] >= pr[1,0] and p[1] <= pr[1,1]
        # case: in x-range?
        else:
            return p[0] >= pr[0,0] and p[0] <= pr[0,1]

    def is_ap(self,p):
        '''
        is activation point?

        NOTE: use at discretion, method assumes curve direction is oriented
              by ascending order on the number line, but correct usage 
              could be ascending or descending order.
        '''

        vp = self.value_on_curve(p)
        axis = 1 if self.ad in {'t','d'} else 0

        if self.ad in {'t','r'}:
            return p[axis] <= vp
        return p[axis] >= vp

    def value_on_curve(self,p):
        if self.ad in {'t','b'}:
            return round(self.y_given_x(p[0]),5)
        return round(self.x_given_y(p[1]),5)

    def modulate_fit(self):
        if type(self.fs) == Line:
            return

        if type(self.fs) == LogFit22:
            c = Exp2Fit22(deepcopy(self.fs.ps),self.fs.direction)
        else:
            c = LogFit22(deepcopy(self.fs.ps),self.fs.direction)
        self.fs = c

    def form_point_sequence(self,pointHop = DEFAULT_TRAVELLING_HOP):
        if type(self.fs) == Line:
            self.fs.form_point_sequence(pointHop = pointHop)
            return self.fs.data

        xys = []
        xs = self.point_range()[0]
        i = xs[0]
        while i < xs[1]:
            y = self.y_given_x(i)  
            xys.append((i,y))
            i += pointHop
        return xys


class ChainedDCurves: 

    def __init__(self,ps,fittype_vec,axis=0): 
        assert is_2dmatrix(ps) 
        assert len(ps) > 1
        assert len(ps) == len(fittype_vec) + 1 
        assert set(fittype_vec).issubset({0,1}) 
        assert axis in {0,1} 

        self.ps = ps[np.argsort(ps[:,axis])] 
        self.fvec = fittype_vec 
        self.axis = axis 
        self.axis_extremum() 

        self.dcurve_seq = [] 

    def axis_extremum(self):

        self.amin = np.min(self.ps[:,self.axis])
        self.amax = np.max(self.ps[:,self.axis])
        return self.amin,self.amax 

    def modulate_fit(self,bvec):
        assert len(bvec) == len(self.fvec)

        for (i,b) in enumerate(bvec):
            if b:
                self.dcurve_seq[i].modulate_fit()
                self.fvec[i] = (self.fvec[i] + 1) % 2 

    """
    main method; draws Fit22 instances b/t every contiguous 
    point in 
    """
    def draw(self):
        self.dcurve_seq.clear() 

        adir = "l" if self.axis == 1 else "t"
        for i in range(1,len(self.ps)):
            p0,p1 = self.ps[i - 1], self.ps[i]
            d = [0,1]
            px = np.array([p0,p1])
            d = [0,1] if px[0,1] < px[1,1] else [1,0]

            #px = np.array([px[d[0]],px[d[1]]])

            if self.fvec[i-1]: 
                fs = LogFit22(px,d)
            else: 
                fs = Exp2Fit22(px,d) 
            dc = DCurve(fs,adir)
            self.dcurve_seq.append(dc)
        return 

    def point_to_dcurve(self,p):
        if p < self.amin or p > self.amax: 
            return -1 
        for (i,dc_) in enumerate(self.dcurve_seq):
            pr = dc_.point_range()[self.axis] 

            if p >= pr[0] and p <= pr[1]:
                return i 
        return -1 

    def fit(self,p):
        index = self.point_to_dcurve(p)

        if index == -1: 
            return None

        dc = self.dcurve_seq[index]
        
        if self.axis == 0: 
            return dc.y_given_x(p) 
        return dc.x_given_y(p) 
