from mathlib import add, subtract, multiply, divide
import pytest


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 3) == 2


def test_multiply():
    assert multiply(4, 3) == 12


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError, match="Zero division is not allowed"):
        divide(10, 0)


def test_dividend_zero():
    divide(0, 10) == 0
