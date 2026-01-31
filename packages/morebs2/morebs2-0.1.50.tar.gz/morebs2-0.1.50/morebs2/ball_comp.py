from .ball_volume_estimators import *
from .ball_operator import *
from .violation_handler import *

def dec1(u,t,p):
    x1 = 1 - u / t
    x2 = t / p
    return (x1 + x2) / 2.0

def dec2(b1,b2):
    return b1/b2 * 1/2

"""
if verbose is set to 2, includes computation of disjunction scores, as well 
as display from verbose==1. 
"""
class BallComp:

    MIN_LENGTH_RATIO = 0.01

    def __init__(self, maxBalls,maxRadius,vh1,verbose = 0):
        assert maxRadius > 0.0 and maxBalls > 0, "invalid args. for BallComp"
        self.maxBalls = maxBalls
        self.maxRadius = maxRadius

        self.balls = {} # int:idn -> Ball
        self.pointMem = None # (label of last point added, last point added)
        self.ballNeighborsUpdate = None

        assert verbose in [2,1,0]
        self.verbose = verbose
        self.dve = DisjunctionVolumeEstimator()
        self.ballCounter = 0

        if type(vh1) == type(None): 
            self.vh = ViolationHandler1(maxBalls,maxRadius) 
        else: 
            self.vh = vh1

        self.terminateDelta = False

        self.ts = 0 # timestamp

        # keeps track of argument history
        # each element is (value,timestamp)
        self.bah = []
        self.rah = []

    ###################################### start: main function 

    """
    main method #1: add point to solution
    """
    def conduct_decision(self,p):
        if self.terminateDelta:
            return -1

        self.dve.clear_cache()
        if self.verbose == 2:
            print("\t* pre-decision measures")
            self.summarize_volume_measures()
        d1 = self.decision_1_score(p)
        d2 = self.decision_2_score()
        self.dve.clear_cache()

        # case: make new ball
        if d2 < d1[2]:
            if self.verbose >= 1:
                print("-- choose decision 2")
            b = Ball(p,self.ballCounter)
            b.add_element(p)
            b.radius = BallComp.MIN_LENGTH_RATIO * self.maxRadius
            self.ballCounter += 1

            ## TODO: add ball here
            self.add_ball(b)
            self.load_recommendation((2,p,b.idn))
            if self.verbose >= 1:
                print("-------------------------------------------")
            return 2 if not self.terminateDelta else -1 

        # case: add to present ball
        self.balls[d1[1]].add_element(p)
        if self.verbose >= 1:
            print("--- decision 1 ball")
            print(self.balls[d1[1]])
            print("----")

            # update neighbors
        self.update_neighbors_of_ball(d1[1])

            # subcase: no merge
            ## update ball volume and its neighbor 2-intersection volumes
        if d1[0] == 1:
            if self.verbose >= 1: print("-- choose decision 1-no merge")
            self.update_target_ball_volume(d1[1])
            self.update_target_ball_2int(d1[1])
            nbi = d1[1]
        else:
                # subcase: merge
                ## merge balls into one
            if self.verbose >= 1: print("-- choose decision 1-merge")
                ##bs = self.dataless_ball_copies(self.balls[d1[1]].neighbors | {d1[1]})
            x = self.balls[d1[1]].neighbors | {d1[1]}
            bs = [self.balls[x_] for x_ in x]
            ball0 = BallComp.merge_ball_list(bs)
            ball0.idn = int(self.ballCounter)
            self.ballCounter += 1
                ## delete all values in self.balls[d1[1]].neighbros | {d1[1]}
            self.remove_ballset(self.balls[d1[1]].neighbors | {d1[1]})
                ## add ball0
            self.add_ball(ball0)
            nbi = ball0.idn

        self.load_recommendation((1,self.balls[nbi].radius,nbi))
        
        if self.verbose >= 1:
            print("-------------------------------------------")
        return 1 if not self.terminateDelta else -1 

    """
    main method #2: point classification, nearest ball 
    """
    def ball_label_for_point(self, p):
        '''
    determines the ball idn for point based on minumum
    euclidean point distance
        '''
        bc = np.array([(euclidean_point_distance(b.center,p),b.idn)\
            for b in self.balls.values()])

        if len(bc) == 0:
            return -1
        i = np.argmin(bc[:,0])
        return int(bc[i,1])

    """
    main method #3: point classification, nearest ball that captures point 
    """
    def ball_label_for_point__qualify_radius(self,p):
        """
        Determines ball label for point based on balls' current radii, as they say,
        "variantate` de las labelovos de los qualifacados"

        :param p: vector
        :type p: np.array
        :return: los labelovas
        :rtype: int
        """
        bc = np.array([(euclidean_point_distance(b.center,p),b.idn)\
            for b in self.balls.values()])

        if len(bc) == 0:
            return -1

        # sort by ascending euclidean point distance
        order = np.argsort(bc[:,0])
        for o in order:
            if bc[o,0] <= self.maxRadius:
                return self.balls[bc[o,1]].idn
        return -1

    def summarize_volume_measures(self):
        print("---- individual ball volumns")
        for k,v in self.dve.ballVolumes.items(): 
            print("ball {} volume {}".format(k,round(v,5))) 

        print("---- intersectional volumes")
        for k,v in self.dve.d.items(): 
            print("intersection {} volume {}".format(k,round(v,5))) 
        print("\t********")

    def summarize_ball_info(self): 
        L = [] 
        for k,v in self.balls.items(): 
            l = (k,v.radius,v.data.newData.shape) 
            L.append(l) 
        return L 

    def point_size(self): 
        return sum([v.data.newData.shape[0] for v in self.balls.values()]) 

    ###################################### end: main function 

    ###################################### start: method requirements for decision 1
    ################################################## start: point add functions

    def update_neighbors_of_ball(self,idn):
        '''
        calculates the new neighbor set N1 of the bl'th ball that used to have the neighbor
        set N0. Then update the `neighbors` variable for all affected neighbors of the
        bl'th ball.

        :param idn:
        :type idn: int
        '''
        q = self.balls[idn].neighbors
        self.balls[idn].neighbors = self.neighbors_of_ball(idn)

        self.ballNeighborsUpdate = (idn,q,deepcopy(self.balls[idn].neighbors))
        self.update_ball_neighbors_var(self.ballNeighborsUpdate[0],\
            self.ballNeighborsUpdate[1],self.ballNeighborsUpdate[2])

    def update_ball_neighbors_var(self,idn,n0,n1):
        '''
        updates the neighbors of each ball after a ball has a radius change by the rule: 
        - positive difference set N1 - N0: adds `idn` to these balls' neighbors.
        - negative difference set N0 - N1: subtracts `idn` from .these balls' neighbors.
        ''' 

        pd = n1 - n0
        nd = n0 - n1
        for p in pd:
            if p not in self.balls: continue 
            self.balls[p].neighbors = self.balls[p].neighbors | {idn}
        for n in nd:
            if n not in self.balls: continue 
            self.balls[n].neighbors = self.balls[n].neighbors - {idn}
        return

    def revert_update_neighbors_of_ball(self):
        self.update_ball_neighbors_var(self.ballNeighborsUpdate[0],\
            self.ballNeighborsUpdate[2],self.ballNeighborsUpdate[1])
        self.ballNeighborsUpdate = None
        return

    #@
    def neighbors_of_ball(self,idn):
        b = self.balls[idn]
        n = set()
        for k,v in self.balls.items():
            if idn == k: continue
            if v.is_neighbor(b): n.add(k)
        return n

    def add_point_to_ball(self,p,idn):
        self.balls[idn].add_element(p)
        return

    ################################################### end: point add functions

    def dataless_ball_copies(self,indices):
        '''
        returnia the dataless ball copies of that indices

        :type indices: iter
        :return: returnia
        :rtype: list<listinia de ballco>
        '''
        return [Ball.dataless_copy(self.balls[i]) for i in indices]

    '''
    assumes all balls are neighbors
    '''
    @staticmethod
    def merge_ball_list(bs):
        if len(bs) == 0: return None

        # sort ball set in ascending distance from .ball-set mean
        q = np.array([bs_.center for bs_ in bs])
        m = np.mean(q,axis = 0)
        d = [euclidean_point_distance(bs_.center,m) for bs_ in bs]
        indices = list(np.argsort(d))

        # merge in that order
        i = indices.pop(0)
        b_ = bs[i]

        while len(indices) > 0:
            i = indices.pop(0)
            b_ = b_ + bs[i]
        return b_

    #### end: method requirements for decision 1

    ##################################### start: decision function 1

    def pre_decision_1_(self,p,idn):

        # add point to ball
        self.add_point_to_ball(p,idn)

        # update its neighbors
        if self.verbose >= 1:
            print("\t\tprevious neighbors:\n\t",vector_to_string(sorted(self.balls[idn].neighbors)))

        self.update_neighbors_of_ball(idn)

        if self.verbose >= 1:
            print("\t\tnew neighbors:\n\t",vector_to_string(sorted(self.balls[idn].neighbors)))

        # update target ball volume
        self.update_target_ball_volume(idn)

        # update target ball 2-int
        self.update_target_ball_2int(idn)

        return

    def update_target_ball_volume(self,idn):
        ###print("logging ball volume for {}: {}".format(idn,self.balls[idn].radius))
        self.dve.log_ball_volume(self.balls[idn])

    def update_target_ball_2int(self,idn):
        q = self.balls[idn].neighbors
        for q_ in q:
            b2 = self.balls[q_]
            self.dve.log_ball_volume_2intersection(self.balls[idn],b2)
        return

    def post_decision_1_(self,idn):
        # revert all changes made
            # target ball add point
        self.balls[idn].revert_add_point()
            # target ball neighbors
        self.revert_update_neighbors_of_ball()
        self.dve.revert_cache_delta(1)
        self.dve.revert_cache_delta(2)

    def decision_1_score(self,p):
        bl = self.ball_label_for_point(p)

        if self.verbose >= 1:
            print("\tSIM:\n\tdecision 1")
            print("\t\tadding point to: ",bl)
        # case: no balls to choose
        if bl == -1:
            return (1,bl,2.0)

        self.pre_decision_1_(p,bl)

        bs1 = self.balls[bl].neighbors | {bl}
        # simulate 1: no merge
        if self.verbose:
            print("estimating disjunction")
        x = True if self.verbose == 2 else False
        vu = self.dve.estimate_disjunction_at_target_ball(self.balls[bl].idn,x,500)
        vt = np.sum([ball_area(self.balls[i].radius,p.shape[0]) for i in bs1])
        vp = ball_area(self.maxRadius,p.shape[0]) * len(bs1)
        d1 = dec1(vu,vt,vp)
        if self.verbose >= 1:
            print("\t\t no-merge volume measures: ",np.round([vu,vt,vp],5))
            print("\t\t no-merge score: ", round(d1,5)) 

        # simulate 2: merge target ball w/ its neighbors
        ballSet = self.dataless_ball_copies(bs1)

        ball0 = BallComp.merge_ball_list(ballSet)
        vu = ball_area(ball0.radius,p.shape[0])
        vt = vu
        vp = ball_area(self.maxRadius,p.shape[0])
        d2 = dec1(vu,vt,vp)
        if self.verbose >= 1:
            print("\t\t merge volume measures: ",np.round([vu,vt,vp],5))
            print("\t\t merge score: ", round(d2,5))

        # choose the better option
        option = (1,bl,d1) if d1 <= d2 else (2,bl,d2)

        if self.verbose >= 1:
            print("\t\t decision 1 option: ",option[0],option[1],round(option[2],5)) 

        # revert changes
        self.post_decision_1_(bl)

        return option

    ############################################## end: decision function 1

    ############################################# start: decision function 2

    def decision_2_score(self):
        score = dec2(len(self.balls) + 1, self.maxBalls)

        if self.verbose >= 1:
            print("\tdecision 2 option:\n\t\tballs {} max balls {} score {}".format(len(self.balls),self.maxBalls,score))
        return score

    #### end: decision function 2

    #### start: decision 1 merge- ballset removal from .neighbors

    def remove_ballset(self,idns):

        s = set()
        # get affected neighbors from .ballset removal
        for idn in idns:
            s = s | self.balls[idn].neighbors

            # delete ball
            del self.balls[idn]

        # filter out all balls found in idns
        s = s - idns

        # remove labels of ballset from .affected neighbors
        self.delete_balls_from_affected_neighbors(idns,s)

        # remove all volume and intersection values in `dve` that contain
        # any label
        self.dve.delete_keyset(idns)

        return

    def delete_balls_from_affected_neighbors(self,bs,neighbors):
        for n in neighbors:
            self.balls[n].neighbors = self.balls[n].neighbors - bs
        return

    #### start: adjustment

    def add_ball(self,b):
        if self.verbose >= 1:
            print("\t * adding ball ", b.idn)
        self.balls[b.idn] = b
        self.update_ball_info(b.idn)
        return

    def update_ball_info(self,idn):
        self.update_neighbors_of_ball(idn)
        self.update_target_ball_volume(idn)
        self.update_target_ball_2int(idn)
        self.dve.clear_cache()

    """
    decision := (1,ball radius::(merged|non-merged),ball idn) | (2,p,ballIdn)
    """
    def load_recommendation(self,decision):
        assert decision[0] in {1,2}, "invalid decision"

        if decision[0] == 1:
            if self.verbose: print("$$ violation 1 check")
            res1 = self.vh.check_violation_1(decision[1],self.maxRadius)

            # perform ball-split
            if res1[0]:
                if self.verbose: print("-- max radius exceeded: splitting ball")
                self.fix_violation_1_by_ball_split(decision[2])

            ### TODO: add ball-split here as well
            elif not res1[0] and type(res1[1]) != type(None):
                # log old argument
                self.log_arg('r')

                # update `maxRadius`
                q = self.maxRadius + res1[1]
                if self.verbose: print("-- updating max radius: {}->{}".format(self.maxRadius,q))
                self.change_arg(('r',q))
                return
        else:
            if self.verbose: print("$$ violation 2 check")
            res2 = self.vh.check_violation_2(len(self.balls),self.maxBalls)
            self.fix_violation_2((decision[2],decision[1]),res2)
            return


    """
    splits balls by a greedy splitting scheme
    """
    def split_ball(self,idn):
        assert self.balls[idn].radius > self.maxRadius, "cannot split ball under radius"

        b = BallOperator(self.balls[idn])
        b.run_subball_split((self.maxRadius * 0.9,"literal"),"minimal",self.verbose)
        return b

    def save_split_ball(self,idn,bo):
        # save balls
        for s in bo.subballs:
            s.idn = self.ballCounter
            self.ballCounter += 1
            self.balls[s.idn] = s

        # update their info
        for s in bo.subballs:
            self.update_ball_info(s.idn)

        # delete ball
        self.remove_ballset({idn})
        return

    """
    violation 1 occurs when target ball needs to be split
    """
    def fix_violation_1_by_ball_split(self,bIdn):
        if self.verbose: print("*** Fixing violation 1 by split")
        bo = self.split_ball(bIdn)
        if self.verbose: print("Number of additional balls {}".format(len(bo.subballs) - 1))
        # check for violation of number of balls
        newNumberOfBalls = len(self.balls) - 1 + len(bo.subballs)
        if newNumberOfBalls > self.maxBalls:
            if self.verbose: print(" violation: {}".format(True))
            res2 = self.vh.check_violation_2(newNumberOfBalls,self.maxBalls)

            # terminate: cannot fix violation 1
            if res2[0]:
                if self.verbose: print("violation 1 cannot be fixed. terminate delta.")
                self.terminateDelta = True

                bo.revert_split()
            # do not terminate:
            else:
                # log old argument
                self.log_arg('b')

                # update `maxBalls`
                q = self.maxBalls + res2[1]
                self.change_arg(('b',q))

                if self.verbose: print("violation 1 -> new max balls: {}".format(q))

                # save split
                self.save_split_ball(bIdn,bo)

        # no violation
        else:
            self.save_split_ball(bIdn,bo)
        return

    """
    number of balls violation

    newBallInfo := (ball idn,new point)
    violation := (bool::violation,value)
    """
    def fix_violation_2(self,newBallInfo,violation):
        # case: max balls reached

        if violation[0]:
            if self.verbose: print("*** violation 2 cannot be fixed")
            # delete new ball
            ## new ball will not have any neighbors
            self.remove_ballset({newBallInfo[0]})

            # find a ball label for point
            l = self.ball_label_for_point__qualify_radius(newBallInfo[1])
            # ball found, add point to ball
            if l != -1:
                if self.verbose: print("found alternative ball @ {}".format(l))
                self.pre_decision_1_(newBallInfo[1],l)
            else: 
                l2 = self.ball_label_for_point(newBallInfo[1]) 
                b = self.balls[l2] 
                distance = euclidean_point_distance(b.center,newBallInfo[1]) 
                if distance <= self.maxRadius: 
                    self.pre_decision_1_(newBallInfo[1],l2) 
                else: 
                    self.terminateDelta = True 
            return
        # case: update maxBalls
        elif not violation[0] and type(violation[1]) != type(None):
            if self.verbose: print("*** violation 2 fixed")
            self.log_arg('b')
            q = self.maxBalls + violation[1]
            self.change_arg(('b',q))
            if self.verbose: print("new max number of balls: ",q)
            return

    ##################################### extraneous methods for changing and logging main BallComp parameters

    def log_arg(self,arg):
        assert arg in {'b','r'}, "invalid argument"
        x = self.maxBalls if arg == 'b' else self.maxRadius

        if arg == 'b':
            self.bah.append((self.maxBalls,self.ts))
        else:
            self.rah.append((self.maxRadius,self.ts))

    def change_arg(self,newArg):
        assert newArg[0] in {'b','r'}, "invalid argument"
        if newArg[0] == 'b':
            self.maxBalls = newArg[1]
        else:
            self.maxRadius = newArg[1]
        return