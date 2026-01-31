from morebs2.ball_comp import *
from morebs2.message_streamer import *
from morebs2.ball_comp_test_cases import *
import unittest    

'''
py -m morebs2.tests.ball_comp_test  
'''
class BallCompClass(unittest.TestCase):

    def test__BallComp__conduct_decision__sample_data_1__case1(self):
        maxBalls = 20
        maxRadius = 5.0
        td = ballcomp_sample_data_1()
        bc = BallComp(maxBalls,maxRadius,None,True)
        
        S = [] 
        for t in td:
            s = bc.conduct_decision(t)
            S.append(s) 

        assert S == [2, 2, 2, 2, 2, 2, 2, 2]
        assert len(bc.balls) == 8 
        return

    def test__BallComp__conduct_decision__sample_data_1__case2(self):

        maxBalls = 4 
        maxRadius = 8.0

        td = ballcomp_sample_data_1()
        bc = BallComp(maxBalls,maxRadius,None,False)

        S = [] 
        L = [] 
        for (i,t) in enumerate(td):
            s = bc.conduct_decision(t)
            S.append(s) 

            l = len(bc.balls) 
            L.append(l)

            if i >= 5: 
                assert bc.terminateDelta
            
        assert S == [2, 2, 2, 1, 2, -1, -1, -1],"got {}".format(S) 
        assert L == [1, 2, 3, 3, 4, 4, 4, 4] 
        
        ball_info = {0:(1,5),\
                    1:(1,5),\
                    3:(2,5),\
                    4:(1,5)} 

        Q = bc.summarize_ball_info()
        for q in Q: 
            ans = ball_info[q[0]] 
            assert ans == q[2] 

    def test__BallComp__conduct_decision__sample_data_2(self): 

        maxBalls = 4
        maxRadius = 0.2
        td = ballcomp_sample_data_2()
        vh = ViolationHandler1(maxBalls,maxRadius)
        bc = BallComp(maxBalls,maxRadius,vh,0)#2)

        c = None 
        for i,t in enumerate(td):
            s = bc.conduct_decision(t)
            print("point size: ",bc.point_size(), s,bc.terminateDelta)
            if type(c) == type(None) and s == -1: 
                c = i 

        print("********************")
        print("BALLS ", len(bc.balls))
        for k,v in bc.balls.items():
            print("k ",k)
            print(v)
            print()
        assert c == 5 

    def test__BallComp__conduct_decision__sample_data_3(self): 

        maxBalls = 5
        maxRadius = .5
        td = ballcomp_sample_data_3()
        vh = ViolationHandler1(maxBalls,maxRadius)

        # TODO: delete k
        bc = BallComp(maxBalls,maxRadius,vh,True)
        print("TD ",td.shape)

        c = None 
        L = []  
        for (i,t) in enumerate(td):
            s = bc.conduct_decision(t)
            if type(c) == type(None) and s == -1:
                c = i 
            L.append(s) 

        assert L == [2, 2, 2, 2, 1, 2, -1, -1] 
        assert c == 6 

        print("********************")
        print("BALLS ", len(bc.balls))
        for k,v in bc.balls.items():
            print("k ",k)
            print(v)
            print()

    def test__BallComp__conduct_decision__sample_data_4(self): 

        maxBalls = 5
        maxRadius = 20.0

        vh = ViolationHandler1(15,80.0)

        filePath = "morebs2/indep/ballcomp_sample_data_4.txt"
        ms = MessageStreamer(filePath,readMode = 'r')
        bc = BallComp(maxBalls,maxRadius,vh,0)

        q = 20
        s = 0
        S = [] 
        while ms.stream() and q > 0:
            for t in ms.blockData:
                d = bc.conduct_decision(t)
                if d != -1:
                    s += 1
                S.append(d) 
            q -= 1

        assert S.count(1) == 1254 and S.count(2) == 6 
        assert bc.point_size() == 2493 and s == 1260
        ms.end_stream() 

    def test__BallComp__conduct_decision__sample_data_5(self): 
        D = ballcomp_sample_data_LCG_1() 

        num_balls = 50 
        max_radius = 2000  
        vh = ViolationHandler1(num_balls,max_radius)
        bc = BallComp(num_balls,max_radius,vh,verbose=0)

        S = [] 
        L0 = [] 
        for v in D: 
            s = bc.conduct_decision(v) 
            S.append(s)
            L0.append(bc.ball_label_for_point(v)) 
        S = np.array(S)

        L1 = [] 
        L1_ = [] 
        for v in D: 
            L1_.append(bc.ball_label_for_point__qualify_radius(v))  
            L1.append(bc.ball_label_for_point(v)) 
        L1 = np.array(L1)

        freq_1 = list(S).count(1)
        freq_2 = list(S).count(2)
        assert freq_1 == 1652 and freq_2 == 348 

        print("check cumulative difference between real-time and post-solution labeling") 
        assert np.sum(np.abs(L1 - L0)) == 30137 


if __name__ == "__main__":
    unittest.main()