import bel_lang
from bel_lang.defaults import defaults

bel_obj = bel_lang.BEL(defaults['bel_version'], defaults['belapi_endpoint'])

SPECIFIED_VERSION_UNDERLINED = defaults['bel_version'].replace('.', '_')

#######################
# SEMANTIC TEST CASES #
#######################


def test_bad_function():
    s = 'atrocious(CHEBI:"nitric oxide") decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


def test_bad_relationship():
    s = 'tloc(p(HGNC:CYCS), fromLoc(MESHCS:Mitochondria), toLoc(MESHCS:Cytoplasm)) hello bp(GOBP:"apoptotic process")'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


def test_bad_subject():
    s = 'rnaAbundance(MGI:Mir21, extra)'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid


def test_bad_object():
    s = 'r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034")) association path(SDIS:"prostate cancer", bad_arg)'
    parse_obj = bel_obj.parse(s)
    assert not parse_obj.valid

##############################
# VALID STATEMENT TEST CASES #
##############################


def test_valid_statements():
    pass
