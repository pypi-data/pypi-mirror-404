"""
graph-to-tree decomposition
"""
from .graph_basics import * 
from .numerical_generator import prg_seqsort,prg_seqsort_ties,prg__constant,\
    prg__n_ary_alternator

class TNode: 

    def __init__(self,idn,next_cycling:bool=False,root_stat:bool=False,\
        rdistance:int = 0): 
        self.idn = idn 
        self.next_cycling = next_cycling
        self.children = []  
        self.cindex = 0 # used to traverse children node in search process 
        self.root_stat = root_stat 
        self.rdistance = rdistance 
        # children has been set? 
        self.children_set = False 
        self.xclist = [] 
        return

    """
    setattr is None|(varname,g); g a function called by g() 
    """
    @staticmethod
    def dfs(tn,display:bool=True,collect:bool=True,reset_index:bool=True,\
        set_attr=None,fetch_set=set()):

        def settr(tn_): 
            if type(set_attr) == type(None):
                return

            attrname = set_attr[0] 
            vx = set_attr[1]() 
            setattr(tn_,attrname,vx)
            return 

        if reset_index: tn.cindex = 0 
        cache = [tn] 
        d = defaultdict(set)
        mdepth = 0 
        fset = []  
        while len(cache) > 0: 
            t_ = cache.pop(0)
            settr(t_)

            if t_.idn in fetch_set:
                fset.append(t_)
            
            if display: 
                print(t_)
            cx = set([c.idn for c in t_.children])
            if collect: 
                d[t_.idn] = d[t_.idn] | cx 
            
            q = next(t_)
            if type(q) != type(None): 
                if reset_index: 
                    q.cindex = 0 
                cache.insert(0,t_)
                cache.insert(0,q) 
                mdepth = max([q.rdistance,mdepth])
            else: 
                if reset_index:
                    t_.cindex = 0 
        return d,mdepth,fset 

    # TODO: more thorough testing required. 
    @staticmethod
    def collate_keys(tn,is_bfs:bool=True,prg=None):
        tn.cindex = 0 
        q = [tn]
        K = [tn.idn]

        while len(q) > 0: 
            tn_ = q.pop(0) 
            if is_bfs: 
                q2 = [] 
                while True: 
                    tn2 = next(tn_)
                    if type(tn2) == type(None): break 
                    tn2.cindex = 0 
                    q2.append(tn2)
                if type(prg) != type(None): 
                    q2 = prg_seqsort(q2,prg)
                K.extend([q2_.idn for q2_ in q2])
                q.extend(q2) 
            else: 
                stat = True 
                if tn_.idn in K and type(prg) != type(None): 
                    stat = bool(prg() % 2)

                if stat: 
                    K.append(tn_.idn)

                tn2 = next(tn_)
                if type(tn2) == type(None): continue 
                tn2.cindex=0
                q.insert(0,tn_)
                q.insert(0,tn2)
        return K 

    @staticmethod 
    def size_count(tn): 
        q = [tn]
        c = 0 
        
        while len(q) > 0: 
            x = q.pop(0)
            x.cindex = 0 
            c += 1

            while True: 
                x2 = next(x) 
                if type(x2) == type(None): 
                    break 
                q.append(x2) 
        return c 


    def index_of_child(self,idn): 
        for (i,c) in enumerate(self.children): 
            if c.idn == idn: 
                return i 
        return -1 

    def add_children(self,cs): 
        for c in cs: 
            assert type(c) == TNode 
            self.children.append(c)
        self.children_set = True 

    def add_xclusion(self,xclude):
        assert type(xclude) == list 
        self.xclist.extend(xclude) 

    def __next__(self):
        if not self.next_cycling and self.cindex >= len(self.children): 
            return None 
        if len(self.children) == 0: return None 
        
        q = self.children[self.cindex % len(self.children)] 
        self.cindex += 1
        return q

    def __str__(self): 
        s = "idn:\t" + str(self.idn) + "\n"
        s += "rdistance:\t" + str(self.rdistance) + "  index:\t" \
            + str(self.cindex) + "\n"
        q = [str(c.idn) for c in self.children] 
        q = " ".join(q) 
        s += "children: " + q + "\n"
        s += "is root: " + str(self.root_stat) + "\n"
        return s 

class G2TDecomp: 

    def __init__(self,d,decomp_rootnodes=[],excl_mem_depth=float('inf'),\
            child_capacity=float('inf'),parent_capacity=float('inf'),prg=None): 
        """
        finds a directed acyclic graph (DAG) decomposition of a graph `d`. Every 
        directed acyclic graph is of a subclass of the category of DAG. For this 
        subclass of DAG, the siblings from a parent node cannot travel to each other.
        """

        assert type(d) == defaultdict
        assert d.default_factory == set 
        assert child_capacity > 0 and parent_capacity > 0

        graph_childkey_fillin(d)
        self.d = d 
        self.d_ = deepcopy(self.d)
        self.is_directed = is_directed_graph(d) 
        self.rn = decomp_rootnodes
        self.dr_map = defaultdict(int) 
        self.excl_mem_depth = excl_mem_depth
        self.cc = child_capacity
        self.pc = parent_capacity
        self.prg = prg  
        self.predecomp() 

        # vars used for dfs search 
        self.decompositions = [] 
        self.decomp_queue = [] 
            # stores skipped nodes for every dfs search 
            # by a root node 
        self.skipped_nodes = [] 
            # neighbor-parent degree map. used as reference to 
            # satisfy upper-threshold values set by `excl_mem_depth`,
            # `cc`, and `pc`. 
        self.cdeg_map = None 
        self.cdeg_map2 = None 

        self.fstat = False 

    def predecomp(self):
        if len(self.rn) > 0: 
            return 
        
        gd = GraphComponentDecomposition(self.d) 
        gd.decompose() 

        self.preset_depth_rank_map(gd)
        self.rn = [(k,v) for k,v in self.dr_map.items()] 
        if type(self.prg) == type(None): 
            self.rn = sorted(self.rn,key=lambda x:x[1]) 
        else: 
            vf = lambda x: x[1] 
            self.rn = prg_seqsort_ties(self.rn,self.prg,vf)
        self.rn = [k for (k,v) in self.rn]
        return

    def preset_depth_rank_map(self,gd): 
        if self.is_directed: 
            self.dr_map = gd.depth_rank_map() 
        else: 
            for k in self.d.keys(): 
                self.dr_map[k] = 0

    """
    main method 
    """
    def decompose(self): 
        while not self.fstat:
            next(self)

    def __next__(self): 
        if len(self.decomp_queue) == 0: 
            stat = self.next_tree() 
            if not stat: 
                self.fstat = True 
            return 

        self.next_node()
        
    def next_tree(self): 
        '''
        initializes a new tree, represented by class<TNode>. 
        '''
        if len(self.rn) == 0: 
            return False 

        x = self.rn.pop(0)
        tn = TNode(x,False,True,0)
        self.decompositions.append(tn) 
        self.decomp_queue.append(tn) 
        self.store_np_degrees() 
        return True 

    def set_children_for_node(self,tn):
        assert tn.children_set == False 

        # iterate through possible children 
        cx = children_of(self.d_,tn.idn)
        nx = doubly_connected(self.d_,tn.idn)
        cx = cx | nx 
        cx_ = [] 
        for q in cx: 
            if self.is_possible_child(q): 
                cx_.append(q)
        
        cx_ = set(cx_) - flatten_setseq(tn.xclist)

        # case: no children 
        if len(cx_) == 0: return False 

        # case: get the number of children based on `prg` or 
        #       default of `cc`. 
        cx_ = sorted(cx_) 
        cc = len(cx_) if float('inf') == self.cc else self.cc 
        if type(self.prg) != type(None): 
            cx_ = prg_seqsort(cx_,self.prg)
            cc = (self.prg() % cc) + 1 
        cx_ = cx_[:cc]
        self.init_children_for_node(tn,cx_)
        return True 

    def init_children_for_node(self,tn,cx_idn): 
        q = deepcopy(tn.xclist)

        # exclusion list for every child
        df = len(q) + 1 - self.excl_mem_depth
        if df > 0: 
            q = q[df:]
        q.append({tn.idn} | set(cx_idn))

        cxs = []
        E = [] 
        for cx in cx_idn: 
            q2 = deepcopy(q) 
            tn2 = TNode(cx,rdistance=tn.rdistance+1)
            tn2.add_xclusion(q2)
            cxs.append(tn2)
            E.append((tn.idn,cx))
            
        tn.add_children(cxs)
        delete_graph_edges(self.d_,E,is_directed=True)

    def is_possible_child(self,idn): 
        df = self.cdeg_map[idn] - self.cdeg_map2[idn]
        return df < self.pc 

    def next_node(self):
        tn = self.decomp_queue.pop(0) 
        if not tn.children_set: 
            self.set_children_for_node(tn)

        tn2 = next(tn) 
        if type(tn2) == type(None):
            tn.xclist.clear() 
            return False 

        self.decomp_queue.insert(0,tn)
        self.decomp_queue.insert(0,tn2)
        return

    #--------------------- conditional methods for next 

    def store_np_degrees(self): 
        q = np_degree_map(self.d_)
        self.cdeg_map = defaultdict(int) 
        for k,v in q.items(): 
            self.cdeg_map[k] += v[0] + v[1] 
        self.cdeg_map2 = deepcopy(self.cdeg_map)
        return