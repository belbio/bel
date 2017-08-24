import belpy
import pytest
from belpy.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_VERSION_UNDERLINED = '2_0_0'

SPECIFIED_ENDPOINT = 'example-endpoint'

B = belpy.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)

def test_computed_function_list():

    statement = 'list(p(HGNC:MAPK8), p(HGNC:MAPK9))'
    expected = ['list(p(HGNC:MAPK8), p(HGNC:MAPK9)) hasMember p(HGNC:MAPK8)',
                'list(p(HGNC:MAPK8), p(HGNC:MAPK9)) hasMember p(HGNC:MAPK9)']
    ast = B.parse(statement).ast

    assert sorted(expected) == B.computed(ast)


def test_computed_function_composite():

    statement = 'composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng))'
    expected = ['composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng)) hasMember a(SCHEM:Lipopolysaccharide)',
                'composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng)) hasMember p(MGI:Ifng)']
    ast = B.parse(statement).ast

    assert sorted(expected) == B.computed(ast)


def test_computed_function_complex():

    statement = 'complex(p(HGNC:AKT1), p(HGNC:EXAMPLE))'
    expected = ['complex(p(HGNC:AKT1), p(HGNC:EXAMPLE)) hasComponent p(HGNC:AKT1)',
                'complex(p(HGNC:AKT1), p(HGNC:EXAMPLE)) hasComponent p(HGNC:EXAMPLE)']
    ast = B.parse(statement).ast

    print(sorted(expected))
    print(sorted(B.computed(ast)))

    assert sorted(expected) == B.computed(ast)


def test_computed_function_deg():
    statement = 'deg(r(HGNC:MYC))'
    expected = ['deg(r(HGNC:MYC)) directlyDecreases r(HGNC:MYC)']
    ast = B.parse(statement).ast

    assert sorted(expected) == B.computed(ast)


def test_computed_function_act():
    statement = 'act(p(MGI:Met), ma(kin))'
    expected = ['p(MGI:Met) hasActivity act(p(MGI:Met), ma(kin))']
    ast = B.parse(statement).ast

    assert sorted(expected) == B.computed(ast)


def test_computed_function_var():
    statement = 'r(HGNC:CFTR, var("c.1521_1523delCTT"))'
    expected = ['r(HGNC:CFTR) hasVariant r(HGNC:CFTR, var("c.1521_1523delCTT"))']
    ast = B.parse(statement).ast

    assert sorted(expected) == B.computed(ast)


def test_computed_function_fus():
    statement = 'p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))'
    expected = ['p(HGNC:BCR) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))',
                'p(HGNC:JAK2) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))']
    ast = B.parse(statement).ast

    assert sorted(expected) == B.computed(ast)


def test_computed_function_pmod():
    statement = 'p(HGNC:AKT1, pmod(P, S, 473))'
    expected = ['p(HGNC:AKT1) hasModification p(HGNC:AKT1, pmod(P, S, 473))']
    ast = B.parse(statement).ast

    assert sorted(expected) == B.computed(ast)


# statement = 'p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))'
# expected = ['p(HGNC:BCR) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))',
#             'p(HGNC:JAK2) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))']
# ast = B.parse(statement).ast
# B.computed(ast)


