#from morebs2.fit_2n2 import *
#from morebs2.random_generators import *
#from morebs2.deline_helpers import *
from .fit_2n2 import *
from .random_generators import *
from .deline_helpers import *
from collections import defaultdict,Counter

class Delineation:

    def __init__(self,label,clockwise,parentIds = [],childIds = [],idn = "0"):
        """
        data structure used to store and calculate points for delineation of a sequence
        of two-dimensional points

        :attribute d: container for point sequences corresponding to each direction (l,r,t,b)
        :type d: dict 
        :attribute d_: sequence of :class>`DCurves` corresponding to `d`. 
        :type d_: list 
        :attribute label: the classification of the points  
        :type label: int
        :attribute clockwise: is the delineation clockwise? 
        :type clockwise: bool
        """
        
        self.d = {}
        self.d_ = None
        self.label = label
        self.clockwise = clockwise
        self.parentIds = parentIds
        self.childIds = childIds
        return

    def add_edge(self,direction,edge):
        self.d[direction] = edge

    def no_duplicates(self):
        '''
        sequence correction algorithm by condition `no duplicates`. 
        '''
        # left and right
        self.d['l'],self.d['r'] = eliminate_duplicate_points(\
            self.d['l'],self.d['r'],0)

        # top and bottom
        self.d['t'],self.d['b'] = eliminate_duplicate_points(\
            self.d['t'],self.d['b'],1)

    def no_cross(self):
        '''
        sequence correction algorithm by condition `no cross`. 
        '''
        self.d['l'],self.d['r'] = eliminate_contrary_points(\
            self.d['l'],self.d['r'],1)

        self.d['t'],self.d['b'] = eliminate_contrary_points(\
            self.d['t'],self.d['b'],0)

        return

    def no_cross_on_axis(self,axis,maxNumberOfPoints=10):
        """
        NOTE: unnecessary loop, only one iteration will do. 
        """

        if axis == 1:
            k1,k2 = 'l','r'
        else:
            k1,k2 = 't','b'

        while True:
            l1,l2 = len(self.d[k1]), len(self.d[k2])
            self.d[k1],self.d[k2] = eliminate_contrary_points(\
                self.d[k1],self.d[k2],axis) 
            l1_,l2_ = len(self.d[k1]), len(self.d[k2])

            if l1_ == l1 and l2_ == l2:
                break

            if l1_ <= maxNumberOfPoints or l2_ <= maxNumberOfPoints:
                break

    def no_jags(self):
        '''
        sequence correction algorithm by condition `no jags`. 
        '''
        self.no_jags_on_edge('l')
        self.no_jags_on_edge('r')
        self.no_jags_on_edge('t')
        self.no_jags_on_edge('b')

    def no_jags_on_edge(self,direction,maxNumberOfPoints=10):
        assert direction in {'l','r','t','b'}

        while True: 
            l1 = len(self.d[direction])
            self.d[direction] = remove_jags_on_edges(self.d[direction],direction)
            l2 = len(self.d[direction])
            if l2 <= maxNumberOfPoints:
                break
            if l1 == l2: break
            
        return

    def draw_delineation(self):
        '''
        clockwise -> (t,r,b,l)
        counter-clockwise -> (t,l,b,r)
        '''
        self.d_ = []

        one = self.point_sequence_to_curve_set(self.d['t'],'t')
        
        if self.clockwise:
            two = self.point_sequence_to_curve_set(self.d['r'],'r')
            four = self.point_sequence_to_curve_set(self.d['l'],'l')
        else:
            four = self.point_sequence_to_curve_set(self.d['r'],'r')
            two = self.point_sequence_to_curve_set(self.d['l'],'l')

        three = self.point_sequence_to_curve_set(self.d['b'],'b')

        self.d_.extend(one)
        self.d_.extend(two)
        self.d_.extend(three)
        self.d_.extend(four)

    def point_pair_to_curve(self,p1,p2,ad):
        # case: line
        if p1[0] == p2[0] or\
            p1[1] == p2[1]:
            c = Line([p1,p2]) 
        else:
        # case: default is LogFit22
            direction = np.argsort(np.array([p1,p2])[:,1])
            c = LogFit22(np.array([p1,p2]),direction = direction)
        return DCurve(c,ad) 

    def point_sequence_to_curve_set(self,ps,ad):
        l = len(ps) - 1
        cs = []
        for i in range(0,l):
            cs.append(self.point_pair_to_curve(\
                deepcopy(ps[i]),deepcopy(ps[i+1]),ad))
        return cs

    def classify_point(self,p):
        '''
        :rtype: label if p in delineation, otherwise -1
        '''
        x1,x2,x3,x4 = self.point_to_relevant_curvepair(p)

        if x1 == None and x3 == None:
            return -1

        sc = self.classify_point_special_case(p,x1,x2,x3,x4)
        if sc != None:
            return self.label if sc else -1

        x1,x2 = (x1,x2) if type(x1) != None else (x3,x4)

        sc = self.classify_point_by_complementary_curves(p,x1,x2)
        return self.label if sc else -1

    def classify_point_special_case(self,p,c1,c2,c3,c4):
        '''
        provides a classification to point `p` by ('l','t') curves in
        the case where the value by the `l` and `r` OR `t` and `b` curves
        are equal. 

        NOTE: caution 
        '''

        if type(c1) != type(None): 
            p1,p2 = round(c1.x_given_y(p[1]),5),round(c2.x_given_y(p[1]),5)
            if p1 == p2:
                if type(c3) == type(None):
                    return None
                else:
                    return c1.is_ap(p) and c3.is_ap(p)
            return None
        
        if type(c3) != type(None): 
            p1,p2 = round(c3.y_given_x(p[0]),5),round(c4.y_given_x(p[0]),5)

            if p1 == p2:
                if type(c1) == type(None):
                    return None
                else:
                    return c1.is_ap(p) and c3.is_ap(p)
            return None
        return None

    def point_to_relevant_curvepair(self,p):
        '''
        searches for a curve pair (left&right)|(top&bottom)
        that 
        '''
        l,r,t,b = None,None,None,None

        for x in self.d_:
            if x.in_point_range(p):
                if x.ad == 'l': l = x
                elif x.ad == 'r': r = x
                elif x.ad == 't': t = x
                elif x.ad == 'b': b = x

        return l,r,t,b

    def classify_point_by_complementary_curves(self,p,c1,c2):

        s1 = c1.value_on_curve(p)
        s2 = c2.value_on_curve(p)

        if c1.ad in {'t','b'}:
            axis = 1
        else:
            axis = 0
        return p[axis] >= min([s1,s2]) and p[axis] <= max([s1,s2])

    def classify_point_by_curveset(self,p,rp,cs):
        for c in cs:
            if not c.in_point_range(p):
                continue

            if not self.classify_point_by_complementary_curves(p,rp,c):
                return -1

        return self.label

    def complement_set_to_curve(self,c):
        '''
        collects all curves in delineation with an 
        activation direction parallel to that of c
        that have a range that intersects that of c. 

        * note: method can only be called after `delineation_to_initial_estimate`. 
        '''
        axis = 1 if c.ad in {'l','r'} else 0
        pr = c.point_range()[axis]

        if c.ad == 'l':
            x = 'r'
        elif c.ad == 'r':
            x = 'l'
        elif c.ad == 'b':
            x = 't'
        else:
            x = 'b'

        q = []
        for c_ in self.d_:
            if c_.ad != x: continue
            pr2 = c_.point_range()[axis]
            if pr2[0] >= pr[0] and pr2[0] <= pr[1]:
                q.append(deepcopy(c_))
            elif pr2[1] >= pr[0] and pr2[1] <= pr[1]:
                q.append(deepcopy(c_))
        return q

    def visualize_delineation(self):
        ps = []
        colors = {'l': [1.,0.,0.,1.],\
            'r': [0.,1.,0.,1.],\
            't': [0.,0.,1.,1.],\
            'b': [0.,0.,0.,1.]
        }

        cs = []
        for c in self.d_:
            l = c.form_point_sequence(0.001)
            ps.extend(l)
            cs.extend([colors[c.ad] for j in range(len(l))])
        ps = np.array(ps)
        basic_2d_scatterplot(ps[:,0],ps[:,1],c=cs)
        return

    def is_proper_subset(self,d2):
        '''

        iterate through each curve, and check that their
        endpoints lay in the bounds of class:`Delineation` `d2`.

        NOTE: inefficient

        :return: bool, is instance in d2?
        '''

        for x in self.d_:
            p = x.get_point()
            for p_ in p:
                if d2.classify_point(p_) == -1:
                    return False
        return True

    @staticmethod
    def pertinent_curves_to_point(d,p):
        '''
        :return: list(curves with point `p` in its range)
        '''

        cs = []
        for c in d.d_:
            if c.in_point_range(p): cs.append(c)
        return cs 

class DLineate22:

    def __init__(self,xyl,clockwise=True,dmethod = "nocross",idn="0"):
        """
        Delineates a sequence of three-dimensional points using the :class:`Delineator`
        by one of the methods `nojag`,`nocross`, or `nodup`, each of which provides a
        different and possibly inaccurate delineation of the points (if data is "complex").

        Delineation targets the subset of points with the label of lowest frequency.

        :attribute xyl: three-dimensional points of (x,y,label). 
        :type xyl: np.ndarray 
        :attribute xyl_sorted_x: the `xyl` points sorted by x-axis. 
        :type xyl_sorted_x: nd.nparray 
        :attribute xyl_sorted_y: the `xyl` points sorted by y-axis. 
        :type xyl_sorted_y: nd.nparray  
        :attribute lc: label to label indices
        :type lc: dict  

        :attribute clockwise: is delineation clockwise?
        :type clockwise: bool
        :attribute label: target label of points to delineate
        :type label: int
        :attribute lpoints: target points to delineate
        :type lpoints: np.ndarray
        :attribute linfo: information of target points, [x-center,y-center,x-min,x-max,y-min,y-max]
        :type linfo: np.ndarray
        :attribute d: used to delineate the target points
        :type d: :class:`Delineator`
        :attribute dmethod: methodology used to correct points
        :type dmethod: string
        :attribute idn: identifier of class 
        :type idn: stringized int
        """


        assert xyl.shape[1] == 3, "invalid shape"
        assert dmethod in ["nodup","nojag","nocross"]
        
        self.xyl = np.round(xyl,5)
        self.xyl_sorted_x = None
        self.xyl_sorted_y = None 
        self.lc = None
        self.clockwise = clockwise
        self.label = None
        self.lpoints = None
        self.linfo = None
        self.d = None
        self.dmethod = dmethod
        self.idn = idn
        return

    ############# preprocessing methods

    def preprocess(self):
        self.label_counts()
        self.set_target_label()        
        self.sort_data() 
        
    def label_counts(self):
        self.lc = defaultdict(list)
        for (i,x) in enumerate(self.xyl):
            self.lc[x[2]].append(i)
        return

    def set_target_label(self,l=None):
        # default: choose min label
        if l == None:
            x = np.array([(k,len(v)) for (k,v) in self.lc.items()])
            a = np.argmin(x[:,1])
            self.label = x[a,0]
        else:
            self.label = l

        self.lpoints = deepcopy(self.xyl[self.lc[self.label]])
        self.lpoints = self.lpoints[:,:2]

    def target_label_analysis(self):
        c = self.calculate_center()
        ex = self.calculate_extremum()
        self.linfo = c + ex

    def calculate_center(self):
        '''
        calculates center for the lpoints
        '''
        return [np.mean(self.lpoints[:,0]),np.mean(self.lpoints[:,1])]

    def calculate_extremum(self):
        '''
        calculates extremum for the lpoints
        '''
        # x-min point
        xi = np.argmin(self.lpoints[:,0])
        # x-max point
        xa = np.argmax(self.lpoints[:,0])
        # y-min point
        yi = np.argmin(self.lpoints[:,1])
        # y-max point
        ya = np.argmax(self.lpoints[:,1])
        return [xi,xa,yi,ya]

    def sort_data(self):
        xs = np.argsort(self.lpoints[:,0])
        self.xyl_sorted_x = deepcopy(self.lpoints[xs]) #  deepcopy(self.xyl[xs])
        ys = np.argsort(self.lpoints[:,1])
        self.xyl_sorted_y = deepcopy(self.lpoints[ys]) #deepcopy(self.xyl[ys])
        return

    ################## initial delineation

    def collect_break_points(self,pi=[],ci=[]):
        '''
        clockwise -> [l + t -> increasing order, others in decreasing order]
        counter-clockwise -> [r + b -> increasing order, others in decreasing order]
        '''

        ds = ['l','r','t','b']
        self.d = Delineation(label=self.label,clockwise=self.clockwise,parentIds=pi,childIds=ci,idn =self.idn)
        for x in ds:
            edge = self.break_points_on_edge(x)
            self.d.add_edge(x,edge)

        if self.dmethod == "nodup":
            self.d.no_duplicates()
        elif self.dmethod == "nojag":
            self.d.no_jags()
        else:
            self.d.no_cross()

        self.assign_circular_directionality()
        self.d.draw_delineation()
        return

    def assign_circular_directionality(self):
        if self.clockwise:
            self.d.d['r'] = self.d.d['r'][::-1]
            self.d.d['b'] = self.d.d['b'][::-1]
        else:
            self.d.d['l'] = self.d.d['l'][::-1]
            self.d.d['t'] = self.d.d['t'][::-1]

    def break_points_on_edge(self,direction):
        '''
        direction := `l` is left edge,`r` is right edge,`t` is top edge,
                     `b` is bottom edge.

                     if `l`|`r`, output is ordered by axis 1. Otherwise, by axis 0. 
        '''
        edge = []

        stat = True
        i = None
        rd = self.xyl_sorted_y if direction in\
            {'l','r'} else self.xyl_sorted_x

        while stat:
            i = self.next_break_point(i,direction)
            if i == None: 
                stat = not stat
                continue
            edge.append(deepcopy(rd[i,:2]))
        return np.array(edge)

    def next_break_point(self,refi,direction):
        rd = None
        axis = None
        if direction in  {'l','r'}:
            rd = self.xyl_sorted_y
            axis = 1
        else:
            rd = self.xyl_sorted_x
            axis = 0
        
        j = None
        if refi == None:
            j = 0
        else:
            # next greater element
            q = rd[refi]
            md = np.inf
            for i in range(refi,len(rd)):
                if rd[i,axis] <= q[axis]:
                    continue
                if rd[i,axis] > q[axis]:
                    if rd[i,axis] - q[axis] < md:
                        md = rd[i,axis] - q[axis]
                        j = i
            if j == None:
                return None
        return self.break_point_tiebreakers(j,direction)

    def break_point_tiebreakers(self,refni,direction):
        #a = 1 if direction in {'l','r'} else 0
        if direction in {'l','r'}: 
            rd = self.xyl_sorted_y
            a = 1
        else:
            rd = self.xyl_sorted_x
            a = 0 

        rp = rd[refni]
        indices = np.where(rd[:,a] == rp[a])

        pp = rd[indices]
        s = None
        if direction == 'r':
            s = np.argmax(pp[:,0])
        elif direction == 'l':
            s = np.argmin(pp[:,0])
        elif direction == 't':
            s = np.argmax(pp[:,1])
        else:
            s = np.argmin(pp[:,1])

        ss = np.where((rd == pp[s]).all(axis=1))
        return ss[0][0]

    ######### start: delineation optimizer

    def optimize_delineation(self):
        s = 0 
        for (i,x) in enumerate(self.d.d_):
            s += self.improve_curve(x)
        return s

    def improve_curve(self,c):
        # get pertinent points to curve
        pp = self.pertinent_points_to_curve(c)
        # get curveset
        cs = self.d.complement_set_to_curve(c)

        # classify points
        s1 = self.classify_pertinent_points(c,cs,pp)
        # alternate and reclassify
        c.modulate_fit()
        s2 = self.classify_pertinent_points(c,cs,pp)

        if s1 > s2:
            c.modulate_fit()
            return 0 
        return s2 - s1

    def classify_pertinent_points(self,rc,cs,pp):

        s = 0
        for p in pp:
            l = self.d.classify_point_by_curveset(p[:2],rc,cs)
            if l != -1:
                s += 1
        return s

    def pertinent_points_to_curve(self,c):
        '''
        :return: np.ndarray, points pertinent to curve `c`
        '''
        
        ps = []
        for p in self.xyl:
            if c.in_point_range(p):
                ps.append(p)
        return ps

    ######### analyze delineation

    def analyze_delineation(self):
        '''
        method is called after `optimize_delineation`;
        delineation `d` is put into the cache, and
        delineation is done on the points in `d` for
        separability.

        :return: [indices of xyl points in delineation,\
                counter(label->count),score of delineation] 
        '''

        # iterate through all points and collect those in
        # delineation
        indices = []
        counter = Counter()
        q = 0 # number of correctly labelled points
        for (i,p) in enumerate(self.xyl):
            c = self.d.classify_point(p)
            if c != -1:
                indices.append(i)
                # case: classification equals label
                if c == int(p[2]): 
                    q += 1
                counter[int(p[2])] += 1
            else:
                if int(p[2]) == self.label:
                    counter[-1] += 1




            '''
                if c == int(p[2]): q += 1
            else:
                if int(p[2]) == self.label:
                    counter[-1] += 1
                counter[int(p[2])] += 1
            else:
                if p[2] 
                counter[c]
            '''

        return indices,counter,q

    def full_process(self,preprocess = True):
        '''
        main method
        '''
        if preprocess:
            self.preprocess()
            print("finished preprocessing ")
        self.collect_break_points()
        self.optimize_delineation()
        indices,c,q = self.analyze_delineation()
        # remove those indices from xyl
        self.xyl = np.delete(self.xyl,indices,0)
        return indices,c,q

def test_dataset__Dlineate22_1():
    '''
    x      x
    
    x   x       
    
    x   x      
                x
    x
    
    x      x
    '''
    return np.array([[5.,15.,0],\
        [5.,12.,0],\
        [5.,9.,0],\
        [5.,6.,0],\
        [5.,0.,0],\
        [15.,12.,0],\
        [15.,9.,0],\
        [20.,15.,0],\
        [20.,0.,0],\
        [25.,7.5,0]])

def test_dataset__Dlineate22_1_v2():
    d = test_dataset__Dlineate22_1()
    t2 = generate_random_xyl_points_at_center(\
        [12.,8.55,5],[[0.,5.,5],[15.,25.,8]],1)
    return np.vstack((d,t2))


def test_dataset__Dlineate22_1_v3(numPoints,rdistance):
    data = test_dataset__Dlineate22_1()
    dl = DLineate22(data)
    dl.preprocess()
    dl.collect_break_points()

    l = len(dl.d.d_)
    ps = 0
    points = []
    i = 0
    while ps < numPoints:
        a = random.random()
        if a > 0.5:
            pr = dl.d.d_[i].get_point()
            rp = random_point_near_2d_point_pair(\
                pr,rdistance)
            rp_ = [rp[0],rp[1],1.]
            points.append(rp_)
            ps += 1
        i = (i + 1) % l
    points = np.array(points)
    return np.vstack((data,points))

def test_dataset__Dlineate22_2():
    '''
    x      x

    
    x      x
    '''
    return np.array([[5.,15.,0],\
        [5.,0.,0],\
        [20.,15.,0],\
        [20.,0.,0]])


def test_dataset__Dlineate22_3():
    # NOTE: delineation does not work for triangles
    '''
       x   

    
    x      x
    '''
    return np.array([[5.,0.,0],\
        [7.5,15.,0],\
        [20.,0.,0]])


def test_dataset__Dlineate22_4():
    # NOTE: delineation does not work for triangles
    '''
       x   

    
    x      
            x
    '''
    return np.array([[5.,0.,0],\
        [7.5,15.,0],\
        [20.,-5.,0]])


def test_dataset__DLineateMC_1():
    '''
    completely separable; 4 labels.
    '''
    c1 = [0.,0.]
    drnp1 = [[0.,5.,1000],[5.,15.,10000],[15.,30.,300]]
    l1 = 0
    d1 = generate_random_xyl_points_at_center(c1,drnp1,l1)

    c2 = [80.,20.]
    drnp2 = [[0.,5.,500],[10.,20.,5000],[10.,15.,300]]
    l2 = 1
    d2 = generate_random_xyl_points_at_center(c2,drnp2,l2)

    c3 = [-50.,-30.]
    drnp3 = [[10.,15.,5000],[20.,25.,500],[25.,27.,300]]
    l3 = 2
    d3 = generate_random_xyl_points_at_center(c3,drnp3,l3)

    c4 = [-150.,-70.]
    drnp4 = [[10.,20.,5000],[20.,40.,5000]]
    l4 = 3
    d4 = generate_random_xyl_points_at_center(c4,drnp4,l4)
    
    d = d1
    d = np.vstack((d,d2))
    d = np.vstack((d,d3))
    d = np.vstack((d,d4))
    return d