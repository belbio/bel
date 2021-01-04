# Standard Library
import json
import pprint

# Third Party
import pytest

# Local
import bel.lang.ast
from bel.schemas.bel import AssertionStr, ValidationError

# cSpell:disable


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("p(HGNC:AKT1)", "p(EG:207)"),
        ("complex(p(HGNC:IL12B), p(HGNC:IL12A))", "complex(p(EG:3592), p(EG:3593))"),
        (
            'complex(loc(GO:"extracellular space"), p(HGNC:IL12A), p(EG:207), p(HGNC:IL12B))',
            "complex(p(EG:207), p(EG:3592), p(EG:3593), loc(GO:0005615))",
        ),
        (
            'complex(p(HGNC:MTOR), a(CHEBI:"phosphatidic acid"), a(CHEBI:sirolimus))',
            "complex(a(CHEBI:16337), a(CHEBI:9168), p(EG:2475))",
        ),
        (
            'rxn(reactants(a(CHEBI:hypoxanthine), a(CHEBI:water), a(CHEBI:dioxygen)), products(a(CHEBI:xanthine), a(CHEBI:"hydrogen peroxide"))',
            "rxn(reactants(a(CHEBI:15377), a(CHEBI:15379), a(CHEBI:17368)), products(a(CHEBI:15318), a(CHEBI:16240)))",
        ),
        (
            "p(HGNC:MAPK1, pmod(Ph, Thr, 185), pmod(Ph, Tyr, 187), pmod(Ph))",
            "p(EG:5594, pmod(Ph), pmod(Ph, Thr, 185), pmod(Ph, Tyr, 187))",
        ),
        (
            "p(HGNC:KRAS, pmod(Palm, Cys), pmod(Ph, Tyr, 32))",
            "p(EG:3845, pmod(Palm, Cys), pmod(Ph, Tyr, 32))",
        ),
        (
            "p(HGNC:TP53, var(p.His168Arg), var(p.Arg249Ser))",
            "p(EG:7157, var(p.Arg249Ser), var(p.His168Arg))",
        ),
        (
            "p(HGNC:NFE2L2, pmod(Ac, Lys, 596), pmod(Ac, Lys, 599), loc(GO:nucleus))",
            "p(EG:4780, loc(GO:0005634), pmod(Ac, Lys, 596), pmod(Ac, Lys, 599))",
        ),
        (
            "path(DO:0080600!COVID-19)",
            "path(DO:0080600)",
        ),
    ],
)
def test_ast_canonicalization(test_input, expected):
    """Test AST canonicalization and sorting function arguments

    See issue: https://github.com/belbio/bel/issues/13
    """

    assertion = AssertionStr(entire=test_input)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.canonicalize()

    print("Canonicalized", ast.to_string())

    assert ast.to_string() == expected


def test_ast_canonicalization_2():
    """Test AST canonicalization and sorting function arguments

    See issue: https://github.com/belbio/bel/issues/13
    """

    test_input = "path(DO:0080600!COVID-19)"
    expected = "path(DO:0080600)"

    assertion = AssertionStr(entire=test_input)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.canonicalize()

    print("Canonicalized", ast.to_string())

    assert ast.to_string() == expected


def test_ast_subcomponents_simple():

    test_input = "path(DO:0080600!COVID-19)"
    assertion = AssertionStr(entire=test_input)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    subcomponents = ast.subcomponents()

    print("Subcomponents", subcomponents)

    assert subcomponents == ["path(DO:0080600!COVID-19)", "DO:0080600!COVID-19", "DO:COVID-19"]


def test_ast_nsarg():

    test_input = "HGNC:AKT1"

    assertion = AssertionStr(entire=test_input)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    ast.canonicalize()
    print("Canonicalized", ast.to_string())

    assert ast.to_string() == "EG:207"
