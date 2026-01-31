from morebs2 import fit_2n2
import numpy as np

import unittest

'''
python -m morebs2.tests.fit_2n2_test  
'''
class TestFit22Class(unittest.TestCase):

    def test__Exp2Fit22__inverse(self):
        # case 1
        lf22 = fit_2n2.Exp2Fit22(np.array([[60.,80.],[30.,12.]]),direction=[1,0])
        (x1,y1) = (40,lf22.f(40))
        (x2,y2) = (lf22.g(y1),y1) 
        assert(x1 == x2 and y1 == y2)

        (x1,y1) = (30,lf22.f(30))
        (x2,y2) = (lf22.g(y1),y1) 
        assert(x1 == x2 and y1 == y2)

        (x1,y1) = (60,lf22.f(60))
        (x2,y2) = (lf22.g(y1),y1) 
        assert(x1 == x2 and y1 == y2)

    def test__LogFit22__inverse(self):
        lf22 = fit_2n2.LogFit22(np.array([[60.,80.],[30.,12.]]),direction=[1,0])
        (x1,y1) = (40,lf22.f(40))
        (x2,y2) = (lf22.g(y1),y1) 
        assert(x1 == x2 and y1 == y2)

        (x1,y1) = (30,lf22.f(30))
        (x2,y2) = (lf22.g(y1),y1) 
        assert(x1 == x2 and y1 == y2)

        (x1,y1) = (60,lf22.f(60))
        (x2,y2) = (lf22.g(y1),y1) 
        assert(x1 == x2 and y1 == y2), "got {} want {}".format((x1,x2),(y1,y2))

    def test__ChainedDCurves__fit__case1(self): 
        P = np.array([[0,14],\
                    [12,22],\
                    [8,24],\
                    [40,17]])

        fvec = [0,1,1]
        cdc = fit_2n2.ChainedDCurves(P,fvec,axis=0)
        cdc.draw() 

        cdc2 = fit_2n2.ChainedDCurves(P,fvec,axis=1)
        cdc2.draw() 

        # case 1 
        x = cdc.amin 
        h = (cdc.amax - cdc.amin) / 10

        xs = np.zeros((10,2),dtype=float)
        for i in range(1,11):
            x2 = x + i * h
            y = cdc.fit(x2) 

            xs[i-1] = [x2,y]

        xs = np.round(xs,5)
        sol = np.array([[ 4.     , 16.5    ],
            [ 8.     , 24.     ],
            [12.     , 22.     ],
            [16.     , 21.70116],
            [20.     , 21.35453],
            [24.     , 20.94185],
            [28.     , 20.4319 ],
            [32.     , 19.76421],
            [36.     , 18.79511],
            [40.     , 17.     ]])

        assert np.all(xs == sol)

        # case 2 
        x = cdc2.amin 
        h = (cdc2.amax - cdc2.amin) / 10

        xs2 = np.zeros((10,2),dtype=float)
        for i in range(1,11):
            x2 = x + i * h
            y = cdc2.fit(x2) 
            xs2[i-1] = [x2,y]

        sol2 = np.array([[15.     , 23.09401],
            [16.     , 32.65986],
            [17.     , 40.     ],
            [18.     , 38.18033],
            [19.     , 35.29635],
            [20.     , 30.72555],
            [21.     , 23.48133],
            [22.     , 12.     ],
            [23.     , 11.03899],
            [24.     ,  8.     ]])

        assert np.all(xs2 == sol2)

if __name__ == '__main__':
    unittest.main()