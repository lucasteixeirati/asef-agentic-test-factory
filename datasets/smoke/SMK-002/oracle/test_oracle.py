import pytest

from reference_sut import divide


def test_curated_division_oracle() -> None:
    assert divide(9, 3) == 3
    assert divide(-8, 2) == -4
    with pytest.raises(ValueError, match="division by zero"):
        divide(1, 0)
