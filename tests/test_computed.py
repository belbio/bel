import bel_lang
import pytest
from bel_lang.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_ENDPOINT = 'example-endpoint'

B = bel_lang.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)


def test_computed_list_function():

    s = 'list(p(HGNC:MAPK8), p(HGNC:MAPK9))'
    expected = ['{} hasMember p(HGNC:MAPK8)'.format(s),
                '{} hasMember p(HGNC:MAPK9)'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result

    s = 'list(p(HGNC:CAV1, pmod(Ph, Y, 14)), p(HGNC:SLC2A4))'
    expected = ['{} hasMember p(HGNC:CAV1, pmod(Ph, Y, 14))'.format(s),
                '{} hasMember p(HGNC:SLC2A4)'.format(s),
                'p(HGNC:CAV1) hasModification p(HGNC:CAV1, pmod(Ph, Y, 14))']
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result

    s = 'list(p(MGI:Il6), bp(MESHPP:Apoptosis), path(MESHD:Inflammation))'
    expected = ['{} hasMember p(MGI:Il6)'.format(s),
                '{} hasMember bp(MESHPP:Apoptosis)'.format(s),
                '{} hasMember path(MESHD:Inflammation)'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result


def test_computed_composite_function():

    s = 'composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng))'
    expected = ['{} hasMember a(SCHEM:Lipopolysaccharide)'.format(s),
                '{} hasMember p(MGI:Ifng)'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result

    s = 'composite(p(HGNC:IL6), complex(GOCC:"interleukin-23 complex"))'
    expected = ['{} hasMember p(HGNC:IL6)'.format(s),
                '{} hasMember complex(GOCC:"interleukin-23 complex")'.format(s),
                'complex(GOCC:"interleukin-23 complex") hasComponent GOCC:"interleukin-23 complex"']
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result

    s = 'compositeAbundance(proteinAbundance(HGNC:TGFB1), proteinAbundance(HGNC:IL6))'
    expected = ['{} hasMember proteinAbundance(HGNC:TGFB1)'.format(s),
                '{} hasMember proteinAbundance(HGNC:IL6)'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result

    s = 'composite(p(SFAM:"Histone H3 Family", pmod(Ac)), p(SFAM:"Histone H4 Family", pmod(Ac)))'
    expected = ['{} hasMember p(SFAM:"Histone H3 Family", pmod(Ac))'.format(s),
                '{} hasMember p(SFAM:"Histone H4 Family", pmod(Ac))'.format(s),
                'p(SFAM:"Histone H3 Family") hasModification p(SFAM:"Histone H3 Family", pmod(Ac))',
                'p(SFAM:"Histone H4 Family") hasModification p(SFAM:"Histone H4 Family", pmod(Ac))']
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result


def test_computed_complex_function():

    s = 'complex(p(HGNC:AKT1), p(HGNC:EXAMPLE))'
    expected = ['{} hasComponent p(HGNC:AKT1)'.format(s),
                '{} hasComponent p(HGNC:EXAMPLE)'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result


def test_computed_deg_function():
    s = 'deg(r(HGNC:MYC))'
    expected = ['{} directlyDecreases r(HGNC:MYC)'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result


def test_computed_act_function():
    s = 'act(p(MGI:Met), ma(kin))'
    expected = ['p(MGI:Met) hasActivity {}'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result


def test_computed_var_function():
    s = 'r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    expected = ['r(HGNC:CFTR) hasVariant {}'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result


def test_computed_fus_function():
    s = 'p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))'
    expected = ['p(HGNC:BCR) hasFusion {}'.format(s),
                'p(HGNC:JAK2) hasFusion {}'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result


def test_computed_pmod_function():
    s = 'p(HGNC:AKT1, pmod(P, S, 473))'
    expected = ['p(HGNC:AKT1) hasModification {}'.format(s)]
    result = B.computed(B.parse(s).ast)
    assert sorted(expected) == result
