from bel.lang.bel_utils import _default_to_version

EXAMPLE_AVAILABLE_VERSIONS = [
    "1.0.0",
    "0.0.3",
    "3.0.1",
    "2.0.1",
    "2.0.0",
    "6.1.1",
    "0.5.1",
]


def test_version_one_digit():

    version_given = "2"

    expected_version = "2.0.1"
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_one_digit_dot():

    version_given = "8."

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_two_digits():

    version_given = "0.0"

    expected_version = "0.0.3"
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_two_digits_dot():

    version_given = "2.0."

    expected_version = "2.0.1"
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_three_digits():

    version_given = "0.4.2"

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_three_digits_dot():

    version_given = "0.0.2."

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_more_than_three_digits():

    version_given = "0.0.9.1.5"

    expected_version = None  # BEL should consider given version as 0.0.9
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_string():

    version_given = "random_string"

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_empty_string():

    version_given = ""

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_string_with_digits_begin():

    version_given = "3string"

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_string_with_digits_mid():

    version_given = "s1t2r3i4ng"

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version


def test_version_string_with_digits_end():

    version_given = "string3"

    expected_version = None
    actual_version = _default_to_version(version_given, EXAMPLE_AVAILABLE_VERSIONS)

    assert expected_version == actual_version
