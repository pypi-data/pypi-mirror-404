def radians(deg):
    return (pi/180)*deg
    
def degrees(rad):
    return (180/pi)*rad
    
def sin(x, terms=20):
    quarter = ((x // tau) + 1) % 4
    if x == pi:
        return 0
    x = x % tau
    # Input validation
    if not isinstance(x, (int, float)):
        raise TypeError("x must be a number (int or float).")
    if not isinstance(terms, int) or terms <= 0:
        raise ValueError("terms must be a positive integer.")
    sine_value = 0.0
    for n in range(terms):
        term = ((-1)**n) * (x**(2*n + 1)) / factorial(2*n + 1)
        sine_value += term
    return sine_value
    if quarter == 1:
        return sine_value
    elif quarter == 2:
        return sqrt(1 - (sine_value**2))
    elif quarter == 3:
        return -sine_value
    elif quarter == 0:
        return -sqrt(1 - (sine_value**2))
        
def cos(x):
    return sin((pi/2)-x)
    
def tan(x):
    return sin(x) / cos(x)

def cot(x):
    return 1 / tan(x)

def sec(x):
    return 1 / cos(x)
    
def cosec(x):
    return 1 / sin(x)

def arcsin(x, iterations=10):
    if abs(x) > 1:
        raise ValueError("x must be in [-1, 1]")
    y = x
    for _ in range(iterations):
        y -= (sin(y) - x) / cos(y)
    return y
    
def arccos(x):
    return (pi / 2) - arcsin(x)
    
def arctan(x):
    return arcsin(x / sqrt(1+ x**2))
    
def arccot(x):
    return (pi/2) - arctan(x)

def arcsec(x):
    return arccos(1/x)
    
def arccosec(x):
    return arcsin(1/x)