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


def test_computed_edges():

    assertion = AssertionStr(entire="deg(a(CHEBI:water))")
    expected = [{'subject': 'deg(a(CHEBI:water))', 'relation': 'directlyDecreases', 'object': 'a(CHEBI:water)'}]
    edges = bo.parse(assertion=assertion).computed_edges()

    print("Edges", edges)

    assert edges == expected


