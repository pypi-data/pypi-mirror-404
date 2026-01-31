import pytest
from numericals import root

import math

f1 = lambda x: math.sin(x)
f2 = lambda x: math.sqrt(x) - 1

df1 = lambda x: math.cos(x)
df2 = lambda x: 1 / (2 * math.sqrt(x))


def test_bisection():
    assert root.bisection(f1, 2, 4, 1e-10, 10_000) == pytest.approx(math.pi, abs=1e-8)
    assert root.bisection(f2, 0, 2, 1e-10, 10_000) == pytest.approx(1, abs=1e-8)


def test_secant():
    assert root.secant(f1, 2, 4, 1e-10, 10_000) == pytest.approx(math.pi, abs=1e-8)
    assert root.secant(f2, 0, 2, 1e-10, 10_000) == pytest.approx(1, abs=1e-8)


def test_newton():
    assert root.newton(f1, df1, 3, 1e-10, 10_000) == pytest.approx(math.pi, abs=1e-8)
    assert root.newton(f2, df2, 2, 1e-10, 10_000) == pytest.approx(1, abs=1e-8)


def test_regula_falsi():
    assert root.regula_falsi(f1, 2, 4, 1e-10, 10_000) == pytest.approx(
        math.pi, abs=1e-8
    )
    assert root.regula_falsi(f2, 0, 2, 1e-10, 10_000) == pytest.approx(1, abs=1e-8)


def test_illinois():
    assert root.illinois(f1, 2, 4, 1e-10, 10_000) == pytest.approx(math.pi, abs=1e-8)
    assert root.illinois(f2, 0, 2, 1e-10, 10_000) == pytest.approx(1, abs=1e-8)
