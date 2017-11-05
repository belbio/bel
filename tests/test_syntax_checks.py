import bel_lang
import pytest
from bel_lang.exceptions import MissingParenthesis

from bel_lang.defaults import defaults

bel_obj = bel_lang.BEL(defaults['bel_version'], defaults['belapi_endpoint'])

SPECIFIED_VERSION_UNDERLINED = defaults['bel_version'].replace('.', '_')

#####################
# SYNTAX TEST CASES #
#####################


def test_extra_right_paren():
    s = 'a(CHEBI:"nitric oxide")) decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    with pytest.raises(MissingParenthesis):
        bel_obj.parse(s)


def test_extra_left_paren():
    s = 'a((CHEBI:"oxygen atom")'
    with pytest.raises(MissingParenthesis):
        bel_obj.parse(s)


def test_missing_parens():
    s = 'act(p(MGI:Akt1), ma(kin)) decreases MGI:Cdkn1b'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


def test_bad_namespace():
    s = 'abundance(CHEBI:"prostaglandin J2":TEST)'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


def test_arg_outside():
    s = 'act(p(HGNC:FOXO1)) ma(tscript)'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


def test_no_comma_between_args():
    s = 'act(p(HGNC:FOXO3) ma(tscript)) =| r(HGNC:MIR21)'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


def test_no_func_given():
    s = 'act(p(MGI:Akt1), ma(kin)) decreases (MGI:Cdkn1b)'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


##############################
# VALID STATEMENT TEST CASES #
##############################


def test_valid_statements():
    pass
