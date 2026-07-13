import pytest

from reference_sut import divide


def test_curated_oracle_exposes_seeded_defect() -> None:
    with pytest.raises(ValueError, match="division by zero"):
        divide(1, 0)
