from reference_sut import normalize_whitespace


def test_curated_normalization_oracle() -> None:
    assert normalize_whitespace("  Quality   Engineering ") == "Quality Engineering"
    assert normalize_whitespace("\tQuality\nEngineering\t") == "Quality Engineering"
    assert normalize_whitespace("") == ""
    assert normalize_whitespace("   ") == ""
