from .ball_operator_test_cases import *

def test__BallOperator__run_subball_split():
    print("SUB-BALL SPLIT TEST")
    balls = sample_balls_1()

    # choose 3 random
    ballIndices = [0,3,5]

    b = BallOperator(balls[ballIndices[0]])

    print("initial")
    print(balls[ballIndices[0]])
    print()

    r = balls[ballIndices[0]].radius / 1.1
    b.run_subball_split((r,"literal"),"minimal")

    print("after split")
    print("number of balls ", len(b.subballs))
    for b_ in b.subballs:
        print(b_)
        print()

    print("average subball radius")
    radius = np.mean([b_.radius for b_ in b.subballs])
    print(radius)
    print("average subball data size")
    ds = np.mean([b_.data.newData.shape[0] for b_ in b.subballs])
    print(ds)
    print()

    print("base ball")
    print(b.ball)

    # comment the line below to see information on ball that was split
    return -1

    fp = BallClumpDataGenerator.ballclump_frame_filepath(ballClumpDataFilePath1)
    fobj = pickle_obj_from_file(fp)

    print("--- Ball information")
    print("cluster centers")
    print(fobj[3][0])
    print()

    print("cluster radii")
    print(fobj[4][0])

    print("cluster densities")
    print(fobj[5][0])
    print()
    print("-------------------------------")
    return
