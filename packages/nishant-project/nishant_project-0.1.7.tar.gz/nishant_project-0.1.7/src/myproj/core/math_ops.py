def add(a: int, b: int) -> int:
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b


def subtract(a: int, b: int) -> int:
    return a - b


def division(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("b must not be zero")
    return a / b
