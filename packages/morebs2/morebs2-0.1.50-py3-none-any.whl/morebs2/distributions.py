"""
file contains code for distributions
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from math import sqrt,pi,e,log

import random

random.seed(100)

############################# start: plotting functions

def basic_2d_lineplot(x,y):
    fig, ax = plt.subplots()  # Create a figure containing a single axes.
    ax.plot(x, y)
    plt.show()


def basic_2d_scatterplot(x,y,c=None):
    plt.scatter(x, y,c=c,s=1)#, s=area, c=colors, alpha=0.5)
    plt.show()

def generate_2d_data_from_function(f,xRange,xInc,additionalArgs = ()):
    """generates a sequence of (x,y) pairs such that every x-value has exactly one y-value and the x-values are evenly distributed across the x-range.
    """
    
    x = []
    y = []
    q = xRange[0]
    while q <= xRange[1]:
        x.append(q)
        y.append(f(q,*additionalArgs))
        q = q + xInc
    return x,y

def generate_2d_data_from_function__multipleY(f,xRange,xInc,additionalArgs = ()):
    """generates a sequence of (x,y) pairs such that every x-value can have any integer n >= 0 of y-values according to arguments. 
    """

    x = []
    y = []
    q = xRange[0]
    while q <= xRange[1]:
        ys = f(q,*additionalArgs) 
        if len(ys) != 0:
            x.extend([q] * len(ys))
            y.extend(ys)
        q = q + xInc
    return x,y

def function_to_2dplot(g,f,xRange,xInc,additionalArgs=(),mode="scatter"):
    assert mode in ["line","scatter"]
    x,y = g(f,xRange,xInc,additionalArgs)
    if mode == "line":
        basic_2d_lineplot(x,y)
    else:
        basic_2d_scatterplot(x,y)
    return

############################# end: plotting functions

############################# start: distribution functions

def normal_distribution_function(x,mean,stddev):
    m = 1.0 / sqrt(2. * pi)
    exp = -0.5 * ((x - mean) / (stddev**2.))**2
    return m * e ** exp
    
def holtzmann_distribution_function():
    return -1

def poisson_distribution_function():
    return -1

def multiple_y_function_stdrand(x,yRange,multipleRange):
    """generates multiple y-values for the x-value based on python standard random. The x-value has no bearing on the y-values generated.
    """

    assert yRange[1] >= yRange[0], "invalid range for y-values"
    assert multipleRange[1] >= multipleRange[0], "invalid range for multiples"

    # determine the number of points
    p1 = multipleRange[0] + int((multipleRange[1] - multipleRange[0]) * random.random())
    l = []
    for i in range(p1):
        l.append(yRange[0] + (yRange[1] - yRange[0]) * random.random())
    return l

def multiple_y_function_x_effector(x,f,multipleRange):
    """generates variable # of y-values for the 
    x-value in which the x-value has an 
    effect on the y-values generated.
    """

    p1 = multipleRange[0] + int((multipleRange[1] - multipleRange[0]) * random.random())
    l = []
    for i in range(1,p1 + 1):
        l.append(f(x,i))
    print("L: ", len(l))
    return l

def x_effector_function_type_modulo(xyiOp,yRange):
    """outputs a function 
                `f(x,i) -> y`
        using a function `xyiOp(x,yRange,i)`. 

    :param xyiOp: function
    :param yRange: range of the y-values 
    """

    def q(x,i):
        return xyiOp(x,yRange,i)
    return q

def xyi_op_type_1(x,yRange,i):
    r = yRange[1] - yRange[0]
    x2 = (x * i * 10) % r
    return yRange[0] + x2

def log_function(x,m=e):
    return log(x) / log(m)

######### test function

### gaussian dist.
#function_to_2dplot(generate_2d_data_from_function,normal_distribution_function,[-5.,5.],0.1,(0.,5.))

### multiple y function 1
#f = x_effector_function_type_modulo(xyi_op_type_1,[200.,600.])#[-112.5,400.3])
#function_to_2dplot(generate_2d_data_from_function__multipleY,\
#    multiple_y_function_x_effector,[-20.,40.],0.25,additionalArgs=(f,[0,2]),mode="scatter")

### multiple y function 2
#function_to_2dplot(generate_2d_data_from_function__multipleY,\
#    multiple_y_function_stdrand,[-20.,40.],0.25,additionalArgs=([100.,170.],[1,6]),mode="scatter")

############################# end: distribution functions