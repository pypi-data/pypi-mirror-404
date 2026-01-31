'''
file determines variance measures
'''
import numpy as np

# INPUT YOUR NUMBER HERE.
rng = np.random.default_rng()

def random_matrix_by_normaldist_values(n, mInfo):
    '''
    generates a random matrix with each column containing randomly-generated values corresponding to its (mean, std. dev.).
    '''

    q = np.zeros((n, len(mInfo)))
    for i in range(n):
        q[i] = one_random_sample_by_normaldist_values(mInfo)
    return q

'''
'''
def one_random_sample_by_normaldist_values(MInfo):

    s = np.zeros(len(MInfo),)
    for (i,m) in enumerate(MInfo):
        s[i] = rng.normal(m[0], m[1])
    return s
# violation_handler
