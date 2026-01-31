from morebs2.deline import *

class DPointAnalysis:
    '''
    provides a description of the complexity of the dataset
    of two-dimensional labelled points that :class:`DLineateMC`
    delineates. 
    '''

    def __init__(self):
        return

class DLineateMetric:
    '''
    :attribute label:
    :attribute posMiss: points found inside delineation with a different label
    :attribute negMiss: points found outside delineation with the same label 
    '''

    def __init__(self,label,counter):
        self.label = label
        self.count = counter[label]
        self.posMiss = np.sum(np.array(list(counter.values())))\
            - counter[label]
        self.negMiss = counter[-1]

class DLineateMC:
    '''
    NOTE: inefficiencies exist. 
    '''

    def __init__(self,xyl,dmethod="nodup"):
        self.xyl = xyl
        self.dmethod = dmethod
        self.xyl_unproc = deepcopy(self.xyl)
        self.d = None
        self.dds = []
        self.last_process = [None,None]
        self.num_labels_rem = None
        self.didn = "0"
        self.bilabel = None # [delineator id, label]

    def delineate_one(self,clockwise = True):
        # case: done
        if self.num_labels_rem == 1:
            return True

        self.declare_DLineate22(clockwise)
        l = self.d.idn
        c = self.delineate_remainder(clockwise)

        # case: only two remaining
        if self.num_labels_rem == 2:
            q = list(c.values())
            q_ = None
            for q2 in q: 
                if q2 != self.d.label: 
                    q_ = q2
                    break
            self.bilabel = [l,q_] 
        return False

    def delineate_remainder(self,clockwise=True):
        '''
        delineates the points in `xyl`

        return := bool to further delineate on the points in `d`. 
        '''

        i,c,q = self.d.full_process(False)
        print("I")
        print(i)
        print("C")
        print(c)
        print("Q")
        print(q)

        self.dds.append(self.d)
        # case: perfect delineation
        if c[self.d.label] == c[-1] + c[self.d.label]:
            #self.xyl_unproc = np.delete(self.xyl_unproc,i,0)
            return c 

        self.delineate_delineation(c,i,clockwise)
        #self.xyl_unproc = np.delete(self.xyl_unproc,i,0)
        return c

    def delineate_delineation(self,c,indices,clockwise):
        '''
        '''
        assert type(self.d) != type(None), "no delineation to delineate"

        # declare a disposable `DLineate22` to get labelCounts
        d = DLineate22(deepcopy(self.xyl_unproc[indices]),
            clockwise,"nojag",self.didn)
        d.label_counts()
        lc = deepcopy(d.lc)

        for c_ in c:
            if c_ == self.d.label:
                continue
            
            d = self.declare_sub_DLineate22(c_,indices,lc)
            i2,c2,q2 = d.full_process(False)

            # get increase and decrease score
            inc = q2
            dec = sum(c2.values()) - q2
            inc -= dec

            # case: improvement, add to solution
            if inc > 0:
                self.dds.append(d)
            else:
            # case: no improvement, do not add
                self.decrement_didn()

        return

    def declare_sub_DLineate22(self,targetLabel,indices,labelCounts):
        d = DLineate22(deepcopy(self.xyl_unproc[indices]),
            clockwise,self.dmethod,self.didn)
        self.increment_didn()
        d.lc = deepcopy(labelCounts)
        d.set_target_label(targetLabel)
        d.sort_data()
        return d

    def declare_DLineate22(self,clockwise):
        '''
        '''

        # remove processed points from
        if type(self.d) != type(None):
            self.xyl_unproc = deepcopy(self.d.xyl)

        self.d = DLineate22(deepcopy(self.xyl_unproc),clockwise,"nojag",self.didn)
        self.increment_didn()
        self.d.preprocess()


        # get the number of labels remaining
        self.num_labels_rem = len(self.d.lc)
        return

    def increment_didn(self):
        self.didn = str(int(self.didn) + 1)

    def decrement_didn(self):
        self.didn = str(int(self.didn) - 1)

def test_dataset__DLineateMC_2():
    '''
    points of different labels spatially intersect; 5 labels. 
    '''
    return -1

def test_dataset__DLineateMC_3():
    '''
    points of different labels spatially intersect (entirely); 4 labels. 
    '''
    return -1

########