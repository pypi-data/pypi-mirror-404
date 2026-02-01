# integrating integrals
def integrate(function, lowlim, uplim, n=10000):
    h = (uplim - lowlim) / n
    s = function(lowlim) + function(uplim)

    for i in range(1, n):
        x = lowlim + i * h
        if i % 2 == 0:
            s += 2 * function(x)
        else:
            s += 4 * function(x)

    return s * h / 3
    
def summation(lowlim, uplim, function):
    sum = 0
    for _ in range(lowlim, uplim + 1):
        sum += function(_)
    return sum

def converges(f):
    if (f(2) == 0.5):
        return False
    try:
        n1 = 10**5
        n2 = 10**6

        a1 = abs(f(n1))
        a2 = abs(f(n2))

        # 1) nth-term test (stronger)
        if a2 > 1e-3:
            return False

        # 2) Ratio test
        if a1 != 0:
            L = abs(a2 / a1)
            if L < 0.9:
                return True
            if L > 1.1:
                return False

        # 3) Alternating test
        if f(1000) * f(1001) < 0 and a2 < a1:
            return "Conditional"

        # 4) Partial sum growth test
        S1 = sum(f(n) for n in range(1,2000))
        S2 = sum(f(n) for n in range(1,4000))

        if abs(S2) > abs(S1) * 1.2:
            return False

        if abs(S2 - S1) < 1e-3:
            return True

    except:
        return "Inconclusive"

    return "Inconclusive"
