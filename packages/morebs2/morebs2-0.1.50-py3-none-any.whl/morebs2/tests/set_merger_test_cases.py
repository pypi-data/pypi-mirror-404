from morebs2 import set_merger

######################### sample cases
def sample_set_sequence_1():
    return [set((1,2)),set((2,3))]

def sample_set_sequence_2():
    return [set((1,2)),set((1,3)),set((2,3))]

def sample_set_sequence_6():
    return [set((1,2)),set((1,3)),set((1,4)),set((2,3)),set((2,4)),set((3,4))]

def sample_set_sequence_10():
    return [set((1,2,3)),set((1,2,4)),set((1,3,4)),set((2,3,4))]

def sample_set_sequence_11():

    q = [set([0,1]),set([0,2]),set([0,3]),set([0,4]),set([0,5]),\
        set([1,2]),set([1,3]),set([1,4]),set([1,5]),\
        set([2,3]),set([2,4]),set([2,5]),\
        set([3,4]),set([3,5]),\
        set([4,5])]
    return q

def sample_set_sequence_12():

    q = sample_set_sequence_11()
    q2 = [set((5,6)),set((5,7)),set((5,8)),\
        set((6,7)),set((6,8)),\
        set((7,8))]
    q.extend(q2)
    return q

def sample_set_sequence_13():
    return [set((0,1))]
