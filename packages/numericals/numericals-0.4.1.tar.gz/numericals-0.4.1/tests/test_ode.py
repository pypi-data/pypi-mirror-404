import pytest
from numericals import ode

import math

f1 = lambda x, y: y
f1_solution = lambda x: math.e**x
f1_params = (lambda x: math.e**x, 0, 1, 1, 1e-2)

f2 = lambda x, y: (6 * x) - (3 * y) + 5
f2_solution = lambda x: 2 * math.e ** (-3 * x) + 2 * x + 1
f2_params = (lambda x: 2 * math.e ** (-3 * x) + 2 * x + 1, 0, 5, 3, 1e-2)


def partition(alpha, beta, h):
    """Generate x values to test the verify the solution at.
    
    Parameters
    ----------
    alpha : float
        The lower bound.
    beta : float
        The upper bound.
    h : float
        The step size.
    """
    x_values = []
    x = alpha
    x_values.append(x)

    n = int((beta - alpha) // h)

    for _ in range(n - 1):
        x += h
        x_values.append(x)

    h_final = (beta - alpha) - n * h
    x += h_final
    x_values.append(x)

    return x_values


f1_x_vals = partition(f1_params[1], f1_params[2], f1_params[4])
f2_x_vals = partition(f2_params[1], f2_params[2], f2_params[4])

f1_points = [f1_solution(i) for i in f1_x_vals]
f2_points = [f2_solution(i) for i in f2_x_vals]


def test_euler():
    f1_analytic, alpha, beta, y0, h = f1_params

    f1_euler = ode.euler(f1, alpha, beta, y0, h)

    assert f1_euler[1] == pytest.approx(f1_points, abs=1e-1)

    f1_analytic, alpha, beta, y0, h = f2_params

    f2_euler = ode.euler(f2, alpha, beta, y0, h)

    assert f2_euler[1] == pytest.approx(f2_points, abs=1e-1)


def test_heun():
    f1_analytic, alpha, beta, y0, h = f1_params

    f1_heun = ode.heun(f1, alpha, beta, y0, h)

    assert f1_heun[1] == pytest.approx(f1_points, abs=1e-3)

    f2_analytic, alpha, beta, y0, h = f2_params

    f2_heun = ode.heun(f2, alpha, beta, y0, h)

    assert f2_heun[1] == pytest.approx(f2_points, abs=1e-3)


def test_rk4():
    f1_analytic, alpha, beta, y0, h = f1_params

    f1_rk4 = ode.rk4(f1, alpha, beta, y0, h)

    assert f1_rk4[1] == pytest.approx(f1_points, abs=1e-3)

    f2_analytic, alpha, beta, y0, h = f2_params

    f2_rk4 = ode.rk4(f2, alpha, beta, y0, h)

    assert f2_rk4[1] == pytest.approx(f2_points, abs=1e-3)
