from .set_merger_test_cases import *
import unittest

#########################################################

'''
python -m morebs2.tests.set_merger_test  
'''
class TestSetMerger(unittest.TestCase):

    def test__SetMerger__is_nclosed_implication(self):#

        s1 = sample_set_sequence_1()
        closed = set_merger.SetMerger.is_nclosed_implication(s1,3)
        assert not closed, "case 1 not closed"

        s2 = sample_set_sequence_2()
        closed = set_merger.SetMerger.is_nclosed_implication(s2,3)
        assert closed, "case 2 closed"

        s11 = sample_set_sequence_11()
        closed = set_merger.SetMerger.is_nclosed_implication(s11,3)
        assert closed, "case 3.1 closed"
        closed = set_merger.SetMerger.is_nclosed_implication(s11,4)
        assert closed, "case 3.2 closed"
        closed = set_merger.SetMerger.is_nclosed_implication(s11,5)
        assert closed, "case 3.3 closed"
        closed = set_merger.SetMerger.is_nclosed_implication(s11,6)
        assert closed, "case 3.4 closed"
        closed = set_merger.SetMerger.is_nclosed_implication(s11,7)
        assert not closed, "case 3.5 not closed"
        closed = set_merger.SetMerger.is_nclosed_implication(s11,8)
        assert not closed, "case 3.6 not closed"

        s12 = sample_set_sequence_12()
        closed = set_merger.SetMerger.is_nclosed_implication(s12,3)
        assert not closed, "case 4 not closed"

        s13 = sample_set_sequence_13()
        closed = set_merger.SetMerger.is_nclosed_implication(s13,2)
        assert closed, "case 6 closed"

    def test__SetMerger__possible_merges_at_index(self):
        s12 = sample_set_sequence_12()
        sm = set_merger.SetMerger(s12)

        q = sm.possible_merges_at_index(0)
        assert q == [{0, 2}, {0, 3}, {0, 4}, {0, 5}, {1, 2}, {1, 3}, {1, 4}, {1, 5}]

        q = sm.possible_merges_at_index(1)
        assert q == [{0, 3},{0,4},{0,5},{1,2},{2,3},{2,4},{2,5}]

    def test__SetMerger__merges_at_index(self):
        s12 = sample_set_sequence_12()
        sm = set_merger.SetMerger(s12)
        merges = sm.merges_at_index(True)
        assert merges == [{0, 2, 3}, {0, 2, 4}, {0, 2, 5}]

    def test__SetMerger__merge_one(self):
        s12 = sample_set_sequence_12()
        sm = set_merger.SetMerger(s12)
        sm.merge_one(True)
        assert sm.sv == [{0, 1, 2}, {0, 1, 3}, {0, 1, 4}, {0, 1, 5},\
            {0, 2, 3}, {0, 2, 4}, {0, 2, 5}, {0, 3, 4}, {0, 3, 5},\
            {0, 4, 5}, {1, 2, 3}, {1, 2, 4}, {1, 2, 5}, {1, 3, 4},\
            {1, 3, 5}, {1, 4, 5}, {2, 3, 4}, {2, 3, 5}, {2, 4, 5},\
            {3, 4, 5}, {5, 6, 7}, {5, 6, 8}, {5, 7, 8}, {6, 7, 8}]

        sm.merge_one(True)
        assert sm.sv == [{0, 1, 2, 3}, {0, 1, 2, 4}, {0, 1, 2, 5},\
                    {0, 1, 3, 4}, {0, 1, 3, 5}, {0, 1, 4, 5}, {0, 2, 3, 4},\
                    {0, 2, 3, 5}, {0, 2, 4, 5}, {0, 3, 4, 5}, {1, 2, 3, 4},\
                    {1, 2, 3, 5}, {1, 2, 4, 5}, {1, 3, 4, 5}, {2, 3, 4, 5}, {5, 6, 7, 8}]


    def test__SetMerger__merge(self):
        sm = set_merger.SetMerger(sample_set_sequence_12())
        sm.merge()
        assert sm.sv == [{0, 1, 2, 3, 4, 5}]
    

if __name__ == '__main__':
    unittest.main()
