import pytest
from numericals import integrate

import random
import math

f1 = lambda x: x**2
f2 = lambda x: math.sin(math.pi * x)
f3 = lambda x: -math.log(x)


def test_trapezoidal():
    assert integrate.trapezoidal(f1, 0, 1, 10_000) == pytest.approx(1 / 3, abs=1e-4)
    assert integrate.trapezoidal(f2, 0, 1, 10_000) == pytest.approx(
        2 / math.pi, abs=1e-4
    )
    with pytest.raises(ValueError):
        integrate.trapezoidal(f3, 0, 1, 10_000)


def test_midpoint():
    assert integrate.midpoint(f1, 0, 1, 10_000) == pytest.approx(1 / 3, abs=1e-4)
    assert integrate.midpoint(f2, 0, 1, 10_000) == pytest.approx(2 / math.pi, abs=1e-4)
    assert integrate.midpoint(f3, 0, 1, 10_000) == pytest.approx(1, abs=1e-4)


def test_simpson():
    assert integrate.simpson(f1, 0, 1, 10_000) == pytest.approx(1 / 3, abs=1e-4)
    assert integrate.simpson(f2, 0, 1, 10_000) == pytest.approx(2 / math.pi, abs=1e-4)
    with pytest.raises(ValueError):
        integrate.simpson(f3, 0, 1, 10_000)


def test_monte_carlo():
    random.seed(10)
    assert integrate.monte_carlo(f1, 0, 1, 10_000) == pytest.approx(1 / 3, abs=1e-2)
    assert integrate.monte_carlo(f2, 0, 1, 10_000) == pytest.approx(
        2 / math.pi, abs=1e-2
    )
    assert integrate.monte_carlo(f3, 0, 1, 10_000) == pytest.approx(1, abs=1e-2)


def test_gaussian():
    orders = [2, 3]
    for order in orders:
        assert integrate.gaussian(f1, 0, 1, order) == pytest.approx(1 / 3, abs=1e-4)
        assert integrate.gaussian(f2, 0, 1, order) == pytest.approx(
            2 / math.pi, abs=2e-1
        )
        assert integrate.gaussian(f3, 0, 1, order) == pytest.approx(1, abs=2e-1)
