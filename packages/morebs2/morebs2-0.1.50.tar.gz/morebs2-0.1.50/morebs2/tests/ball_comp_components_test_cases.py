from morebs2 import ball_comp_components
import numpy as np

def sample_ball_pair_1():
    c1 = np.array((10.0,10.0,10.0,10.0))
    c2 = np.array((17.0,10.0,10.0,10.0))
    r1 = 5.0
    r2 = 4.0
    b1 = ball_comp_components.Ball.one_ball_(c1,r1)
    b2 = ball_comp_components.Ball.one_ball_(c2,r2)
    return b1,b2

def sample_ball_pair_2():
    c1 = np.array((10.0,10.0,10.0,10.0))
    c2 = np.array((10.0,8.0,10.0,10.0))
    r1 = 5.0
    r2 = 2.0
    b1 = ball_comp_components.Ball.one_ball_(c1,r1)
    b2 = ball_comp_components.Ball.one_ball_(c2,r2)
    return b1,b2

def sample_ball_pair_3():
    c1 = np.array((10.0,10.0,10.0,10.0))
    c2 = np.array((8.0,8.0,8.0,8.0))
    r1 = 5.0
    r2 = 2.0
    b1 = ball_comp_components.Ball.one_ball_(c1,r1)
    b2 = ball_comp_components.Ball.one_ball_(c2,r2)
    return b1,b2

def sample_ball_pair_4():
    c1 = np.array((10.0,10.0,10.0,10.0))
    c2 = np.array((15.0,15.0,15.0,15.0))
    r1 = 5.0
    r2 = 2.0
    b1 = ball_comp_components.Ball.one_ball_(c1,r1)
    b2 = ball_comp_components.Ball.one_ball_(c2,r2)
    return b1,b2
