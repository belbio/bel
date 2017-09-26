import bel_lang
import pytest
from bel_lang.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_VERSION_UNDERLINED = '2_0_0'

SPECIFIED_ENDPOINT = 'example-endpoint'

B = bel_lang.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)

#######################
# SEMANTIC TEST CASES #
#######################


def test_bad_function():
    s = 'atrocious(CHEBI:"nitric oxide") decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    v_obj = B.validate(s)
    assert not v_obj.valid


def test_bad_relationship():
    s = 'tloc(p(HGNC:CYCS), fromLoc(MESHCS:Mitochondria), toLoc(MESHCS:Cytoplasm)) hello bp(GOBP:"apoptotic process")'
    v_obj = B.validate(s)
    assert not v_obj.valid


def test_bad_subject():
    s = 'rnaAbundance(MGI:Mir21, extra)'
    v_obj = B.validate(s)
    assert not v_obj.valid


def test_bad_object():
    s = 'r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034")) association path(SDIS:"prostate cancer", bad_arg)'
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
