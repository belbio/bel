import bel_lang
import pytest
from bel_lang.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_VERSION_UNDERLINED = '2_0_0'

SPECIFIED_ENDPOINT = 'example-endpoint'

B = bel_lang.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)

#####################
# SYNTAX TEST CASES #
#####################


def test_extra_right_paren():
    s = 'a(CHEBI:"nitric oxide")) decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    with pytest.raises(MissingParenthesis):
        v_obj = B.validate(s)


def test_extra_left_paren():
    s = 'a((CHEBI:"oxygen atom")'
    with pytest.raises(MissingParenthesis):
        v_obj = B.validate(s)


def test_missing_parens():
    s = 'act(p(MGI:Akt1), ma(kin)) decreases MGI:Cdkn1b'
    v_obj = B.validate(s)
    assert not v_obj.valid


def test_bad_namespace():
    s = 'abundance(CHEBI:"prostaglandin J2":TEST)'
    v_obj = B.validate(s)
    assert not v_obj.valid


def test_arg_outside():
    s = 'act(p(HGNC:FOXO1)) ma(tscript)'
    v_obj = B.validate(s)
    assert not v_obj.valid


def test_no_comma_between_args():
    s = 'act(p(HGNC:FOXO3) ma(tscript)) =| r(HGNC:MIR21)'
    v_obj = B.validate(s)
    assert not v_obj.valid


def test_no_func_given():
    s = 'act(p(MGI:Akt1), ma(kin)) decreases (MGI:Cdkn1b)'
    v_obj = B.validate(s)
    assert not v_obj.valid


##############################
# VALID STATEMENT TEST CASES #
##############################


def test_valid_statements():
    list_of_valid_statements = [
        'example',
        'example',
        'example',
        'example',
        'example',
        'example',
    ]


# stmts = B.load('dev/bel2_test_statements.txt', preprocess=True)
#
# for s in stmts:
#     print('\n\n\n\n')
#
#     print(s)
#     p = B.parse(s)
#     st = B.flatten(p.ast)
#
#     print(st)
#     print(s)
#     assert st == s

# statement = 'a(CHEBI:"nitric oxide") decreases (a(CHEBI:"nitric oxide") decreases (a(CHEBI:"nitric oxide") decreases r(HGNC:CFTR, ' \
#             'var("c.1521_1523delCTT"))))'
# print(statement)
