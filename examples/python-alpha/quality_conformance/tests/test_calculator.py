from quality_fixture import classify, multiply


def test_positive_value_is_classified() -> None:
    assert classify(2) == "positive"


def test_multiplication_uses_both_operands() -> None:
    assert multiply(3, 4) == 12
