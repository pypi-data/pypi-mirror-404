from .ball_operator import *
from .ball_clump_data_generator import *
from .numerical_space_data_generator import *
from .message_streamer import *

# obtain the test data
ballClumpDataFilePath1 = "indep/ball_clump_data_1.txt"
ballXFilePath = "indep/ball_data.txt"


def sample_ball_x():

    q = MessageStreamer(ballXFilePath,readMode = "r")
    B = None
    c = 0
    x = []
    while q.stream():
        x.extend(q.blockData)
        c += 1

    B = Ball(x[0])
    for i in range(1,len(x)):
        B.add_element(x[i])
    return B

def pickle_obj_from_file(fp):
    fobj = open(fp,"rb")
    obj = pickle.load(fobj)
    fobj.close()
    return obj

"""
constructs a list of balls that use data generated from .BallClumpDataGenerator
"""
def sample_balls_1():

    def point_to_balls(p):
        ##print("adding point ",p)
        for (i,b) in enumerate(ballList):
            if euclidean_point_distance(b.center,p) <= radiiList[i]:
                b.add_element(p)

    def block_data_to_balls():
        for v in q.blockData:
            point_to_balls(v)

    # get the original frame of the ball clump
    fp = BallClumpDataGenerator.ballclump_frame_filepath(ballClumpDataFilePath1)
    fobj = pickle_obj_from_file(fp)
    ballList = [Ball(c) for c in fobj[1]]
    radiiList = np.round(np.array(fobj[2]),5)

    q = MessageStreamer(ballClumpDataFilePath1,readMode = "r")
    B = None
    c = 0

    while q.stream():
        block_data_to_balls()
        c += 1
    return ballList

# try splitting all the balls.
