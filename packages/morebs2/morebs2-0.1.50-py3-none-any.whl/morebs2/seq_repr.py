from .matrix_methods import * 
from .measures import zero_div
from copy import deepcopy
from math import floor 

#------------------------------------------- methods for contiguous representation 
"""
given: a sequence S, either an np.array or a list 
output: sequence S' corresponding to `S`. Every 
    element of S' is a pair of the form 
    [0] value v of S at the j'th index 
    [1] number of contiguous indices, from the 
        j'th index in increasing order, with 
        values that equal v. 

EX: 
S = <0,0,1,2,1,2,3,3,4,4,4>
S' = <(0,2),(1,1),(2,1),(1,1),(2,1),(3,2),(4,3)> 
"""
def contiguous_repr__sequence(S):
    assert is_vector(S) or type(S) == list
    assert len(S) > 0

    q = [[S[0],1]]
    ref = q[-1]

    for i in range(1,len(S)):
        if S[i] == ref[0]:
            ref[1] += 1
        else:
            ref_ = [S[i],1]
            q.append(ref_) 
            ref = ref_
    return q

def contiguous_repr_size_measure(S,measure=np.var): 
    q = [s[1] for s in S] 
    return measure(q)

def contiguous_repr_size_ratio(S): 
    if len(S) == 0: return 0.0 

    qs = sum([s[1] for s in S])
    q = contiguous_repr_size_measure(S,np.mean) 
    return zero_div(q,qs,0)  


def repeat_cycle_for_length(c,l,ci=0):
    q = np.zeros((l,))

    # go forward 
    for i in range(ci,l,len(c)): 
        x = i 
        x2 = min([i+len(c),l])
        q[x:x2] = c[:x2-x]  

    # go backward
    cx = len(c) - 1 
    for i in range(ci-1,-1,-1):
        q[i] = c[cx] 
        cx = (cx - 1) % len(c) 
    
    return q 

def contiguous_cyclical_difference(V,sv,diff_type="bool"):
    assert diff_type in {"abs","bool"}
    assert len(V) >= len(sv)

    # find the first occurrence of sv in V 
    ir = index_range_of_subvec(V,sv,is_contiguous=True)
    
    if type(ir) == type(None): 
        return float('inf')
    
    vc = repeat_cycle_for_length(sv,len(V),ir[0])
    
    l = np.where(V != vc)[0]

    if diff_type == "bool": return len(l) 
    return np.sum(np.abs(V[l]))

#------------------------------------------ methods for processing (value,freq) vectors 

"""
V is a vector of (value,frequency) pairs 
assumed to be sorted in ascending or descending 
order. Function finds the sequence of all 
(value,frequency) pairs that tie for a place 
in the ranking of frequency. 
"""
def valuefreq_pair_vector__nth_place(V,i=0):

    j = None

    ip = 0
    ref = V[0]
    seq = []
    for i_ in range(1,len(V)):
        if ip == i:
            if ref[1] != V[i_][1]:
                break
            else: 
                seq.append(V[i_][0]) 
            continue
    
        if ref[1] != V[i_][1]:
            ip += 1 
            ref = V[i_] 
    return seq

def valuefreq_pair_vector_to_tie_partition(V):

    j = None
    ip = 0
    ref = V[0]
    seqs = []
    seq = []
    for i_ in range(1,len(V)):
        if ref[1] != V[i_][1]:
            ip += 1 
            ref = V[i_] 
            seqs.append(seq) 
            seq = [V[i_][0]]
        else: 
            seq.append(V[i_][0]) 
    return seqs 

#--------------------------------------------------------------------

"""
most common contiguous subsequence search 
"""
class MCSSearch:

    def __init__(self,L,cast_type=int,is_bfs:bool=True):  
        assert type(L) == list or is_vector(L) 
        assert type(is_bfs) == bool
        self.l = np.array(L)  
        self.cast_type = cast_type 
        self.is_bfs = is_bfs 

        self.preproc()
        # stringized subsequence of L --> index list of occurrence 
        self.subseq_occurrences = defaultdict(list) 
        self.key_queue = [] 
        self.key_cache = []
        return
    
    def preproc(self):
        self.d2index = defaultdict(list) 
        for (i,l_) in enumerate(self.l):
            self.d2index[l_].append(i) 
    
    def most_frequent_(self):
        q = sorted([(k,len(v)) for k,v in self.d2index.items()],key=lambda x:x[1],reverse=True) 

        q_ = q.pop(0)   
        s = set() 
        s |= {q_[0]} 
        while len(q) > 0:
            q2_ = q.pop(0) 
            if q2_[1] != q_[1]:
                break 
            s |= {q2_[0]} 
        return s 
    
    """
    post-search main method 
    """
    def mcs(self):
        x = [(k,len(v)) for k,v in self.subseq_occurrences.items()] 
        x = sorted(x,key=lambda x:x[1])
        q = x.pop(-1)
        s = [string_to_vector(q[0],castFunc=self.cast_type)]
        while len(x) > 0:
            q_ = x.pop(-1)
            if q_[1] == q[1]:
                s_ = string_to_vector(q_[0],castFunc=self.cast_type)
                s.append(s_)
            else: 
                break 
        return s 

    def mcs_nth(self,i=0): 
        x = [(k,len(v)) for k,v in self.subseq_occurrences.items()] 
        x = sorted(x,key=lambda x_:x_[1],reverse=True)
        return valuefreq_pair_vector__nth_place(x,i)
    
    def init_search(self):

        self.subseq_occurrences.clear() 
        self.key_queue.clear()
        self.key_cache.clear() 

        #ss = sorted(self.most_frequent())
        ss = sorted(set(np.unique(self.l)))

        for ss_ in ss: 
            v = self.d2index[ss_] 
            ssv = vector_to_string([ss_],castFunc=self.cast_type)
            self.subseq_occurrences[ssv] = v
            self.key_queue.append(ssv)  
        return
    
    def __next__(self):
        if len(self.key_queue) == 0: 
            return False 
        
        x = self.key_queue.pop(0)
        q = self.extend_subseq(x) 

        self.key_cache.append(x) 

        # sort q by frequency
        q_ = []
        for q2 in q:
            v = self.subseq_occurrences[q2] 
            q_.append((q2,v)) 
        q_ = sorted(q_,key=lambda x:x[1],reverse=True)  
        q_ = [q2[0] for q2 in q_] 

        if self.is_bfs:
            self.key_queue.extend(q_)
        else:
            while len(q_) > 0:
                self.key_queue.insert(0,q_.pop(-1)) 
        return True 

    def extend_subseq(self,subseq_str): 
        q = self.subseq_occurrences[subseq_str] 
        subseq_base = string_to_vector(subseq_str,castFunc=self.cast_type)
        new_subseq_ = set() 
        for q_ in q:
            # get the next index
            i = len(subseq_base) + q_ 

            if i >= len(self.l): continue

            subseq = deepcopy(subseq_base) 
            subseq = np.append(subseq,self.l[i])

            subseq_str_ = vector_to_string(subseq,castFunc=self.cast_type) 
            self.subseq_occurrences[subseq_str_].append(q_)  
            new_subseq_ |= {subseq_str_}
        return new_subseq_ 
    
    """
    pre-search main method 
    """
    def search(self):
        self.init_search() 

        stat = True 
        while stat: 
            stat = self.__next__()
        return 
    
    def kcomplexity(self,keys=None,diff_type="bool",diff_type2="contiguous"):
        assert diff_type in {"bool","abs"}
        assert diff_type2 in {"contiguous","best"}

        #dx = float('inf')
        #rep_set = set()  
        rep_vec = [] 
        if type(keys) == type(None): 
            keys = list(self.subseq_occurrences.keys()) 

        def diff_func(k): 
            v = string_to_vector(k,castFunc=self.cast_type) 
            if diff_type2 == "contiguous": 
                d = contiguous_cyclical_difference(self.l,v,diff_type=diff_type)
                return d 
            ql = len(self.subseq_occurrences[k])
            return len(self.l) - len(v) * ql   
            
        for k in keys:
            d = diff_func(k) 
            rep_vec.append((k,d))
        rep_vec = sorted(rep_vec,key=lambda x:x[1])
        return rep_vec 
    
    def kcomplexity_at_nth_set(self,i,diff_type="bool",diff_type2="contiguous"):
        assert diff_type in {"bool","abs"}
        assert diff_type2 in {"contiguous","best"}

        qs = self.mcs_nth(i) 
        return self.kcomplexity(keys=qs,diff_type=diff_type,diff_type2=diff_type2)

    def default_kcomplexity(self,diff_type="bool",diff_type2="contiguous",\
        basis="most frequent"):

        assert diff_type in {"bool","abs"}
        assert diff_type2 in {"contiguous","best"}
        assert basis in {"most frequent","median"} 

        if basis == "most frequent": 
            qx = self.kcomplexity_at_nth_set(0,diff_type,diff_type2) 
            qx = [qx_[1] for qx_ in qx] 
            return np.mean(qx)

        x = [(k,len(v)) for k,v in self.subseq_occurrences.items()] 
        x = sorted(x,key=lambda x:x[1])

        stat = len(x) % 2
        q = [] 
        # odd
        if stat:
            q_ = x[int(len(x) / 2)] 
            q.append(q_[0]) 
        # even
        else: 
            q_ = x[int(len(x) / 2) - 1] 
            q1_ = x[int(len(x) / 2)] 
            q = [q_[0],q1_[0]] 

        res = self.kcomplexity(keys=q,diff_type=diff_type)
        q = [res_[1] for res_ in res] 
        return np.mean(q) 

def MCS_kcomplexity(L,cast_type,diff_type="bool",\
    diff_type2="contiguous",basis="most frequent"):
    mcs = MCSSearch(L,cast_type=cast_type,is_bfs=True)
    mcs.search() 
    return mcs.default_kcomplexity(diff_type,diff_type2,\
        basis) 

