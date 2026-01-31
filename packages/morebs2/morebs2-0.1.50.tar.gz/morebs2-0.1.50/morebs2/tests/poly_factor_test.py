from morebs2 import poly_factor,poly_struct
from copy import deepcopy
import unittest
import numpy as np

def pfe_case1():
    pa = np.array([[24,12],[-88,11],[176,10],[-286,9],[300,8],
            [-348,7],[465,6],[-252,5],[126,4],[-135,3]])
    p = poly_struct.CEPoly(pa)

    pfe1 = poly_factor.PolyFactorEst(p)
    pfe1.set_exponential_bounds((0,6),(3,6))
    return pfe1 

'''
python -m morebs2.tests.poly_factor_test  
'''
class TestPolyFactorEst(unittest.TestCase):

    def test__pfe__initial_bounds_hypothesis(self):
        pfe1 = pfe_case1()
        pfe1.initial_bounds_hypothesis()
        assert str(pfe1.p1) == ' 12x^6 + 45x^0'
        assert str(pfe1.p2) == ' 2x^6  -3x^3'

    def test__pfe__guess(self):
        pa = np.array([[24,12],[-88,11],[176,10],[-286,9],\
            [300,8],[-348,7],[465,6],[-252,5],[126,4],[-135,3]])

        p = poly_struct.CEPoly(pa)
        pfe1 = poly_factor.PolyFactorEst(deepcopy(p))
        pfe1.set_exponential_bounds((0,6),(3,6))
        pfe1.initial_bounds_hypothesis()
        pfe1.guess()
        assert pfe1.f1 * pfe1.f2 == p, "incorrect factorization"

    def test__pfe__guess__case2(self):
        pa = np.array([[1,2],[-1,0]])
        p = poly_struct.CEPoly(pa)
        pfe1 = poly_factor.PolyFactorEst(deepcopy(p))
        pfe1.set_exponential_bounds((0,1),(0,1))
        pfe1.initial_bounds_hypothesis()
        pfe1.guess()
        assert pfe1.f1 * pfe1.f2 == p, "incorrect factorization #2"

    def test__possible_new_elements_of_factor_for_exponent(self):
        pfe1 = pfe_case1()
        pfe1.initial_bounds_hypothesis()

        q = poly_factor.possible_new_elements_of_factor_for_exponent(\
            pfe1.p1,pfe1.p2,pfe1.p1eb,pfe1.p2eb,pfe1.p,6)
        assert q == [3, 2, 1]

        q = poly_factor.possible_new_elements_of_factor_for_exponent(\
            pfe1.p1,pfe1.p2,pfe1.p1eb,pfe1.p2eb,pfe1.p,8)
        assert q == [5, 4, 3, 2]

        q = poly_factor.possible_new_elements_of_factor_for_exponent(\
            pfe1.p1,pfe1.p2,pfe1.p1eb,pfe1.p2eb,pfe1.p,4)
        assert q == [1]

if __name__ == '__main__':
    unittest.main()