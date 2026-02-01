def absolute(x):
    if (x > 0):
        return x
    else:
        return -x
        
def sqrt(a, x0=None, tol=1e-30, max_iter=20):
    if a < 0:
        raise ValueError("a must be non-negative")

    if a == 0:
        return 0.0

    # Initial guess
    x = a if x0 is None else x0

    for _ in range(max_iter):
        x2 = x * x
        x_new = x * (x2 + 3*a) / (3*x2 + a)

        if abs(x_new - x) < tol * x_new:
            return x_new

        x = x_new

    return x


def cbrt(N, tolerance=1e-10, max_iterations=1000):
    x = N / 3.0 if N != 0 else 0.0
    for i in range(max_iterations):
        x_next = x - (x**3 - N) / (3 * x**2)
        if abs(x_next - x) < tolerance:
            return x_next
        x = x_next 
    return x

def gamma(x):
    # Lanczos approximation constants
    p = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    ]

    if x < 0.5:
        # Reflection formula
        return pi / (sin(pi * x) * gamma(1 - x))

    x -= 1
    t = p[0]
    for i in range(1, len(p)):
        t += p[i] / (x + i)

    g = 7
    return sqrt(2 * pi) * (x + g + 0.5)**(x + 0.5) * (e**(-(x + g + 0.5))) * t
    
def factorial(x):
    if (x // 1 == x):
        f = 1
        while x > 0:
            f *= x
            x -= 1
        return f
    else:
        return gamma(x+1)

def zeta(n):
    zetval = 0
    if n <= 1:
        raise ValueError("zeta(n) diverges for n <= 1")
    for _ in range(1, 100001):
        zetval += (1 / _**n)
    return zetval
    
def beta(n):
    if n == 0:
        return 0.5
    total = 0.0
    for i in range(100000):
        total += ((-1)**i) / ((2*i + 1)**n)
    return total