# Copyright 2026 Andrew Yoo.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import random
import math
from collections.abc import Callable


def trapezoidal(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    n: int = 10_000,
) -> float:
    """Numerically integrate a function using the Trapezoidal Rule.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower limit.
    beta : float
        The upper limit.
    n : int
        The number of partitions.

    Returns
    -------
    float
        An integral approximation.
    """
    delta = (beta - alpha) / n
    sum = 0.5 * (function(alpha) + function(beta))
    for i in range(1, n):
        sum += function(alpha + i * delta)
    return delta * sum


def midpoint(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    n: int = 10_000,
) -> float:
    """Numerically integrate a function using the Midpoint Method.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower limit.
    beta : float
        The upper limit.
    n : int
        The number of partitions.

    Returns
    -------
    float
        An integral approximation.
    """
    delta = (beta - alpha) / n
    sum = 0
    for i in range(n):
        sum += function(alpha + (i + 0.5) * delta)
    return delta * sum


def simpson(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    n: int = 10_000,
) -> float:
    """Numerically integrate a function using Simpson's Rule.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower limit.
    beta : float
        The upper limit.
    n : int
        The number of partitions.

    Returns
    -------
    float
        An integral approximation.
    """
    h = (beta - alpha) / n
    sum = function(alpha) + function(beta)

    for i in range(1, n, 2):
        sum += 4 * function(alpha + i * h)

    for i in range(2, n - 1, 2):
        sum += 2 * function(alpha + i * h)

    return sum * (h / 3)


def monte_carlo(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    n: int = 10_000,
) -> float:
    """Numerically integrate a function using Monte Carlo Integration.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower limit.
    beta : float
        The upper limit.
    n : int
        The number of random samples.

    Returns
    -------
    float
        An integral approximation.
    """
    width = beta - alpha
    total = 0
    for _ in range(n):
        r = random.random()
        x = alpha + r * width
        total += function(x)
    average = total / n
    return average * width


def gaussian(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    order: int,
) -> float:
    """Numerically integrate a function using Gaussian Quadrature.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower limit.
    beta : float
        The upper limit.
    order : int
        The order of the quadrature (i.e., the number of points used).

    Returns
    -------
    float
        An integral approximation.
    """
    if not order in (2, 3):
        raise ValueError

    transform = lambda x: ((beta - alpha) * x + alpha + beta) * 0.5
    w = (beta - alpha) * 0.5

    if order == 2:
        x1 = transform(-math.sqrt(1 / 3))
        x2 = transform(math.sqrt(1 / 3))
        w = (beta - alpha) * 0.5

        return w * (function(x1) + function(x2))

    else:  # Order must be 3
        x1 = transform(-math.sqrt(3 / 5))
        x2 = transform(0)
        x3 = transform(math.sqrt(3 / 5))
        w1 = 5 / 9
        w2 = 8 / 9

        return w * (w1 * function(x1) + w2 * function(x2) + w1 * function(x3))
