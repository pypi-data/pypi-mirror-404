from .poly_interpolation import *


class ChainedLagrangePolySolver:
    '''
    extended version of :class:`LagrangePolySolver` that interpolates points
    over n dimensions.

    * Point-set conditions for use:
    
    - non-duplicate values for each dimension
    
    * Requires a valid axis order of interpolation:
    
    - path that allows for lagrange interpolation in n-dim.
    '''

    def __init__(self, points):
        self.points = points
        self.assert_valid_points()
        self.oi = None
        self.lapassio = None
        return

    '''
    '''
    def assert_valid_points(self):
        assert is_2dmatrix(self.points), "invalid points"
        for i in range(self.points.shape[1]):
            q = self.points[:,i]
            assert len(set(q)) > 2, "invalidati invalidatini #2"

    def set_axis_order_of_interpolation(self,o):
        assert len(set(o)) == len(o)
        assert max(o) == self.points.shape[1] - 1
        assert min(o) == 0
        self.oi = o

    def interpolate_pair(self,ref,on):
        refs = self.points[:,ref]
        ons = self.points[:,on]
        pts = np.array([refs,ons]).T
        lps = LagrangePolySolver(pts)
        return lps#.form_point_sequence(hopIncrement = hopIncrement,capture = False)

    """
    """
    def formulate_ordering(self):
        q = [i for i in range(self.points.shape[1])]

        def swap_pathos(p,i,j):
            p[j],p[i] = p[i],p[j]

        pathos = np.copy(self.oi)
        # if i does not end at the second to last...
        for i in range(self.points.shape[1] - 1):
            # check i for swap
            q = np.copy(self.points[:,i])
            q2 = np.copy(self.points[:,i+1])
            if len(set(q)) < 2:
                print("swapping index pair")
                swap_pathos(pathos,i,i+1)
        return pathos

    # CAUTION: unstable formulation
    def check_valid_ordering(self):
        noi = self.formulate_ordering()
        self.oi = noi

        # check the last 2 indices
        x1,x2 = self.oi[-1],self.oi[-2]
        q1,q2 = self.points[:,x1],self.points[:,x2]

        return len(set(q1)) == len(set(q2))

    '''
    sets a lapassio, a sequence of LagrangePolySolvers
    '''
    def formulate(self):
        assert self.check_valid_ordering(),"invalid ordering"

        self.lapassio = []

        res = self.points[:,0].reshape((self.points.shape[0],1))
        for i in range(self.oi.shape[0] - 1):
            q = self.interpolate_pair(i,i+1)#[:,1]
            self.lapassio.append(q)
        return

    '''
    '''
    def at_x1(self,x1):
        assert x1 >= min(self.points[:,self.oi[0]]) and\
            x1 <= max(self.points[:,self.oi[0]])

        p = [x1]
        for i in range(self.points.shape[1] - 1):
            q = self.lapassio[i].output_by_lagrange_basis(p[-1])
            p.append(q)
        return np.array(p)

    def form_point_sequence(self,hopIncrement):
        assert type(self.oi) != type(None), "invalidati invalidatini"
        res = self.points[:,0].reshape((self.points.shape[0],1))
        for i in range(self.oi.shape - 1):
            q = self.interpolate_pair(i,i+1,hopIncrement)
            q = q.form_point_sequence(hopIncrement = hopIncrement,capture = False)[:,1]
            res = np.vstack((res,q))
        return res
