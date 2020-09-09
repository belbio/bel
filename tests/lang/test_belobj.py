import bel.lang.belobj
from bel.lang.belobj import AssertionStr
import pytest

bo = bel.lang.belobj.BEL()


@pytest.mark.parametrize("assertion, expected", [
    ("p(HGNC:PBX2)", "p(EG:5089)")
])
def test_canonicalization(assertion, expected):
    """Test canonicalization"""

    assertion = AssertionStr(entire=assertion)
    assert expected == bo.parse(assertion=assertion).canonicalize().to_string()


def test_object_only():
    """Test object only bel assertion"""


    assertion = AssertionStr(object="p(HGNC:AKT1)")
    bo.parse(assertion=assertion)

    print("Validation messages", bo.validation_messages)

    assert False
