import bel.lang.partialparse
import pytest


def test_parse():

    bel_version = '2.0.0'
    belstr = 'sec(a(CHEBI:"3-hydroxybutyrate"))'
    ast = bel.lang.partialparse.get_ast_obj(belstr, bel_version)

    print(ast.to_string())

    assert ast.to_string() == 'sec(a(CHEBI:3-hydroxybutyrate))'


@pytest.mark.skip(reason="Not finished with this test")
def test_parse_bad_tloc():

    # Mis-matched parenthesis and missing colon after first GOCC
    belstr = 'tloc(HGNC:CTNNB1),GOCC"cytoplasm",GOCC:"nucleus")'

    bel_version = '2.0.0'
    ast = bel.lang.partialparse.get_ast_obj(belstr, bel_version)

    print(ast.to_string())

    assert False
