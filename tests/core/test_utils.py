import bel.core.utils


def test_html_wrap_span():
    """Test wrapping part of assertion string with visual error indicators"""

    string = "0123456789"

    pairs = [(2, 3), (6, 8)]

    expected = '01<span class="accentuate">2</span>345345<span class="accentuate">67</span>89'

    result = bel.core.utils.html_wrap_span(string, pairs)

    print("Wrapped string", result)

    assert result == expected
