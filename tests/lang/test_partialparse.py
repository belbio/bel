import bel.lang.partialparse


def test_parse():

    bel_version = '2.0.0'
    belstr = 'sec(a(CHEBI:"3-hydroxybutyrate"))'
    ast = bel.lang.partialparse.get_ast_obj(belstr, bel_version)

    print(ast.to_string())

    assert ast.to_string() == 'sec(a(CHEBI:3-hydroxybutyrate))'

