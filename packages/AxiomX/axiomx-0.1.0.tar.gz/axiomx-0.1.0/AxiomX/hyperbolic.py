def sinh(x):
    return (e**x - e**(-x))/2
    
def cosh(x):
    return (e**x + e**(-x))/2
    
def tanh(x):
    return sinh(x) / cosh(x)
    
def coth(x):
    return cosh(x) / sinh(x)
    
def sech(x):
    return 1 / cosh(x)
    
def cosech(x):
    return 1 / sinh(x)
    
def arcsinh(x):
    return ln(x + sqrt(x**2 + 1))
    
def arccosh(x):
    return abs(arcsinh(sqrt(x**2 - 1)))
    
def arccoth(x):
    return 0.5 * ((x+1)/(x-1))
    
def arctanh(x):
    return arccoth(1/x)
    
def arcsech(x):
    return arccosh(1/x)
    
def arccosech(x):
    return arcsinh(1/x)