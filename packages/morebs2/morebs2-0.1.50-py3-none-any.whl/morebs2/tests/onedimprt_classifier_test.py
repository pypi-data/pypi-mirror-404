from morebs2.numerical_space_data_generator import * 
from morebs2.modular_labeller import * 
from morebs2.onedimprt_classifier import * 
import unittest

def OneDimClassifier_test_dataset_1(): 

    bounds = np.zeros((4,2)) 
    bounds[:,0] -= 10 
    bounds[:,1] += 10 

    startPoint = np.zeros((4,)) - 10 
    columnOrder = np.array([0,1,2,3]) 
    ssi_hop = 3 

    rch2 = sample_rch_1_with_update(deepcopy(bounds),deepcopy(bounds),ssi_hop,0.1)
    cv = 0.4
    rssi2 = ResplattingSearchSpaceIterator(bounds, startPoint, \
        columnOrder, SSIHop = ssi_hop,resplattingMode = ("relevance zoom",rch2), additionalUpdateArgs = (cv,))

    ##xr = np.array([next(rssi) for _ in range(1000)]) 
    xr2 = np.array([next(rssi2) for _ in range(1000)])
    return xr2 

class TestOneDimClassifierClass(unittest.TestCase):

    '''
    '''
    def test__OneDimClassifier__adjust_partition__case_1(self):
        D = OneDimClassifier_test_dataset_1() 
        L = np.array([label_vector__type_binary_alt_sum(v) for v in D]) 
        
        # subcase 1 
        odc = OneDimClassifier(D,L,2,0)

        qx = deepcopy(odc.prt) 
        odc.adjust_partition()
        qx2 = deepcopy(odc.prt) 

        qx_ans = np.array([\
            [0.,-10.,7.55144,1.46531272],\
            [2.,-10.,7.55144,1.02932592],\
            [3.,-10.,7.55144,1.48707732],\
            [1.,-9.59191,7.55144,1.86464141],\
            [4.,-9.59191,7.55144,1.77047391]])
        qx2_ans = np.array([[2.,-10.,7.55144]])

        assert equal_iterables(qx,qx_ans) 
        assert equal_iterables(qx2,qx2_ans) 

        # subcase 2 
        odc2 = OneDimClassifier(D,L,2,1)
        qx_ = deepcopy(odc2.prt) 
        odc2.adjust_partition()
        qx2_ = deepcopy(odc2.prt) 

        qx2_ans_ = np.array([\
            [0.,-10.,1.46531272],\
            [4.,1.46531272,7.55144]])

        assert equal_iterables(qx_,qx_ans)
        assert equal_iterables(qx2_,qx2_ans_), "got {}".format(qx2_)
        return

    def test__OneDimClassifier__adjust_partition__case_2(self): 
        D = OneDimClassifier_test_dataset_1() 
        L2_ = np.array([label_vector__type_uniform_partition_sum(v,[-40,40]) for v in D])

        # subcase 1 
        odc = OneDimClassifier(D,L2_,2,0)
        qx = deepcopy(odc.prt) 
        odc.adjust_partition()
        qx2 = deepcopy(odc.prt) 

        qx_ans = np.array([\
            [0.,-10.,3.33334,-7.47449313],\
            [1.,-10.,7.55144,-5.7634775 ],\
            [2.,-10.,7.55144,0.79704803],\
            [3.,-9.58848,7.55144,5.36958762],\
            [4.,4.69136,7.55144,7.07476]])
        qx2_ans = np.array([\
            [2.,-10.,7.55144]])

        assert equal_iterables(qx,qx_ans) 
        assert equal_iterables(qx2,qx2_ans) 

        # subcase 2  
        odc = OneDimClassifier(D,L2_,2,1)
        qx = deepcopy(odc.prt) 
        odc.adjust_partition()
        qx2 = deepcopy(odc.prt) 

        qx_ans = np.array([[0.,-10.,3.33334,-7.47449313],\
            [1.,-10.,7.55144,-5.7634775],\
            [2.,-10.,7.55144,0.79704803],\
            [3.,-9.58848,7.55144,5.36958762],\
            [4.,4.69136,7.55144,7.07476]])
        qx2_ans = np.array([\
            [2.,-10.,0.79704803],\
            [3.,0.79704803,5.36958762],\
            [4.,5.36958762,7.55144]])

        assert equal_iterables(qx,qx_ans) 
        assert equal_iterables(qx2,qx2_ans) 

    def test__OneDimClassifier__adjust_partition__case_3(self): 

        D = OneDimClassifier_test_dataset_1() 
        L2__ = np.array([label_vector__type_uniform_partition_index(v,[-10,10],2,num_labels=2) for v in D])

        # subcase 1 
        odc = OneDimClassifier(D,L2__,2,0)
        
        qx = deepcopy(odc.prt) 
        odc.adjust_partition()
        qx2 = deepcopy(odc.prt) 

        qx_ans = np.array([\
            [0.,-10.,-1.11111,-6.19388667],\
            [1.,1.11111,7.55144,4.87319363]])
        qx2_ans = np.array([\
            [0.,-10.,-1.11111],\
            [1.,-1.11111,7.55144]])

        assert equal_iterables(qx,qx_ans) 
        assert equal_iterables(qx2,qx2_ans), "got \n{} \nexpected \n{}".format(qx2,qx2_ans)

        # subcase 2 
        odc = OneDimClassifier(D,L2__,2,1)

        qx = deepcopy(odc.prt) 
        odc.adjust_partition()
        qx2 = deepcopy(odc.prt) 

        qx_ans = np.array([\
            [0.,-10.,-1.11111,-6.19388667],\
            [1.,1.11111,7.55144,4.87319363]])

        qx2_ans = np.array([\
            [0.,-10.,-6.19388667],\
            [1.,-6.19388667,7.55144]])

        assert equal_iterables(qx,qx_ans) 
        assert equal_iterables(qx2,qx2_ans) 

    def test__OneDimClassifier__adjust_partition__case_4(self): 


        D2 = np.zeros((1000,4)) 
        D2[:,0] += 10 
        D2[:,1] -= 5
        D2[:,2] += 10 
        D2[:,3] -= 5 

        D2[:500,0] /= 2 
        D2[500:,1] *= 2 
    
        L2 = [0] * 500 + [1] * 500 
        L2 = np.array(L2)

        odc = OneDimClassifier(D2,L2,0,0) 
        odc.make() 
        c3 = 0 
        for d,l in zip(D2,L2): 
            l_ = odc.classify(d)
            c3 += bool(l_ == l)
        assert c3 == 1000, "got {}".format(c3) 

class TestRecursiveOneDimClassifierClass(unittest.TestCase): 

    def test__RecursiveOneDimClassifier__fit_case_1(self): 

        D = OneDimClassifier_test_dataset_1() 
        L2 = np.array([label_vector__type_binary_alt_sum(v) for v in D]) 

        # subcase 1
        prg = prg__LCG(-56.7,122.3,-31.6,-3121.66) 
        #prg = prg__LCG(0,2,1,21) 
        rodc = RecursiveOneDimClassifier(D,L2,prg,0)
        rodc.fit() 
        c = rodc.score_accuracy(D,L2)

        # subcase 2
        rodc2 = RecursiveOneDimClassifier(D,L2,prg,1)
        rodc2.fit() 
        c2 = rodc2.score_accuracy(D,L2)

        # subcase 3 
        rodc3 = RecursiveOneDimClassifier(D,L2,prg,prg)
        rodc3.fit() 
        c3 = rodc3.score_accuracy(D,L2)

        assert c == 238
        assert c2 == 283
        assert c3 == 210, "got {}".format(c3)

    def test__RecursiveOneDimClassifier__fit_case_2(self): 
        D = OneDimClassifier_test_dataset_1() 
        L2_ = np.array([label_vector__type_uniform_partition_sum(v,[-40,40]) for v in D])

        prg = prg__LCG(-56.7,122.3,-31.6,-3121.66) 

        # subcase 1
        rodc = RecursiveOneDimClassifier(D,L2_,prg,0)
        rodc.fit() 
        c = rodc.score_accuracy(D,L2_)

        # subcase 2
        rodc2 = RecursiveOneDimClassifier(D,L2_,prg,1)
        rodc2.fit() 
        c2 = rodc2.score_accuracy(D,L2_)

        # subcase 3
        rodc3 = RecursiveOneDimClassifier(D,L2_,prg,prg)
        rodc3.fit() 
        c3 = rodc3.score_accuracy(D,L2_)

        assert c == 563, "got {}".format(c)
        assert c2 == 760, "got {}".format(c2)
        assert c3 == 459, "got {}".format(c3)

    def test__RecursiveOneDimClassifier__fit_case_3(self): 
        D = OneDimClassifier_test_dataset_1() 
        L2__ = np.array([label_vector__type_uniform_partition_index(v,[-10,10],2,num_labels=2) for v in D])

        prg = prg__LCG(-56.7,122.3,-31.6,-3121.66) 

        # subcase 1
        rodc = RecursiveOneDimClassifier(D,L2__,prg,0)
        rodc.fit() 
        c = rodc.score_accuracy(D,L2__)

        # subcase 2
        rodc2 = RecursiveOneDimClassifier(D,L2__,prg,1)
        rodc2.fit() 
        c2 = rodc2.score_accuracy(D,L2__)

        # subcase 3
        rodc3 = RecursiveOneDimClassifier(D,L2__,prg,prg)
        rodc3.fit() 
        c3 = rodc3.score_accuracy(D,L2__)

        assert c == 1000
        assert c2 == 862
        assert c3 == 719, "got {}".format(c3)

    def test__RecursiveOneDimClassifier__fit_case_4(self): 
        D = np.zeros((1000,4)) 
        D[:,0] += 10 
        D[:,1] -= 5
        D[:,2] += 10 
        D[:,3] -= 5 

        prg = prg__LCG(-56.7,122.3,-31.6,-3121.66) 
        f = lambda x,x2: x - x2
        L = np.array([label_vector__type_prgANDindex_output(i,prg,f,5) for i in range(len(D))]) 

        rodc = RecursiveOneDimClassifier(D,L,prg,0)
        rodc.fit() 
        c = rodc.score_accuracy(D,L)
        assert c == 199 

    def test__RecursiveOneDimClassifier__fit_case_5(self): 
        # subcase 1 
        D2 = np.zeros((1000,4)) 
        D2[:,0] += 10 
        D2[:,1] -= 5
        D2[:,2] += 10 
        D2[:,3] -= 5 

        D2[:500,0] /= 2 
        D2[500:,1] *= 2 

        L2 = [0] * 500 + [1] * 500 
        L2 = np.array(L2)

        prg = prg__LCG(-56.7,122.3,-31.6,-3121.66) 
        
        rodc = RecursiveOneDimClassifier(D2,L2,prg,0)
        rodc.fit() 
        c = rodc.score_accuracy(D2,L2)
        assert c == 1000, "got {}".format(c) 

        # subcase 2 
        D3 = deepcopy(D2) 
        D3[250:500,2] *= 2 
        D3[250:500,3] /= 2 
        L3 = [0] * 250 + [1] * 250 + [2] * 250 + [3] * 250
        L3 = np.array(L3) 

        rodc2 = RecursiveOneDimClassifier(D3,L3,prg,0)
        rodc2.fit() 
        c2 = rodc2.score_accuracy(D3,L3)
        assert c2 == 750, "got {}".format(c2)  

    

if __name__ == "__main__":
    unittest.main()
