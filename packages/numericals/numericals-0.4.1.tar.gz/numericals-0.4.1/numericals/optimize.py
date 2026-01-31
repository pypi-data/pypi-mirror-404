# Copyright 2026 Andrew Yoo.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import math
from collections.abc import Callable


def golden(
    function: Callable[[float], float],
    alpha: float,
    beta: float,
    tolerance: float = 1e-10,
    max_iterations: int = 10_000,
) -> tuple:
    """Find local minimum using the Golden Section Search.

    Parameters
    ----------
    function : Callable
        The function.
    alpha : float
        The lower bound.
    beta : float
        The upper bound.
    tolerance : float
        The tolerance.
    max_iterations : int
        The maximum number of iterations.

    Returns
    -------
    tuple
        Minimizer, local minimum.
    """
    reciprocal_phi = (math.sqrt(5) - 1) * 0.5

    a = min(alpha, beta)
    b = max(alpha, beta)
    h = b - a

    for _ in range(max_iterations):
        if b - a <= tolerance:
            break

        c = b - (b - a) * reciprocal_phi
        d = a + (b - a) * reciprocal_phi

        if function(c) < function(d):
            b = d

        else:
            a = c

    minimizer = (a + b) * 0.5

    return (minimizer, function(minimizer))
