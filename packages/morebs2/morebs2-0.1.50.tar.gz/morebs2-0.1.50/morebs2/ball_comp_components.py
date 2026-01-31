from .numerical_generator import *
from .point_weight_function import *

#################### start: area estimation methods

"""
table contains values of curvature estimation between two
circles that intersect.

These values are used to `gauge` the volume of intersection between
two n-balls.
"""
CURVATURE_EST = {1.0:0.46792,\
                5/6:0.52544,\
                2/3:0.61026,\
                1/2:0.72842,\
                1/3:0.88860,\
                1/4:0.96300,\
                1/6:1.0}

CURVATURE_EST_KEYS = [1/6,1/4,1/3,1/2,2/3,5/6,1]

def intersection_ratio(b1,b2):
    """
Calculates the intersection ratios of b1 and b2.
The intersection ratio of a ball is the proportion of its diameter that
lies in the intersection.

:return: intersection ratio of b1, intersection ratio of b2
:rtype: (float,float)|(None,None)
    """
    ed = euclidean_point_distance(b1.center,b2.center)

    # case: no intersection
    if ed >= b1.radius + b2.radius:
        return None,None

    # case: b2 completely in b1
    if b2.radius + ed <= b1.radius:
        return 0.0,1.0

    # case: b1 completely in b2
    if b1.radius + ed <= b2.radius:
        return 1.0,0.0

    # get intersection ratio of b1
        # first point is the farthest boundary point of b1 that lies in b2
        # point on ray (b1.center,b2.center) of distance b1.radius from .b1.center
    coeff1 = b1.radius / ed
    x1 = b1.center + coeff1 * (b2.center - b1.center)

        # second point of interest is the farthest boundary point of b2 that lies in b1
        # the point on the ray (b2.center,b1.center) at
        # distance b1.radius + ed
    coeff2 = b2.radius / ed
    x2 = b2.center + coeff2 * (b1.center - b2.center)
    distance = euclidean_point_distance(x1,x2)
    return round(distance / (b1.radius * 2),5), round(distance / (b2.radius * 2),5)

def prelim_2intersection_estimate(b1,ir):
    """
    estimate does not include curvature estimation
    """
    if ir <= 0.5:
        return ball_area(b1.radius, b1.center.shape[0]) * ir
    return ball_area(b1.radius,b1.center.shape[0]) * 0.5 + prelim_2intersection_estimate(b1,ir - 0.5)

def reference_intersection_ratio_to_curvature_est_key(ri):
    assert ri >= 0 and ri <= 1, "invalid intersection ratio"
    x = np.array([abs(ri - k) for k in CURVATURE_EST_KEYS])
    i = np.argmin(x)
    return CURVATURE_EST_KEYS[i]

# CAUTION
##this is an approximation for Ball volume.
##Value calculated from .this method is to be used as a reference
##rather than directly as a numerical value.
def ball_area(r,k):
    assert k >= 2,"invalid k"
    x = math.pi * float(r) ** 2
    x2 = (k - 1) ** 2
    return x * x2

def reference_volume_ratio(b1,b2):
    return min([b1.radius / b2.radius,b2.radius / b1.radius])

def volume_2intersection_estimate(b1,b2):
    r1,r2 = intersection_ratio(b1,b2)
    ###print("RI: ",r1,r2, ball_area(b1.radius,6),ball_area(b2.radius,6))
    # case: no intersection
    if type(r1) == type(None):
        return 0.0

    # case: ball 1 in ball 2
    if r1 == 1.0:
        return ball_area(b1.radius,b1.center.shape[0])

    # case: ball 2 in ball 1
    if r2 == 1.0:
        return ball_area(b2.radius,b2.center.shape[0])

    # case: intersection
    ie1 = prelim_2intersection_estimate(b1,r1)
    ie2 = prelim_2intersection_estimate(b2,r2)

    ###print("IE1 ", ie1, "\t",ie2)

    referenceIntersectionRatio = r1 if b1.radius > b2.radius else r2
    cek = reference_intersection_ratio_to_curvature_est_key(referenceIntersectionRatio)
    rv = reference_volume_ratio(b1,b2)
    curvatureEst = CURVATURE_EST[cek] + (1.0 - CURVATURE_EST[cek]) * rv
    return min([ie1,ie2]) * curvatureEst

#################### end: area estimation methods

class Ball:
    '''
    implementation of n-ball, see `ball_operator` for related methods.

    :param center: center of ball
    :type center: np.ndarray, vector
    :param idn: int
    :type idn: int
    '''
    # used for reversion
    DELTA_MEMORY_CAPACITY = 3

    def __init__(self, center,idn = None):
        assert is_vector(center), "invalid center point for Ball"
        self.center = center
        self.idn = idn
        self.data = PointSorter(np.empty((0,self.center.shape[0])))
        self.radius = 0.0

        # [0] is radial reference, [1] is
        self.radiusDelta = (None,None)
        self.radiusDeltas = []
        self.pointAddDeltas = []

        # container that holds the most recent delta
        self.clear_delta() # (point,radius delta)
        self.neighbors = set() # of ball neighbor identifiers
        return

    def __str__(self):
        s0 = "ball idn: {}".format(self.idn)
        s = "\nball center:\n\t{}".format(vector_to_string(self.center,float))
        s2 = "\nball radius: {}".format(self.radius)
        s3 = "\nball neighbors: {}".format(self.neighbors)
        s3 = "\nball data shape: {}".format(self.data.newData.shape)

        return s0 + s + s2 + s3
    '''
    '''
    @staticmethod
    def dataless_copy(b):
        b_ = Ball(np.copy(b.center))
        b_.radius = b.radius
        b_.neighbors = set(b.neighbors)
        return b_

    def is_neighbor(self,b):
        return euclidean_point_distance(self.center,b.center) <= self.radius + b.radius

    def area(self):
        b = ball_area(self.radius, self.center.shape[0])
        return round(b,5)

    @staticmethod
    def one_ball(center, points):
        b = Ball(center)

        for p in points:
            b.add_element(p)
        return b

    @staticmethod
    def one_ball_(center,radius,centerAsPoint = True):
        b = Ball(center)
        c = random_npoint_from_point(np.copy(center),radius)
        b.add_element(c)
        b.add_element(center)
        return b

    # TODO: test this.
    def in_bounds(self,bounds):
        assert self.center.shape[0] == bounds.shape[0], "invalid bounds"

        bs = []
        for (i,c) in enumerate(self.center):
            c0,c1 = c - self.radius,c + self.radius
            bs.append((c0,c1))
        bs = np.array(bs)
        bs = np.round(bs,5)
        return bounds_is_subbounds(bounds,bs)

    def point_in_data(self,p):
        return self.data.vector_exists(p)

    def point_in_ball(self,p):
        ed = euclidean_point_distance(p,self.center)
        return ed <= self.radius

    '''
    adds single point to Ball
    and updates mean
    '''
    def add_element(self, p):
        self.data.insert_point(p)
        self.pointAddDeltas.insert(0,p)
        self.pointAddDeltas = self.pointAddDeltas[:Ball.DELTA_MEMORY_CAPACITY]

        # update radius
        r = euclidean_point_distance(self.center,p)
        if r > self.radius:
            self.radiusDeltas.insert(0,self.radiusDelta)
            self.radiusDeltas = self.radiusDeltas[:Ball.DELTA_MEMORY_CAPACITY]
            self.radiusDelta = (p, r - self.radius)
            self.radius = r

    def revert_add_point(self):
        if len(self.pointAddDeltas) == 0: return
        q = self.pointAddDeltas.pop(0)

        # remove from .data
        if type(self.radiusDelta[0]) != type(None):
            if equal_iterables(q,self.radiusDelta[0]):
                self.revert_delta()
        else:
            self.data.delete_point(q)
        return

    # TODO:
    '''
    '''
    def revert_delta(self):
        if type(self.radiusDelta[0]) == type(None):
            return
        self.data.delete_point(self.radiusDelta[0])
        self.radius = self.radius - self.radiusDelta[1]

        self.radiusDelta = self.radiusDeltas.pop(0) if len(self.radiusDeltas) > 0\
                        else (None,None)

        return

    def clear_delta(self):
        self.radiusDelta = (None,None)

    '''
    determines if two balls intersect
    '''
    @staticmethod
    def does_intersect(b1,b2):
        epd = euclidean_point_distance(b1.center,b2.center)
        epd = epd - b1.radius - b2.radius
        return epd <= 0

    '''
    upper-bound estimate on the k-dimensional sub-area of
    intersection b/t b1 and b2.
    '''
    @staticmethod
    def area_intersection_estimation(b1,b2):
        a1 = Ball.area_intersection_estimation_(b1,b2)
        a2 = Ball.area_intersection_estimation_(b2,b1)
        x1 = min([b2.area() * a1, b1.area() * a2])
        return max([0.0,x1])


    '''
    merges two balls
    '''
    def __add__(self, b2):

        r1,r2 = intersection_ratio(self,b2)
        # case: self in b2
        if r1 == 1.0:
            return b2

        # case: b2 in self
        if r2 == 1.0:
            return self

        # case: other
        ed = euclidean_point_distance(self.center,b2.center)
            # get the farthest boundary point of b2 on line (b1.center,b2.center)
        x2 = b2.radius / ed
        e2 = b2.center + x2 * (b2.center - self.center)

            # get the farthest boundary point of b1 on line (b1.center,b2.center)
        x1 = self.radius / ed
        e1 = self.center + x1 * (self.center - b2.center)

            # get midpoint of line
        center = np.round((e1 + e2) / 2.0,5)
        b3 = Ball(center)
        b3.radius = np.round(euclidean_point_distance(e1,e2) / 2.0,5)
        dr = np.vstack((self.data.newData,b2.data.newData))
        b3.data = PointSorter(dr)
        return b3
