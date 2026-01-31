from collections import defaultdict 

#------------- single component graphs of directed or undirected. 

def graph_case_1(): 
    D = defaultdict(set) 
    D[0] = set([1])
    D[1] = set([2,0])
    D[2] = set([0])
    D[3] = set([0])
    return D 

def graph_case_2():
    D = defaultdict(set) 
    D[0] = set([])
    D[1] = set([0])
    D[2] = set([0])
    D[3] = set([0])
    D[4] = set([0])
    return D 

def graph_case_3():
    D = defaultdict(set) 
    D[0] = set([1,2,3,4])
    D[1] = set([0])
    D[2] = set([0])
    D[3] = set([0])
    D[4] = set([0])
    return D 

def graph_case_4():
    D = defaultdict(set) 
    D[0] = set([1,2])
    D[1] = set([3,4])
    D[2] = set([5,6])
    D[3] = set([7])
    D[7] = set([0,3])
    return D 

def graph_case_5():
    D = defaultdict(set) 
    D[0] = set([1,2])
    D[1] = set([3,4])
    D[2] = set([5,6])
    D[3] = set([7])
    D[7] = set([0,3])
    return D 

def graph_case_6(): 
    D = defaultdict(set) 
    D[0] = set([1,2])
    D[1] = set([0,3,4])
    D[2] = set([0,5,6])
    D[3] = set([1,4])
    D[4] = set([1,3])
    D[5] = set([2])
    D[6] = set([2])
    return D 

def graph_case_7():
    D = defaultdict(set) 
    D[0] = set([1,2])
    D[1] = set([3,4])
    D[2] = set([5,6])
    D[3] = set([7])
    D[7] = set([0,3,8])
    D[8] = set([7,9,10])
    D[9] = set([8,10])
    return D 

def graph_case_8(): 
    D = defaultdict(set) 
    D[0] = set([1,2])
    D[1] = set([3,4])
    D[2] = set([5,6])
    D[3] = set([7])
    D[7] = set([0,3,8])
    D[8] = set([7,9,10])
    D[9] = set([8,10])
    D[10] = set([8,9])
    return D 

def graph_case_9(): 
    D = defaultdict(set) 
    D[0] = set([1,2,3,4]) 
    D[1] = set([0,5,6])
    D[2] = set([0])
    D[3] = set([0])
    D[4] = set([0])
    D[5] = set([0])
    return D 


def graph_case_12(): 
    D = defaultdict(set) 
    D[0] = set([1,2,3,4])
    D[1] = set([0,2,8])
    D[2] = set([0,1,6,7])
    D[3] = set([10])
    D[4] = set([10])
    D[5] = set([0])
    D[6] = set([7])
    D[7] = set([6])
    D[8] = set([1,3,9])
    D[9] = set([8,10])
    D[10] = set([3,4,9])
    return D 

def graph_case_13(): 
    D = defaultdict(set) 
    D[0] = set([6,7])
    D[6] = set([8,9])
    D[7] = set([0])
    D[8] = set([0,10])
    D[9] = set([6,8])
    D[10] = set([])
    return D 


def graph_case_14(): 
    D = graph_case_13() 
    D[10] |= {11,12}
    D[11] |= {13}
    D[12] |= {10,13}
    # delete below edge for different result 
    D[13] |= {10}
    return D 

def graph_case_15(): 
    D = defaultdict(set) 
    D[0] = set([1,2,3,4]) 
    D[1] = set([0,2,3,4]) 
    D[2] = set([1,0,3,4]) 
    D[3] = set([1,2,0,4]) 
    D[4] = set([1,2,3,0]) 
    return D 

#----------------------------------------
#----------- multi-component graphs 


def graph_case_10(): 
    D = defaultdict(set) 
    D[0] = set([1,2,3,4]) 
    D[1] = set([0,2,3,4])
    D[2] = set([0,1,3,4])
    D[3] = set([0,1,2,4])
    D[4] = set([1,2,3,0])

    D[7] = set([8,9]) 
    D[8] = set([7,9])
    D[9] = set([7,8])

    D[10] = set([111]) 
    D[111] = set([10])
    return D 


def graph_case_11(): 
    D = defaultdict(set) 
    D[0] = set([1,2,3,4]) 
    D[1] = set([0,5,6])
    D[2] = set([0])
    D[3] = set([0])
    D[4] = set([0])
    D[5] = set([0])

    D2 = defaultdict(set) 
    D[7] = set([12,20])
    D[12] = set([38,41])
    D[20] = set([15,64])
    D[38] = set([11])
    D[11] = set([7,31])

    D.update(D2)
    return D 
