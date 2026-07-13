def add(left: int, right: int) -> int:
    return left + right


def divide(dividend: float, divisor: float) -> float:
    if divisor == 0:
        raise ValueError("division by zero is not allowed")
    return dividend / divisor
