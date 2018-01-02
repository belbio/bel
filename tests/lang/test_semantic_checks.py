import bel.lang
from bel.Config import config

bo = bel.lang.bel.BEL(config['bel']['lang']['default_bel_version'], config['bel_api']['servers']['api_url'])

SPECIFIED_VERSION_UNDERLINED = config['bel']['lang']['default_bel_version']

#######################
# SEMANTIC TEST CASES #
#######################


def test_bad_function():
    s = 'atrocious(CHEBI:"nitric oxide") decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    bo.parse(s)
    print('1', bo.parse_valid, 'Msg', bo.validation_messages)
    assert not bo.parse_valid


def test_bad_relation():
    s = 'tloc(p(HGNC:CYCS), fromLoc(MESHCS:Mitochondria), toLoc(MESHCS:Cytoplasm)) hello bp(GOBP:"apoptotic process")'
    bo.parse(s)
    assert not bo.parse_valid
    print('2', bo.validation_messages)


def test_bad_subject():
    s = 'rnaAbundance(MGI:Mir21, extra)'
    bo.parse(s)
    print('3', bo.parse_valid, 'Msg', bo.validation_messages)
    assert not bo.parse_valid


def test_bad_object():
    s = 'r(fus(HGNC:TMPRSS2, "r.1_79", HGNC:ERG, "r.312_5034")) association path(SDIS:"prostate cancer", bad_arg)'
    bo.parse(s)
    assert not bo.parse_valid
    print('4', bo.validation_messages)


##############################
# VALID STATEMENT TEST CASES #
##############################
def test_valid_statements():
    stmts = [
        "p(HGNC:AKT1) increases p(HGNC:EGF)",
        'proteinAbundance(HGNC:AKT1, proteinModification(P, T, 308)) directlyIncreases activity(proteinAbundance(HGNC:AKT1), molecularActivity(DEFAULT:kin))',
        'a(CHEBI:"nitric oxide") decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))',
    ]

    for s in stmts:
        bo.parse(s)
        error_msgs = [msg for msg_level, msg in bo.validation_messages if msg_level == 'ERROR']
        assert error_msgs == []


##############################
# VALID STATEMENT TEST CASES #
##############################
def test_arg_values():
    stmts = [
        'activity(complexAbundance(SCOMP:"TORC2 Complex"), molecularActivity(DEFAULT:kin))'
    ]

    # TODO - Invalid Term - statement term SCOMP:"TORC2 Complex" allowable entity types: [] do not match API term entity types: ['Complex']

    for s in stmts:
        bo.parse(s)
        assert False
