import pytest
from numericals import optimize

f1 = lambda x: (x - 1) ** 2
f2 = lambda x: 0.5 * x**3 + x**2
f3 = lambda x: abs(x)


def test_golden():
    assert optimize.golden(f1, 0, 2, 1e-10, 10_000) == pytest.approx((1, 0), abs=1e-8)
    assert optimize.golden(f2, -1, 1, 1e-10, 10_000) == pytest.approx((0, 0), abs=1e-8)
    assert optimize.golden(f3, -1, 1, 1e-10, 10_000) == pytest.approx((0, 0), abs=1e-8)
