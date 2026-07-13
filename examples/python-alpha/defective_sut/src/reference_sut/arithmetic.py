def add(left: int, right: int) -> int:
    return left + right


def divide(dividend: float, divisor: float) -> float:
    # Intentional seed: the public requirement says division by zero must fail.
    if divisor == 0:
        return 0.0
    return dividend / divisor
