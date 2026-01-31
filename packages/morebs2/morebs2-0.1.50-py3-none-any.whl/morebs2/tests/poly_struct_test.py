from morebs2 import poly_struct
import unittest
import numpy as np

'''
python -m morebs2.tests.poly_struct_test  
'''
class TestPolyClasses(unittest.TestCase):
    
    def test__SPoly__apply(self):

        # poly case 1
        sp = poly_struct.SPoly(np.array([12.0,0.0,3.0,1.0,2.0]))

        #   x1
        v1 = sp.apply(3.0)
        print(v1)
        assert v1 == 999 + 3 + 2, "incorrect SPoly case 1.1"

        v2 = sp.apply(0.0)
        assert v2 == 2.0, "incorrect SPoly case 1.2"

    def test__ISPoly__apply(self):
        s = poly_struct.ISPoly(3.0)
        v1 = s.apply(np.array([12.0,0.0,3.0,1.0,2.0]))
        assert v1 == 999 + 3 + 2, "incorrect case 1.1"

    def test__CEPoly____add__(self):
        x = poly_struct.CEPoly(np.array([[4,5],[3,2],[6,7],[5,0]]))
        x2 = poly_struct.CEPoly(np.array([[10,5],[13,7],[122,0]]))
        assert str(x + x2) == ' 19x^7 + 14x^5 + 3x^2 + 127x^0'

    def test__CEPoly____mul__(self):
        x = poly_struct.CEPoly(np.array([[4,5],[3,2],[6,7],[5,0]]))
        x2 = poly_struct.CEPoly(np.array([[4,1],[3,0]]))
        assert str(x * x2) == " 24x^8 + 18x^7 + 16x^6 + 12x^5 + 12x^3 + 9x^2 + 20x^1 + 15x^0"
        assert str(x * 14) == ' 84x^7 + 56x^5 + 42x^2 + 70x^0'

if __name__ == "__main__":
    unittest.main()
    print()
