from .line import *
import random
################ START: line generators

def generate_random_line(startPoint, length):
    """
    generates a random line of `length` from .`startPoint` by a random angle in
    [0,360].
    """
    # random angle
    angle = random.uniform(0, 360)
    endPoint = hypotenuse_from_point(startPoint, length, angle)
    return Line((startPoint, endPoint))

def generate_random_line_at_center(centerPoint, length):
    """
    generates a random line of `length` at center `centerPoint`.

    :param centerPoint: 2-tupules de duos
    :type centerPoint: iterable
    :param length: lengua
    :type length: float
    """
    # random angle
    angle = random.uniform(0, 360)
    altAngle = (angle + 180.0) % 360.0

    e1 = hypotenuse_from_point(centerPoint, length / 2.0, angle)
    e2 = hypotenuse_from_point(centerPoint, length / 2.0, altAngle)
    return Line((e1, e2))

################ END: line generators

def generate_line_by_length_and_angle(startPoint, length, angle):
    endPoint = hypotenuse_from_point(startPoint, length, angle)
    return Line((startPoint, endPoint))

def hypotenuse_from_point(point, length, angle):
    """
    Outputs an endpoint given `point`; `endpoint` is distance `length` from .`point` and at `angle`
    """

    # get the x-delta and y-delta
    q = math.sin(math.radians(angle))
    opp = q * length

    q = math.cos(math.radians(angle))
    adj = q * length

    return [point[0] + adj, point[1] + opp]

    ##################################################################

# TODO: necessary??
"""
"""
def closest_right_angle_to_angle(angle):
    angle = angle % 360
    right = [0, 90, 180, 270, 360]
    diff = [abs(angle - r) for r in right]
    index = np.argmin(diff)
    return right[index]

"""
"""
def quadrant_of_angle(angle):
    """
    determinini es angle y quadrillas
    """

    assert not (angle < 0 or angle > 360), "invalid angle"

    if (angle >= 0 and angle <= 90) or angle == 360:
        return 0

    if (angle > 90 and angle <= 180):
        return 1

    if (angle > 180 and angle <= 270):
        return 2

    return 3

############################### END: line generator

################ START: area identification

def random_point_in_area(area):
    assert is_valid_area(area), "area is invalid"
    x = random.uniform(area[0,0], area[1,0])
    y = random.uniform(area[0,1], area[1,1])
    return (x,y)

def random_point_in_circle(center, radiusRange):
    # random x-delta    
    xDelta = random.uniform(radiusRange[0],radiusRange[1])

    # select a radius range in [xDelta,radiusRange[1]]
    rr = random.uniform(xDelta,radiusRange[1])

    # random y-delta
    yDelta = math.sqrt(rr**2 - xDelta**2)

    s1 = 1 if random.random() >= 0.5 else -1 
    s2 = 1 if random.random() >= 0.5 else -1 
    return (center[0] + xDelta * s1, center[1] + yDelta * s2)

def random_point_near_2d_point_pair(pair,rdistance):
    '''
    generates a random point near a 2d point pair by first
    constructing a line b/t the the points in the pair,
    choosing a random point `r` on the line, and then a random point
    of distance `d` in range `rdistance` from `r`.  
    '''
    assert len(pair) == 2, "invalid pair"
    l = Line([pair[0],pair[1]])

    s = 0
    v = random.random()
    p = l.point_from_source_by_value(v,s)
    return random_point_in_circle(p,rdistance)

def generate_random_xyl_points_at_center(c,drnp,l):
    '''
    for each element in `drnp`, generates 
            by std. python.

    c := center point, (x,y,label)
    drnp := list(<(distance min to c,distance max to c, number of points)>)
    l := int,label
    '''

    def process_drn(drn):
        rps = []
        for i in range(drn[2]):
            p = list(random_point_in_circle(c[:2],drn[:2])) + [l]
            rps.append(p)
        return rps

    ps = []
    for drn in drnp:
        ps.extend(process_drn(drn))
    return np.array(ps)

"""
"""
def random_game_table_matrix(xMoveSize, yMoveSize, rangeX, rangeY):#, rule):
    assert len(rangeX) == 2 and len(rangeY) == 2, "arg. range is wrong"
    q = np.empty((xMoveSize, yMoveSize, 2))

    for i in range(xMoveSize):
        for j in range(yMoveSize):
            q[i,j] = (random.randrange(rangeX[0], rangeX[1]), random.randrange(rangeY[0], rangeY[1]))
    return q
