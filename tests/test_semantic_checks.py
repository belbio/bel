import belpy
import pytest
from belpy.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_VERSION_UNDERLINED = '2_0_0'

SPECIFIED_ENDPOINT = 'example-endpoint'

B = belpy.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)


#######################
# SEMANTIC TEST CASES #
#######################

def test_bad_function():
    s = 'atrocious(CHEBI:"nitric oxide") decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    v_obj = B.validate(s)
    assert v_obj.valid is False


def test_bad_relationship():
    s = 'tloc(p(HGNC:CYCS), fromLoc(MESHCS:Mitochondria), toLoc(MESHCS:Cytoplasm)) hello bp(GOBP:"apoptotic process")'
    v_obj = B.validate(s)
    assert v_obj.valid is False


def test_bad_subject():
    s = 'rnaAbundance(MGI:Mir21, extra)'
    v_obj = B.validate(s)
    assert v_obj.valid is False


def test_bad_object():
    s = 'r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034")) association path(SDIS:"prostate cancer", bad_arg)'
    v_obj = B.validate(s)
    assert v_obj.valid is False

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
