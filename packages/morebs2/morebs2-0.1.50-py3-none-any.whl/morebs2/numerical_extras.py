'''
methods on integers such as multiple-finding
'''

def all_multiples(i):
    l = abs(int(i / 2))
    m = set()
    for j in range(1,l + 1):
        if j in m: break
        if not i % j:
            m |= set([j,int(i/j)])
    return m

def all_multiple_pairs(i):
    if i == 1: return [(1,1)]
    if i == -1: return [(-1,1),(1,-1)]
    
    l = abs(int(i / 2))
    m = []
    s = set()
    for j in range(1,l + 1):
        if not i % j:
            if j in s: break
            if int(i/j) in s: break
            m.append((j,int(i/j)))
            m.append((int(i/j),j))
            s |= set([j,int(i/j)])

            # case: negative
            if i < 0:
                s |= set([-j,-int(i/j)])
                m.append((-j,-int(i/j)))
                m.append((-int(i/j),-j))            
    return m

def gcd(i1,i2):
    i1 = to_natural_number(i1)
    i2 = to_natural_number(i2)
    q = max([int(min([i1,i2]) / 2),2])
    m = int(min([i1,i2]))
    c = 1
    for i in range(1,q):
        if not i1 % i and not i2 % i\
            and i > c:
            c = i
        
        if not m % i:
            if not i1 % (m / i) and not\
                i2 % (m / i) and (m / i) > c:
                c = int(m / i)
    return c

def to_natural_number(i):
    if type(i) == complex:
        return to_natural_number(int((i / 1j).real))
    if i < 0:
        return i * -1
    return i

def fractional_add(f1,f2):
    if f1[1] == f2[1]:
        s = (f1[0] + f2[0],f2[1])
        return reduce_fraction(s) 
    f1_ = (f1[0] * f2[1],f1[1] * f2[1])
    f2_ = (f2[0] * f1[1],f2[1] * f1[1])
    return fractional_add(f1_,f2_)

def fractional_mul(f1,f2):
    f3 = (f1[0] * f2[0],f1[1] * f2[1])
    return reduce_fraction(f3)

def reduce_fraction(f):
    d = gcd(f[0],f[1])
    return (int(f[0] / d), int(f[1] / d))

def is_rational(f):
    assert f >= -1. and f <= 1., "invalid float"
    return "TODO"

