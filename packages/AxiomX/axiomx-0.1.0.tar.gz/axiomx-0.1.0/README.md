# 🔢 AxiomX

**AxiomX** is a lightweight pure-Python mathematical library focused on implementing core numerical methods and elementary functions **from first principles** — without relying heavily on Python’s built-in `math` module.

It is designed for:

- Learning numerical analysis  
- Exploring series expansions & iterative solvers  
- Building symbolic/numeric math engines  
- Educational and experimental use  

---

# 🌐 Website Notice

**We have permanently shifted to:**  
👉 https://axiomxpy.wordpress.com  

All official announcements, documentation updates, and project news will now be published on this site.

Please update any old bookmarks or links to ensure you are accessing the latest resources.

---

## 📦 Package Structure

```
AxiomX/
│
├── constants.py      # Mathematical constants
├── functions.py      # Utility & root functions
├── exp.py            # Exponential & logarithmic
├── trig.py           # Trigonometric & inverse trig
├── hyperbolic.py     # Hyperbolic functions
├── calculus.py       # Numerical integration
└── __init__.py       # Loader & module imports
```

---

## 🚀 Installation

```bash
pip install axiomx
```

Or locally:

```bash
git clone https://github.com/yourname/axiomx
cd axiomx
pip install .
```

---

## ▶ Importing

```python
import AxiomX
from AxiomX import trig, exp, calculus, constants
```

---

# 📐 constants.py

Provides fundamental mathematical constants:

```
pi, e, lemniscate, gauss, euler_mascheroni,
sqrt_2, sqrt_3, sqrt_5, golden_ratio
```

---

# 🧮 functions.py

```
absolute(x)
sqrt(a, x0=None, tol=1e-30, max_iter=20)
```

---

# 📈 exp.py

```
exp(x)
ln(x)
```

---

# 📐 trig.py

```
radians(deg)
degrees(rad)
sin(x, terms=20)
cos(x)
tan(x)
cot(x)
sec(x)
cosec(x)
arcsin(x, iterations=10)
arccos(x)
arctan(x)
arccot(x)
arcsec(x)
arccosec(x)
```

---

# 🔁 hyperbolic.py

```
sinh(x)
cosh(x)
tanh(x)
coth(x)
```

---

# ∫ calculus.py

```
integrate(function, lowlim, uplim, n=10000)
```

---

## 🧪 Example

```python
from AxiomX.constants import pi
from AxiomX.trig import sin
from AxiomX.calculus import integrate

print(sin(pi/2))
print(integrate(lambda x: x**2, 0, 1))
```

---

## 📜 License

MIT License
