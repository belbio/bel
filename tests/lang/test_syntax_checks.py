import bel.lang.belobj
from bel.Config import config

bo = bel.lang.belobj.BEL(config['bel']['lang']['default_bel_version'], config['bel_api']['servers']['api_url'])

SPECIFIED_VERSION_UNDERLINED = config['bel']['lang']['default_bel_version']

#####################
# SYNTAX TEST CASES #
#####################


def test_extra_right_paren():
    s = 'a(CHEBI:"nitric oxide")) decreases r(HGNC:CFTR, var("c.1521_1523delCTT"))'

    bo.parse(s)
    print(bo.validation_messages)


def test_extra_left_paren():
    s = 'a((CHEBI:"oxygen atom")'

    bo.parse(s)
    print(bo.validation_messages)


def test_missing_parens():
    s = 'act(p(MGI:Akt1), ma(kin)) decreases MGI:Cdkn1b'

    bo.parse(s)
    print(bo.validation_messages)


def test_bad_namespace():
    s = 'abundance(CHEBI:"prostaglandin J2":TEST)'

    bo.parse(s)
    assert not bo.parse_valid


def test_arg_outside():
    s = 'act(p(HGNC:FOXO1)) ma(tscript)'
    bo.parse(s)
    assert not bo.parse_valid


def test_no_comma_between_args():
    s = 'act(p(HGNC:FOXO3) ma(tscript)) =| r(HGNC:MIR21)'

    bo.parse(s)
    assert not bo.parse_valid


def test_no_func_given():
    s = 'act(p(MGI:Akt1), ma(kin)) decreases (MGI:Cdkn1b)'

    bo.parse(s)
    assert not bo.parse_valid


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
        assert bo.parse_valid
