from morebs2 import numerical_space_data_generator,relevance_functions
import unittest
import numpy as np

'''
py -m morebs2.tests.numerical_space_data_generator_test  
'''

def sample_nsdi_1(q, filePath = "tests/s.txt", nr = None):
    """
    :param q: one of [relevance zoom,prg,np.ndarray]
    :param filePath: str, file path 
    :param nr: noise range,np.ndarray w/ length of 1 or 4. 
    """

    if type(q) == str:
        assert q in ['relevance zoom', 'prg']
    else:
        assert type(q) == np.ndarray, "333"

    bounds = np.array([[0,1.2],[-0.5,1.7],[-1.0,0.8],[-0.5,1.2]])
    sp = np.copy(bounds[:,0])
    columnOrder = None
    ssih = 4
    cv = 0.6
    bInf = (bounds,sp,columnOrder,ssih,(cv,))

    # make relevance function
    rch = relevance_functions.sample_rch_1_with_update(bounds, np.copy(bounds), ssih, cv)
    rm = (q, rch)

    ##sp = np.copy(bounds[:,1])
    modeia = 'w'

    q = numerical_space_data_generator.NSDataInstructions(bInf,rm,filePath,modeia,nr)
    return q

def sample_nsdi_2(q, filePath = "tests/s.txt", nr = None):
    """
    :param q: one of [relevance zoom,prg,np.ndarray]
    :param filePath: str, file path 
    :param nr: noise range,np.ndarray w/ length of 1 or 4. 
    """

    if type(q) == str:
        assert q in ['relevance zoom', 'prg']
    else:
        assert type(q) == np.ndarray, "333"

    bounds = np.array([[0,1.2],[-0.5,1.7],[-1.0,0.8],[-0.5,1.2]])
    sp = np.copy(bounds[:,0])
    columnOrder = None
    ssih = 7
    bInf = (bounds,sp,columnOrder,ssih,())

    # make relevance function
    rch = relevance_functions.sample_rch_2_with_update(bounds, np.copy(bounds))
    rm = (q, rch)
    modeia = 'w'

    q = numerical_space_data_generator.NSDataInstructions(bInf,rm,filePath,modeia,nr)
    return q


def sample_nsdi_3(wom=relevance_functions.idv,filePath = "ARGHONIAX"):
    assert wom == relevance_functions.idv or wom == relevance_functions.binary_labelling_scheme_1
    bounds = np.array([[0,33],[-3,42],[-3,15],[30,69],[20,200],[-10,370],[-100,100],[-250,100],[100,1000],[-400,250]])

    sp = np.copy(bounds[:,0])
    columnOrder = None
    ssih = 3
    bInf = (bounds,sp,columnOrder,ssih,())

    rch = relevance_functions.sample_rch_hop_counts_scheme_type_2(np.copy(bounds),np.copy(bounds),ssih,15,wom)
    rm = ("relevance zoom",sample_rch_blind_accept())

    nsdi = NSDataInstructions(bInf, rm,"ARGHONIAY.txt",'w',noiseRange = None,writeOutMode = rch)
    return nsdi 
    

class TestNSDataInstructionClass(unittest.TestCase):

    '''
    '''
    def test__sample_nsdi_11(self):
        print("Test 1 for: NS Data Instruction")
        q = sample_nsdi_1("relevance zoom",filePath="tests/s11.txt")
        q.make_rssi()

        c = 0
        while q.fp:
            q.next_batch_()
            c += 1
        print("case 1")
        print("# batches: ",c)
        q.batch_summary()

    def test__sample_nsdi_12(self):
        print("Test 2 for: NS Data Instruction")
        q = sample_nsdi_1('prg',"tests/s12.txt")
        q.make_rssi()

        c = 0
        while q.fp and c < 100:
            q.next_batch_()
            c += 1
        print("case 2")
        print("# batches: ",c)

        if q.fp:
            q.fp.close()

        q.batch_summary()

    def test__sample_nsdi_13(self):
        print("Test 3 for: NS Data Instruction")
        b1 = np.array([[0.9,1.2],[1.2,1.7],[-1.0,-0.5],[0.7,1.1]])
        bx = np.array([b1])

        q = sample_nsdi_1(bx,"tests/s13.txt")
        q.make_rssi()

        while q.fp:
            q.next_batch_()
        assert q.c == 3, "incorrect number of batches,got {} want {}".format(q.c,1)
        print("case 3")
        q.batch_summary()

    def test__sample_nsdi_14(self):
        print("Test 4 for: NS Data Instruction")
        nr = np.array([[0.01,0.07]])
        q = sample_nsdi_1('relevance zoom',"tests/s14.txt",nr)
        q.make_rssi()

        c = 0
        while q.fp and c < 100:
            q.next_batch_()
            c += 1
        if q.fp:
            q.fp.close()
        print("# batches: ",c)
        q.batch_summary()

    def test__sample_nsdi_21(self):
        print("Test 5 for: NS Data Instruction")
        q = sample_nsdi_2("relevance zoom",filePath="tests/s21.txt")
        q.make_rssi()
        while q.fp:
            q.next_batch_()
        return

    def test__sample_rch_blind_accept(self):
        bounds = np.array([[0,3],[-3,3],[-3,0],[3,6]])
        sp = np.copy(bounds[:,0])
        columnOrder = None
        ssih = 2
        bInf = (bounds,sp,columnOrder,ssih,())
        rm = ("relevance zoom",relevance_functions.sample_rch_blind_accept())
        nsdi = numerical_space_data_generator.NSDataInstructions(bInf, rm,"ARGHONIA.txt",'w',noiseRange = None,writeOutMode = "literal")
        nsdi.make_rssi()

        c = 0
        while nsdi.fp:
            nsdi.next_batch_()
            #nsdi.batch_summary()
            c += 1
        assert c == 11, "incorrect number of batches,got {} want {}".format(c,11) 

    def test__sample_rch_hop_counts_scheme_type_1(self):

        bounds = np.array([[0,3],[-3,3],[-3,0],[3,6]])
        sp = np.copy(bounds[:,0])
        columnOrder = None
        ssih = 3
        bInf = (bounds,sp,columnOrder,ssih,())
        rch = relevance_functions.sample_rch_hop_counts_scheme_type_1(np.copy(bounds),np.copy(bounds),ssih)
        rm = ("relevance zoom",relevance_functions.sample_rch_blind_accept())
        nsdi = numerical_space_data_generator.NSDataInstructions(bInf, rm,"ARGHONIA2.txt",'w',noiseRange = None,writeOutMode = rch)
        nsdi.make_rssi()

        while nsdi.fp:# and c < 1:
            nsdi.next_batch_()

if __name__ == '__main__':
    unittest.main()
