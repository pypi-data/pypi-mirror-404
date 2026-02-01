def exp(n):
    return e**n

def ln(x):
    if x <= 0:
        raise ValueError("ln(x) is undefined for x <= 0")
    k = 0
    while x >= 2.0:
        x *= 0.5
        k += 1
    while x < 1.0:
        x *= 2.0
        k -= 1
    y = (x - 1) / (x + 1)
    y2 = y * y
    s = 0.0
    term = y
    n = 1
    while absolute(term) > 1e-17:
        s += term / n
        term *= y2
        n += 2
    return 2*s + k * (0.693147180559945309417232121458176568) # ln 2
    
def log10(x):
    return ln(x) / ln(10)
    
def log2(x):
    return log10(x) / log10(2)
    
def log(arg, base):
    return log2(arg) / log2(base)