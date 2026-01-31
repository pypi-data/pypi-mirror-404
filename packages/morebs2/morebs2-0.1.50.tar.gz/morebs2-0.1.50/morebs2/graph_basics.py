from collections import defaultdict 
from copy import deepcopy 
from .globalls import invert_map__seqvalue 

def is_undirected_graph(d):
    assert type(d) in {defaultdict,dict}
    
    for k,v in d.items(): 
        for v_ in v: 
            if k not in d[v_]: return False 
    return True

def is_directed_graph(d): 
    return not is_undirected_graph(d)

def graph_childkey_fillin(d): 
    kx = list(d.keys()) 
    for k in kx: 
        V = d[k]
        for v in V: 
            if v not in d: 
                d[v] = set()

def edge_count(d): 
    return sum([len(v) for v in d.values()])

def index_of_element_in_setseq(s,n):
    for (i,s_) in enumerate(s): 
        if n in s_: return i 
    return None 

def directed_edge_partition(d,k,V): 
    partition = [set(),set()]
    for v_ in V: 
        if k not in d[v_]: 
            partition[1] |= {v_} 
        else: 
            partition[0] |= {v_} 
    return partition

"""
neighbor-child degree map. A node n's neighbor-child degree is 
    [|neighbors(n)|,|children(n)|]

:return: map of node idn to its neighbor-child degree
:rtype: defaultdict(list) 
"""
# TODO: test 
def nc_degree_map(G): 

    G_ = deepcopy(G) 
    d = defaultdict(list)
    for k in G_.keys(): 
        d[k] = [0,0]

    for k,v in G_.items():
        q = list(v)  
        for v_ in q: 
            # case: v_ is child 
            if k not in G_[v_]: 
                d[k][1] += 1 
            else: 
                d[k][0] += 1 
                d[v_][0] += 1 
            G_[v_] -= {k} 
        G_[k] = set() 
    return d

"""
neighbor-parent degree map. A node n's neighbor-parent degree is 
    [|neighbors(n)|,|parent(n)|]

:return: map of node idn to its neighbor-child degree
:rtype: defaultdict(list) 
"""
# TODO: test 
def np_degree_map(G): 

    G_ = deepcopy(G) 
    d = defaultdict(list)
    for k in G_.keys(): 
        d[k] = [0,0]

    for k,v in G_.items():
        q = list(v) 
        for v_ in q: 
            # case: neighbors 
            if k in G_[v_]: 
                d[k][0] += 1
                d[v_][0] += 1  
                G_[v_] -= {k}
            else: 
                d[v_][1] += 1 
        G_[k] = set() 
    return d 


def connected_to(G,n): 
    ks = list(G[n]) 
    for k,v in G.items():
        if k == n: continue 
        if n in v: ks.append(k) 
    return set(ks)

def parents_of(G,n): 
    p = [] 
    for k,v in G.items(): 
        if k == n: continue 
        if n in v and k not in G[n]: 
            p.append(k) 
    return set(p)

def children_of(G,n): 
    p = G[n]
    l = []
    for p_ in p: 
        if n not in G[p_]: 
            l.append(p_)
    return set(l) 

def doubly_connected(G,n): 
    ks = list(G[n]) 
    i = 0 
    while i < len(ks): 
        v = G[ks[i]] 
        if n not in v: 
            ks.pop(i)
        else: 
            i+=1 
    return set(ks)

def cpc_order(G,n): 
    return connected_to(G,n),parents_of(G,n),children_of(G,n) 

def delete_graph_edges(G,E,is_directed:bool=False): 
    
    while len(E) > 0: 
        e1 = E.pop() 
        G[e1[0]] = G[e1[0]] - {e1[1]} 

        if not is_directed: 
            e2 = (e1[1],e1[0]) 
            G[e2[0]] = G[e2[0]] - {e2[1]} 
            E = E - {e2}
    return

def flatten_setseq(s): 
    s_ = set() 
    for s2 in s: s_ |= s2 
    return s_

class GraphComponentDecomposition:

    def __init__(self,d): 
        """
        Calculates the components of a graph `d`. If `d` is a directed graph, 
        output (see class variable `components`) is a list of directed components. 
        Each directed component is a list of nodesets. The nodesets are ordered 
        in ascending order based on its depth rank. Additionally, the class variable 
        `cyclic_keys` maps each node to the nodeset that is its cyclic children. A cyclic 
        child is a parent of a node `n` but a child of another node `n2` connected to `n`. 
        The `cyclic_keys` map is used to determine if a directed component is of a 
        cyclic ordering, as opposed to static order. In a directed component `C` of 
        cyclic ordering, there exists at least a pair of nodes (`n1`,`n2`). The nodes 
        `n1` and `n2` belong to different nodesets of indices `i` and `i+j`. All nodes 
        in the nodesets of `C[i:i+j+1]` are of the same depth. If `d` is an undirected 
        graph, every element of `components` is a nodeset. If a directed component is 
        of static ordering, the depth rank of a node `n` in it is the index of the nodeset 
        that `n` is present in. 

        :param d: map representation of a graph 
        :type d: defaultdict(<set>)
        """

        assert type(d) == defaultdict
        assert d.default_factory == set 

        graph_childkey_fillin(d) 
        self.d = d 
        self.d_ = deepcopy(self.d)
        self.is_directed = is_directed_graph(self.d)

        self.components = []
        self.key_queue = [] 
        self.key_cache = set()

        self.cyclic_keys = defaultdict(set) 
        self.cyclic_keys_inverted = defaultdict(set) 

        self.finstat = False 

    def finstat_(self): 
        self.finstat = len(self.key_cache) == len(self.d) 
        return self.finstat

    '''
    main method 
    '''
    def decompose(self): 
        while not self.finstat:
            self.next_key()
        q = invert_map__seqvalue(self.cyclic_keys) 
        for k,v in q.items(): 
            self.cyclic_keys_inverted[k] = set(v) 
        return 

    def next_key(self): 
        if self.finstat_(): 
            return 

        if not self.is_directed: 
            self.undirected_next_key() 
            return 

        if len(self.key_queue) == 0: 
            x = set(self.d_.keys()) - self.key_cache
            x = sorted(list(x))
            self.init_decomp(x[0]) 
            return 

        k = self.key_queue.pop(0) 
        self.update_dircomp_by_kv_pair(k)

    def undirected_next_key(self): 

        if len(self.key_queue) == 0: 
            x = set(self.d_.keys()) - self.key_cache
            x = sorted(list(x))
            self.key_queue.append(x[0])

        q = self.key_queue.pop(0) 
        self.merge_by_edges(q)
        self.key_cache |= {q}  
        rem = self.d[q] - self.key_cache 
        self.key_queue.extend(list(rem)) 
        return 

    def depth_rank_map(self): 
        if not self.is_directed: return None 

        def update_map(Dx): 
            for k,v in Dx.items(): 
                D[k] += v 

        D = defaultdict(int) 
        
        for i in range(len(self.components)): 
            dx = self.depth_rank_map__component(i)
            update_map(dx)
        return D 

    def cyclic_component_indices(self): 
        if not self.is_directed: 
            return [] 

        j = [] 
        for i in range(len(self.components)): 
            if self.is_dcomponent_cyclic(i):
                j.append(i)
        return j 

    def depth_rank_map__component(self,ci): 
        D = defaultdict(int) 
        q = self.dcomponent_cyclic_indices(ci) 
        C = self.components[ci] 

        indexia = (-2,-2) if len(q) == 0 else q.pop(0)
        d = 0 
        for (i,c) in enumerate(C): 
            # case: nodeset in cycle, all of same depth 
            if i >= indexia[0] and i <= indexia[1]:
                for c_ in c: 
                    D[c_] = d
                continue 
            # case: move on to the next indexia 
            elif i == indexia[1] + 1: 
                indexia = (-2,-2) if len(q) == 0 else q.pop(0)
                d += 1
            for c_ in c: 
                D[c_] = d 
            d += 1 
        return D 

    def dcomponent_cyclic_indices(self,ci): 
        c = self.components[ci] 
        prev = 0 

        # each element is (head index,tail index)
        soln = []
        for (i,c_) in enumerate(c): 
            n_ = set()
            V = set() 
            for n in c_: 
                if n in self.cyclic_keys: 
                    n_ |= {n} 
                    V |= self.cyclic_keys[n] 
                    break 
            
            if len(n_) == 0: 
                continue 

            k = None 
            for j in range(prev,i): 
                if len(c[j].intersection(V)) > 0: 
                    k = j 
                    break 

            if type(k) == type(None):
                print("[!] weird") 
                continue 

            element = (j,i)
            soln.append(element) 
        return soln 
            
    def is_dcomponent_cyclic(self,ci): 
        if not self.is_directed: 
            return False 

        q = flatten_setseq(self.components[ci])
        for q_ in q: 
            ck = self.cyclic_keys[q_] 
            if ck.intersection(q): 
                return True  
        return False 
    
    #---------------- undirected case 

    def merge_by_edges(self,k): 
        i = index_of_element_in_setseq(self.components,k)
        kx = {k} | self.d[k]

        if type(i) == type(None): 
            self.components.append(kx)
            return 
        self.components[i] |= kx 

    #------------------------------ directed update methods 

    def init_decomp(self,k): 
        self.key_cache |= {k}

        partition = directed_edge_partition(self.d_,k,list(self.d_[k]))

        if len(partition[0]) + len(partition[1]) == 0: 
            self.components.append([{k}])
            return 

        nc = self.doubly_connected_subsets(partition[1])
        if len(nc) == 0: 
            self.components.append([{k} | partition[0]]) 
        else: 
            nc = [[{k} | partition[0],nc_] for nc_ in nc] 
            self.components.extend(nc) 

        self.queue_update(partition)
        self.graph_edge_update(k,partition)

    def update_dircomp_by_kv_pair(self,k): 
        V = [k] + list(self.d_[k]) 

        partition = directed_edge_partition(self.d_,V[0],V[1:]) 

        partition[0] |= {k}
    
        i = 0 
        new_comps = [] 
        cc = set()
        while i < len(self.components): 
            o1,new_comp,cyclic_children = self.update_dircomp(i,partition)
            if type(o1) == type(None): 
                i += 1 
                continue 
            self.components.pop(i)
            new_comps.extend(new_comp)
            cc |= cyclic_children
        self.components.extend(new_comps) 
        partition[0] -= {k}
        self.key_cache |= {k} 
        self.queue_update(partition)
        self.graph_edge_update(k,partition)
        self.update_cyclic_children(k,cc)

    def update_cyclic_children(self,k,cc):
        if len(cc) == 0: return  
        self.cyclic_keys[k] |=  cc 

    def update_dircomp(self,i,partition): 

        o1,o2,o3 = self.check_dircomp_with_partition(i,partition)
        
        # case: no connection 
        if type(o1) == type(None):
            return o1,[],o2 

        # case: connection, reform 
            # subcase: there are cyclic children 
        cp = deepcopy(self.components[i]) 
        cp[o1] = cp[o1] | partition[0] 

        if len(o3) == 0: 
            return o1,[cp],o2 

        new_components = self.new_components_from_children_(cp,o1,o3) 
        return o1,new_components,o2  

    def new_components_from_children_(self,cp,i,c_q): 
        
        nc = []
        # case: neighbor set in cp is last element 
        if i == len(cp) - 1: 
            for x in c_q: 
                cp2 = deepcopy(cp) 
                cp2.append(x) 
                nc.append(cp2)
            return nc         

        # case: not of the last 
        ns1 = flatten_setseq(cp[i+1:])
        nc = [deepcopy(cp)] 
        for x in c_q: 
            chk = x - ns1 
            # component has unrelated children from previous 
            # make new component without cp[i+1:]
            if len(chk) > 0:     
                cp2 = deepcopy(cp[:i+1]) 
                cp2.append(x) 
                nc.append(cp2) 
                continue 
        return nc 

    """
    return: 
    - index of intersected nodeset with partition neighbors in component
    - set of cyclic children 
    - remaining children (not cyclic) grouped into neighbors and lones 
    """
    def check_dircomp_with_partition(self,ci,partition): 

        C_d = self.components[ci]
        # check for intersection of neighbors with any in 
        # directed component 
        i = -1 
        for (j,c) in enumerate(C_d):
            cx = c.intersection(partition[0]) 
            if len(cx) > 0: 
                i = j 
                break 
        
        # case: no relation, nothing to do 
        if i == -1: return None,None,None 

        # check that there are no children before the i'th 
        # index 
        cyclic_children = set()
        for c in partition[1]: 
            j = index_of_element_in_setseq(C_d,c) 
            if type(j) == type(None): continue 

            if j < i: 
                cyclic_children |= {c}

        p2 = partition[1] - cyclic_children
        q = self.doubly_connected_subsets(p2)
        return i,cyclic_children,q

    def doubly_connected_subsets(self,ns): 
        s = [{ns_} for ns_ in ns]  
        for ns_ in ns: 
            q = index_of_element_in_setseq(s,ns_) 
            dconn = doubly_connected(self.d,ns_)

            to_remove = []
            for d in dconn: 
                q2 = index_of_element_in_setseq(s,d) 
                if type(q2) != type(None): 
                    s[q] = s[q] | s[q2] 
                    to_remove.append(q2) 
            
        return list(s)


    #---------------- indexing and travel memory

    def index_of(self,k): 
        if not self.is_directed: 
            return index_of_element_in_setseq(self.components,k)

        for (i,d_) in enumerate(self.components): 
            i2 = index_of_element_in_setseq(d_,k) 
            if type(i2) != type(None): 
                return (i,i2) 
        return None 

    def graph_edge_update(self,k,partition): 
        px0 = set([(k,p) for p in partition[0]])
        px1 = set([(k,p) for p in partition[1]])

        delete_graph_edges(self.d_,px0,is_directed=False)
        delete_graph_edges(self.d_,px1,is_directed=True)

    def queue_update(self,partition): 
        q = partition[0] | partition[1]

        for q_ in q: 
            if q_ not in self.key_cache: 
                self.key_queue.append(q_)