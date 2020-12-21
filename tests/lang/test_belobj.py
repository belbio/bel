# Third Party
import pytest

# Local
import bel.lang.belobj
from bel.lang.belobj import AssertionStr

bo = bel.lang.belobj.BEL()


@pytest.mark.parametrize("assertion, expected", [("p(HGNC:PBX2)", "p(EG:5089!PBX2)")])
def test_canonicalization(assertion, expected):
    """Test canonicalization"""

    assertion = AssertionStr(entire=assertion)
    assert expected == bo.parse(assertion=assertion).canonicalize().to_string()


def test_smart_quotes_cleaning():
    """Remove smart quotes"""

    assertion = AssertionStr(subject="bp(MESH:”Something here”)")
    expected = 'bp(MESH:"Something here")'

    assert bo.parse(assertion=assertion).to_string() == expected
