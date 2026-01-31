# Numericals

[![PyPI version](https://badge.fury.io/py/numericals.svg)](https://badge.fury.io/py/numericals)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/numericals?period=total&units=NONE&left_color=GRAY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/numericals)
[![License: LGPL-3.0-or-later](https://img.shields.io/badge/License-LGPL--3.0--or--later-orange.svg)](https://spdx.org/licenses/LGPL-3.0-or-later.html)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


-----

Numerical methods in pure Python.

[Documentation](docs/docs.md) is available, but it might be easier to just read the code.

## Installation
```pip install numericals```

## Algorithms
- Integration
    - Trapezoidal Rule
    - Midpoint Rule
    - Simpson's Rule
    - Monte Carlo
    - Gaussian Quadrature

- ODE
    - Euler's Method
    - Heun's Method
    - Runge-Kutta 4

- Optimization
    - Golden Section Search

- Root-finding
    - Bisection Method
    - Secant Method
    - Newton's Method
    - Regula Falsi
    - Illinois Algorithm

## Tests
```
python -m pytest tests
```

## Copyright

Copyright (C) 2026 Andrew Yoo

Numericals is free software. You may redistribute or modify it under the terms of the GNU Lesser General Public License: feel free to choose either version 3.0 or a later one.

You should have received a copy of the GNU LGPL along with this program, located in the LICENSE file. If not, see http://www.gnu.org/licenses/lgpl.