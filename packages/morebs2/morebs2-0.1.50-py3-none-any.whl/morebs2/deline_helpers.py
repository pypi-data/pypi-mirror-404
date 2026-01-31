'''
functions to aid in Delineation

make-shift
'''
import numpy as np

def eliminate_duplicate_points(edges1,edges2,axis):

    delete1,delete2 = [],[]
    m1,m2 = np.mean(edges1,axis=0), np.mean(edges2,axis=0)
    el1,el2 = len(edges1),len(edges2)

    for (i,x) in enumerate(edges1):
        ss = np.where((edges2 == x).all(axis=1))[0]
        if len(ss) == 0:
            continue
        assignIt = assign_duplicate_point_to_edge(m1,m2,el1,el2,axis,x)
        
        # case: assign duplicate edge 
        if assignIt == 1:
            delete2.extend(ss)
        else:
            delete1.append(i)
    
    delete2 = set(delete2)
    delete1 = set(delete1)

    delete2 = list(delete2 - {0,el2 - 1})
    delete1 = list(delete1 - {0,el1 - 1})

    edges1 = np.delete(edges1,delete1,axis=0)
    edges2 = np.delete(edges2,delete2,axis=0)
    return edges1,edges2

def assign_duplicate_point_to_edge(edgesMean1,edgesMean2,edges1Len,edges2Len,axis,p):
    x1 = abs(edgesMean1[axis] - p[axis]) / edges1Len
    x2 = abs(edgesMean2[axis] - p[axis]) / edges2Len

    if x1 < x2: return 1
    return 2


######################### approach: no cross

def eliminate_contrary_points(e1,e2,axis):
    '''
    * assume the point sequences e1 and e2 are
    ordered by axis 0 or 1. 


    if duplicate: assign t
    '''

    # use the last element as first point to edges
    e1_,e2_ = [e1[0]],[e2[0]]
    e1,e2 = e1[1:],e2[1:]

    while len(e1) > 1 and len(e2) > 1:
        edge1 = np.array([e1_[-1],e1[0]])
        
        # iterate through e2 and pop each point not in range
        # stopping at the first point
        j = next_point_in_range(e2,edge1,axis)
        if j == -1:
            e1_.append(e1[0])
            e1 = e1[1:]
            continue

        for j2 in range(j):
            e2_.append(e2[0])
            e2 = e2[1:]

        # check edge 1 and edge 2
        edge2 = np.array([e2_[-1],e2[0]])
        s1,s2 = correct_rectangle_cross(edge1,edge2,axis)

        # case: delete the second point
        if not s1:
            e1 = e1[1:]

        if not s2:
            e2 = e2[1:]
        else:
            e2_.append(e2[0])
            e2 = e2[1:]
    e1_.extend(e1)
    e2_.extend(e2)
    return e1_,e2_

def eliminate_contrary_points_indices(e1,e2,axis):
    e1_,e2_ = [0],[0]
    ei1,ei2 = 1,1
    l1,l2 = len(e1) - 1, len(e2) - 1
    while ei1 < l1 and ei2 < l2: 
        edge1 = np.array([e1[e1_[-1]],e1[ei1]])
        j = next_point_in_range(e2[ei2:],edge1,axis)

        if j == -1:
            e1_.append(ei1)
            ei1 += 1
            continue

        for j2 in range(j):
            e2_.append(j2 + ei2) 

        edge2 = np.array([e2[e2_[-1]],e2[j + ei2]])
        s1,s2 = correct_rectangle_cross(edge1,edge2,axis)
        
        # case: edges cross for s1
        if not s1:
            ei1 += 1 

        # case: edges do not cross for s2
        if s2:
            e2_.append(ei2) 
        ei2 += j + 1

    e1_.extend([i for i in range(ei1,l1 + 1)])
    e2_.extend([i for i in range(ei2,l2 + 1)])
    return e1_,e2_

def next_point_in_range(ep,edge,axis):

    for (i,p) in enumerate(ep):
        if p[axis] >= min(edge[:,axis])\
            and p[axis] <= max(edge[:,axis]):
            return i
    return -1

def next_point_that_crosses_diag_area(ep,d,axis):
    '''
    # NOTE: inefficient
    
    return := index of next point of `ep` that is in diagonal `d`
    '''
    for (i,p) in enumerate(ep):
        if point_in_diag_area(p,d): return i
    return -1


def correct_rectangle_cross(l1,l2,axis):
    q = line_segments_cross_in_rectangle(l1,l2)
    p1,p2 = True,True
    
    if q[0][1]:
        if closer_edge(l1[0],l2[0],l1[1],axis) != 1:
            p1 = False

    if q[1][1]:
        if closer_edge(l1[0],l2[0],l2[1],axis) != 2:
            p2 = False
            
    '''
    if q[0][1]:
        p1 = False
    if q[1][1]:
        p2 = False
    '''
    return p1,p2


def closer_edge(e1r,e2r,p,axis):
    a2 = (axis + 1) % 2
    d = abs(e1r[a2] - p[a2])
    d2 = abs(e2r[a2] - p[a2])

    if d < d2:
        return 1
    return 2

def line_segments_cross_in_rectangle(l1,l2):
    '''
    determines if l1[1] or l1[0] in rectangle containing l2
    or vice-versa.

    return := sequence<(0|1 denoting line,point 0|1 of line)> of points
              that fall in rectangles.
    '''

    s10 = point_in_diag_area(l1[0],l2)
    s11 = point_in_diag_area(l1[1],l2)
    s20 = point_in_diag_area(l2[0],l1)
    s21 = point_in_diag_area(l2[1],l1)

    s2 = point_in_diag_area(l2[1],l1)
    return ((s10,s11),(s20,s21))

def point_in_diag_area(p,d):
    return p[0] >= min(d[:,0]) and p[0] <= max(d[:,0])\
        and p[1] >= min(d[:,1]) and p[1] <= max(d[:,1])

######################## approach: no jags
def remove_jags_on_edges(edges,direction):
    je = jags_on_edges(edges,direction)
    je.pop(-1)
    indices = []
    for (i,j) in enumerate(je):
        if j == -1:
            indices.append(i + 1)
    indices = np.array(indices)
    if len(indices) != 0: 
        edges = np.delete(edges,indices,0)
    return edges

def jags_on_edges(edges,direction):
    '''
    a jag is defined as three consecutive
    points in a sequence of points ordered
    by an axis q such that the middle point
    is directionally less than the other two
    points, thereby creating a triangular shape
    without the bottom edge. 
    '''

    x = edges[0]
    edges = edges[1:]
    jags = []
    while len(edges) > 0:
        q = np.array([x,edges[0]])
        ij = is_jagged(q,direction)
        if ij:
            jags.append(-1)
        else:
            jags.append(1)
        x = edges[0]
        edges = edges[1:]
    return jags

def is_jagged(edge,direction):

    if direction == 'l':
        return edge[1,0] > edge[0,0]
    
    if direction == 'r':
        return edge[1,0] < edge[0,0]

    if direction == 't':
        return edge[1,1] < edge[0,1]

    if direction == 'b':
        return edge[1,1] > edge[0,1]

############## approach: partitioning

def critical_dpoints_by_partition(edges,direction,p):

    if direction == 'l':
        qf = lambda em: np.argmin(em[:,0])
    elif direction == 'r':
        qf = lambda em: np.argmax(em[:,0])
    elif direction == 't':
        qf = lambda em: np.argmax(em[:,1])
    else:
        qf = lambda em: np.argmin(em[:,1])

    i = 1
    psz = len(edges) / p
    ps = [np.copy(edges[0])]
    while True:
        se = edges[i:i + psz]
        if len(se) == 0: break

        si = qf(se)

        ps.append(np.copy(se[si]))
        i += psz
    
    ps.append(np.copy(edges[-1]))
    return np.array(ps)

###################################################

def delineation_in_delineation(d1,d2):

    # go curve by curve
    



    return -1

# given i1,i2 for e1,e2
# 
#
# if 