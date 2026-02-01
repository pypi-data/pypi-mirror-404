from math import factorial
from .classes import range_plus


class ArithmeticProgression:
    def __init__(self, first: float, difference: float):
        self.first = first
        self.difference = difference

    def __getitem__(self, n: int):
        if n <= 0:
            raise IndexError('n must be positive')
        if n == 1:
            return self.first
        return self.first + (self.difference * (n - 1))


class GeometricProgression:
    def __init__(self, first: float, denominator: float):
        if first == 0:
            raise ValueError("First cannot be zero")
        if denominator == 0:
            raise ValueError("Denominator cannot be zero")
        self.first = first
        self.denominator = denominator

    def __getitem__(self, n: int):
        if n <= 0:
            raise IndexError('n must be positive')
        if n == 1:
            return self.first
        return self.first * (self.denominator ** (n - 1))


def subfactorial(n: int) -> int:
    if n < 0:
        raise ValueError("n must be positive")
    elif n == 0:
        return 1
    elif n == 1:
        return 0
    result = 0
    for i in range_plus(n):
        result += (-1 ** n) / factorial(i)
    return factorial(n) * result
