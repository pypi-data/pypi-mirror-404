# some more functions for class<RChainHead>. 
import numpy as np

def vector_summation_modulo(m,v):
    '''
    multiplies all values of `v` by 10^5 to convert them to integers. Then 
    adds all values of `v` into a sum and modulo `m` that sum.

    :param v:
    :param m: 
    :return: non-negative integer less than `m`
    :rtype: int
    '''

    d = decimal_order_of_vector(v)
    v = np.array([int(v_) for v_ in v * 10**d])
    x = np.sum(v)
    return x % m

def decimal_order_of_vector(v):
    '''
    maximum decimal places of values in vector
    '''

    return max([decimal_places_of_float(v_) for v_ in v])

def decimal_places_of_float(f,maxPlaces = 5):
    for i in range(maxPlaces):
        f_ = f * 10 ** i
        if int(f_) == f_: return i
    return maxPlaces

def update_modulo_function(a,m2):

    def update_f(m):
        return (m + a) % m2

    return update_f



# NEXT: subvector selector
# NEXT: add verbose mode for processing each vector in NSDataInstruction
# NEXT: add verbose mode for RChainHead