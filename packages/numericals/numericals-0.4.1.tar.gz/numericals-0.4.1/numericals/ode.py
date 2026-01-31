# Copyright 2026 Andrew Yoo.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from collections.abc import Callable


def euler(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    y0: float,
    h: float,
) -> list:
    """Solve ODE initial value problem using Euler's Method.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower bound.
    beta : float
        The upper bound.
    y0 : float
        The initial value.
    h : float
        The step size.

    Returns
    -------
    x_values : list
        A list of x values at which the solution was approximated.
    y_values : list
        A list of solution approximations.
    """
    x_values, y_values = [], []

    n = int((beta - alpha) // h)
    x = alpha
    y = y0

    x_values.append(x)
    y_values.append(y)

    for _ in range(n - 1):
        y = y + h * function(x, y)
        x = x + h

        x_values.append(x)
        y_values.append(y)

    h_final = (beta - alpha) - n * h

    y = y + h_final * function(x, y)
    x = x + h_final

    x_values.append(x)
    y_values.append(y)

    return x_values, y_values


def heun(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    y0: float,
    h: int,
) -> list:
    """Solve ODE initial value problem using Heun's Method.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower bound.
    beta : float
        The upper bound.
    y0 : float
        The initial value.
    h : float
        The step size.

    Returns
    -------
    x_values : list
        A list of x values at which the solution was approximated.
    y_values : list
        A list of solution approximations.
    """
    x_values, y_values = [], []

    n = int((beta - alpha) // h)
    x = alpha
    y = y0

    x_values.append(x)
    y_values.append(y)

    for _ in range(n - 1):
        y_predictor = y + h * function(x, y)

        y += (h / 2) * (function(x, y) + function(x + h, y_predictor))
        x += h

        x_values.append(x)
        y_values.append(y)

    h_final = (beta - alpha) - n * h

    y_predictor = y + h_final * function(x, y)

    y += (h_final / 2) * (function(x, y) + function(x + h_final, y_predictor))
    x += h_final

    x_values.append(x)
    y_values.append(y)

    return x_values, y_values


def rk4(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    y0: float,
    h: float,
) -> list:
    """Solve ODE initial value problem using Runge-Kutta 4.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower bound.
    beta : float
        The upper bound.
    y0 : float
        The initial value.
    h : float
        The step size.

    Returns
    -------
    x_values : list
        A list of x values at which the solution was approximated.
    y_values : list
        A list of solution approximations.
    """
    x_values, y_values = [], []

    n = int((beta - alpha) // h)
    x = alpha
    y = y0

    x_values.append(x)
    y_values.append(y)

    for _ in range(n - 1):
        k1 = function(x, y)
        k2 = function(x + h / 2, y + h * (k1 / 2))
        k3 = function(x + h / 2, y + h * (k2 / 2))
        k4 = function(x + h, y + h * k3)

        y += (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
        x += h

        x_values.append(x)
        y_values.append(y)

    h_final = (beta - alpha) - n * h
    k1 = function(x, y)
    k2 = function(x + h_final / 2, y + h_final * (k1 / 2))
    k3 = function(x + h_final / 2, y + h_final * (k2 / 2))
    k4 = function(x + h_final, y + h_final * k3)

    y += (h_final / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
    x += h_final

    x_values.append(x)
    y_values.append(y)

    return x_values, y_values
