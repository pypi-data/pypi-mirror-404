from morebs2.ball_comp import *
from morebs2.numerical_space_data_generator import *
from morebs2.ball_clump_data_generator import *

####### basic cases
def ballcomp_sample_data_1():
    x1 = np.ones((5,)) * 5.0
    x2 = np.ones((5,)) * 10.0
    x3 = np.ones((5,)) * 15.0
    x4 = np.ones((5,)) * 20.0
    x5 = np.ones((5,)) * 25.0
    x6 = np.ones((5,)) * 30.0
    x7 = np.ones((5,)) * 35.0
    x8 = np.ones((5,)) * 40.0
    return np.array([x1,x2,x3,x4,x5,x6,x7,x8])

def ballcomp_sample_data_2():
    x1 = np.ones((5,)) * 5.0
    x2 = np.ones((5,)) * 5.1
    x3 = np.ones((5,)) * 5.2
    x4 = np.ones((5,)) * 5.3
    x5 = np.ones((5,)) * 5.4
    x6 = np.ones((5,)) * 4.9
    x7 = np.ones((5,)) * 4.8
    x8 = np.ones((5,)) * 4.7
    return np.array([x1,x2,x3,x4,x5,x6,x7,x8])

def ballcomp_sample_data_3():
    x1 = np.ones((5,)) * 5.0
    x2 = np.ones((5,)) * 5.3
    x3 = np.ones((5,)) * 6.0
    x4 = np.ones((5,)) * 6.2
    x5 = np.ones((5,)) * 6.4
    x6 = np.ones((5,)) * 4.5
    x7 = np.ones((5,)) * 4.2
    x8 = np.ones((5,)) * 4.0
    return np.array([x1,x2,x3,x4,x5,x6,x7,x8])

def ballcomp_sample_data_LCG_1(): 
    prg = prg__LCG(144,544,-32,4012) 
    prg_ = prg__single_to_nvec(prg,7)

    V = [] 
    for i in range(2000): 
        V.append(prg_())
    return V 

###########

def ballcomp_sample_data_4__rch():

    rch = RChainHead()# np.array()

    ### not enough points generated
    """
    rv1 = np.array([[-100.0,-90],\
                    [0,10],\
                    [-100,-90],\
                    [0,10],\
                    [-100,-90],\
                    [0,10]])

    rv2 = np.array([[-90.0,-75],\
                    [10,20],\
                    [-90,-70],\
                    [10,30],\
                    [-90,-70],\
                    [10,25]])

    rv3 = np.array([[90.0,100],\
                    [90.0,100.0],\
                    [80.0,100.0],\
                    [80.0,100],\
                    [-90,-70],\
                    [85.0,100]])

    rv4 = np.array([[0.0,20.0],\
                    [50.0,65.0],\
                    [-5.0,12.0],\
                    [40.0,60],\
                    [-10,5],\
                    [45.0,55.0]])
    """
    ###

    rv1 = np.array([-90,10,-90,10,-90,10])
    rv2 = np.array([-90.0,10,-90,10,-90,10])
    rv3 = np.array([90.0,90.0,80.0,80.0,-90,85.0])
    rv4 = np.array([20.0,50.0,-5.0,40.0,-10,45.0])
    dt_ = [rv1,rv2,rv3,rv4]
    q = 387.2983346207417 / 6.0
    ##q_ = [q * 1/6, q * 1/8, q * 1/7, q * q * 1/7]

    def cf(x,dt):
        for r in dt:
            if euclidean_point_distance(x,r) <= q:
            ##if point_in_bounds(r,x):
                return True
        return False

    kwargs = ['nr',cf,dt_]
    rch.add_node_at(kwargs)
    return rch

"""
generates data into file
"""
def ballcomp_sample_data_4(noiseRange = None):

    bounds = np.array([[-100.0,100],\
                    [0,100],
                    [-100,100],
                    [0,100],
                    [-100,100],
                    [0,100]])
    startPoint = np.copy(bounds[:,0])
    columnOrder = [0,3,2,4,1,5]
    ssih = 6
    bInf = (bounds,startPoint,columnOrder,ssih,())
    rch = ballcomp_sample_data_4__rch()

    rm = ("relevance zoom",rch)
    filePath = "indep/ballcomp_sample_data_4.txt"
    modeia = 'w'
    writeOutMode = 'relevant' # 'literal'

    nsdi = NSDataInstructions(bInf,rm,filePath,modeia,noiseRange,writeOutMode)
    nsdi.make_rssi()

    c = ssih ** 6
    c_ = 0
    while nsdi.fp and c_ < c:
        print("batch @ ",c_)
        nsdi.next_batch_()
        c_ += DEFAULT_SINGLE_WRITE_SIZE

    if nsdi.fp:
        print("YESS")
        nsdi.fp.close()
    return
