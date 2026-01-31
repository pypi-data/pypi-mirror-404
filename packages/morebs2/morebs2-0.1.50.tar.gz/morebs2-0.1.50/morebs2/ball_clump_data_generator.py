from .numerical_space_data_generator import *
from .ball_comp_components import *
import pickle

class BallClumpDataGenerator:
    """
    generates points of n-dimensional balls based on parameters that detail the bounds
    of the balls, their radii, and then writes those points into a file 

    :param bounds: proper bounds array
    :type bounds: np.ndarray
    :param ballRadii: sequence of ball radii required
    :type ballRadii: iter
    :param clusterInfo: 2-tuple, [0] is sequence of i'th ball's cluster radii ratios, and [1] is sequence of i'th ball's density measures d, each cluster will have d points
    :type clusterInfo: np.ndarray
    :param filePath: save filepath
    :type filePath: str
    """

    def __init__(self,bounds,ballRadii,clusterInfo,filePath):
        self.bounds = np.round(bounds,5) # target bounds
        self.rbounds = None # refitted bounds
        assert len(ballRadii) == len(clusterInfo[0]), "invalid cluster arg. 0"
        assert len(ballRadii) == len(clusterInfo[1]), "invalid cluster arg. 1"

        self.ballRadii = ballRadii
        self.clusterInfo = clusterInfo
        self.clusterInfo_ = []
        self.filePath = filePath

    def set_frame(self):
        """
        Constructs a sequence of balls, and assigns points to them based on `clusterInfo`.

        NOTE: points that may exist in multiple balls will be assigned to only one ball.
        """
        self.balls = BallClumpDataGenerator.ball_clump_frame_generator_1(self.bounds,deepcopy(self.ballRadii))
        self.rbounds = BallClumpDataGenerator.bounds_for_ball_set(self.balls)

        # make cluster frames for each ball
        for (i,b) in enumerate(self.balls):
            bci = BallClumpDataGenerator.ball_data_cluster_frame(b,self.clusterInfo[0][i])
            self.clusterInfo_.append(bci)

        # make points for each ball
        for (i,b) in enumerate(self.balls):

            centers = self.clusterInfo_[i][0]
            radii = self.clusterInfo_[i][1]

            for j, (c,r) in enumerate(zip(centers,radii)):
                d = self.clusterInfo[1][i][j]
                BallClumpDataGenerator.cluster_points_to_ball(b,c,r,d)


    def make_data(self):
        """
        Constructs the dataset by popping one random element in one random ball
        until all Balls are empty.
        """
        def pop_one_random():
            i = random.randrange(len(aliveBalls))
            bi = aliveBalls[i]

            j = random.randrange(self.balls[bi].data.newData.shape[0])
            p = self.balls[bi].data.newData[j]
            self.balls[bi].data.newData = np.concatenate((self.balls[bi].data.newData[:j],\
                                    self.balls[bi].data.newData[j + 1:]))
            if self.balls[bi].data.newData.shape[0] == 0:
                aliveBalls.pop(i)
            return p

        aliveBalls = [i for i in range(len(self.balls))]
        fp = open(self.filePath,'w')
        while len(aliveBalls) > 0:
            q_ = pop_one_random()
            q = vector_to_string(q_,cr)
            fp.write(q + "\n")

        fp.close()

    @staticmethod
    def ballclump_frame_filepath(fp):
        x2 = fp[::-1].find("/")

        # case: no directories
        if x2 == -1:
            x1 = fp.find(".")
            r = fp[:x1]
            r += "__frame" + fp[x1:]
        else:
            r1,r2 = fp[::-1][:x2][::-1], fp[::-1][x2:][::-1]
            x1 = r1.find(".")
            r1 = r1[:x1] + "__frame" + r1[x1:]
            r = r2 + r1
        return r

    def save_frame(self):
        """
        saves instance's data in the form of a list with the variables
        -- rbounds, ball centers, ball radius, cluster centers, cluster radii, cluster densities
        """
        fp = BallClumpDataGenerator.ballclump_frame_filepath(self.filePath)

        ballCenters = [b.center for b in self.balls]
        ballRadii = [b.radius for b in self.balls]
        clusterCenters = [c[0] for c in self.clusterInfo_]
        clusterRadii = [c[1] for c in self.clusterInfo_]
        clusterDensities = self.clusterInfo[1]

        q = [self.rbounds,ballCenters,ballRadii,clusterCenters,\
            clusterRadii,clusterDensities]

        fobj = open(fp,"wb")
        pickle.dump(q,fobj)
        fobj.close()

    @staticmethod
    def ball_clump_frame_generator_1(bounds,ballRadii):
        """
        Calculates a vector of ball centers corresponding to a connected ball set

        :param bounds: proper bounds array
        :type bounds: np.ndarray
        :param ballRadii: sequence of ball radii required
        :type ballRadii: iter
        :return: listia ballco
        :rtype: list
        """

        """
        connects random ball with one present in the running solution
        at a random intersection ratio
        """
        def connect_random_ball(ballRadius):
            i = random.randrange(len(balls))
            maxDistance = ballRadius + balls[i].radius
            randomIntersectionRatio = random.uniform(0.1,0.75)
            q = randomIntersectionRatio * np.min([ballRadius,balls[i].radius])
            maxDistance -= q
            p2 = random_npoint_from_point(balls[i].center,maxDistance)
            b2 = Ball.one_ball_(p2,ballRadius)
            balls.append(b2)

        # choose a random vertex in bounds
        start = random_bounds_edge(bounds)
        c1 = random_npoint_from_point_in_bounds(bounds,start,ballRadii[0])
        r = round(ballRadii.pop(0),5)
        b1 = Ball.one_ball_(c1,ballRadii[0])
        balls = [b1]

        while len(ballRadii) > 0:
            r = round(ballRadii.pop(0),5)
            connect_random_ball(r)
        return balls

    """
    return:
    - [0]: np.ndarray, cluster centers
    - [1]: list, radius
    """
    @staticmethod
    def ball_data_cluster_frame(ball,clusterRadiiRatios):
        """
        Calculates a vector of ball centers corresponding to a connected ball set

        :param bounds: proper bounds array
        :type bounds: np.ndarray
        :param ballRadii: sequence of ball radii required
        :type ballRadii: iter
        :return: (array<centerios pointist>,list<radius>)
        :rtype: (ICE)
        """

        ci1 = np.empty((0,ball.center.shape[0]))
        ci2 = []
        for r in clusterRadiiRatios:
            assert r > 0 and r <= 1.0, "invalid ratio"
            r_ = r * ball.radius

            # calculate max distance from .center
            maxDistance = ball.radius - r_
            distance = random.uniform(0.0,maxDistance)
            p = random_npoint_from_point(ball.center,distance)
            ci1 = np.vstack((ci1,p))
            ci2.append(r_)
        return (ci1,ci2)

    # CAUTION: clusterCenter not checked for existing in Ball
    """
    clusterCenter := vector, lies in `ball`
    clusterDensity := int, number of points to add to cluster
    """
    @staticmethod
    def cluster_points_to_ball(ball,clusterCenter,clusterRadii,clusterDensity):
        for i in range(clusterDensity):
            p = random_npoint_from_point(clusterCenter,clusterRadii)
            ball.add_element(p)

    # CAUTION: not tested!
    # CAUTION: `bl` not checked for dimensions
    @staticmethod
    def bounds_for_ball_set(bl):
        assert len(bl) >0, "invalid ballset"

        def extremum_at_index(i):
            x = [(b.center[i] - b.radius,b.center[i] + b.radius)\
                for b in bl]
            x = np.array(x)
            minimum,maximum = np.min(x[:,0]), np.max(x[:,1])
            return (minimum,maximum)

        q = bl[0].center.shape[0]
        bounds = []
        for i in range(q):
            bounds.append(extremum_at_index(i))
        return np.round(np.array(bounds),5)

    @staticmethod
    def ball_set_in_bounds(bounds,bl):
        for b in bl:
            if not b.in_bounds(bounds): return False
        return True

    @staticmethod
    def ball_subset_size_in_bounds(bounds,bl):
        c = 0
        for b in bl:
            if b.in_bounds(bounds):
                c += 1
        return c

    @staticmethod
    def ballset_is_connected(bl):
        assert len(bl) > 0, "invalid ball-set"

        # NOTE: inefficient
        def neighbors_of_ball(bi):
            neighbors = []
            for i in range(len(bl)):
                if i == bi: continue
                if bl[bi].is_neighbor(bl[i]):
                    neighbors.append(i)
            return neighbors

        connected = set()
        cache = [0]
        while len(cache) > 0:
            c = cache.pop(0)
            if c in connected: continue
            connected |= {c}
            ns = neighbors_of_ball(c)
            cache.extend(ns)
        return len(connected) == len(bl)

    # RE-WRITE THIS
    """
    @staticmethod
    def make_relevance_function(clusterInfo):

        def cf(v):
            for (i,c) in enumerate(clusterInfo[0]):
                #print("euclid's distance ", euclidean_point_distance(c,v))
                #print("cluster radius ", clusterInfo[1][i])
                if euclidean_point_distance(c,v) <= clusterInfo[1][i]:
                    return True
            return False

        rch = RChainHead()
        kwargs = ['nr',cf]
        rch.add_node_at(kwargs)
        return rch
    """

    @staticmethod
    def load_data_by_frame(frame,fp):
        return "list<balls>"
