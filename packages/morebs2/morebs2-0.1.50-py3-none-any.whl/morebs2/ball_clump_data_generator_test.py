from .ball_clump_data_generator import *

def sample_args__ball_clump_frame_generator1():

    bounds = np.array([[-100,100.0],\
                    [-100,100.0],\
                    [-100,100.0],\
                    [-100,100.0],\
                    [-100,100.0],\
                    [-100,100.0]])

    # case 1
    ballRadii = [10.0,40.0,50.0,100.0,10.0,30.0,15.0]

    c1  = [[0.25,0.4,0.55],\
            [0.1],\
            [0.2,0.2,0.2,0.2],\
            [0.5, 0.5],
            [0.3,0.3,0.2],\
            [0.1,0.25,0.3],\
            [0.05,0.4]]

    c2 = [[1000,100,500],\
            [300],\
            [250,450,180,220],\
            [2000,4000],\
            [2000,2000,300],\
            [500,400,1800],\
            [100,200]]

    cs = (c1,c2)
    filePath = "indep/ball_clump_data_1.txt"
    return bounds,ballRadii,cs,filePath

def test__BallClumpDataGenerator__sample1():
    bounds,ballRadii,cs,filePath = sample_args__ball_clump_frame_generator1()

    bcdg = BallClumpDataGenerator(bounds,ballRadii,cs,filePath)
    bcdg.set_frame()

    for b in bcdg.balls:
        print(b)
        print()

    ssz = BallClumpDataGenerator.ball_subset_size_in_bounds(bcdg.rbounds,bcdg.balls)
    ##print("SSZ ",ssz)
    assert BallClumpDataGenerator.ball_set_in_bounds(bcdg.rbounds,bcdg.balls), "invalid balls generated"
    print("* after setting frame")
    bcdg.make_data()
    bcdg.save_frame()


def test__BallClumpDataGenerator__ballclump_frame_filepath():
    fp = "indep/ball_clump_data_1.txt"
    fp2 = BallClumpDataGenerator.ballclump_frame_filepath(fp)
    assert fp2 == "indep/ball_clump_data_1__frame.txt"

    fp = "ball_clump_data_1.txt"
    fp2 = BallClumpDataGenerator.ballclump_frame_filepath(fp)
    assert fp2 == "ball_clump_data_1__frame.txt"
    return
