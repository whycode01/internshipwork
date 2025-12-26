from __future__ import annotations
from typing import List
from math import sqrt, gcd as math_gcd, factorial as math_factorial
from fastmcp import FastMCP

mcp = FastMCP(name="CalcMCP")

@mcp.tool
def add(a: float, b: float) -> float:
    return a + b

@mcp.tool
def subtract(a: float, b: float) -> float:
    return a - b

@mcp.tool
def multiply(a: float, b: float) -> float:
    return a * b

@mcp.tool
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

@mcp.tool
def power(base: float, exponent: float) -> float:
    return float(base) ** float(exponent)

@mcp.tool
def sqroot(x: float) -> float:
    if x < 0:
        raise ValueError("sqrt domain error: x < 0")
    return sqrt(x)

@mcp.tool
def gcd(a: int, b: int) -> int:
    return abs(math_gcd(int(a), int(b)))

@mcp.tool
def lcm(a: int, b: int) -> int:
    g = abs(math_gcd(int(a), int(b)))
    if g == 0:
        return 0
    return abs(int(a) // g * int(b))

@mcp.tool
def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("factorial domain error: n < 0")
    return math_factorial(int(n))

@mcp.tool
def mean(values: List[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)

@mcp.tool
def median(values: List[float]) -> float:
    if not values:
        raise ValueError("median requires at least one value")
    vals = sorted(values)
    k = len(vals)
    mid = k // 2
    if k % 2 == 1:
        return float(vals[mid])
    return (vals[mid-1] + vals[mid]) / 2.0

if __name__ == "__main__":
    mcp.run()
