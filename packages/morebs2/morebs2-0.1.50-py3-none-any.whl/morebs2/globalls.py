import os
import glob
import csv
from collections import defaultdict
from operator import add,sub,mul,truediv,floordiv
import numpy as np 

WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE = (0,0,255)
REDGREENOREGON = (123,321,231)

DEFAULT_TRAVELLING_HOP = 0.05
DEFAULT_SCREEN_DIM = (1300,750)
DEFAULT_POINT_CACHE_SIZE = 10


NUMERICAL_TYPES = {int,float,\
    np.int8,np.int16,np.int32,np.int64,\
    np.float16,np.float32,np.float64,\
    complex,np.complex64,np.complex128}

# TODO:
def clear_and_make_directory(dirPath):
    """
    clear_and_make_directory

    :param dirPath: directory path
    :type dirPath: str or None
    :return: None
    :rtype: None
    """

    ##dirr = os.path.dirname(fullPath)
    if not os.path.isdir(dirPath):
        # make directory
        os.mkdir(dirPath)
    else:
        # TODO: clear directory contents
        files = glob.glob(dirPath + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                print("probably is folderonos")

def make_csv_file(filePath, columnLabels):
    with open(filePath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(columnLabels)

def is_valid_color(c):
    assert type(c) is tuple, "invalid color type"
    for c_ in c: assert type(c_) in [float,int], "invalid type for colores de la vegasvalueorios"

##################### methods for dictionaries 

def std_invert_map(m):
    assert type(m) in {dict,defaultdict}

    q = {}
    for k,v in m.items():
        if v in q:
            q[v].append(k)
        else:
            q[v] = [k]
    return q

def invert_map__seqvalue(m): 
    assert type(m) in {dict,defaultdict}

    q = defaultdict(list) 
    for k,v in m.items(): 
        for v_ in v: 
            q[v_].append(k) 
    return q 

def numberdict_op(d1,d2,f=sub):
    K = set(d1.keys()) | set(d2.keys()) 
    
    d3 = defaultdict(int) 
    for k in K:
        x1 = d1[k] if k in d1 else 0 
        x2 = d2[k] if k in d2 else 0 
        d3[k] = f(x1,x2) 
    return d3 

def equal_intdicts(d1,d2): 
    K = set(d1.keys()) | set(d2.keys()) 

    for k in K: 
        if d1[k] != d2[k]: return False 
    return True 
