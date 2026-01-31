from .numerical_generator import * 
from types import MethodType,FunctionType

def sort_matrix_by_index(M,index,axis=0): 
    assert 0 <= index < M.shape[(axis+1) % 2] 
    v = M[:,index] if axis == 0 else M[index,:] 
    indices = np.argsort(v)
    return list(indices)

class OneDimClassifierFunction: 

    def __init__(self,modulo,index,dim,mod2label_dict): 
        assert is_number(modulo)
        assert type(dim) == int == type(index)
        self.modulo = modulo 
        self.index = index 
        self.dim = dim 
        self.mod2label_dict = mod2label_dict
        return 

    def __str__(self):
        s = "modulo {} index {} dim {}\n".format(self.modulo,self.index,self.dim) 
        s += str([(int(k),float(v)) for k,v in self.mod2label_dict.items()])
        s += "\n"
        return s 

    def classify(self,V): 
        assert len(V) == self.dim 
        q = V[self.index] 
        #x = q % self.modulo  

        labels = [] 
        labels2 = [] 
        for k,v in self.mod2label_dict.items(): 
            if q <= v: 
                labels.append((k,v-q)) 
            labels2.append((k,abs(v-q)))
        if len(labels) == 0: 
            labels = labels2  

        return min(labels,key=lambda x:x[1])[0]

"""
classifier is used to classify vectors D labeled by L. 
Classifier fixates itself on one column `index` of D. 

#------------------------- fitting process 
It determines a partition based on (min value,max value, mean value) 
of every label from L, w.r.t. column `index` of D. This partitioning 
uses one of three schemes: 
- 0: max predominant intersection  
- 1: mean predominent intersection 
- prg: uses a PRNG to decide partitioning values.  

Partitioning for scheme 0 and 1 starts with ordering elements 
    P := list w/ each element (label,min value,max value, mean value) 
by index 1.

In partitioning scheme 0, for every pair of elements (p_i,p_j), 
if there is non-null intersection I, in (min,max) between (p_i,p_j), 
determine the label i XOR j that is more frequent in I. Reassign I 
to that element p_x. 

In partitioning scheme 1, correct each element to 
    (label,min value,mean value,mean value). 

Afterwards, algorithm iterates through P and removes invalid partitions. 

In partitioning scheme `prng`, algorithm uses a PRNG to choose a partition 
of l parts, |set(L)| = l. 

#------------------------- classification process 

For a vector V, select value v = V[index]. Iterate through 
partition P for the max threshold values, that is, index 2. 
The threshold value t_l, of minimum distance to v, that v is less than 
corresponds to label l. 
In the case where v is greater than all threshold values, choose 
t_h that is of minimum absolute distance to v. 
"""
class OneDimClassifier: 

    def __init__(self,D,L,index,partition_scheme=0): 
        assert is_2dmatrix(D) 
        assert is_vector(L) 
        assert 0 <= index < D.shape[1] 
        self.D = D 
        self.L = L 
        self.index = index 
        self.partition_scheme = partition_scheme

        self.label2index_map = dict() 
        # (label, min value,max value) [along `index`] 
        self.prt = [] 
        self.sort() 
        self.partition() 
        self.clf = None

        self.full_filter = True   
        return

    def __str__(self): 
        return str(self.clf) 

    def add_past_indices(self,indices): 
        self.past_indices = indices 

    def make(self): 
        self.adjust_partition()
        self.make_classifier() 
        self.clear_data() 
        return

    def make_classifier(self): 
        # case: empty partition, uniform dataset, select first (label,range) 
        if len(self.prt) == 0: 
            self.partition() 
            self.prt = self.prt[:1] 

        modulo = self.prt[0,1]
        modulo_cat = {} 
        for p in self.prt: 
            modulo_cat[p[0]] = p[2] 
        
        self.clf = OneDimClassifierFunction(modulo,self.index,\
            self.dim,modulo_cat)
        return 

    def classify(self,V): 
        assert type(self.clf) == OneDimClassifierFunction
        return self.clf.classify(V) 

    def clear_data(self): 
        self.D_ = None 
        self.L = None 

    ######################## preprocessing methods 

    def sort(self): 
        indices = sort_matrix_by_index(self.D,self.index,0)
        self.D_ = self.D[indices] 
        self.D = None 
        self.L = self.L[indices] 
        self.dim = self.D_.shape[1] 
        return

    def partition(self): 
        if type(self.partition_scheme) in {MethodType,FunctionType}: 
            prt = prg_partition_for_sz__n_rounds(1000,len(set(self.L)),\
                prg__single_to_int(self.partition_scheme),0.5,5) 
            prt = np.array(prt) / 1000. 
            mini,maxi = self.D_[:,self.index][0],self.D_[:,self.index][-1]  

            keys = sorted(set(self.L)) 
            prev = mini
            self.prt = [] 
            for (i,k) in enumerate(keys): 
                r = [prev,prev + (maxi-mini) * prt[i]] 
                prev = r[1] 
                self.prt.append((k,r[0],r[1])) 
            self.prt = np.array(self.prt) 
            return 

        l_dict = self.partition_eval()
        l_ = np.array([[k] + list(v) for k,v in l_dict.items()]) 
        indices = sort_matrix_by_index(l_,1,0)
        self.prt = l_[indices] 
        return

    def partition_eval(self): 
        l_info = dict() 
        q = set(self.L) 

        for q_ in q: 
            l_info[q_] = list(self.index_info(q_))
            
        return l_info 

    """
    return: 
    - (min value,max value, mean value) of label along `index`
    """
    def index_info(self,l,store_indices:bool=True): 
        indices = self.indices_of_label(l)
        assert len(indices) > 0 
        if store_indices: 
            self.label2index_map[l] = indices 

        values = sorted([self.D_[i,self.index] for i in indices])
        min,max = values[0],values[-1] 
        ave = np.mean(values)
        return min,max,ave 

    ######################## partitioning methods 
    
    def adjust_partition(self): 
        self.adjust_partition__() 

        if len(self.prt) == 0: 
            self.full_filter = False 
        else: 
            return 

        self.partition() 
        self.adjust_partition__() 

    def adjust_partition__(self): 
        if self.partition_scheme == 0: 
            self.adjust_partition__scheme0() 
        elif self.partition_scheme == 1: 
            self.adjust_partition__scheme1() 

    def adjust_partition__scheme1(self): 
        p = [] 
        for x in self.prt[:-1]: 
            p.append((x[0],x[1],x[3],x[3])) 
        p.append(self.prt[-1]) 
        self.prt = np.array(p) 

        self.filter_partition(self.full_filter)
        while not self.final_partition_adjustment(): continue  
        self.filter_partition(self.full_filter) 
        

    def adjust_partition__scheme0(self): 
        self.adjust_partition_() 
        while not self.final_partition_adjustment(): continue 
        self.filter_partition(self.full_filter) 

    def adjust_partition_(self): 
        for i in range(len(self.prt)-1): 
            self.adjust_partition_at_index(i)
        self.filter_partition(self.full_filter)  
        return 

    def filter_partition(self,full_filter:bool):  
        prt = [] 

        if full_filter: 
            fx = lambda x,x2: x >= x2 
        else: 
            fx = lambda x,x2: x > x2 
        
        #fx = lambda x,x2: x >= x2 

        for (i,p) in enumerate(self.prt): 
                
            if fx(p[1],p[2]): continue  

            #if i < len(self.prt) -1: 
            #    p2 = self.prt[i+1] 
            #    if self.

            prt.append((p[0],p[1],p[2]))
        self.prt = np.array(prt) 

    def adjust_partition_at_index(self,index): 

        l_info1 = self.prt[index]
        biggest_diff = None 
        for j in range(index+1,len(self.prt)): 
            l_info2 = self.prt[j]
            s0,s1 = self.intersection_score(l_info1,l_info2)

            # case: no intersection 
            if s0 == 0: 
                continue 

            # case: label 1 is predominant to 2 
            if s0 > s1: 
                continue 

            l = l_info2[0]
            d = s1 - s0 
            if type(biggest_diff) == type(None): 
                biggest_diff = (l,d) 
            else: 
                if d > biggest_diff[1]: 
                    biggest_diff = (l,d) 
        
        # case: no change in partition 
        if type(biggest_diff) == type(None): 
            return 

        # case: change up the partition 
        i = self.index_of_label_in_partition(biggest_diff[0])
        l_info2 = self.prt[i] 

        l_info1[2] = l_info2[1] 
        return
        ######

    def final_partition_adjustment(self): 
        stat = True  
        for j in range(1,len(self.prt)): 
            l_info1 = self.prt[j-1] 
            l_info2 = self.prt[j] 
            s0,s1 = self.intersection_score(l_info1,l_info2)

            # strange case 
            if l_info1[1] <= l_info2[2] <= l_info1[2]: 
                self.prt = np.delete(self.prt, j, 0)
                stat = False 
                break 

            if s1 > s0: 
                l_info1[2] = l_info2[1] 
            else: 
                l_info2[1] = l_info1[2] 

            I = sort_matrix_by_index(self.prt,1)
            if I != sorted(I): 
                stat = False 

            self.prt = self.prt[I]
        return stat 

    #################################### accessory methods for partitioning 

    def index_of_label_in_partition(self,l): 
        q = self.prt[:,0] 
        x = np.where(q == l)[0]
        assert len(x) == 1 
        return x[0]

    """
    l_info1 := (label,min,max,mean)
    l_info2 := (label,min,max,mean)
    """
    def intersection_score(self,l_info1,l_info2): 
        assert l_info1[1] <= l_info2[1] 

        if l_info2[1] > l_info1[2]: 
            return 0,0  

        # range of interest is  
        #   R = [l_info2[1],l_info1[2]]
        R = [l_info2[1],l_info1[2]]

        # get the number of elements of label 1 in range R  
        count1 = self.number_of_elements_in_range(l_info1[0],R) 
        # do the same for label 2 
        count2 = self.number_of_elements_in_range(l_info2[0],R) 
        return count1,count2  

    def number_of_elements_in_range(self,label,R): 

        indices = self.label2index_map[label]
        c = 0 
        for i in indices: 
            q = self.D_[i,self.index] 
            if R[0] <= q <= R[1]:  
                c += 1 
        return c 
    
    def indices_of_label(self,l): 
        return np.where(self.L==l)[0] 

    ######################################## 

"""
unit for decision-tree classifier <RecursiveOneDimClassifier>. 
"""
class ODCNode: 

    def __init__(self,odc,nextnode_dict=dict(),previous_indices=set()):
        assert type(odc) == OneDimClassifierFunction
        assert type(previous_indices) == set 
        self.odc = odc 
        self.nextnode_dict= nextnode_dict 
        self.previous_indices = previous_indices

    def __str__(self): 
        s = str(self.odc) + "\n" 
        s += "next labels:\n\t{}\n".format(sorted(self.nextnode_dict)) 
        return s 

    def add_nextnode(self,node,label): 
        assert type(node) == ODCNode 
        self.nextnode_dict[label] = node 
        return

    def add_previous_indices(self,indices): 
        assert type(indices) == set 
        self.previous_indices = indices 

    def classify(self,v): 
        l = self.odc.classify(v)
        if l not in self.nextnode_dict: 
            return l,None 
        return l,self.nextnode_dict[l] 

"""
A dataset classifier, based on decision tree format. 
Uses the classifier <OneDimClassifier> as a unit node. 
"""
class RecursiveOneDimClassifier: 

    def __init__(self,D,L,prg=None,pscheme=0,verbose:bool=False): 
        assert is_2dmatrix(D) 
        assert is_vector(L) 
        self.D = D 
        self.L = L 
        self.fin_stat = False 

        if type(prg) not in {MethodType,FunctionType}: 
            self.prg = default_std_Python_prng()
        else: 
            self.prg = prg 
        assert pscheme in {0,1} or type(pscheme) in {MethodType,FunctionType}
        self.pscheme = pscheme 

        assert type(verbose) == bool 
        self.verbose = verbose 
        self.root = None 
        self.node_cache = [] 
        self.current = None 

        self.sample_cls_path = [] 

    def clear_data(self): 
        self.D = None 
        self.L = None 

    #--------------------------- main methods 

    """
    main method #3 
    """
    def score_accuracy(self,D,L): 
        assert len(D) == len(L) 

        c = 0 
        for (x,l) in zip(D,L): 
            l_ = self.classify(x) 
            if l_ == l: 
                c += 1 
        return c 

    """
    main method #2 
    """
    def classify(self,v): 
        q = self.root 
        l = None 
        self.sample_cls_path.clear() 
        while type(q) != type(None): 
            l,q = q.classify(v) 
            self.sample_cls_path.append(l) 
        return l 

    #------------------------------------- used to find classification solution 

    """
    main method #1 
    """
    def fit(self): 
        self.init_root() 
        while not self.fin_stat: 
            self.next_process() 
        self.clear_data() 

    def init_root(self): 
        self.one_process(self.D,self.L)  
        self.root = self.node_cache[0][0] 

    def next_process(self): 
        if self.fin_stat: 
            return 

        # case: load a new node of interest 
        if type(self.current) == type(None): 
            if len(self.node_cache) == 0: 
                self.fin_stat = True 
                return 
            self.current = self.node_cache.pop(0) 

        # iterate through and clear out any labels with 0 error s
        keys = sorted(self.current[2].keys())
        key0 = [] 
        for k in keys: 
            if self.current[2][k] == 0:
                del self.current[2][k] 
                key0.append(k) 
        rem_keys = sorted(set(keys) - set(key0)) 

        # case: perfect labeling 
        if len(rem_keys) == 0: 
            if self.verbose: 
                print("\t\t** one node")
                print(self.current[0]) 
            self.current = None 
            return 

        i = prg__single_to_int(self.prg)() % len(rem_keys) 
        subset_label = rem_keys[i] 
        del self.current[2][subset_label]

        D,L = [],[]
        for i in self.current[1][subset_label]: 
            D.append(self.current[3][i]) 
            L.append(self.current[4][i]) 
        D,L = np.array(D),np.array(L)
        odcn2,P2,E2 = self.one_child(self.current[0],subset_label,D,L)

    def one_process(self,D,L,previous_indices=set()): 
        odc,P,E = self.one_classification_process_(D,L,previous_indices)
        if type(odc) == type(None): 
            return None,None,None 

        self.node_cache.append((odc,P,E,D,L)) 
        return odc,P,E 

    def one_classification_process_(self,D,L,previous_indices=set()):  
        # instantiate one classifier 
        all_cols = set([i for i in range(D.shape[1])]) 
        candidates = sorted(all_cols - previous_indices) 
        if len(candidates) == 0: 
            if self.verbose: print("? no more indices")
            return None,None,None 

        i = prg__single_to_int(self.prg)() % len(candidates)  
        index = candidates[i] 
        odc = OneDimClassifier(D,L,index,self.pscheme)
        odc.make() 

        # partition by classification 
        P = defaultdict(set) 
        E = defaultdict(int)
        for i,x in enumerate(D): 
            l = odc.classify(x) 
            P[l] |= {i} 
            if l != L[i]: 
                E[l] += 1
        odcn = ODCNode(odc.clf,dict(),previous_indices | {index}) 
        return odcn,P,E 

    def one_child(self,odcn,subset_label,D,L): 
        previous_indices = odcn.previous_indices
        odcn2,P,E = self.one_process(D,L,previous_indices)
        if type(odcn2) ==type(None): return None,None,None 
        odcn.add_nextnode(odcn2,subset_label) 
        return odcn2,P,E 
