"""Epic 1: Name and version normalization tests."""

from bin_to_wheel import normalize_package_name, normalize_version


def test_hyphens_become_underscores():
    assert normalize_package_name("erpl-adt") == "erpl_adt"


def test_dots_become_underscores():
    assert normalize_package_name("my.package") == "my_package"


def test_already_normalized():
    assert normalize_package_name("erpl_adt") == "erpl_adt"


def test_uppercase_lowered():
    assert normalize_package_name("My-Package") == "my_package"


def test_mixed_separators():
    assert normalize_package_name("My.Cool-Package") == "my_cool_package"


# --- Version normalization (PEP 440) ---

def test_version_strips_leading_zeros():
    assert normalize_version("26.02.16") == "26.2.16"


def test_version_already_normalized():
    assert normalize_version("1.0.0") == "1.0.0"


def test_version_single_segment():
    assert normalize_version("07") == "7"


def test_version_preserves_non_numeric():
    assert normalize_version("1.0.0rc1") == "1.0.0rc1"


def test_version_mixed_zeros():
    assert normalize_version("2026.01.05") == "2026.1.5"
