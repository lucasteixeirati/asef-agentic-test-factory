from reference_sut import add


def test_curated_add_oracle_after_correction() -> None:
    assert add(2, 3) == 5
    assert add(-2, 2) == 0
    assert add(0, 0) == 0
