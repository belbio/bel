import bel_lang
from bel_lang.defaults import defaults

bel_obj = bel_lang.bel.BEL(defaults['bel_version'], defaults['belapi_endpoint'])

# TODO Add test for specified canonical_targets - need to make sure BEL.bio API endpoint is updated to handle this querystring arg


def test_canon_one():

    statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'

    expected = 'activity(p(EG:207), ma(GO:"kinase activity"))'

    bel_obj.parse(statement)

    bel_obj.canonicalize()

    assert bel_obj.ast.to_string() == expected


def test_canon_two():

    statement = 'act(p(HGNC:MYD88), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:MYD88),p(HGNC:IRAK1),p(HGNC:IRAK4))'

    expected = 'activity(p(EG:4615), ma(GO:"catalytic activity")) directlyIncreases complexAbundance(p(EG:4615), p(EG:3654), p(EG:51135))'

    bel_obj.parse(statement)

    bel_obj.canonicalize()

    assert bel_obj.ast.to_string() == expected


def test_decanon_one():

    statement = 'act(p(EG:207), ma(GO:"kinase activity"))'

    expected = 'activity(p(HGNC:AKT1), ma(GO:"kinase activity"))'

    bel_obj.parse(statement)

    bel_obj.decanonicalize()

    assert bel_obj.ast.to_string() == expected


def test_decanon_two():

    statement = 'act(p(EG:4615), ma(GO:"catalytic activity")) directlyIncreases complex(p(EG:4615), p(EG:3654), p(EG:51135))'

    expected = 'activity(p(HGNC:MYD88), ma(GO:"catalytic activity")) directlyIncreases complexAbundance(p(HGNC:MYD88), p(HGNC:IRAK1), p(HGNC:IRAK4))'

    bel_obj.parse(statement)

    bel_obj.decanonicalize()

    print(bel_obj.ast.to_string())

    assert bel_obj.ast.to_string() == expected
