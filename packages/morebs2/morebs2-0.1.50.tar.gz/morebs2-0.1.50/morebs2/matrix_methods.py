from .globalls import *
import math

def equal_iterables(i1, i2, roundPlaces = 5):
    """
    equal_iterables

    :param i1: iterable
    :type i1: iter
    :param i2: iterable
    :type i2: iter
    :param roundPlaces: positive int.
    :type roundPlaces: int
    :return: equal_iterables
    :rtype: bool
    """

    if len(i1) != len(i2): return False

    """
    if np.all(np.equal(np.round(i1, roundPlaces), np.round(i2, roundPlaces)) == True): return True
    return False
    """
    q = np.abs(np.array(i1) - np.array(i2))
    return np.all(q <= 10 ** -roundPlaces)

def indices_of_vector_in_matrix(a, v):
    assert is_2dmatrix(a) and is_vector(v), "invalid criteria"
    a = np.round(a,5)
    v = np.round(v,5)
    indices = []
    for (i, x) in enumerate(a):
        if np.all(np.equal(x, v) == True): indices.append(i)
    return np.array(indices)

def is_2dmatrix(m):
    if type(m) is not np.ndarray: return False
    if len(m.shape) != 2: return False
    return True

def is_bounds_vector(b):
    q = is_2dmatrix(b)
    if not q: return q
    return b.shape[1] == 2

def is_vector(m):
    if type(m) is not np.ndarray: return False
    if len(m.shape) != 1: return False
    return True

def is_binary_vector(b):
    assert is_vector(b), "invalid vector"
    q = np.unique(b)
    return q, len(q) == 2

def is_valid_point(point):
    assert not type(point) is np.ndarray, "point cannot be np.ndarray"
    if len(point) != 2: return False
    if not type(point[0]) in [int, float, np.int64, np.float64]: return False# or type(point[0]) is float): return False
    if not type(point[1]) in [int, float, np.int64, np.float64]: return False
    return True

def is_valid_range(r,is_int:bool=True,inclusive:bool=True):
    if not (type(r) in [list,tuple]): return False
    if not (len(r) == 2): return False

    if is_int: 
        if not (type(r[0]) == type(r[1])): return False
        if not (type(r[0]) == int): return False

    if inclusive:
        if not (r[0] <= r[1]): return False
    else: 
        if not (r[0] < r[1]): return False
    return True 

def is_number(n,exclude_types=set()): 
    q = NUMERICAL_TYPES - set(exclude_types)
    return type(n) in q 

def np_array_to_string(a):
    assert type(a) is np.ndarray, "not np.ndarray"
    s = str(a).replace("\n", "\t")
    return s

# TODO: expand on criteria
# TODO: unused
def frequency_count_over_2dmatrix(a, floatValue, rowOrColumn = None):
    r,c = np.where(a == floatValue)
    if rowOrColumn == "r": return r
    elif rowOrColumn == "c": return c
    return r,c

# TODO: test
def range_intersection(range1,range2):
    assert is_valid_range(range1,is_int=False,inclusive=True)
    assert is_valid_range(range2,is_int=False,inclusive=True)

    # check range 1
    if range1[0] >= range2[0] and range1[0] <= range2[1]: return True
    if range1[1] >= range2[0] and range1[1] <= range2[1]: return True

    # check range 2
    if range2[0] >= range1[0] and range2[0] <= range1[1]: return True
    if range2[1] >= range1[0] and range2[1] <= range1[1]: return True

    return False

# TODO: test
def complement_of_range_in_range(range1, range2):
    assert range1[0] <= range1[1], "invalid range 1"
    if range2 == None: return range1

    assert range2[0] <= range2[1], "invalid range 2"
    assert range2[0] >= range1[0] and range2[1] <= range1[1], "range 2 not in range 1"

    filter_null_range = lambda r: False if abs(r[0] - r[1])\
                                <= 10 ** -5 else True

    q1 = (range1[0], range2[0])
    q2 = (range2[1], range1[1])
    output = []

    if filter_null_range(q1): output.append(q1)
    if filter_null_range(q2): output.append(q2)

    return output

'''
- 2dmatrix, sequence of values, partition centers
'''
def central_sequence_of_sequence(ps):
    assert type(ps) is np.ndarray, "invalid partition sequence"

    cs = np.empty((ps.shape[0] - 1, ps.shape[1]))
    for i in range(1, len(ps)):
        center = (ps[i] + ps[i - 1]) / 2.0
        cs[i - 1] = center
    return np.round(cs,5)

################################################ START: area measures
def is_valid_area(area):
    """
    Area is 2 x 2 matrix in which [0] represents bottom left, [1] represents upper right.
    """
    return False if not is_2dmatrix(area) else True
    if area.shape[0] != 2 or area.shape[1] != 2: return False
    if area[0,0] > area[1,0]: return False
    if area[0,1] > area[1,1]: return False
    return True

def dim_of_area(area):
    assert is_valid_area(area), "invalid area"
    return area[1,0] - area[0,0], area[1,1] - area[0,1]

def value_of_area(area):
    dim = dim_of_area(area)
    return dim[0] * dim[1]

def area_in_area(a1, a2):
    """
is a1 in a2
    """
    assert is_valid_area(a1) and is_valid_area(a2), "input are not areas"
    if not (a1[0,0] >= a2[0,0] and a1[1,0] <= a2[1,0]): return False
    if not (a1[0,1] >= a2[0,1] and a1[1,1] <= a2[1,1]): return False
    return True

def area_intersects(a1, a2):
    assert is_valid_area(a1) and is_valid_area(a2), "input are not areas"

    # left bottom
        # intersects
    # bottom left
    if a1[0,0] >= a2[0,0] and a1[0,0] <= a2[1,0]\
        and a1[0,1] >= a2[0,1] and a1[0,1] <= a2[1,1]:
        return True

    # upper left
    if a1[0,0] >= a2[0,0] and a1[0,0] <= a2[1,0]\
        and a1[1,1] >= a2[0,1] and a1[1,1] <= a2[1,1]:
        return True

    # bottom right
    if a1[1,0] >= a2[0,0] and a1[1,0] <= a2[1,0]\
        and a1[0,1] >= a2[0,1] and a1[0,1] <= a2[1,1]:
        return True

    # upper right
    if a1[1,0] >= a2[0,0] and a1[1,0] <= a2[1,0]\
        and a1[1,1] >= a2[0,1] and a1[1,1] <= a2[1,1]:
        return True
    return False

# TODO: necessary?
def is_area_qualified(unqualified, area):
    for x in unqualified:
        if area_intersects(x, area): return False
    return True

# TODO: test
def point_in_area(point, area):
    assert is_valid_point(point)
    if not (point[0] >= area[0,0] and point[0] <= area[1,0]):
        return False
    if not (point[1] >= area[0,1] and point[1] <= area[1,1]):
        return False
    return True

def is_point_qualified(unqualifiedAreas, point):

    for x in unqualifiedAreas:
        if point_in_area(point, x): return False
    return True

"""
if degree in [0,90,180,270],

0: 0
90: 1
180: 2
270: 3
"""
def quadrant_of_corner_point_in_area(cp, area):
    corners = area_to_corners(area)
    indices = indices_of_vector_in_matrix(corners, cp)
    if len(indices) != 1: raise ValueError("quadrant for corner point {} could not be obtained for\n{}".format(cp, corners))
    return indices[0]

############################################ END: area

############################################ START: qualifying area search

"""
incrementInfo: dict, keys are [str::"axis" = x|y, float::"increment"]
"""
def extreme_xy_from_point(unqualifiedAreas, area, point, incrementInfo):
    # set up increment and qualifying methods for point increment
    if incrementInfo["axis"] == "x":
        if incrementInfo["increment"] >= 0: qf = lambda p: True if p[0] <= area[1,0] else False
        else: qf = lambda p: True if p[0] >= area[0,0] else False
        ifunc = lambda p: (p[0] + incrementInfo["increment"], p[1])
    elif incrementInfo["axis"] == "y":
        if incrementInfo["increment"] >= 0: qf = lambda p: True if p[1] <= area[1,1] else False
        else: qf = lambda p: True if p[1] >= area[1,0] else False
        ifunc = lambda p: (p[0], incrementInfo["increment"] + p[1])
    else:
        raise ValueError("invalid axis")

    # increment
    prev = None
    pp = point
    while qf(pp):
        if not is_point_qualified(unqualifiedAreas, pp):
            break
        prev = pp
        pp = ifunc(pp)

    return prev

# TODO: implement this.
def greatest_qualifying_area_in_vector_direction(vector, unqualifiedAreas, area, incrementDirections, areaWanted):
    return -1

# TODO: areaWanted needs to be tested.
"""
description:
- approximately determines the greatest quadrilateral with point as one of the four corner points.
  Given the start `point`, determines the extreme x and extreme y point using `incrementDirections`.

arguments:
- point: iterable, length 2
- unqualifiedAreas: np.ndarray, n x 2 x 2
- area: np.ndarray, 2 x 2
- incrementDirections: dict, (increment::float), (direction::((0&1)::(1|-1)))
- areaWanted: max|xmax|ymax
"""
def greatest_qualifying_area_in_direction(point, unqualifiedAreas, area, incrementDirections, areaWanted):

    assert type(incrementDirections["increment"]) is float and incrementDirections["increment"] > 0, "inc. wrong type"
    assert incrementDirections["direction"][0] in [-1,1], "axis 0 inc. wrong"
    assert incrementDirections["direction"][1] in [-1,1], "axis 1 inc. wrong"

    # extreme x
    id1 = {"axis": 0}
    id1["increment"] = incrementDirections["increment"] * incrementDirections["direction"][0]
    pointX = greatest_qualifying_fourway_point_at_point(point, unqualifiedAreas, area, id1)

    # extreme y
    id2 = {"axis": 1}
    id2["increment"] = incrementDirections["increment"] * incrementDirections["direction"][1]
    pointY = greatest_qualifying_fourway_point_at_point(point, unqualifiedAreas, area, id2)

    # TODO: refactor below.
    if areaWanted == "max":
        # get other extremes
        maxYGivenX = greatest_qualifying_fourway_point_at_point(pointX, unqualifiedAreas, area, id2)
        maxXGivenY = greatest_qualifying_fourway_point_at_point(pointY, unqualifiedAreas, area, id1)

        # get areas for each
        #   [0]
        mp1 = missing_area_point_for_three_points(np.array([maxYGivenX, pointX, point]))
        area1 = trim_area(area, corners_to_area(np.array([maxYGivenX, pointX, point, mp1])))
        a1 = value_of_area(area1)
        #   [1]
        mp2 = missing_area_point_for_three_points(np.array([maxXGivenY, pointY, point]))
        area2 = trim_area(area, corners_to_area(np.array([maxXGivenY, pointY, point, mp2])))

        a2 = value_of_area(area2)

        if a1 > a2: return area1
        return area2

    elif areaWanted == "xmax":
        maxYGivenX = greatest_qualifying_fourway_point_at_point(pointX, unqualifiedAreas, area, id2)
        mp1 = missing_area_point_for_three_points(np.array([maxYGivenX, pointX, point]))
        area1 = trim_area(area, corners_to_area(np.array([maxYGivenX, pointX, point, mp1])))
        return area1

    elif areaWanted == "ymax":
        maxXGivenY = greatest_qualifying_fourway_point_at_point(pointY, unqualifiedAreas, area, id1)
        mp2 = missing_area_point_for_three_points(np.array([maxXGivenY, pointY, point]))
        area2 = trim_area(area, corners_to_area(np.array([maxXGivenY, pointY, point, mp2])))
        return area2
    raise ValueError("invalid wanted area arg.")

"""
iterate from .min x (point) in `incrementDirections` at in

incrementDirections: increment|axis
"""
def greatest_qualifying_fourway_point_at_point(point, unqualifiedAreas, area, incrementDirections):

    if incrementDirections["increment"] >= 0:
        term = lambda s: True if point >= area[1,incrementDirections["axis"]] else False
    else:
        ##assert not (increment < 0), "invalid increment"
        term = lambda s: True if point <= area[1,incrementDirections["axis"]] else False

    inc = lambda p: (p[0], p[incrementDirections["axis"]] + incrementDirections["increment"]) if incrementDirections["axis"] == 1 else\
                (p[incrementDirections["axis"]] + incrementDirections["increment"], p[1])

    prevPoint = None
    point_ = (point[0], point[1])
    while point_in_area(point_, area):
        # check for qual
        if not is_point_qualified(unqualifiedAreas, point_): break
        prevPoint = point_
        point_ = inc(point_)
    return prevPoint

"""
description:
- given a 4 x 2 matrix with each element a corner, determines the lower left and upper
  right points.

arguments:
- fourSizedArea: 4 x 2 np.ndarray

return:
- 2 x 2 np.ndarray
"""
def corners_to_area(fourSizedArea):
    assert not (len(fourSizedArea.shape) != 2 or fourSizedArea.shape[0] != 4\
        or fourSizedArea.shape[1] != 2)

    # get min x, min y
    minXIndices, minYIndices = np.where(fourSizedArea[:,0] == np.min(fourSizedArea[:,0])),\
                            np.where(fourSizedArea[:,1] == np.min(fourSizedArea[:,1]))

    index = np.intersect1d(minXIndices, minYIndices)
    if len(index) != 1:
        print("MI")
        print(minXIndices)
        print(minYIndices)
        print("\nFSA")
        print(fourSizedArea)

        raise ValueError("points do not compose an area")
    minPoint = fourSizedArea[index[0]]

    #   frequency count, minPoint[0] occurs twice, minPoint[1] occurs twice
    locs = np.where(fourSizedArea[:,0] == minPoint[0])[0]
    if len(locs) != 2: raise ValueError("x coord. violation 1")

    locs = np.where(fourSizedArea[:,1] == minPoint[1])[0]
    if len(locs) != 2: raise ValueError("y coord. violation 1")

    # get max x, max y
    maxXIndices, maxYIndices = np.where(fourSizedArea[:,0] == np.max(fourSizedArea[:,0])),\
                            np.where(fourSizedArea[:,1] == np.max(fourSizedArea[:,1]))
    index = np.intersect1d(maxXIndices, maxYIndices)
    if len(index) != 1: raise ValueError("points do not compose an area")
    maxPoint = fourSizedArea[index[0]]

    #   frequency count, maxPoint[0] occurs twice, maxPoint[1] occurs twice
    locs = np.where(fourSizedArea[:,0] == maxPoint[0])[0]
    if len(locs) != 2: raise ValueError("x coord. violation 1")

    locs = np.where(fourSizedArea[:,1] == maxPoint[1])[0]
    if len(locs) != 2: raise ValueError("y coord. violation 1")
    return np.array([minPoint, maxPoint])

"""
"""
def trim_area(totalArea, area):
    assert is_valid_area(totalArea), "invalid total area"
    assert is_valid_area(area), "invalid area"
    # check min x
        # case: less than min x total
    if area[0,0] < totalArea[0,0]:
        area[0,0] = totalArea[0,0]

        # case: greater than max x total
    elif area[0,0] > totalArea[1,0]:
        area[0,0] = totalArea[1,0]

    # check min y
        # case: less than min y total
    if area[0,1] < totalArea[0,1]:
        area[0,1] = totalArea[0,1]

        # case: greater than max y total
    elif area[0,1] > totalArea[1,1]:
        area[0,1] = totalArea[1,1]

    # check max x
        # case: greater than max x total
    if area[1,0] > totalArea[1,0]:
        area[1,0] = totalArea[1,0]

        # case: less than min x total
    elif area[1,0] < totalArea[0,0]:
        area[1,0] = totalArea[0,0]

    # check max y
        # case: greater than max y total
    if area[1,1] > totalArea[1,1]:
        area[1,1] = totalArea[1,1]

        # case: less than min y total
    elif area[1,1] < totalArea[0,1]:
        area[1,1] = totalArea[0,1]
    return area

# TODO: matrix index accessor (using list of int.)
# TODO: approximate decimals to 5 places.

# TODO: needs to be tested.

# TODO: does not perform argument check on three points!
"""
description:
- determines the missing rectangular area point given three points.

arguments:
- threePoints: numpy array.

return:
- (float,float)
"""
def missing_area_point_for_three_points(threePoints):
    assert is_2dmatrix(threePoints)

    # find the center point
    index = center_point(threePoints)
    if index == -1: raise ValueError("[0] points given is invalid area")
    center = threePoints[index]

    # find the extreme-y point
    index2 = np.where(threePoints[:,0] == center[0])[0]
    if len(index2) != 2: raise ValueError("[1] points given is invalid area")
    yPoint = threePoints[index2[0] if index2[0] != index else index2[1]]

    # find the extreme-x point
    index3 = np.where(threePoints[:,1] == center[1])[0]
    if len(index3) != 2: raise ValueError("[2] points given is invalid area")
    xPoint = threePoints[index3[0] if index3[0] != index else index3[1]]

    return (xPoint[0], yPoint[1])

# TODO: test this 
def diagonal_type__2d(twoPoints): 
    """
    :return: 0 for not diagonal, 1 for left-hand diagonal, 2 for right-hand diagonal
    :rtype: int
    """
    assert is_2dmatrix(twoPoints), "invalid points"
    assert twoPoints.shape[0] == 2 and twoPoints.shape[1] == 2, "invalid shape for points"

    dx = round(twoPoints[0,0] - twoPoints[1,0],5)
    if dx == 0.0: return 0 
    dy = round(twoPoints[0,1] - twoPoints[1,1],5)
    if dy == 0.0: return 0 

    p1,p2 = None,None
    if twoPoints[0,0] < twoPoints[1,0]: 
        p1 = twoPoints[0]
        p2 = twoPoints[1] 
    else: 
        p1 = twoPoints[1]
        p2 = twoPoints[0]  

    if p1[1] > p2[1]: 
        return 1 
    return 2 

# TODO: untested, wrong
def other_points_for_two_points_in_area(twoPoints):
    assert is_2dmatrix(twoPoints), "invalid points"
    assert twoPoints.shape[0] == 2 and twoPoints.shape[1] == 2, "invalid shape for points"

    dt = diagonal_type__2d(twoPoints) 
    if dt == 0: 
        return None,None 

    px0,py0,px1,py1 = None,None,None,None 
    if dt == 1: 
        px0 = min(twoPoints[:,0])
        py0 = min(twoPoints[:,1])
        px1 = max(twoPoints[:,0])
        py1 = max(twoPoints[:,1])
    else: 
        px0 = min(twoPoints[:,0])
        py0 = max(twoPoints[:,1])
        px1 = max(twoPoints[:,0])
        py1 = min(twoPoints[:,1])        

    M = np.array([[px0,py0],[px1,py1]])
    return M 

# TODO: untested
def two_points_to_area(twoPoints):

    assert abs(twoPoints[0,0] - twoPoints[1,0]) > 10 ** -5, "two points cannot have same x-coord."
    assert abs(twoPoints[0,1] - twoPoints[1,1]) > 10 ** -5, "two points cannot have same y-coord."

    p0 = (max(twoPoints[:,0]), max(twoPoints[:,1]))
    p1 = (min(twoPoints[:,0]), max(twoPoints[:,1]))
    p2 = (min(twoPoints[:,0]), min(twoPoints[:,1]))
    p3 = (max(twoPoints[:,0]), min(twoPoints[:,1]))
    data = np.array([p0,p1,p2,p3])
    return corners_to_area(data)

def diagonal_line_from_corner_point_in_area(area, cornerPoint):
    q = quadrant_of_corner_point_in_area(area,cornerPoint)
    q2 = (q + 2) % 4
    return Line(np.array([q,q2]))

"""
description:
- given three points that form a right angle, determines the point in the middle.
  If the three points do not form a right angle, then returns -1 .
"""
def center_point(threePoints:np.ndarray, index = 0):
    if index < 0: raise ValueError("invalid index")
    if index >= threePoints.shape[0]: return -1

    indices = np.where(threePoints[:,0] == threePoints[index,0])[0] # TODO: check that equality works
    indices2 = np.where(threePoints[:,1] == threePoints[index,1])[0]
    if (True if len(indices) == 2 and len(indices2) == 2 else False):
        return index
    return center_point(threePoints, index + 1)

def area_to_corners(area):
    assert is_valid_area(area), "invalid area {}".format(area)
    upperLeft = [area[0,0], area[1,1]]
    lowerRight = [area[1,0], area[0,1]]
    return np.round(np.array([area[1], upperLeft, area[0], lowerRight]),5)

############################################ START: qualifying area search

"""
return:
- (start)::float,(end)::float,(distance)::float
"""
###
def largest_subrange_of_coincidence_between_ranges(r1,r2, roundDepth = 5):
    assert len(r1) == 2 and len(r2) == 2, "invalid ranges {} and {}".format(r1,r2)
    r1,r2 = sorted(r1), sorted(r2)

    # use r2 as reference

    # case: r2[0] in r1
    if r2[0] >= r1[0] and r2[0] <= r1[1]:
        # check r2[1] in r1
        if r2[1] >= r1[0] and r2[1] <= r1[1]:
            rx = list(r2) + [r2[1] - r2[0]]
            return tuple(np.round(rx,roundDepth))
        else:
            rx = [r2[0],r1[1]] + [r1[1] - r2[0]]
            return tuple(np.round(rx,5))

    elif r2[1] >= r1[0] and r2[1] <= r1[1]:
        rx = [r1[0],r2[1]] + [r2[1] - r1[0]]
        return tuple(np.round(rx,5))
    return None,None,0.0

def is_proper_color(color):
    if color == None or type(color) in [int,float]: return False
    if len(color) != 3: return False #, "invalid length {} for color".format(len(color))
    for c in color:
        if type(c) not in [int,float]: return False #, "invalid type {} for color".format(type(c))
    return True

def area_to_pygame_rect_format(area):
    assert is_valid_area(area), "area {} is not valid!".format(area)
    lt = area[0]
    w,h = area[1,0] - area[0,0], area[1,1] - area[0,1]
    return np.array([lt, [w,h]])

## TODO:
"""
def area_from_point(p, areaWidth, areaHeight):
    q2 = (p[0] + areaWidth, p[1] + areaHeight)
    return np.array([p,q2])
"""

def point_to_area(p, areaWidth, areaHeight):
    assert is_valid_point(p), "invalid point {}".format(p)
    assert areaWidth > 0.0 and areaHeight > 0.0, "invalid width and height"
    w,h = areaWidth / 2.0, areaHeight / 2.0
    start = (p[0] - w, p[1] - h)
    end = (p[0] + w, p[1] + h)
    return np.array([start,end])



################################## START: cast functions

def float_func(s):
    q = float(s)
    return np.round(q, 5)

"""
always floor
"""
def int_func(s):
    return int(floorceil_to_n_places(float(s), 'f', places = 5))

def floorceil_to_n_places(f, mode, places = 5):
    assert places >= 0 and type(places) is int, "invalid places {}".format(places)
    assert mode in ["f","c"], "invalid mode {}".format(mode)

    d = f % 1.0
    w = f // 1.0
    q = 0.0
    lastDelta = 0.0
    for i in range(places):
        ten = 10 ** (-(i + 1))
        newD = d % ten
        q += (d - newD)
        if (d - newD) > 0: lastDelta = ten
        d = newD
    o = w + q
    if mode == "f": return o
    if f - o > 0:
        return o + lastDelta

################################## END: cast functions

#
cr = lambda x: round(float(x),5)

# TODO: rename to `iterable`
def vector_to_string(v, castFunc = int):
    assert castFunc in [int,float, float_func,cr], "invalid cast func"
    if len(v) == 0: return ""

    s = ""
    for v_ in v:
        s += str(castFunc(v_)) + ","
    return s[:-1]

# TODO: untested
def string_to_vector(s, castFunc = int):
    assert castFunc in [float, float_func, int,cr], "invalid cast func"

    def next_item(s):
        indo = len(s)
        for (i, q) in enumerate(s):
            if q == ",":
                indo = i
                break
        return s[:indo], s[indo + 1:]

    q = []
    while s != "":
        s1,s2 = next_item(s)
        v = castFunc(s1)
        q.append(v)
        s = s2
    return np.array(q)

def float_to_string(f,exclude_int:bool=False,exclude_exp:bool=False):
    sf = str(f)

    if exclude_int:
        q = sf.find(".")
        if q != -1:
            sf = sf[q+1:] 
    
    if exclude_exp:
        q = sf.find("E")
        if q != -1:
            sf = sf[:q] 
    return sf  

def write_vector_sequence_to_file(f,s,mode='w'):
    with open(f,mode) as fo:
        s2 = [vector_to_string(s_,cr) + "\n" for s_ in s]
        fo.writelines(s2)

######## start: some methods on bounds

euclidean_point_distance = lambda p1, p2: np.sqrt(np.sum((p1 - p2)**2))

'''
'''
def intersection_of_bounds(b1,b2):
    # check for each column
    assert is_2dmatrix(b1) and is_2dmatrix(b2),"invalid bounds {}\n\n\t{}".format(b1,b2)
    assert b1.shape == b2.shape, "must have equal shape"

    # check for each index
    bx = []
    for i in range(b1.shape[0]):
        q1,q2 = b1[i],b2[i]
        start,end,dist = largest_subrange_of_coincidence_between_ranges(q1,q2,5)
        if dist != 0:
            bx.append([start,end])
        else:
            return None
    return np.array(bx)

'''
b2 in b1?
'''
def bounds_is_subbounds(b1,b2):
    assert is_proper_bounds_vector(b1) and is_proper_bounds_vector(b2), "invalid args."
    assert b1.shape[0] == b2.shape[0], "invalid args. 2"

    def x(i):
        return b2[i,0] >= b1[i,0] and b2[i,1] <= b1[i,1]
    for i in range(b1.shape[0]):
        if not x(i): return False
    return True

"""
Calculates a subbound of bound `b` w/ start equal to the start of `b`,

boundRange := list({0,1})
"""
def subbound_of_bound(b, boundRange):
    assert is_2dmatrix(b), "invalid type for bounds"
    assert b.shape[1] == 2, "invalid shape for bounds"

    assert is_valid_point(boundRange), "[0] invalid bound range"
    assert np.all(np.array(boundRange) >= 0) and np.all(np.array(boundRange) <= 1), "[1] invalid bound range"
    assert len(boundRange) == 2, "[2] invalid bound range"

    diff = b[:,1] - b[:,0]

    s = b[:,0] + (diff * boundRange[0])
    e = b[:,0] + (diff * boundRange[1])
    return np.vstack((s,e)).T

def n_partition_for_bound(b, partition):

    q = (b[:,1] - b[:,0]) / float(partition)
    x0 = np.copy(b[:,0])
    partition_ = [x0]
    for i in range(partition):
        x1 = x0 + q
        x0 = np.copy(x1)
        partition_.append(x0)
    return np.array(partition_)

def invert_bounds(b):
    assert is_bounds_vector(b), "invalid bounds vector"
    b2 = np.empty((b.shape[0],2))

    b2[:,0] = np.copy(b[:,1])
    b2[:,1] = np.copy(b[:,0])
    return b2

def to_proper_bounds_vector(b):
    assert is_bounds_vector(b), "invalid bounds vector"

    b2 = np.empty((b.shape[0],2))
    b2[:,0] = np.min(b,axis=1)
    b2[:,1] = np.max(b,axis=1)
    return b2

def is_proper_bounds_vector(b):
    assert is_bounds_vector(b), "invalid bounds vector {}".format(b)
    return np.all(b[:,0] <= b[:,1])

def partial_invert_bounds(b, indices):
    return -1

# TODO: untested
def extremum_for_points(a):
    '''
    calculates the `n` extreme (min & max) values for the
    `m x n` matrix `a`.
    '''

    assert is_2dmatrix(a), "invalid points"
    mi = np.min(a,axis = 0)
    ma = np.max(a,axis = 0)
    b = np.empty((a.shape[1],2))
    b[:,0] = mi
    b[:,1] = ma
    return b

def point_in_bounds(b,p):
    '''
    determines if point `p` in bounds `b`

    :param b: proper bounds vector
    :param p: vector
    :rtype: bool
    '''

    assert is_proper_bounds_vector(b), "invalid bounds vector"
    assert is_vector(p), "invalid point"
    assert b.shape[0] == p.shape[0]
    return np.all(b[:,0] <= p) and np.all(b[:,1] >= p)

def point_in_bounds_(b,p):
    if b.shape[0] == 1:
        return np.all(b[0,0] <= p) and np.all(b[0,1] >= p)
    return point_in_bounds(b,p)

def point_in_improper_bounds(parentBounds,bounds,p):

    if is_proper_bounds_vector(bounds):
        assert bounds_is_subbounds(parentBounds,bounds), "invalid parent bounds"
        return point_in_bounds(bounds,p)

    ibs = split_improper_bound(parentBounds,bounds,checkPoints = True)

    rf = lambda f,i: (f >= ibs[0][i,0] and f <= ibs[0][i,1]) or\
                (f >= ibs[1][i,0] and f <= ibs[1][i,1])

    for (i,p_) in enumerate(p):
        if not rf(p_,i): return False
    return True


def point_difference_of_improper_bounds(improperBounds,parentBounds):
    """
    point difference of improper bounds is a non-negative vector
    with each i'th element the positive distance between the two points
    of the `improperBounds` in the context of the `parentBounds`. 
    
    :param improperBounds: bounds located in parentBounds
    :param parentBounds: bounds used as context for `improperBounds`. 
    """

    assert improperBounds.shape == parentBounds.shape, "bounds must have equal shape"
    if is_proper_bounds_vector(improperBounds):
        return improperBounds[:,1] - improperBounds[:,0]

    diff = []
    for i in range(improperBounds.shape[0]):
        r = improperBounds[i]
        j = parentBounds[i]

        # proper dim.
        if r[0] < r[1]:
            d = r[1] - r[0]
        # improper dim.
        else:
            d = j[1] - r[0]
            d += (r[1] - j[0])
        diff.append(d)
    return np.array(diff)


# TODO: unused
'''
'''
def split_improper_bound(properBounds,improperBounds,checkPoints = True):
    if checkPoints:
        assert point_in_bounds(properBounds,improperBounds[:,0]), "end0 of bounds not in proper bounds,\npoint {}\nbounds {}".format(improperBounds[:,0],properBounds)
        assert point_in_bounds(properBounds,improperBounds[:,1]), "end1 of bounds not in proper bounds"

    q1,q2 = [],[]
    for i in range(properBounds.shape[0]):
        r = improperBounds[i]
        # proper dim.
        if r[0] < r[1]:
            s1,s2 = np.copy(r),np.array([np.nan,np.nan])
        # improper dim.
        else:
            s1,s2 = np.array([r[0],properBounds[i,1]]), np.array([properBounds[i,0],r[1]])
        q1.append(s1)
        q2.append(s2)
    return np.array(q1),np.array(q2)

def point_on_bounds_by_ratio_vector(b,rv):
    x = rv * (b[:,1] - b[:,0])
    return b[:,0] + x

def point_on_improper_bounds_by_ratio_vector(parentBounds,bounds,rv,roundDepth = 5):

    if is_proper_bounds_vector(bounds):
        return point_on_bounds_by_ratio_vector(bounds,rv)

    ib = split_improper_bound(parentBounds,bounds,checkPoints = True)
    q = point_difference_of_improper_bounds(bounds,parentBounds)
    pd1 = ib[0][:,1] - ib[0][:,0] # point diff
    s = rv * q # point add
    p2 = np.copy(bounds[:,0])

    for (i,s_) in enumerate(s):
        d = pd1[i] - s_

        # if addition is greater than first half
        if d < 0:
            px = parentBounds[i,0] - d
        else:
            px = p2[i] + s_
        p2[i] = px

    return np.round(p2,roundDepth)

def vector_ratio(bound,point):
    assert point_in_bounds(bound,point), "point not in bounds"
    return (point - bound[:,0]) / (bound[:,1] - bound[:,0])

'''
'''
def vector_ratio_improper(parentBounds,bounds,point):
    ib = split_improper_bound(parentBounds,bounds,checkPoints = True)
    assert len(ib) > 1, "bounds not improper"
    pd = point_difference_of_improper_bounds(bounds,parentBounds)

    def h(p_,i):
        t = pd[i]

        if p_ >= ib[0][i,0] and p_ <= ib[0][i,1]:
            x = p_ - ib[0][i,0]
        else:
            x = (ib[0][i,1] - ib[0][i,0]) + (p_ - parentBounds[i,0])
        return x / t

    v_ = []
    for (i,p_) in enumerate(point):
        v_.append(h(p_,i))
    return np.round(v_,5)

def bounded_point_to_hop_counts(parentBound,bound,p,h):
    '''
    maps each value of the point `p` relative to the bound to the number
    '''
    r = vector_ratio_improper(parentBound,bound,p)
    r = np.array([r_ if not np.isnan(r_) else 1. for r_ in r])
    h_ = 1. / h
    q = np.array([int(round(r_ / h_)) for r_ in r]) 
    return q

def refit_points_for_new_bounds(points,oldBounds,newBounds):
    q = []
    for p_ in points:
        q.append(refit_point_for_new_bounds(p_,oldBounds,newBounds))
    return np.array(q)

def refit_point_for_new_bounds(p,oldBounds,newBounds):
    vr = vector_ratio(oldBounds,p)
    return point_on_bounds_by_ratio_vector(newBounds,vr)

def area_of_bounds(bounds):
    assert is_proper_bounds_vector(bounds), "not proper bounds vector"
    pd = bounds[:,1] - bounds[:,0]
    return np.product(pd)

######## end: some methods on bounds

def submatrix__2d(M,p,plabel): 
    assert plabel in {"L+U","L+L","R+U","R+L"}

    span_c = None
    span_r = None 
    if plabel[-1] == "U":
        span_c = [0,p[1]+1] 
    else: 
        span_c = [p[1],M.shape[1]+1] 
    
    if plabel[0] == "L":
        span_r = [p[0],M.shape[0] + 1]
    else: 
        span_r = [0,p[0] + 1] 

    q = np.zeros((M.shape[0],M.shape[1]),dtype=M.dtype) 
    q = M[span_r[0]:span_r[1],span_c[0]:span_c[1]]
    return q 

#------------------------- subvector operations 

def subvec(l,start_index,length):
    assert is_vector(l) or type(l) == list 
    assert 0 <= start_index < len(l)
    assert 0 < length <= len(l) 

    q = list(l[start_index:start_index+length])

    l1 = len(q) 
    excess = length - l1
    q2 = [] 
    if excess > 0: 
        q2 = list(l[:excess]) 
    return q + q2

"""
calculates the minimal index range of subvector `sv` in `v`
"""
def index_range_of_subvec(v,sv,is_contiguous=True): 
    v,sv = np.array(v),np.array(sv) 
    if is_contiguous:
        q = contiguous_subvec_search(v,sv)
        return (q,q+len(sv)) 
    return noncontiguous_subvec_search(v,sv) 

def contiguous_subvec_search(v,sv):
    indices = list(np.where(v == sv[0])[0]) 
    for i in indices:
        q = v[i:i+len(sv)] 
        if np.all(q == sv):
            return i 
    return -1 

def noncontiguous_subvec_search(v,sv): 
    indices = list(np.where(v == sv[0])[0]) 

    def stat_at_index(sv_index,index):
        q = sv[sv_index] 
        return v[index] == q
    
    def next_element(sv_,sv_index,start_index): 
        for x in range(start_index,len(v)):
            stat = stat_at_index(sv_index,x)
            if stat: 
                sv_.append(sv[sv_index])
                return x 
        return -1 

    def subvec_at_index(sv_,j): 
        qi = j 
        for i in range(1,len(sv)): 
            qi = next_element(sv_,i,j)
            if qi == -1: 
                return False,None
            j = qi + 1 
        return True, qi 

    while len(indices) > 0:
        ix = indices.pop(0) 
        sx = [sv[0]] 
        stat,end_index = subvec_at_index(sx,ix+1)
        if stat:
            return (ix,end_index)  
    return None