'''
file practices with techniques to navigate a ball.

ATTENTION:
methods will get transferred to test after completion
'''
from .ball_operator_test_cases import *

#######-------------------------------------------------

def test__BallOperator__nav_basis():
    p = np.array([13,41,50,71,-10])
    b = BallOperator.nav_basis(p)
    sol = np.array([[13,41,50,71,-10],\
            [-10,13,41,50,71],\
            [71,-10,13,41,50],\
            [50,71,-10,13,41],\
            [41,50,71,-10,13]])
    assert equal_iterables(b,sol), "incorrect navigational basis"
    return

def test__BallOperator__set_navigation__AND__basis_division():
    ball = sample_ball_x()
    b = BallOperator(ball)

    # test: set_navigation
    p = np.copy(ball.radiusDelta[0])
    b.set_navigation(p)
    assert equal_iterables(b.location - ball.center,-(b.counterLocation - ball.center))

    # test:
    multiplier = np.array([-1,1,1,-1])
    point = np.array([-39,-1.75,32.5,-7])
    x = BallOperator.basis_division(b.location,b.counterLocation,multiplier)

    assert equal_iterables(x[0],point), "incorrect basis division"
    return

def test__BallOperator__hop_in_division():

    p = np.array([13,41,50,71,-10])
    b = BallOperator.nav_basis(p)

    center = np.array([0.0,0.0,0.0,0.0,0.0])

    hid = BallOperator.hop_in_division(b,0.0,center)
    sol = np.copy(center)
    assert equal_iterables(hid,sol), "incorrect case 1"

    hid = BallOperator.hop_in_division(b,0.25,center)
    d = 1/4 * (np.array([-10,13,41,50,71]) - np.array([13,41,50,71,-10]))
    sol = np.array([13,41,50,71,-10]) + d
    assert equal_iterables(hid,sol), "incorrect case 2"

    hid = BallOperator.hop_in_division(b,0.1,center)
    sol = np.array([6.5,20.5,25.,35.5,-5.])
    assert equal_iterables(hid,sol), "incorrect case 3"

    hid = BallOperator.hop_in_division(b,1.0,center)
    sol = np.array([41,50,71,-10,13])
    assert equal_iterables(hid,sol), "incorrect case 4"

    hid = BallOperator.hop_in_division(b,0.8,center)
    sol = np.array([50,71,-10,13,41])
    assert equal_iterables(hid,sol), "incorrect case 5"
    return
