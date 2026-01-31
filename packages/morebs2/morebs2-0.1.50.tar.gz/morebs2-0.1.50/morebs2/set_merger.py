from collections import Counter
from math import factorial
from .numerical_generator import *
from copy import deepcopy

def number_combinations(n,m):
    try:
        return factorial(n) / (factorial(m) * factorial(n - m))
    except:
        return 0

def select_indices_from_sequence(sequence,boolV):
    return np.array([sequence[i] for i,s in enumerate(sequence) if boolV[i]])

class SetMerger:
    '''
    Similar to the frequent item-set mining algorithm, Apriori algorithm. Conducts merging of sets based on their likeness.

    :param sv: vector of sets
    :type sv: list<set<T>>
    '''
    def __init__(self, sv):
        self.sv = sv

    @staticmethod
    def set_difference_score(s1,s2):
        '''
        non-commutative operation b/t two equally-sized sets
        '''
        assert type(s1) == type(s2) and type(s1) is set, "[0] invalid sets"
        assert len(s1) == len(s2), "[1] invalid sets"
        return len(s1 - s2)

    ###################### start: determine if nclosed implication
    @staticmethod
    def correct_number_of_elements(n,m):
        assert n >= m, "invalid args."
        number = 0
        for i in range(1,n):
            number += number_combinations(n - i,m-1)
        return number

    @staticmethod
    def is_nclosed_implication(s,n, checkArgs = True):
        if checkArgs:
            q = np.array([len(s_) for s_ in s])
            assert np.all(q == q[0]), "invalid sequence of sets"

        def log_set(s_):
            counter = counter + Counter(s_)

        # check correct number of elements
        if SetMerger.correct_number_of_elements(n,len(s[0])) > len(s):
            return False

        # check correct number of objects
        counter = Counter()

        for s_ in s:
            counter = counter + Counter(s_)
        counts = np.array(list(counter.values()))
        return np.all(counts == counts[0]) and len(counts) >= n

    ###################### end: determine if nclosed implication

    @staticmethod
    def number_of_sets_at_distance_to_others(s,others,wantedDistance):
        assert type(wantedDistance) is int and wantedDistance >= 0, "invalid wanted distance"
        q = 0
        for o in others:
            d = SetMerger.set_difference_score(s,o)
            if d != wantedDistance: continue
            q += 1
        return q

    ######################## start: methods for merging elements

    @staticmethod
    def merge_elements(s):
        q = set()
        for s_ in s:
            q = q | s_
        return q

    def merges_at_index(self,i,outputSource = False):
        """
        Calculates the merges involving the i'th element of `sv`.

        :return: if `outputSource`: list::(merge),list::(elements that make up the merge) o.w. list::(merge)
        :rtype: (list,list) or list
        """
        n = len(self.sv[i])
        pm = self.possible_merges_at_index(i)
        merges = []
        while len(pm) > 0:
            p = pm.pop(0)
            # determine which merges to add to
            for m in merges:
                if SetMerger.number_of_sets_at_distance_to_others(p,m,1) == len(m) and len(m) < n +1:
                    p_ = deepcopy(m)
                    p_.append(p)
                    merges.append(p_)
            merges.append([self.sv[i],p])

        # determine closed implications
        i = 0
        src = []
        while i < len(merges):
            if not SetMerger.is_nclosed_implication(merges[i],n+ 1):
                merges.pop(i)
            else:
                if outputSource:
                    src.append(merges[i])
                merges[i] = SetMerger.merge_elements(merges[i])
                i += 1

        if len(merges) == 0: return None
        return (merges,src) if outputSource else merges

    def possible_merges_at_index(self,i):
        merges = []
        for j in range(i + 1,len(self.sv)):
            if SetMerger.set_difference_score(self.sv[i],self.sv[j]) == 1:
                merges.append(self.sv[j])
        return merges

    def merge_one(self,saveToVar = False,outputSource = False,verbose = False):
        results = []
        results2 = []
        for i in range(len(self.sv) -1):
            ms = self.merges_at_index(i,outputSource)
            if type(ms) != type(None):
                if outputSource:
                    results.extend(ms[0])
                    results2.extend(ms[1])
                else:
                    results.extend(ms)

        if saveToVar and len(results) > 0:
            self.sv = results

        if verbose:
            print("# length of merges @ : ",len(results))

        return (results,results2) if outputSource else results

    def merge(self,verbose = 0):
        c = 1
        while len(self.merge_one(True,False,c)) > 0:#True:#  > 1:
            c +=1
            continue
