# Third Party
import pytest

# Local
import bel.core.utils


def test_html_wrap_span():
    """Test wrapping part of assertion string with visual error indicators"""

    string = "0123456789"

    pairs = [(2, 3), (6, 8)]

    expected = '01<span class="accentuate">2</span>345345<span class="accentuate">67</span>89'

    result = bel.core.utils.html_wrap_span(string, pairs)

    print("Wrapped string", result)

    assert result == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("HGNC:391!AKT1", ("HGNC", "391", "AKT1")),
    ],
)
def test_split_key_label(test_input, expected):

    result = bel.core.utils.split_key_label(test_input)

    print("Result", result)

    assert result == expected


@pytest.mark.parametrize(
    "test_string,expected",
    [
        (" ", ""),
        ('"s"', "s"),
        (' "s " ', "s"),
        ("s!", '"s!"'),
        ("s)", '"s)"'),
        ('"s!"', '"s!"'),
    ],
)
def test_quote_strings(test_string, expected):

    s = bel.core.utils.quote_string(test_string)

    print("Result", s, "Expected", expected)

    assert s == expected
