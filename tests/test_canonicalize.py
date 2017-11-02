import bel_lang
import pytest
from bel_lang.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_ENDPOINT = 'example-endpoint'

B_OBJ = bel_lang.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)


def test_canon_one():

    expected = {'subject': 'act(p(EG:207), ma(GO:"kinase activity"))',
                'relation': None,
                'object': None}

    statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'
    parse_obj = B_OBJ.parse(statement)

    canonicalized = B_OBJ.canonicalize(parse_obj.ast)

    assert canonicalized == expected


def test_canon_two():

    expected = {'subject': 'act(p(EG:4615), ma(GO:"catalytic activity"))',
                'relation': 'directlyIncreases',
                'object': 'complex(p(EG:4615), p(EG:3654), p(EG:51135))'}

    statement = 'act(p(HGNC:MYD88), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:MYD88),p(HGNC:IRAK1),p(HGNC:IRAK4))'
    parse_obj = B_OBJ.parse(statement)

    canonicalized = B_OBJ.canonicalize(parse_obj.ast)

    assert canonicalized == expected
