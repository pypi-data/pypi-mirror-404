from .line import *
from collections import defaultdict
from copy import deepcopy

ndim_point_distance = lambda p1, p2: np.sum([np.sqrt((p1 - p2)**2)])


def tie_sets_for_vector(vector):
    """Iterate through sorted vector for sets of
    indices. Tie-sets are represented as a sequence of
    (startIndex,endIndex) pairs due to vector
    being ordered.
    """
    if len(vector) == 0: return []

    l = vector.shape[0]

    tss = []
    ts = [0]
    tsv = vector[0]
    i = 1
    while i < l:

        if ts == []:
            if i + 1 == l:
                i += 1
                continue

            if vector[i] == vector[i + 1]:
                ts = [i, i + 1]
                tsv = vector[i]
                i += 2
            else:
                i += 1

        else:
            # pass
            if vector[i] != tsv:

                if ts == [0]:
                    ts = []
                    continue

                tss.append(ts)
                ts = []
            else:
                ##print("NN")
                ts = [ts[0], i]
            i += 1

    if ts != []: tss.append(ts)

    return tss

def sorted_vector_value_range_search(vector, value):

    head, stat = sorted_vector_value_search(vector, value)

    if not stat:
        return head,stat
    q = head + 1
    if q >= vector.shape[0]: return [head,head], stat

    while vector[q] == value:
        q += 1
        if q >= vector.shape[0]: break
    return [head,q - 1], stat

def sorted_vector_value_search(vector, value, irange = None):
    """
    Iterates through a sorted vector for `value`.
    Outputs the "head" index of the value if it exists
    """
    s = np.where(vector == value)[0]

    if len(s) == 0:
        return None,False
    return s[0],True

class PointSorter:
    """
    class can be used by one of these ways: 
    
        (1) instantiate class w/ vector of data, and sort data using
    method<sort_it>, 
        (2) instantiate class w/ empty vector, call method<insert_point>
    to add to data. The sorted vector point data will be variable<newData>.
    
    """

    def __init__(self,data):
        assert is_2dmatrix(data), "invalid data"

        # initial data variable (static)
        self.data = data
        self.newData = np.copy(data)
        self.pointMean,self.pointVar = None,None

        # key: -1 for min, 1 for max
        # value: [0] is vector, [1] is accomodating float
        '''
        variable contains referential extremum pertaining to a reference point.
        Extreme points are calculated based on their magnitudes to reference point.
        '''
        self.extremumData = defaultdict(tuple)
        self.deltaCache = defaultdict(list)
        self.sort_it()
        return

    def clear_delta_cache(self):
        self.deltaCache = defaultdict(list)
        self.deltaCache[-1] = np.empty((0,self.pointMean.shape[0]))
        self.deltaCache[1] = np.empty((0,self.pointMean.shape[0]))

    def sort_it(self):
        if self.newData.shape[0] <= 1:
            return
        self.sort_at_column(0, [0, self.newData.shape[0] - 1])

    def sort_at_column(self, columnIndex, submatrixIndices):

        if columnIndex >= self.newData.shape[1]:
            print("doncesorded")
            return

        # sort submatrix at column
        submatrix = self.newData[submatrixIndices[0]:submatrixIndices[1] + 1]
        q = submatrix[:,columnIndex]

        indices = np.argsort(q)
        newSM = submatrix[indices]
        self.newData[submatrixIndices[0]:submatrixIndices[1] + 1] = newSM

        # check for tie-sets in submatrix
        newV = newSM[:,columnIndex]
        ts = tie_sets_for_vector(newV)
        if len(ts) == 0:
            return
        else:
            for t in ts:
                # calibrate indices
                ci = [submatrixIndices[0] + t[0], submatrixIndices[0] + t[1]]
                # sort
                self.sort_at_column(columnIndex + 1, ci)
        return

    ###---------------------start: point existence --------------------------------------------------------

    def vector_exists(self, vector):
        """
        :return: index of vector that it exists at, -1 if does not exist.
        :rtype: int
        """
        return self.does_vector_exist_(vector, 0, [0, self.newData.shape[0]])

    def does_vector_exist_(self, vector, columnIndex, sampleIndices):

        # case: possible ties due to no more columns, return the head
        if columnIndex >= vector.shape[0]:
            return sampleIndices[0]

        c = self.newData[sampleIndices[0]: sampleIndices[1] + 1][:,columnIndex]
        irange,stat = sorted_vector_value_range_search(c, vector[columnIndex])

        # case: column value does not exist, !vector
        if not stat: return -1

        # case: single sample
        if irange[1] - irange[0] == 0:
            return irange[0] + sampleIndices[0]
        else:
        # multiple samples, iterate on next column
            # new sample indices are irange + calibration ()
            nsi = [sampleIndices[0] + irange[0], sampleIndices[0] + irange[1]]
            return self.does_vector_exist_(vector, columnIndex + 1, nsi)

    ###---------------------end: point existence --------------------------------------------------------

    ###---------------------start: point insertion/deletion --------------------------------------------------------

    def insert_point(self,p):

        # case: empty data, insert
        if self.newData.shape[0] == 0:
            self.newData = np.vstack((self.newData, p))
            return

        # case: non-empty data
        index = 0
        insertIndex = -1
        remVar = np.arange(self.newData.shape[0])
        while index < self.newData.shape[1]:
            v = p[index]
            insertIndex, remVar = self.data_index_for_value_at_column(v,index,remVar)
            if remVar == []:
                break
            index += 1

        # insert at index
        self.insert_at(p, insertIndex)

    '''
    return:
    - index::int, (tie set vector)::bool
    '''
    def data_index_for_value_at_column(self, v, c, possibleIndices):
        # case: zero choices, output -1
        if len(possibleIndices) == 0: return -1

        x = None
        for (i,j) in enumerate(possibleIndices):
            if v <= self.newData[j,c]:
                x = i
                break

        # case: found index, check for ties
        if x != None:
            # subcase: no ties
            if v != self.newData[possibleIndices[x],c]:
                return possibleIndices[x],[]

            # subcase: ties, collect all ties
            l = len(possibleIndices)
            q = [possibleIndices[x]]
            q2 = self.newData[possibleIndices[x],c]
            for j in range(x + 1, l):
                if self.newData[possibleIndices[j],c] == q2:
                    q.append(possibleIndices[j])
                    continue
                break

            return possibleIndices[x],q

        # case: after possible indices, no ties
        return possibleIndices[-1] + 1, []

    def insert_at(self, p, i):
        self.newData = np.concatenate((self.newData[:i], [p], self.newData[i:]))

    def delete_point(self,p):
        i = self.vector_exists(p)

        # case: point does not exist
        if i == -1: return
        self.newData = np.concatenate((self.newData[:i], self.newData[i + 1:]))
        return

    ###---------------------end: point insertion/deletion --------------------------------------------------------

    ###---------------------start: point update by timestamp -----------------------------------------------------

    def log_delta_cache(self,p,additionBool):
        assert additionBool in [1,-1], "invalid addition bool"
        q = self.deltaCache[additionBool]

        if len(q) == 0:
            q = np.array([p])
        else:
            q = np.vstack((q,p))
        self.deltaCache[additionBool] = q

    def update_points_from_cache(self, referencePoint = None):
        '''
        Updates points from delta cache and clears it.
        '''

        # update mean and var
            # update +1
        p = 1
        q = self.delta_points(p)
        self.update_points(q,p)

            # update -1
        p = -1
        q = self.delta_points(p)
        self.update_points(q,p)

        # update extremum
        if type(referencePoint) != type(None):
            self.update_extremum(referencePoint)
        #
        self.deltaCache[-1] = []
        self.deltaCache[1] = []

    def update_points(self,additionalPoints,additionBool):

        if additionBool == -1:
            self.safe_deletion_check(additionalPoints)

        # update measures
        self.update_mean(additionalPoints,additionBool)
        self.update_var(additionalPoints,additionBool)

        # update point data
        f = self.insert_point if additionBool == 1 else self.delete_point
        for i in range(additionalPoints.shape[0]):
            f(additionalPoints[i])

    def delta_points(self,additionBool):
        q = self.deltaCache[additionBool]

        # case: empty
        if type(q) is list:
            return np.empty((0,self.newData.shape[1]))
        else:
            return q

    ###---------------------end: point update by timestamp -----------------------------------------------------

    ###---------------------start: measure update functions

        ####----- methods below perform calculations on entire data `newData`

    def calculate_mean(self):
        self.pointMean = np.mean(self.newData,0)

    def calculate_variance(self):
        self.pointVar = np.var(self.newData,0)

    def calculate_extremum(self,referencePoint):
        d = [ndim_point_distance(referencePoint,p) for p in self.newData]
        imin,imax = np.argmin(d),np.argmax(d)

        self.extremumData[-1] = (self.newData[imin], d[imin])
        self.extremumData[1] = (self.newData[imax], d[imax])

    @staticmethod
    def update_meanbasedvalue(meanBasedValue, pointShape,additionalPoints,additionBool = 1):
        assert is_vector(meanBasedValue) or type(meanBasedValue) is type(None), "invalid mean based value"
        assert is_valid_point(pointShape),"invalid point shape"
        assert is_2dmatrix(additionalPoints), "invalid additional points"
        assert additionalPoints.shape[1] == pointShape[1], "invalid shape for additional points"

        # case: no additional points
        if additionalPoints.shape[0] == 0: return meanBasedValue

        if type(meanBasedValue) is type(None):
            meanBasedValue = np.zeros((pointShape[1]))
        assert meanBasedValue.shape[0] == pointShape[1], "invalid shape for meanBasedValue w/ {}".format(pointShape)

        # case: points are to be subtracted
        if additionBool == -1:
            assert additionalPoints.shape[0] <= pointShape[0], ""

        # prev sum
        s = float(pointShape[0]) * meanBasedValue
        # additional sum
        s2 = np.sum(additionalPoints,axis=0)

        if additionBool == 1:
            # new average
            l = additionalPoints.shape[0] + pointShape[0]
            s3 = (s + s2) / float(l)
        else:
            # new average
            l = pointShape[0] - additionalPoints.shape[0]
            s3 = (s - s2) / float(l)

        return np.round(s3,5)

    def update_mean(self, additionalPoints,additionBool):
        mbs = PointSorter.update_meanbasedvalue(self.pointMean, tuple(self.newData.shape),additionalPoints,additionBool)
        self.pointMean = mbs

    def update_var(self,additionalPoints,additionBool):
        mbs = PointSorter.update_meanbasedvalue(self.pointVar, tuple(self.newData.shape),additionalPoints,additionBool)
        self.pointVar = mbs

    def safe_deletion_check(self,points):
        for p in points: assert self.vector_exists(p)

    def update_extremum(self,referencePoint):
        '''
        Updates extremum based on euclidean distance of reference point to
        points in cache.

        Call this method after `deltaCache` has been updated
        '''
        # addition
        self.update_extremum_(referencePoint,self.deltaCache[1])

        # subtraction
        if type(self.deltaCache[-1]) != list:

            self.calculate_extremum(referencePoint)

    def update_extremum_(self,referencePoint, additionalPoints):
        # case: no additional points
        if len(additionalPoints) == 0: return
        if additionalPoints.shape[0] == 0: return

        q = 0

        # case: empty
        if self.extremumData[-1] == () and self.extremumData[1] == ():

            p = additionalPoints[0]
            d = ndim_point_distance(referencePoint,p)
            self.extremumData[-1] = (p,d)
            self.extremumData[1] = (p,d)
            q = 1

        # update remainder
        for i in range(q,additionalPoints.shape[0]):
            p = additionalPoints[i]
            d = ndim_point_distance(referencePoint,p)

            if d < self.extremumData[-1][1]:
                self.extremumData[-1] = (p,d)

            elif d > self.extremumData[1][1]:
                self.extremumData[1] = (p,d)

        return

    def extreme(self,maxBool):
        assert maxBool in [-1,1]
        return deepcopy(self.extremumData[maxBool])

    ###---------------------end: measure update functions
