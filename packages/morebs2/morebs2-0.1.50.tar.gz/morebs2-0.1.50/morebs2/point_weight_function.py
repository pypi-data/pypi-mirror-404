from .point_sorter import *

lambda_geq = lambda x,x2: True if x >= x2 else False
lambda_leq = lambda x,x2: True if x <= x2 else False
lambda_ratio = lambda x, x2: float(x) / float(x2)
########## START: similarity measures
'''
some variations on similarity measures, functions that
measure the similarity between two vectors.
'''

def similarity_measure_cast(bounds,weights, measureType):
    assert measureType in [43,44], "invalid measure type {}".format(measureType)

    if measureType == 43:
        q = lambda v1,v2: similarity_measure__type43(v1,v2,bounds,weights)
    else:
        q = lambda v1,v2: similarity_measure__type44(v1,v2,bounds,weights)
    return q

'''
return:
- inf if `centroidValue` is `point`
  0 if inf away
'''
def similarity_measure__type1(v1,v2):
    pd = ndim_point_distance(v1,v2)
    if pd == 0: return np.inf
    pd = pd ** -1.0
    return round(pd,5)

'''
'''
def similarity_measure__type43(v1,v2, bounds, weights):
    assert len(v1) == len(v2), "unequal vector lengths"
    assert bounds.shape[0] == len(v1), "[0] invalid bounds dim"
    assert bounds.shape[1] == 2, "[1] invalid bounds dim"
    assert np.all(weights >= 0.0) and np.all(weights <= 1.0), "invalid weights"

    diff = np.abs(bounds[:,0] - bounds[:,1])

    def f_at(index):
        q = abs(v1[index] - v2[index]) / diff[index]
        return q * weights[index]

    k = len(v1)
    s = 0.0
    for i in range(k):
        s += f_at(i)
    return round(s / k, 5) if k != 0 else 0.0

def similarity_measure__type44(v1,v2,bounds,weights):
    assert len(v1) == len(v2), "unequal vector lengths"
    assert bounds.shape[0] == len(v1), "[0] invalid bounds dim"
    assert bounds.shape[1] == 2, "[1] invalid bounds dim"
    assert weights.shape[0] == len(v1), "[0] invalid weights dim"
    assert weights.shape[1] == 2, "[1] invalid weights dim"

    #
    def vector_sign(v):
        if np.all(v >= 0.0):
            return 1
        elif np.all(v <= 1.0):
            return -1
        else:
            return 0

    def half_of_value(v, b, defaultHalf = None):
        assert len(b) == 2, "invalid range"
        assert defaultHalf in [-1,1,None], "default half is incorrect"
        m = (b[1] - b[0]) / 2.0
        if v > m: return 1
        elif v < m: return -1
        else: return defaultHalf

    vs1 = vector_sign(weights[:,0])
    vs2 = vector_sign(weights[:,1])

    # special assertions for weight signs
    assert vs1 != 0 and vs2 != 0, "invalid column signs for weights"
    assert vs1 != vs2, "must have opposing signs for weights"

    def f_score(v_, index):
        assert v_ in [1,2], "invalid v"
        q = v1 if v_ == 1 else v2
        hf = half_of_value(q[index], bounds[index],None)

        if hf == 1:
            return 2.0 * abs(bounds[index,hf] - q[index]) / abs(bounds[index,0] - bounds[index,1])
        elif hf == -1:
            return 2.0 * abs(bounds[index,hf + 1] - q[index]) / abs(bounds[index,0] - bounds[index,1])
        else:
            return 0

    def f_at(index):
        # get the two f-scores
        fs1 = f_score(1,index)
        fs2 = f_score(2,index)

        # multiply by weights
        fs1 = fs1 * weights[index,0]
        fs2 = fs2 * weights[index,1]

        return abs(fs1 - fs2)

    k = len(v1)
    s = 0.0
    for i in range(k):
        s += f_at(i)

    return round(s / (k * 2.0),5) if k != 0 else 0.0


'''
description:
- similarity measure considers radius info of centroid that v1 belongs to.
  Points `v2` that are farther away from the centroid C(v1) will have higher score.
'''
def similarity_measure__type45(v1,v2, meanRadius,minRadius,maxRadius):

    # perform calculation involving radiusInfo
    # get ratio of mean point to min and max point

    # ratio > 1 => mean radius is closest to max radius\
    if maxRadius - minRadius != 0:
        ratio = meanRadius / float (maxRadius - minRadius)

    pd = similarity_measure__type1(v1,v2)
    return round(pd * ratio,5)

############################ TODO: future
'''
description:
- memory-aware of last significant point score

centroidValue := vector, must be equal in length to `point`
point := vector, point to measure the weight of
lastSignificantPointScore := float
moreSignificant := 1 to use (>=), 0 to use (<=)

return:
- float, `lastSignificantPointScore` if score S of `point` passes `pwf` else S
'''
def point_weight_function_3(centroidValue, point, lastSignificantPointScore, pwf, scoreCompFunc):

    s = pwf(centroidValue,point)
    if scoreCompFunc(lastSignificantPointScore,s):
        # replacement value is lastSignificantPointScore
        s = lastSignificantPointScore
    return s
