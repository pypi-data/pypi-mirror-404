from .ball_comp_components import *
from .set_merger import *

def estimate_n_intersection(intersectionAreas):
    return min(intersectionAreas) * 0.5

class DisjunctionVolumeEstimator:
    """
    Estimates the disjunction of a set of balls based on
    induction using 2-intersection volumes.
    """

    def __init__(self):

        # single-ball volumes: int->float
        self.ballVolumes = {}

        # all 2-intersection volumes
        self.d = {}

        # ball-set intersection volumes: str->float
        self.bv = {}

        self.cache1 = [] # single-ball volume
        self.cache2 = [] # 2-intersection volume

    def log_ball_volume(self,b1):
        prev = self.ballVolumes[b1.idn] if b1.idn in self.ballVolumes else None
        self.ballVolumes[b1.idn] = ball_area(b1.radius,b1.center.shape[0])
        self.cache1.append([b1.idn,prev])

    def log_ball_volume_2intersection(self,b1,b2,updateValue=True):
        k = vector_to_string(sorted([b1.idn,b2.idn]))

        # case: do not update
        if not updateValue and k in self.d:
            return

        # log previous value into cache
        x = None if k not in self.d else self.d[k]
        self.cache2.append([k,x])

        est = volume_2intersection_estimate(b1,b2)
        ###print("$EST FOR {}: {}".format(k,est))
        self.d[k] = est

    def clear_cache(self):
        self.cache1 = []
        self.cache2 = []
        return

    def revert_cache_delta(self,cacheId):
        if cacheId == 1:
            c = self.cache1
            d = self.ballVolumes
        else:
            c = self.cache2
            d = self.d

        while len(c) > 0:
            p = c.pop(0)
            if type(p[1]) == type(None):
                del d[p[0]]
            else:
                d[p[0]] = p[1]

    def revert_cache2_delta(self):
        while len(self.cache2) > 0:
            p = self.cache2.pop(0)
            if type(p[1]) == type(None):
                del self.d[p[0]]
            else:
                self.d[p[0]] = p[1]

    def two_intersection_ball_volume(self,k):
        if k not in self.d: return None
        return self.d[k]

    def target_ball_neighbors(self,bIdn):
        s = set()
        for x in self.d.keys():
            q = string_to_vector(x)
            if bIdn in q:
                s = s | {q[0] if q[0] != bIdn else q[1]}
        return s

    def relevant_2intersections_for_ballset(self,bs):
        twoIntersections = []
        for x in self.d.keys():
            q = string_to_vector(x)
            if q[0] in bs and q[1] in bs:
                twoIntersections.append(set(q))
        return twoIntersections

    def estimate_disjunction_at_target_ball(self,bIdn, verbose,capacity = 500):
        # get 1-intersection volume
        tan = self.target_ball_neighbors(bIdn) | {bIdn}
        q = sum([self.ballVolumes[k] for k in tan])

        # get 2-intersection volumes
        ##ti = self.relevant_2intersections_for_ballset(tan)
        ti = self.relevant_2intersections_for_ballset({bIdn})

        # case: no intersections
        if len(ti) == 0:
            return q

        # minus two-intersection volumes
        q2 = np.sum([self.d[vector_to_string(sorted(t))] for t in ti])
        q -= (q2 * 2)
        j = 3
        c = 1.0
        if verbose:
            print("\t\t{} relevant 2-int".format(len(ti)))
        self.sm = SetMerger(ti)

        self.bv = deepcopy(self.d)
        # alternately add and minus j'th intersection volumes
        x = j if verbose else False
        while True:
            # estimate the j'th disjunction value
            a = self.estimate_disjunction_at_target_ball_(x,capacity)
            if a == 0.0:
                break
            q += (a * j * c)

            # increment the coefficients
            c = -1 * c
            j += 1
            if verbose: print("^ depth @ ", j)
        return q

    def estimate_disjunction_at_target_ball_(self,verbose = False,capacity = None):
        """
        Performs a `SetMerger.merge_one` operation and estimate volumes of new
        intersection sets.

        :param verbose:
        :type verbose: bool
        :param capacity: size capacity for merges, use to prevent memory use error.
        :type capacity: int
        """

        # merge one and collect the new merges and their predecessors
        r1,r2 = self.sm.merge_one(True,True,verbose)

        if len(r1) == 0:
            return 0.0

        if len(r1) >= capacity:
            return 0.0

        # calculate the intersection estimate of each predecessor
        vs = []
        for r in r2:
            iv = self.estimate_int_value(r)
            vs.append(iv)

        self.bv = {}
        q = 0.0
        for (r1_,vs_) in zip(r1,vs):
            k = vector_to_string(sorted(r1_))
            self.bv[k] = vs_
            q += vs_
        return q

    def estimate_int_value(self,iSet,):
        """
        Calculates the intersection-related value for disjunction estimation

        :param iSet: ^^^^^
        :type iSet: iter<vector>
        """

        # collect volumes
        ##print("BV\n", self.bv)
        v = []
        for x in iSet:
            q = vector_to_string(sorted(x))
            v.append(self.bv[q])
        return estimate_n_intersection(v)

    def delete_keyset(self,keySet):
        """
        iterates through keyset and deletes all keys found in keyset from
        `ballVolumes` and `d`

        :param keySet: settias correspondas es keys
        :type keySet: list<int>
        """
        # delete ball volume
        for k in keySet:
            del self.ballVolumes[k]

        # delete 2-intersections
        ks = list(self.d.keys())

        for k in ks:
            q = string_to_vector(k)
            if q[0] in keySet or q[1] in keySet:
                del self.d[k]
        return
